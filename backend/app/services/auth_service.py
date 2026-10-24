import math
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.common.exceptions import BusinessException
from app.database import get_db
from app.models.user import User
from app.schemas.user import APPLY_COOLDOWN_DAYS, PRIMARY_ADMIN_USERNAME, UserResponse
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.auth import LoginResponse
from app.services import notification_service
from app.utils.password import verify_password, hash_password
from app.utils.jwt import create_access_token


def login(db: Session, data: LoginRequest):
    # 根据用户账号查询数据库
    user = db.query(User).filter(User.username == data.username).first()

    # 判断账号和密码是否正确
    if not user or not verify_password(data.password, user.password):
        raise BusinessException(message="账号或密码错误")
    # 申请管理员但还没审核通过的账号：给出更明确的提示
    if user.pending_admin == 1 and user.status != 1:
        raise BusinessException(message="管理员申请正在等待主管理员审核，通过后即可登录")
    # 验证账号的状态
    if user.status != 1:
        raise BusinessException(message="账号被禁用")
    # 登录入口与账号角色必须匹配：学生在「管理员登录」里登不进去，反之亦然
    if data.role and user.role != data.role:
        if data.role == "admin":
            raise BusinessException(message="该账号不是管理员账号，请使用普通登录")
        raise BusinessException(message="该账号是管理员账号，请使用管理员登录")
    # 创建token
    token = create_access_token(user.id)
    return LoginResponse(token=token, user=UserResponse.model_validate(user))


def register(db: Session, data: RegisterRequest):
    # 根据用户账号查询数据库
    user = db.query(User).filter(User.username == data.username).first()
    if user:
        raise BusinessException(message="账号已存在")

    # 注册为管理员 = 提交申请：先建一个禁用的学生账号，主管理员通过后才变成管理员
    apply_admin = data.role == "admin"
    note = (data.apply_note or "").strip()
    if apply_admin and len(note) < 5:
        raise BusinessException(message="请填写申请说明（至少 5 个字），主管理员审核时会看")
    user_model = User(
        username=data.username,
        password=hash_password(data.password),
        name=data.name or data.username,
        role="student",
        status=0 if apply_admin else 1,
        pending_admin=1 if apply_admin else 0,
        apply_time=datetime.now() if apply_admin else None,
        apply_note=note if apply_admin else None,
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    # 通知主管理员：有新申请待审核
    if apply_admin:
        _notify_primary(db, user_model)


def _notify_primary(db: Session, applicant: User):
    """给主管理员发一条「新的管理员申请」通知"""
    primary = db.query(User).filter(User.username == PRIMARY_ADMIN_USERNAME).first()
    if not primary:
        return
    note = (applicant.apply_note or "").strip()
    detail = f"申请说明：{note[:60]}{'…' if len(note) > 60 else ''}\n" if note else ""
    notification_service.notify(
        db,
        primary.id,
        "新的管理员申请",
        f"「{applicant.name}」（账号 {applicant.username}）申请成为管理员，请到「管理员申请」页面审核。\n{detail}",
        link="/manager/admin-apply",
        ref_user_id=applicant.id,
    )
    db.commit()


def apply_admin(db: Session, user: User, note: str):
    """已登录的学生申请成为管理员。

    和注册时的申请区别：**不动 status**，所以他还能继续以学生身份用系统，
    只是多了一个待审核标记；审核通过后 role 才会变成 admin。
    被拒绝后 7 天内不能再次申请，避免反复骚扰主管理员。
    """
    if user.role == "admin":
        raise BusinessException(message="你已经是管理员了")
    if user.pending_admin == 1:
        raise BusinessException(message="你已经提交过申请，请等待主管理员审核")
    if user.apply_rejected_at:
        retry_at = user.apply_rejected_at + timedelta(days=APPLY_COOLDOWN_DAYS)
        if datetime.now() < retry_at:
            days = max(
                1, math.ceil((retry_at - datetime.now()).total_seconds() / 86400)
            )
            raise BusinessException(
                message=f"上次申请未通过，请在 {retry_at:%Y-%m-%d} 之后再申请（约 {days} 天后）"
            )
    text = (note or "").strip()
    if len(text) < 5:
        raise BusinessException(message="请填写申请说明（至少 5 个字），主管理员审核时会看")
    user.pending_admin = 1
    user.apply_time = datetime.now()
    user.apply_note = text
    db.commit()
    db.refresh(user)
    _notify_primary(db, user)
