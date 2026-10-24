from datetime import datetime

from operator import or_
from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.schemas.equipment import EquipmentResponse
from app.schemas.lab import (
    LabCreateRequest,
    LabEquipmentItem,
    LabResponse,
    LabUpdateRequest,
)
from app.services import reservation_service
from sqlalchemy.orm import Session


def _fill_live_status(db: Session, labs: list[LabResponse]):
    """给列表补上「当前状态」：使用中 / 空闲 / 已关闭，以及今天的预约条数。

    只看「整间实验室」的预约（equipment_id 为空）——按项目规则，
    设备预约只占用设备，不占用整间实验室。
    """
    if not labs:
        return labs
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current = now.strftime("%H:%M")
    lab_ids = [lab.id for lab in labs]
    rows = (
        db.query(Reservation)
        .filter(
            Reservation.lab_id.in_(lab_ids),
            Reservation.date == today,
            Reservation.equipment_id.is_(None),
            Reservation.status.in_([0, 1]),  # 待审核、已通过都算占用
        )
        .all()
    )
    busy_until: dict[int, str] = {}
    today_count: dict[int, int] = {}
    for row in rows:
        today_count[row.lab_id] = today_count.get(row.lab_id, 0) + 1
        if row.start_time <= current < row.end_time:
            busy_until[row.lab_id] = max(busy_until.get(row.lab_id, row.end_time), row.end_time)

    for lab in labs:
        lab.today_count = today_count.get(lab.id, 0)
        # 状态为 0（关闭）时，无论是否有预约都不该显示「使用中」
        if lab.status == 1 and lab.id in busy_until:
            lab.busy_now = True
            lab.busy_until = busy_until[lab.id]
        else:
            lab.busy_now = False
            lab.busy_until = None
    return labs


def get_lab_page_list(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    status: int | None = None,
):
    """分页模糊查询列表"""
    # select * from lab where name like '%计算机%';
    query = db.query(Lab)
    if keywords:
        query = query.filter(Lab.name.ilike(f"%{keywords}%"))
    # 注意用 is not None：status=0（关闭）也要能筛出来
    if status is not None:
        query = query.filter(Lab.status == status)
    total = query.count()
    items = (
        query.order_by(Lab.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    labs = [LabResponse.model_validate(item) for item in items]
    return PageResponse(list=_fill_live_status(db, labs), total=total)


def get_lab(db: Session, lab_id: int):
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    return _fill_live_status(db, [LabResponse.model_validate(lab)])[0]


def create_lab(db: Session, data: LabCreateRequest):
    """新增"""
    exist = db.query(Lab).filter(Lab.name == data.name).first()
    if exist:
        raise BusinessException(message="实验室已存在")
    lab = Lab(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def update_lab(db: Session, lab_id: int, data: LabUpdateRequest):
    """更新；如果把实验室改成「关闭」，顺手取消它之后还没开始的预约"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    was_open = lab.status == 1
    payload = data.model_dump(exclude_none=True)
    for filed, value in payload.items():
        setattr(lab, filed, value)
    db.commit()
    db.refresh(lab)

    canceled = 0
    if was_open and lab.status == 0:
        canceled = reservation_service.cancel_reservations_for_lab(
            db, lab.id, f"实验室「{lab.name}」已关闭，系统自动取消"
        )
    res = LabResponse.model_validate(lab)
    res.canceled_count = canceled
    return res


def delete_lab(db: Session, lab_id: int):
    """删除"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    # 连带清理没有预约记录的设备，避免留下孤儿设备
    for equipment in db.query(Equipment).filter(Equipment.lab_id == lab_id).all():
        used = db.query(Reservation).filter(
            Reservation.equipment_id == equipment.id
        ).count()
        if used:
            raise BusinessException(
                message=f"实验室下的设备「{equipment.name}」还有 {used} 条预约记录，不能删除实验室"
            )
        db.delete(equipment)
    db.delete(lab)
    db.commit()


def save_lab_equipments(
    db: Session, lab_id: int, items: list[LabEquipmentItem]
) -> list[EquipmentResponse]:
    """保存某个实验室的设备清单（前端提交完整列表，后端按 id 增/改/删）。"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")

    existing = {
        eq.id: eq
        for eq in db.query(Equipment).filter(Equipment.lab_id == lab_id).all()
    }
    keep_ids: set[int] = set()

    # 同一实验室内设备名不能重复
    names = [item.name.strip() for item in items]
    if len(set(names)) != len(names):
        raise BusinessException(message="同一个实验室里设备名称不能重复")

    for item in items:
        name = item.name.strip()
        if not name:
            continue
        if item.id and item.id in existing:
            equipment = existing[item.id]
            equipment.name = name
            equipment.spec = item.spec
            equipment.quantity = item.quantity
            equipment.status = item.status
            equipment.catalog_id = item.catalog_id
            if item.description is not None:
                equipment.description = item.description
            keep_ids.add(item.id)
        else:
            equipment = Equipment(
                lab_id=lab_id,
                name=name,
                spec=item.spec,
                quantity=item.quantity,
                status=item.status,
                description=item.description,
                catalog_id=item.catalog_id,
            )
            db.add(equipment)
            db.flush()
            keep_ids.add(equipment.id)

    # 列表里没有的 = 被删掉了；有预约记录的设备不允许删
    for equipment_id, equipment in existing.items():
        if equipment_id in keep_ids:
            continue
        used = db.query(Reservation).filter(
            Reservation.equipment_id == equipment_id
        ).count()
        if used:
            raise BusinessException(
                message=f"设备「{equipment.name}」还有 {used} 条预约记录，不能删除"
            )
        db.delete(equipment)

    db.commit()
    result = []
    for equipment in (
        db.query(Equipment).filter(Equipment.lab_id == lab_id).order_by(Equipment.id).all()
    ):
        res = EquipmentResponse.model_validate(equipment)
        res.lab_name = lab.name
        result.append(res)
    return result
