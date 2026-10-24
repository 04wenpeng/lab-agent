from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.common.response import Response
from app.models.user import User
from app.dependencies.auth import get_current_admin, get_current_user
from app.schemas.user import (
    AdminApplicationAuditRequest,
    AdminResetPasswordRequest,
    PasswordUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services import user_service
from app.services.user_service import get_user_info
from app.database import get_db

router = APIRouter(prefix="/user", tags=["用户信息接口"])


@router.get("/me")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return Response.success(data=user_service.get_user_info(current_user))


@router.put("/me")
def update_user_info(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户信息"""
    res = user_service.update_user_info(db, current_user, data)
    return Response.success(data=res)


@router.put("/password")
def update_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_service.update_password(db, current_user, data)
    return Response.success()


@router.get("/list")
def get_user_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    pending_admin: int | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.get_user_page_list(
        db, page, page_size, keywords, pending_admin
    )
    return Response.success(data=res)


@router.post("")
def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.create_user(db, data)
    return Response.success(data=res)


@router.post("/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    data: AdminResetPasswordRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员帮用户重置密码，返回新密码（不填则自动生成 8 位）"""
    pwd = user_service.admin_reset_password(db, user_id, current_user, data.new_password)
    return Response.success(data={"password": pwd}, message="密码已重置")


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.update_user(db, user_id, data, current_user)
    return Response.success(data=res)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user_service.delete_user(db, user_id, current_user)
    return Response.success()


@router.get("/admin-applications")
def list_admin_applications(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """待审核的管理员申请（只有主管理员能看）"""
    return Response.success(data=user_service.list_admin_applications(db, current_user))


@router.get("/admin-applications/count")
def count_admin_applications(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return Response.success(
        data=user_service.count_admin_applications(db, current_user)
    )


@router.post("/{user_id}/admin-application")
def audit_admin_application(
    user_id: int,
    data: AdminApplicationAuditRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """主管理员审核「注册为管理员」的申请：approve=true 通过，false 拒绝（降为普通学生）"""
    res = user_service.audit_admin_application(db, user_id, data.approve, current_user)
    return Response.success(data=res)
