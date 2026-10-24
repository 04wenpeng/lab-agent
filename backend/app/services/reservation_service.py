import asyncio
import json
import re
import threading
import traceback
from datetime import datetime, timedelta

from openai import OpenAI
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.database import SessionLocal
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.reservation import (
    AdminRescheduleRequest,
    ModifyReservationRequest,
    ReservationCreateRequest,
    ReservationResponse,
)
from app.schemas.user import PRIMARY_ADMIN_USERNAME
from app.services import (
    ai_config_service,
    kb_service,
    notification_service,
    setting_service,
)

# 「查冲突 + 写入」的临界区锁：单进程内串行化，避免两个人同时订到同一时段
_booking_lock = threading.Lock()


def get_reservation_page_list(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    status: int | None = None,
    mine: bool = False,
):
    """查询预约的记录（管理员默认看全部，前端传 mine=true 时只看自己的）"""
    query = db.query(Reservation)
    if mine or current_user.role != "admin":
        query = query.filter(Reservation.user_id == current_user.id)
    if status is not None:
        query = query.filter(Reservation.status == status)
    total = query.count()
    items = (
        query.order_by(Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # 批量取审核人姓名，避免逐条查
    auditor_ids = {item.audit_by for item in items if item.audit_by}
    auditors = {}
    if auditor_ids:
        auditors = {
            user.id: user.name
            for user in db.query(User).filter(User.id.in_(auditor_ids)).all()
        }

    result = []
    for item in items:
        res = ReservationResponse.model_validate(item)
        res.user_name = item.user.name if item.user else None
        res.lab_name = item.lab.name if item.lab else None
        res.equipment_name = item.equipment.name if item.equipment else None
        res.type = "设备" if item.equipment_id else "实验室"
        res.audit_by_name = auditors.get(item.audit_by)
        result.append(res)

    return PageResponse(list=result, total=total)


def _find_conflict(db: Session, data: ReservationCreateRequest) -> Reservation | None:
    """同实验室、同一天、时段重叠、且仍然有效的预约"""
    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id,
        Reservation.date == data.date,
        Reservation.status.in_([0, 1]),  # 0待审核，1已通过
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
    )
    if data.equipment_id:
        query = query.filter(Reservation.equipment_id == data.equipment_id)
    else:
        query = query.filter(Reservation.equipment_id.is_(None))
    return query.first()


def create_reservation(db: Session, current_user: User, data: ReservationCreateRequest):
    """创建预约记录"""
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    if data.date < current_date:
        raise BusinessException(message="预约日期不能小于当前的日期")
    if data.end_time < data.start_time:
        raise BusinessException(message="预约的结束时间不能小于开始时间")
    if data.date == current_date and data.start_time < current_time:
        raise BusinessException(message="预约开始时间不能小于当前的时间")
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭")
    if lab.open_time and data.start_time < lab.open_time:
        raise BusinessException(message="预约时间不能早于实验室的开放时间")
    if lab.close_time and data.end_time > lab.close_time:
        raise BusinessException(message="预约时间不能晚于实验室的关闭时间")

    # ===== 预约规则（管理员可在「系统设置」里调）=====
    rules = setting_service.get_reservation_rules(db)
    try:
        date_obj = datetime.strptime(data.date, "%Y-%m-%d").date()
    except ValueError:
        raise BusinessException(message="预约日期格式不正确，应为 2026-01-01")
    ahead_days = (date_obj - datetime.now().date()).days
    if ahead_days > rules.advance_days:
        raise BusinessException(message=f"最多只能提前 {rules.advance_days} 天预约")
    try:
        start_h, start_m = map(int, data.start_time.split(":"))
        end_h, end_m = map(int, data.end_time.split(":"))
    except (ValueError, AttributeError):
        raise BusinessException(message="时间格式不正确，应为 09:00")
    minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m)
    if minutes <= 0:
        raise BusinessException(message="预约的结束时间必须晚于开始时间")
    if minutes / 60 > rules.max_hours:
        raise BusinessException(message=f"单次预约最长 {rules.max_hours} 小时")
    if data.people < 1:
        raise BusinessException(message="使用人数至少 1 人")
    if lab.capacity and data.people > lab.capacity:
        raise BusinessException(message=f"使用人数不能超过实验室容量（{lab.capacity} 人）")
    same_day_count = (
        db.query(Reservation)
        .filter(
            Reservation.user_id == current_user.id,
            Reservation.date == data.date,
            Reservation.status.in_([0, 1]),
        )
        .count()
    )
    if same_day_count >= rules.daily_limit:
        raise BusinessException(
            message=f"每人每天最多预约 {rules.daily_limit} 次，{data.date} 已经约满了"
        )

    # equipment_id 不为空 则表示这次是预约的实验室设备
    if data.equipment_id:
        equipment = (
            db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        )
        if not equipment:
            raise BusinessException(message="实验室设备不存在")
        if equipment.status != 1:
            raise BusinessException(message="实验室设备正在维修")

    # 结束前面这些只读查询开启的事务，保证重新查冲突时读到的是最新数据
    db.commit()

    # 加锁后再查一次：两个人同时提交时，只有一个能进去写
    with _booking_lock:
        conflict = _find_conflict(db, data)
        if conflict:
            raise BusinessException(
                message=f"该时段已被预约（{conflict.start_time}-{conflict.end_time}）"
            )

        reservation_model = Reservation(
            user_id=current_user.id,
            lab_id=data.lab_id,
            equipment_id=data.equipment_id,
            date=data.date,
            start_time=data.start_time,
            end_time=data.end_time,
            people=data.people,
            remark=data.remark,
            status=0,
        )
        db.add(reservation_model)
        db.commit()
        db.refresh(reservation_model)
        return reservation_model


