"""操作日志：把写操作记下来，方便事后查是谁改的。"""

import re

from sqlalchemy.orm import Session

from app.common.response import PageResponse
from app.models.operation_log import OperationLog
from app.models.user import User

# 路径 → 人话。按「方法 + 路径正则」从具体到宽泛匹配
_ACTIONS: list[tuple[str, str, str]] = [
    ("POST", r"^/api/auth/register$", "注册账号"),
    ("POST", r"^/api/auth/apply-admin$", "提交管理员申请"),
    ("PUT", r"^/api/user/password$", "修改自己的密码"),
    ("PUT", r"^/api/user/me$", "修改个人信息"),
    ("POST", r"^/api/user/\d+/reset-password$", "重置用户密码"),
    ("POST", r"^/api/user/\d+/admin-application$", "审核管理员申请"),
    ("POST", r"^/api/user$", "新增用户"),
    ("PUT", r"^/api/user/\d+$", "编辑用户"),
    ("DELETE", r"^/api/user/\d+$", "删除用户"),
    ("POST", r"^/api/lab$", "新增实验室"),
    ("PUT", r"^/api/lab/\d+/equipments$", "修改实验室设备"),
    ("PUT", r"^/api/lab/\d+$", "编辑实验室"),
    ("DELETE", r"^/api/lab/\d+$", "删除实验室"),
    ("POST", r"^/api/equipment$", "新增设备"),
    ("PUT", r"^/api/equipment/\d+$", "编辑设备"),
    ("DELETE", r"^/api/equipment/\d+$", "删除设备"),
    ("POST", r"^/api/equipment-catalog$", "新增设备库条目"),
    ("PUT", r"^/api/equipment-catalog/\d+$", "编辑设备库条目"),
    ("DELETE", r"^/api/equipment-catalog/\d+$", "删除设备库条目"),
    ("POST", r"^/api/reservation$", "提交预约"),
    ("PUT", r"^/api/reservation/\d+/audit$", "审核预约"),
    ("PUT", r"^/api/reservation/\d+/admin-cancel$", "强制取消预约"),
    ("PUT", r"^/api/reservation/\d+/admin-reschedule$", "调整预约时间"),
    ("PUT", r"^/api/reservation/\d+/cancel$", "取消自己的预约"),
    ("PUT", r"^/api/reservation/\d+/modify$", "修改自己的预约"),
    ("PUT", r"^/api/reservation/\d+/check-in$", "签到"),
    ("POST", r"^/api/announcement$", "发布公告"),
    ("PUT", r"^/api/announcement/\d+$", "编辑公告"),
    ("DELETE", r"^/api/announcement/\d+$", "删除公告"),
    ("PUT", r"^/api/setting/reservation-rules$", "修改预约规则"),
    ("PUT", r"^/api/ai/config/me$", "保存个人 AI 配置"),
    ("DELETE", r"^/api/ai/config/me$", "删除个人 AI 配置"),
    ("POST", r"^/api/ai/config/default$", "修改系统默认 AI 配置"),
    ("PUT", r"^/api/notification/read-all$", "全部通知已读"),
    ("PUT", r"^/api/notification/\d+/read$", "通知标记已读"),
    ("POST", r"^/api/files/upload$", "上传文件"),
]

# 这些路径太琐碎，不记录（避免日志被刷屏）
_SKIP_PATHS = (
    "/api/notification/unread-count",
    "/api/user/admin-applications/count",
)


def describe_action(method: str, path: str) -> str | None:
    """把请求翻译成一句人话；返回 None 表示不记录"""
    for skip in _SKIP_PATHS:
        if path.startswith(skip):
            return None
    for m, pattern, label in _ACTIONS:
        if method == m and re.match(pattern, path):
            return label
    return None


def record(
    db: Session,
    user: User | None,
    action: str,
    method: str,
    path: str,
    status_code: int,
    detail: str | None = None,
    ip: str | None = None,
):
    db.add(
        OperationLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            action=action,
            method=method,
            path=path[:200],
            status_code=status_code,
            detail=(detail or "")[:500] or None,
            ip=ip,
        )
    )
    db.commit()


def list_logs(
    db: Session, page: int, page_size: int, keywords: str | None = None
):
    query = db.query(OperationLog)
    if keywords:
        like = f"%{keywords}%"
        query = query.filter(
            (OperationLog.action.like(like))
            | (OperationLog.username.like(like))
            | (OperationLog.path.like(like))
        )
    total = query.count()
    items = (
        query.order_by(OperationLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = [
        {
            "id": item.id,
            "user_id": item.user_id,
            "username": item.username or "未登录",
            "action": item.action,
            "method": item.method,
            "path": item.path,
            "status_code": item.status_code,
            "detail": item.detail,
            "ip": item.ip,
            "create_time": item.create_time,
        }
        for item in items
    ]
    return PageResponse(list=result, total=total)
