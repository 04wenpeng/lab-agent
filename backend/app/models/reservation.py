from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.user import User


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {"comment": "预约信息"}

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), comment="预约人", nullable=False
    )
    lab_id: Mapped[int] = mapped_column(
        ForeignKey("labs.id"), comment="实验室", nullable=False
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipments.id"), comment="设备，空表示预约实验室", nullable=True
    )
    date: Mapped[str] = mapped_column(String(20), comment="预约日期", nullable=False)
    start_time: Mapped[str] = mapped_column(
        String(20), comment="开始时间", nullable=False
    )
    end_time: Mapped[str] = mapped_column(
        String(20), comment="结束时间", nullable=False
    )
    remark: Mapped[str] = mapped_column(String(255), comment="备注", nullable=True)
    people: Mapped[int] = mapped_column(Integer, default=1, comment="使用人数")
    status: Mapped[int] = mapped_column(
        comment="预约状态 0待审核，1已通过，2已拒绝，3已取消", default=0
    )
    # 审核留痕：谁审的、什么时候审的
    audit_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="审核人ID"
    )
    audit_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="审核时间"
    )
    cancel_reason: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="管理员取消/改约原因"
    )
    # admin = 管理员审核，ai = AI 自动审核
    audit_source: Mapped[str] = mapped_column(
        String(20), default="admin", comment="审核来源"
    )
    # 签到 / 违约
    checked_in: Mapped[int] = mapped_column(Integer, default=0, comment="是否已签到")
    check_in_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="签到时间"
    )
    no_show: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否违约（约了没签到）"
    )
    # 学生自己改过几次（有上限）
    modify_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="已修改次数"
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    lab: Mapped[Lab] = relationship()
    equipment: Mapped[Equipment] = relationship()
