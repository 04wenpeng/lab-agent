from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIConfig(Base):
    """AI 模型配置。

    - owner_id 为空 + is_default=1：系统默认配置（只有主管理员能改）
    - owner_id 有值：某个人自己的配置（写进来自动覆盖，一人一条）
    - api_key 只存密文，任何接口都不返回明文
    """

    __tablename__ = "ai_configs"
    __table_args__ = {"comment": "AI 模型配置"}

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="归属用户，空表示系统默认"
    )
    name: Mapped[str] = mapped_column(
        String(50), default="我的配置", comment="配置名称"
    )
    base_url: Mapped[str] = mapped_column(String(255), comment="接口地址")
    model: Mapped[str] = mapped_column(String(100), comment="模型名")
    api_key_enc: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="API Key 密文"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否系统默认配置"
    )
    status: Mapped[int] = mapped_column(default=1, comment="1 启用，0 停用")

    owner = relationship("User")
