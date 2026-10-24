"""公告：管理员发布，所有人可见；删除权限按「主管理员 > 作者本人 > 其他人」区分。"""

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreateRequest,
    AnnouncementResponse,
    AnnouncementUpdateRequest,
)
from app.schemas.user import PRIMARY_ADMIN_USERNAME


def _is_primary(user: User) -> bool:
    return user.username == PRIMARY_ADMIN_USERNAME


def _can_delete(viewer: User, author_id: int) -> bool:
    if viewer.role != "admin":
        return False
    if _is_primary(viewer):
        return True
    return viewer.id == author_id


def list_announcements(
    db: Session, current_user: User, limit: int = 50
) -> list[AnnouncementResponse]:
    items = (
        db.query(Announcement)
        .order_by(Announcement.id.desc())
        .limit(limit)
        .all()
    )
    result = []
    is_admin = current_user.role == "admin"
    for item in items:
        res = AnnouncementResponse.model_validate(item)
        # 普通用户只看标题/内容/时间，不返回发布人信息
        res.author_name = (item.author.name if item.author else None) if is_admin else None
        res.is_primary_author = bool(is_admin and item.author and _is_primary(item.author))
        res.can_delete = _can_delete(current_user, item.author_id)
        res.can_edit = res.can_delete
        result.append(res)
    return result


def create_announcement(
    db: Session, current_user: User, data: AnnouncementCreateRequest
) -> AnnouncementResponse:
    if current_user.role != "admin":
        raise BusinessException(message="只有管理员可以发布公告")
    item = Announcement(
        title=data.title.strip(),
        content=data.content.strip(),
        author_id=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    res = AnnouncementResponse.model_validate(item)
    res.author_name = current_user.name
    res.is_primary_author = _is_primary(current_user)
    res.can_delete = True
    res.can_edit = True
    return res


def update_announcement(
    db: Session, current_user: User, announcement_id: int, data: AnnouncementUpdateRequest
) -> AnnouncementResponse:
    """编辑公告：规则同删除 —— 作者本人或主管理员"""
    item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not item:
        raise BusinessException(message="公告不存在")
    if not _can_delete(current_user, item.author_id):
        raise BusinessException(
            message=(
                "只有管理员可以修改公告"
                if current_user.role != "admin"
                else "只有主管理员可以修改别人的公告"
            ),
            code=403,
        )
    if data.title is not None:
        title = data.title.strip()
        if not title:
            raise BusinessException(message="标题不能为空")
        item.title = title
    if data.content is not None:
        content = data.content.strip()
        if not content:
            raise BusinessException(message="内容不能为空")
        item.content = content
    db.commit()
    db.refresh(item)
    res = AnnouncementResponse.model_validate(item)
    res.author_name = item.author.name if item.author else None
    res.is_primary_author = bool(item.author and _is_primary(item.author))
    res.can_delete = True
    res.can_edit = True
    return res


def delete_announcement(db: Session, current_user: User, announcement_id: int):
    item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not item:
        raise BusinessException(message="公告不存在")
    if not _can_delete(current_user, item.author_id):
        raise BusinessException(
            message=(
                "只有管理员可以删除公告"
                if current_user.role != "admin"
                else "只有主管理员可以删除别人的公告"
            ),
            code=403,
        )
    db.delete(item)
    db.commit()
