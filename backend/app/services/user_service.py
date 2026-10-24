from operator import or_
from datetime import datetime

import secrets

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import (
    PRIMARY_ADMIN_USERNAME,
    PasswordUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from sqlalchemy.orm import Session

from app.utils import password
from app.utils.password import hash_password, verify_password
from app.services import notification_service

# 主管理员（初始管理员）：账号固定，其他管理员不能删除/降级/禁用
INITIAL_ADMIN_USERNAME = PRIMARY_ADMIN_USERNAME
INITIAL_ADMIN_PASSWORD = "123456"


def ensure_initial_admin():
    """保证主管理员账号 123456 一定存在。

    - 账号不存在：用初始密码 123456 重新创建（例如被直接改库删掉、或从旧库导入时缺失）；
    - 账号存在但不是管理员 / 被禁用：恢复成管理员且启用；
    - 密码不动，避免覆盖用户自己改过的密码。
    """
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.username == INITIAL_ADMIN_USERNAME)
            .first()
        )
        if user is None:
            user = User(
                username=INITIAL_ADMIN_USERNAME,
                password=hash_password(INITIAL_ADMIN_PASSWORD),
                name="初始管理员",
                role="admin",
                status=1,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(
                f"[init] 主管理员 {INITIAL_ADMIN_USERNAME} 不存在，已创建（密码 {INITIAL_ADMIN_PASSWORD}），请登录后尽快修改"
            )
            return user
        changed = False
        if user.role != "admin":
            user.role = "admin"
            changed = True
        if user.status != 1:
            user.status = 1
            changed = True
        if changed:
            db.commit()
            print(f"[init] 主管理员 {INITIAL_ADMIN_USERNAME} 已恢复为管理员并启用")
        return user
    finally:
        db.close()


def get_user_info(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


def update_user_info(db: Session, user: User, data: UserUpdateRequest):
    user_dict = data.model_dump(
        exclude_none=True, exclude={"role", "status"}
    )  # pydatic对象转换成字典
    print(user_dict)
    for field, value in user_dict.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_password(db: Session, user: User, data: PasswordUpdateRequest):
    """修改密码"""
    if not verify_password(data.old_password, user.password):
        raise BusinessException(message="原密码错误")
    if data.old_password == data.new_password:
        raise BusinessException(message="新密码不能跟原密码相同")
    user.password = hash_password(data.new_password)
    db.commit()


def _random_password(length: int = 8) -> str:
    """生成一个好念的随机密码（去掉容易看错的 0/O/1/l/I）"""
    alphabet = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def admin_reset_password(
    db: Session, target_id: int, current_user: User, new_password: str | None = None
) -> str:
    """管理员帮别人重置密码，返回重置后的密码（用于告诉对方）"""
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise BusinessException(message="用户不存在")
    if target.id == current_user.id:
        raise BusinessException(message="这是你自己的账号，请用「修改密码」")
    if target.username == PRIMARY_ADMIN_USERNAME:
        raise BusinessException(message="不能重置主管理员的密码")
    if target.role == "admin" and current_user.username != PRIMARY_ADMIN_USERNAME:
        raise BusinessException(message="只有主管理员可以重置其他管理员的密码")

    pwd = (new_password or "").strip() or _random_password()
    if len(pwd) < 6:
        raise BusinessException(message="密码至少 6 位")
    target.password = hash_password(pwd)
    db.commit()

    notification_service.notify(
        db,
        target.id,
        "你的密码已被管理员重置",
        f"管理员重置了你的登录密码，如果不知道新密码，请联系管理员。",
        None,
        "",
    )
    db.commit()
    return pwd


def get_user_page_list(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    pending_admin: int | None = None,
):
    """分页模糊查询用户列表"""
    # select * from user where username like '%张%' or name like '%张%';
    query = db.query(User)
    if keywords:
        query = query.filter(
            or_(User.username.ilike(f"%{keywords}%"), User.name.ilike(f"%{keywords}%"))
        )
    if pending_admin is not None:
        query = query.filter(User.pending_admin == pending_admin)
    total = query.count()
    items = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        list=[UserResponse.model_validate(item) for item in items], total=total
    )


def create_user(db: Session, data: UserCreateRequest):
    """新增用户"""
    exist = db.query(User).filter(User.username == data.username).first()
    if exist:
        raise BusinessException(message="账号已存在")

    user = User(
        username=data.username,
        password=hash_password(data.password),
        name=data.name,
        role=data.role,
        email=data.email,
        phone=data.phone,
        avatar=data.avatar,
        status=data.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def _is_primary(user: User) -> bool:
    return user.username == PRIMARY_ADMIN_USERNAME


def _ensure_not_primary_admin(user: User, action: str):
    """主管理员账号受保护：其他管理员不能删除、降级、禁用"""
    if _is_primary(user):
        raise BusinessException(message=f"「{user.name}」是主管理员账号，不可{action}")


def _ensure_admin_operable_by(current_user: User, target: User, action: str):
    """管理员账号之间的操作：主管理员可以管所有人，普通管理员只能管学生"""
    if target.role == "admin" and not _is_primary(current_user):
        raise BusinessException(message=f"只有主管理员可以{action}管理员账号")


def _ensure_not_last_admin(db: Session, user: User, action: str):
    """系统里必须至少留一个管理员，避免把自己（或唯一管理员）降级/删掉后再也进不来"""
    if user.role != "admin":
        return
    admin_count = db.query(User).filter(User.role == "admin").count()
    if admin_count <= 1:
        raise BusinessException(message=f"系统至少需要保留一个管理员，无法{action}唯一的管理员")


def update_user(db: Session, user_id: int, data: UserUpdateRequest, current_user: User):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在")
    payload = data.model_dump(exclude_none=True)
    new_role = payload.get("role")
    role_changed = bool(new_role) and new_role != user.role
    # 升级（学生→管理员）和降级（管理员→学生）都只允许主管理员操作
    if role_changed and not _is_primary(current_user):
        raise BusinessException(message="只有主管理员可以调整用户角色")
    demote = bool(new_role) and new_role != "admin"
    if demote and user.role == "admin":
        # 主管理员不允许被降级；管理员之间只有主管理员能操作
        _ensure_not_primary_admin(user, "降级为普通用户")
        _ensure_admin_operable_by(current_user, user, "降级")
        _ensure_not_last_admin(db, user, "降级")
    if payload.get("status") == 0:
        _ensure_not_primary_admin(user, "禁用")
    for filed, value in payload.items():
        setattr(user, filed, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def delete_user(db: Session, user_id: int, currut_user: User):
    """删除用户"""
    if user_id == currut_user.id:
        raise BusinessException(message="不能删除当前登录的账号")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在")
    _ensure_not_primary_admin(user, "删除")
    _ensure_admin_operable_by(currut_user, user, "删除")
    _ensure_not_last_admin(db, user, "删除")
    # 先清掉相关通知，避免主管理员铃铛里留下「幽灵申请」
    notification_service.clear_user_notifications(db, user.id)
    db.delete(user)
    db.commit()


def list_admin_applications(db: Session, current_user: User) -> PageResponse:
    """待审核的「注册为管理员」申请（只有主管理员能看）"""
    if not _is_primary(current_user):
        raise BusinessException(message="只有主管理员可以查看管理员申请")
    items = (
        db.query(User)
        .filter(User.pending_admin == 1)
        .order_by(User.id.desc())
        .all()
    )
    return PageResponse(
        list=[UserResponse.model_validate(item) for item in items], total=len(items)
    )


def count_admin_applications(db: Session, current_user: User) -> int:
    if not _is_primary(current_user):
        return 0
    return db.query(User).filter(User.pending_admin == 1).count()


def audit_admin_application(
    db: Session, user_id: int, approve: bool, current_user: User
) -> UserResponse:
    """主管理员审核「注册为管理员」的申请。

    通过：变成管理员并启用；拒绝：降为普通学生并启用（还能正常用系统）。
    """
    if not _is_primary(current_user):
        raise BusinessException(message="只有主管理员可以审核管理员申请")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在")
    if user.pending_admin != 1:
        raise BusinessException(message="该账号没有待审核的管理员申请")

    user.role = "admin" if approve else "student"
    user.status = 1
    user.pending_admin = 0
    if approve:
        user.apply_rejected_at = None
    else:
        # 记录拒绝时间，7 天内不允许再次申请
        user.apply_rejected_at = datetime.now()

    notification_service.notify(
        db,
        user.id,
        "管理员申请已通过" if approve else "管理员申请未通过",
        "你的管理员申请已通过，现在可以用「管理员登录」进入系统。"
        if approve
        else "你的管理员申请未通过，账号已作为普通学生启用，可以继续预约实验室。",
        link="/manager/home",
    )
    # 主管理员那边「新的管理员申请」的通知已经处理完了，标成已读，铃铛数字才和待审数量对得上
    notification_service.mark_ref_read(db, user.id)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
