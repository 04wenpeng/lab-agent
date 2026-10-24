from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EquipmentCatalog(Base):
    """设备库：全局的设备型号清单，实验室里加设备时从这里选。"""

    __tablename__ = "equipment_catalog"
    __table_args__ = {"comment": "设备库"}

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="设备名称")
    spec: Mapped[str | None] = mapped_column(String(100), comment="默认型号规格")
    category: Mapped[str | None] = mapped_column(String(50), comment="分类")
    description: Mapped[str | None] = mapped_column(String(255), comment="说明")
