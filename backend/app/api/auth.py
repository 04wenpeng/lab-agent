from fastapi import APIRouter, Depends, Request
from app.common.response import Response
from app.models.user import User
from app.schemas.auth import ApplyAdminRequest, LoginRequest
from app.schemas.auth import RegisterRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services import auth_service, operation_log_service

router = APIRouter(prefix="/auth", tags=["权限验证"])


@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """登录"""
    result = auth_service.login(db, data)
    # 登录成功后记一条操作日志（中间件拿不到登录人，这里显式记）
    login_user = db.query(User).filter(User.username == data.username).first()
    operation_log_service.record(
        db,
        login_user,
        "登录",
        "POST",
        "/api/auth/login",
        200,
        detail=f"role={data.role}",
        ip=request.client.host if request.client else None,
    )
    # 返回信息
    return Response.success(
        message="登录成功",
        data=result,
    )


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册"""
    auth_service.register(db, data)
    # 返回信息
    return Response.success(message="注册成功")


@router.post("/apply-admin")
def apply_admin(
    data: ApplyAdminRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """已登录的普通学生申请成为管理员（要写申请说明，提交后等主管理员审核）"""
    auth_service.apply_admin(db, current_user, data.note)
    return Response.success(message="申请已提交，等待主管理员审核")
