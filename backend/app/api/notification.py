from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import notification_service

router = APIRouter(prefix="/notification", tags=["站内通知"])


@router.get("/list")
def list_notifications(
    page: int = 1,
    page_size: int = 10,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Response.success(
        data=notification_service.list_notifications(
            db, current_user, page, page_size, unread_only
        )
    )


@router.get("/unread-count")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Response.success(data=notification_service.unread_count(db, current_user))


@router.put("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification_service.mark_read(db, current_user, notification_id)
    return Response.success()


@router.put("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification_service.mark_all_read(db, current_user)
    return Response.success()
