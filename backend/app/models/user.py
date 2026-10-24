from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "用户信息表"}

    username: Mapped[str] = mapped_column(String(50), comment="账号", nullable=False)
    password: Mapped[str] = mapped_column(String(255), comment="密码", nullable=False)
    name: Mapped[str] = mapped_column(String(50), comment="名称", nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), comment="角色：student-学生，admin-管理员", nullable=False
    )
    email: Mapped[str | None] = mapped_column(String(50), comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(50), comment="手机号")
    avatar: Mapped[str | None] = mapped_column(String(50), comment="头像")
    status: Mapped[int] = mapped_column(default=1, comment="状态：0-禁用，1-正常")
    # 1 = 提交了「注册为管理员」的申请，等待主管理员审核
    pending_admin: Mapped[int] = mapped_column(
        default=0, comment="1-管理员申请待审核"
    )
    apply_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最近一次提交管理员申请的时间"
    )
    apply_rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="上次管理员申请被拒绝的时间（用于冷却期）"
    )
    apply_note: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="申请成为管理员的说明"
    )
