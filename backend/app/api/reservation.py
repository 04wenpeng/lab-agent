from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.reservation import (
    AdminCancelRequest,
    AdminRescheduleRequest,
    AuditReservationRequest,
    ModifyReservationRequest,
    ReservationCreateRequest,
)
from app.services import reservation_service

router = APIRouter(prefix="/reservation", tags=["预约相关接口"])


@router.get("/list")
def get_reservation_page_list(
    page: int = 1,
    page_size: int = 10,
    status: int | None = None,
    mine: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = reservation_service.get_reservation_page_list(
        db, current_user, page, page_size, status, mine
    )
    return Response.success(data=res)


@router.get("/{reservation_id}/detail")
def get_reservation_detail(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """单条预约的详细信息（本人或管理员可看）"""
    return Response.success(
        data=reservation_service.get_reservation_detail(
            db, current_user, reservation_id
        )
    )


@router.post("")
def create_reservation(
    data: ReservationCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = reservation_service.create_reservation(db, current_user, data)
    # 新提交的预约优先交给 AI 自动审核；AI 不可用或拿不准时保持在「待审核」，由管理员处理
    if res is not None:
        background_tasks.add_task(reservation_service.ai_review_reservation, res.id)
    return Response.success()


@router.put("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservation_service.cancel_reservation(db, current_user, reservation_id)
    return Response.success()


@router.put("/{reservation_id}/audit")
def audit_reservation(
    reservation_id: int,
    data: AuditReservationRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    reservation_service.audit_reservation(db, reservation_id, data.status, current_user)
    return Response.success()


@router.put("/{reservation_id}/modify")
def modify_reservation(
    reservation_id: int,
    data: ModifyReservationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """学生自己改预约：只能改还没开始的，且有次数上限（系统设置里可调）"""
    reservation_service.modify_reservation(db, current_user, reservation_id, data)
    return Response.success(message="修改成功")


@router.put("/{reservation_id}/check-in")
def check_in(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """签到：已通过的预约，开始前 30 分钟到结束之间可以签"""
    reservation_service.check_in_reservation(db, current_user, reservation_id)
    return Response.success(message="签到成功")


@router.put("/{reservation_id}/admin-cancel")
def admin_cancel(
    reservation_id: int,
    data: AdminCancelRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员强制取消（待审核、已通过都可以）"""
    reservation_service.admin_cancel(db, reservation_id, current_user, data.reason)
    return Response.success()


@router.put("/{reservation_id}/admin-reschedule")
def admin_reschedule(
    reservation_id: int,
    data: AdminRescheduleRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员调整预约时间（待审核、已通过都可以）"""
    reservation_service.admin_reschedule(db, reservation_id, current_user, data)
    return Response.success()
