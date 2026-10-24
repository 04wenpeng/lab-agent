from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SystemSetting(Base):
    """系统设置（键值对），目前存预约规则。"""

    __tablename__ = "system_settings"
    __table_args__ = {"comment": "系统设置"}

    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="配置项")
    value: Mapped[str] = mapped_column(String(500), nullable=False, comment="配置值")
