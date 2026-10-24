from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Announcement(Base):
    """公告：管理员发布，所有人可见。"""

    __tablename__ = "announcements"
    __table_args__ = {"comment": "公告"}

    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="标题")
    content: Mapped[str] = mapped_column(String(1000), nullable=False, comment="内容")
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="发布人"
    )

    author = relationship("User")
