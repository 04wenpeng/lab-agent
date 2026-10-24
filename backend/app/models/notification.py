from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notification(Base):
    """站内通知：预约被审核、被取消、被改约时通知预约人。"""

    __tablename__ = "notifications"
    __table_args__ = {"comment": "站内通知"}

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="接收人"
    )
    title: Mapped[str] = mapped_column(String(100), comment="标题")
    content: Mapped[str] = mapped_column(String(500), comment="内容")
    reservation_id: Mapped[int | None] = mapped_column(nullable=True, comment="关联预约")
    # 关联的用户（比如「新的管理员申请」指向申请人），用户被删时一起清理
    ref_user_id: Mapped[int | None] = mapped_column(
        nullable=True, comment="关联用户"
    )
    # 点这条通知跳到哪个前端路由，例如 /manager/my-reservation
    link: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="跳转路由")
    is_read: Mapped[int] = mapped_column(default=0, comment="0 未读，1 已读")
