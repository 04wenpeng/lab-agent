from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OperationLog(Base):
    """操作日志：记录写操作（非 GET），谁在什么时候改了什么。"""

    __tablename__ = "operation_logs"
    __table_args__ = {"comment": "操作日志"}

    user_id: Mapped[int | None] = mapped_column(nullable=True, comment="操作人ID")
    username: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="操作人账号")
    action: Mapped[str] = mapped_column(String(80), nullable=False, comment="动作说明")
    method: Mapped[str] = mapped_column(String(10), nullable=False, comment="请求方法")
    path: Mapped[str] = mapped_column(String(200), nullable=False, comment="请求路径")
    status_code: Mapped[int] = mapped_column(default=200, comment="响应状态码")
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="补充信息")
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="来源IP")
