"""站内通知：预约状态变化时给预约人留一条消息，前端顶栏铃铛能看到未读数。"""

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationListResponse, NotificationResponse


def notify(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    reservation_id: int | None = None,
    link: str | None = None,
    ref_user_id: int | None = None,
):
    """写一条通知（不单独提交，跟着调用方的事务一起提交）

    link 是点这条通知后前端跳转的路由，比如 /manager/my-reservation。
    ref_user_id 是这条通知「关于谁」，用户被删除时可以据此清理。
    """
    db.add(
        Notification(
            user_id=user_id,
            title=title,
            content=content,
            reservation_id=reservation_id,
            link=link,
            ref_user_id=ref_user_id,
            is_read=0,
        )
    )


def clear_user_notifications(db: Session, user_id: int):
    """用户被删除时：删掉他收到的通知，以及别人收到的、关于他的通知"""
    db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.query(Notification).filter(Notification.ref_user_id == user_id).delete()


def mark_ref_read(db: Session, ref_user_id: int):
    """某个用户的申请被处理了：把「关于他」的未读通知标成已读，铃铛数字才对得上"""
    db.query(Notification).filter(
        Notification.ref_user_id == ref_user_id, Notification.is_read == 0
    ).update({Notification.is_read: 1})


def unread_count(db: Session, user: User) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == 0)
        .count()
    )


def list_notifications(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 10,
    unread_only: bool = False,
) -> NotificationListResponse:
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        query = query.filter(Notification.is_read == 0)
    total = query.count()
    items = (
        query.order_by(Notification.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return NotificationListResponse(
        list=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        unread=unread_count(db, user),
    )


def mark_read(db: Session, user: User, notification_id: int):
    item = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not item:
        raise BusinessException(message="通知不存在")
    item.is_read = 1
    db.commit()


def mark_all_read(db: Session, user: User):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read == 0
    ).update({Notification.is_read: 1})
    db.commit()