# 明显的违规关键词：命中就直接拒绝，不依赖模型判断（小模型容易漏）
_VIOLATION_KEYWORDS = [
    "汽油", "明火", "爆炸", "燃烧", "易燃", "剧毒", "放射性",
    "聚餐", "火锅", "烧烤", "喝酒", "聚会", "party",
    "睡觉", "打游戏", "打牌", "直播", "带货",
    "转卖", "倒卖", "代占", "占座",
]


def _keyword_violation(remark: str | None) -> str | None:
    text = (remark or "").strip()
    if not text:
        return None
    for keyword in _VIOLATION_KEYWORDS:
        if keyword in text:
            return keyword
    return None


def _parse_ai_decision(text: str):
    """从模型输出里解析 {approve, reason}；解析不出来返回 (None, '')"""
    if not text:
        return None, ""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None, ""
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None, ""
    approve = data.get("approve")
    if isinstance(approve, str):
        approve = approve.strip().lower() in ("true", "yes", "1", "通过")
    if not isinstance(approve, bool):
        return None, ""
    return approve, str(data.get("reason") or "").strip()


def ai_review_reservation(reservation_id: int):
    """普通实验室预约（不含设备）交给 AI 自动审核。

    - 拿不到可用模型 / 模型输出解析不了 → 保持「待审核」，交给管理员，不影响正常流程；
    - 通过：状态置为已通过，审核来源记 ai；拒绝：置为已拒绝并写原因。
    """
    db = SessionLocal()
    try:
        item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not item or item.status != 0:
            return

        slot = f"{item.date} {item.start_time}-{item.end_time}"

        # 1) 先过关键词：命中明显的违规内容直接拒绝，不依赖模型
        keyword = _keyword_violation(item.remark)
        if keyword:
            _finish_ai_review(
                db,
                item,
                approve=False,
                reason=f"备注包含违规内容：{keyword}",
                slot=slot,
            )
            return

        try:
            cfg = ai_config_service.resolve_config(db, item.user)
        except Exception:
            return  # 没有可用模型，留给管理员

        knowledge = ""
        try:
            knowledge = kb_service.search(f"{item.lab.name} 预约规则 开放时间")
        except Exception:
            knowledge = ""

        open_time = item.lab.open_time or "08:00"
        close_time = item.lab.close_time or "18:00"
        equipment = item.equipment.name if item.equipment else "（整间实验室）"
        prompt = f"""你是实验室预约审核员。系统已经替你做完了机械校验，下面这些结论是**确定成立**的，不要质疑：
- 预约时间 {slot} 落在实验室开放时间 {open_time}-{close_time} 之内：已通过
- 该时段没有和其他有效预约冲突：已通过
- 预约人账号状态正常：已通过

你只需要判断一件事：**备注里有没有明确违规的内容**。

预约信息：
- 实验室：{item.lab.name}
- 设备：{equipment}
- 时间：{slot}
- 备注：{item.remark or '（空）'}

判断规则（严格照做，不要自己加码）：
只有当备注里**明确出现**下面某一类内容时，才 approve=false：
1. 明火、汽油、酒精之外的易燃易爆物、爆炸、燃烧
2. 剧毒、危险化学品滥用、放射性物质
3. 违规电器、私自改装电路
4. 商用、转卖、收费、代占座牟利
5. 与实验无关的活动（聚餐、睡觉、打游戏、直播带货）

其它所有情况都必须 approve=true，包括：
空备注、只写几个字、写「测试」「调试」「占位」「课程实验」「写论文」「跑程序」「开会」等。
**拿不准的时候一律 approve=true。**

只输出一行 JSON，不要输出任何多余文字：
{{"approve": true, "reason": "备注正常"}}"""

        client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url, timeout=30)
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            timeout=30,
        )
        approve, reason = _parse_ai_decision(
            (resp.choices[0].message.content or "").strip()
        )
        if approve is None:
            print(f"[ai-review] 模型输出无法解析，转人工：#{reservation_id}")
            return

        # 模型思考的这几秒里，管理员可能已经手动处理了 —— 重新读一次，别覆盖人工审核结果
        db.refresh(item)
        if item.status != 0:
            print(f"[ai-review] #{reservation_id} 已被管理员处理，跳过 AI 结果")
            return

        _finish_ai_review(db, item, approve=approve, reason=reason, slot=slot)
    except Exception:
        traceback.print_exc()
    finally:
        db.close()


