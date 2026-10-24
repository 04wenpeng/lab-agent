from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreateRequest,
    AnnouncementUpdateRequest,
)
from app.services import announcement_service

router = APIRouter(prefix="/announcement", tags=["公告"])


@router.get("/list")
def list_announcements(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """公告列表（所有人可见），每条带 can_delete 告诉前端要不要显示删除按钮"""
    return Response.success(
        data=announcement_service.list_announcements(db, current_user, limit)
    )


@router.post("")
def create_announcement(
    data: AnnouncementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布公告（管理员）"""
    return Response.success(
        data=announcement_service.create_announcement(db, current_user, data)
    )


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑公告：作者本人或主管理员"""
    return Response.success(
        data=announcement_service.update_announcement(
            db, current_user, announcement_id, data
        )
    )


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除公告：主管理员可删任意，普通管理员只能删自己的"""
    announcement_service.delete_announcement(db, current_user, announcement_id)
    return Response.success()