def _finish_ai_review(db: Session, item: Reservation, approve: bool, reason: str, slot: str):
    """把 AI 的结论写进预约记录，并通知预约人"""
    item.status = 1 if approve else 2
    item.audit_by = None
    item.audit_time = datetime.now()
    item.audit_source = "ai"
    if not approve:
        item.cancel_reason = reason or "AI 审核未通过"

    notification_service.notify(
        db,
        item.user_id,
        "预约已通过（AI 自动审核）" if approve else "预约未通过（AI 审核）",
        f"「{item.lab.name}」{slot} 的预约"
        + (
            "已由 AI 自动审核通过，可以按时使用。"
            if approve
            else f"未通过审核：{reason or '不符合预约规则'}"
        ),
        item.id,
        "/manager/my-reservation",
    )
    db.commit()
    print(f"[ai-review] #{item.id} -> {'通过' if approve else '拒绝'}（{reason}）")


def get_reservation_detail(db: Session, current_user: User, reservation_id: int):
    """单条预约详情：本人或管理员可看"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if current_user.role != "admin" and item.user_id != current_user.id:
        raise BusinessException(message="无权查看别人的预约", code=403)
    res = ReservationResponse.model_validate(item)
    res.user_name = item.user.name if item.user else None
    res.lab_name = item.lab.name if item.lab else None
    res.equipment_name = item.equipment.name if item.equipment else None
    res.type = "设备" if item.equipment_id else "实验室"
    if item.audit_by:
        auditor = db.query(User).filter(User.id == item.audit_by).first()
        res.audit_by_name = auditor.name if auditor else None
    return res


def modify_reservation(
    db: Session,
    current_user: User,
    reservation_id: int,
    data: ModifyReservationRequest,
):
    """学生自己改还没开始的预约（有次数上限，规则与提交时一致）"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.user_id != current_user.id:
        raise BusinessException(message="只能修改自己的预约", code=403)
    if item.status not in (0, 1):
        raise BusinessException(message="当前状态不能修改（已拒绝/已取消的预约改不了）")

    now = datetime.now()
    try:
        start_at = datetime.strptime(f"{item.date} {item.start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise BusinessException(message="预约时间格式异常，请联系管理员")
    if now >= start_at:
        raise BusinessException(message="预约已经开始了，不能自己修改（找管理员改约）")

    rules = setting_service.get_reservation_rules(db)
    if item.modify_count >= rules.modify_limit:
        raise BusinessException(
            message=f"每条预约最多修改 {rules.modify_limit} 次，这条已经改过了"
        )

    # 提交后 N 天内才能改（0 = 不限）
    if rules.modify_window_days > 0 and item.create_time:
        deadline = item.create_time + timedelta(days=rules.modify_window_days)
        if now > deadline:
            raise BusinessException(
                message=f"预约提交后 {rules.modify_window_days} 天内才能自己修改，这条已经超期（找管理员改约）"
            )

    # 离开场太近就不能自己改（0 = 不限）
    if rules.modify_before_days > 0:
        remain = start_at - now
        if remain < timedelta(days=rules.modify_before_days):
            raise BusinessException(
                message=f"预约开始前 {rules.modify_before_days} 天内不能再自己修改（找管理员改约）"
            )

    # —— 下面这些校验和提交预约时保持一致 ——
    lab = db.query(Lab).filter(Lab.id == item.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭")
    try:
        date_obj = datetime.strptime(data.date, "%Y-%m-%d").date()
        start_h, start_m = map(int, data.start_time.split(":"))
        end_h, end_m = map(int, data.end_time.split(":"))
    except (ValueError, AttributeError):
        raise BusinessException(message="日期或时间格式不正确")
    if (date_obj - now.date()).days > rules.advance_days:
        raise BusinessException(message=f"最多只能提前 {rules.advance_days} 天预约")
    if date_obj < now.date():
        raise BusinessException(message="预约日期不能小于当前的日期")
    minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m)
    if minutes <= 0:
        raise BusinessException(message="结束时间必须晚于开始时间")
    if minutes / 60 > rules.max_hours:
        raise BusinessException(message=f"单次预约最长 {rules.max_hours} 小时")
    if lab.open_time and data.start_time < lab.open_time:
        raise BusinessException(message="预约时间不能早于实验室的开放时间")
    if lab.close_time and data.end_time > lab.close_time:
        raise BusinessException(message="预约时间不能晚于实验室的关闭时间")
    people = item.people if data.people is None else data.people
    if people < 1:
        raise BusinessException(message="使用人数至少 1 人")
    if lab.capacity and people > lab.capacity:
        raise BusinessException(message=f"使用人数不能超过实验室容量（{lab.capacity} 人）")

    # 冲突：同一个实验室、同一天、时段重叠、仍有效、且不是自己这条
    conflict = (
        db.query(Reservation)
        .filter(
            Reservation.id != item.id,
            Reservation.lab_id == item.lab_id,
            Reservation.date == data.date,
            Reservation.status.in_([0, 1]),
            Reservation.start_time < data.end_time,
            Reservation.end_time > data.start_time,
        )
    )
    if item.equipment_id:
        conflict = conflict.filter(Reservation.equipment_id == item.equipment_id)
    else:
        conflict = conflict.filter(Reservation.equipment_id.is_(None))
    hit = conflict.first()
    if hit:
        raise BusinessException(
            message=f"新时段与已有预约冲突（{hit.start_time}-{hit.end_time}）"
        )

    # 每日次数：换到新日期时不能超过上限（不含自己这条）
    if data.date != item.date:
        same_day = (
            db.query(Reservation)
            .filter(
                Reservation.id != item.id,
                Reservation.user_id == current_user.id,
                Reservation.date == data.date,
                Reservation.status.in_([0, 1]),
            )
            .count()
        )
        if same_day >= rules.daily_limit:
            raise BusinessException(
                message=f"每人每天最多预约 {rules.daily_limit} 次，{data.date} 已经约满了"
            )

    old_slot = f"{item.date} {item.start_time}-{item.end_time}"
    item.date = data.date
    item.start_time = data.start_time
    item.end_time = data.end_time
    if data.people is not None:
        item.people = data.people
    if data.remark is not None:
        item.remark = data.remark
    item.modify_count = (item.modify_count or 0) + 1
    db.commit()
    db.refresh(item)

    new_slot = f"{item.date} {item.start_time}-{item.end_time}"
    print(f"[modify] #{item.id} {old_slot} -> {new_slot}（第 {item.modify_count} 次）")
    return item


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    """学生取消预约：还没开始的都能取消，但「开始前 N 天」之后要管理员处理"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.user_id != current_user.id:
        raise BusinessException(message="无权限", code=403)
    if item.status not in (0, 1):
        raise BusinessException(message="当前状态无法取消")

    now = datetime.now()
    try:
        start_at = datetime.strptime(f"{item.date} {item.start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise BusinessException(message="预约时间格式异常，请联系管理员")
    if now >= start_at:
        raise BusinessException(message="预约已经开始，不能自己取消（找管理员处理）")

    rules = setting_service.get_reservation_rules(db)
    if rules.cancel_before_days > 0 and start_at - now < timedelta(days=rules.cancel_before_days):
        raise BusinessException(
            message=f"预约开始前 {rules.cancel_before_days} 天内不能自己取消（找管理员处理）"
        )

    item.status = 3
    item.cancel_reason = "本人取消"
    item.audit_time = datetime.now()
    db.commit()


def audit_reservation(
    db: Session, reservation_id: int, status: int, current_user: User
):
    """管理员审核预约，并记录审核人/审核时间，同时给预约人发站内通知"""
    if status not in [1, 2]:
        raise BusinessException(message="审核状态错误")
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.status != 0:
        raise BusinessException(message="当前状态不支持审核")
    item.status = status
    item.audit_by = current_user.id
    item.audit_time = datetime.now()
    item.audit_source = "admin"

    lab_name = item.lab.name if item.lab else "实验室"
    slot = f"{item.date} {item.start_time}-{item.end_time}"
    if status == 1:
        notification_service.notify(
            db,
            item.user_id,
            "预约已通过",
            f"「{lab_name}」{slot} 的预约已通过审核，可以按时使用。",
            item.id,
            "/manager/my-reservation",
        )
    else:
        notification_service.notify(
            db,
            item.user_id,
            "预约被拒绝",
            f"「{lab_name}」{slot} 的预约未通过审核。如有疑问请联系管理员。",
            item.id,
            "/manager/my-reservation",
        )
    db.commit()


def admin_cancel(
    db: Session, reservation_id: int, current_user: User, reason: str | None = None
):
    """管理员强制取消预约（待审核、已通过都能取消），并通知预约人"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.status not in (0, 1):
        raise BusinessException(message="当前状态无法取消")
    item.status = 3
    item.cancel_reason = reason
    item.audit_by = current_user.id
    item.audit_time = datetime.now()
    item.audit_source = "admin"

    lab_name = item.lab.name if item.lab else "实验室"
    slot = f"{item.date} {item.start_time}-{item.end_time}"
    notification_service.notify(
        db,
        item.user_id,
        "预约已被管理员取消",
        f"「{lab_name}」{slot} 的预约已被取消。原因：{reason or '未说明'}",
        item.id,
        "/manager/my-reservation",
    )
    db.commit()


def admin_reschedule(
    db: Session,
    reservation_id: int,
    current_user: User,
    data: AdminRescheduleRequest,
):
    """管理员调整预约时间（待审核、已通过都能改），并通知预约人"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.status not in (0, 1):
        raise BusinessException(message="当前状态无法调整")
    if data.end_time <= data.start_time:
        raise BusinessException(message="结束时间必须晚于开始时间")
    now = datetime.now()
    if data.date < now.strftime("%Y-%m-%d"):
        raise BusinessException(message="调整后的日期不能早于今天")

    lab = db.query(Lab).filter(Lab.id == item.lab_id).first()
    if lab:
        if lab.open_time and data.start_time < lab.open_time:
            raise BusinessException(message="调整后的时间早于实验室开放时间")
        if lab.close_time and data.end_time > lab.close_time:
            raise BusinessException(message="调整后的时间晚于实验室关闭时间")

    old_slot = f"{item.date} {item.start_time}-{item.end_time}"
    new_slot = f"{data.date} {data.start_time}-{data.end_time}"

    # 与新时段冲突检查（排除自己这条），同样进临界区
    db.commit()
    with _booking_lock:
        query = db.query(Reservation).filter(
            Reservation.lab_id == item.lab_id,
            Reservation.date == data.date,
            Reservation.status.in_([0, 1]),
            Reservation.id != item.id,
            Reservation.start_time < data.end_time,
            Reservation.end_time > data.start_time,
        )
        if item.equipment_id:
            query = query.filter(Reservation.equipment_id == item.equipment_id)
        else:
            query = query.filter(Reservation.equipment_id.is_(None))
        conflict = query.first()
        if conflict:
            raise BusinessException(
                message=f"新时段与已有预约冲突（{conflict.start_time}-{conflict.end_time}）"
            )

        item.date = data.date
        item.start_time = data.start_time
        item.end_time = data.end_time
        if data.remark is not None:
            item.remark = data.remark
        item.cancel_reason = data.reason
        item.audit_by = current_user.id
        item.audit_time = datetime.now()
        item.audit_source = "admin"

        lab_name = lab.name if lab else "实验室"
        notification_service.notify(
            db,
            item.user_id,
            "预约时间已调整",
            f"「{lab_name}」的预约由 {old_slot} 调整为 {new_slot}。原因：{data.reason or '排期调整'}",
            item.id,
            "/manager/my-reservation",
        )
        db.commit()


def check_in_reservation(db: Session, current_user: User, reservation_id: int):
    """学生签到：已通过、未签到、且在签到时间窗内（开始前 30 分钟 ~ 结束）"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.user_id != current_user.id:
        raise BusinessException(message="只能给自己的预约签到", code=403)
    if item.status != 1:
        raise BusinessException(message="只有已通过的预约才能签到")
    if item.checked_in:
        raise BusinessException(message="这次预约已经签过到了")
    now = datetime.now()
    try:
        start_at = datetime.strptime(f"{item.date} {item.start_time}", "%Y-%m-%d %H:%M")
        end_at = datetime.strptime(f"{item.date} {item.end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise BusinessException(message="预约时间格式异常，请联系管理员")
    if now < start_at - timedelta(minutes=30):
        raise BusinessException(message="还没到签到时间，可以提前 30 分钟签到")
    if now > end_at:
        raise BusinessException(message="预约已结束，无法签到")
    item.checked_in = 1
    item.check_in_time = now
    db.commit()


def cancel_reservations_for_lab(db: Session, lab_id: int, reason: str) -> int:
    """实验室关闭时，把这个实验室之后还没开始的预约全部取消并通知预约人"""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    lab_name = lab.name if lab else "实验室"
    items = (
        db.query(Reservation)
        .filter(Reservation.lab_id == lab_id, Reservation.status.in_([0, 1]))
        .all()
    )
    count = 0
    for item in items:
        if item.date < today or (item.date == today and item.end_time <= current_time):
            continue  # 已经过去的不管
        item.status = 3
        item.cancel_reason = reason
        item.audit_source = "system"
        item.audit_time = now
        count += 1
        notification_service.notify(
            db,
            item.user_id,
            "预约已被取消（实验室关闭）",
            f"「{lab_name}」{item.date} {item.start_time}-{item.end_time} 的预约，"
            f"因实验室关闭被系统自动取消。",
            item.id,
            "/manager/my-reservation",
        )
    if count:
        db.commit()
    return count


def expire_pending_reservations():
    """批量取消过期的预约单；并把「通过了但没签到」的标记成违约"""
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M")
        items = db.query(Reservation).filter(Reservation.status == 0).all()
        changed = False
        for item in items:
            if item.date < today or (item.date == today and item.end_time <= time):
                item.status = 3
                changed = True

        # 违约：已通过、没签到、时间已过
        approved = (
            db.query(Reservation)
            .filter(
                Reservation.status == 1,
                Reservation.checked_in == 0,
                Reservation.no_show == 0,
            )
            .all()
        )
        for item in approved:
            if item.date < today or (item.date == today and item.end_time <= time):
                item.no_show = 1
                changed = True
                # 有违约就通知所有管理员
                lab_name = item.lab.name if item.lab else "实验室"
                user_name = item.user.name if item.user else "学生"
                for admin_user in (
                    db.query(User).filter(User.role == "admin", User.status == 1).all()
                ):
                    notification_service.notify(
                        db,
                        admin_user.id,
                        "有预约未签到（违约）",
                        f"{user_name} 预约的「{lab_name}」{item.date} "
                        f"{item.start_time}-{item.end_time} 未签到，已记一次违约。",
                        item.id,
                        "/manager/stats",
                    )

        if changed:
            db.commit()

        # 违约次数超限的自动拉黑（禁用账号）
        rules = setting_service.get_reservation_rules(db)
        counts = {}
        for item in (
            db.query(Reservation)
            .filter(Reservation.no_show == 1)
            .all()
        ):
            counts[item.user_id] = counts.get(item.user_id, 0) + 1
        for user_id, count in counts.items():
            if count < rules.no_show_limit:
                continue
            user = db.query(User).filter(User.id == user_id).first()
            if not user or user.status == 0:
                continue
            if user.username == PRIMARY_ADMIN_USERNAME:
                continue  # 主管理员不自动禁用
            user.status = 0
            notification_service.notify(
                db,
                user.id,
                "账号已被限制预约",
                f"你累计 {count} 次预约未签到，账号已被禁用，请找主管理员处理。",
                None,
                "",
            )
            db.commit()
            print(f"[no-show] 用户 {user.username} 违约 {count} 次，已禁用")
    finally:
        db.close()


async def run_expire_scan():
    """1分钟扫描一次执行业务"""
    try:
        while True:
            await asyncio.to_thread(expire_pending_reservations)
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        return
