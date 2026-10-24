from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

# 主管理员（初始管理员）账号：不可被其他管理员删除、降级、禁用
PRIMARY_ADMIN_USERNAME = "123456"

# 管理员申请被拒绝后，需要等这么多天才能再次申请
APPLY_COOLDOWN_DAYS = 7


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: int
    pending_admin: int = 0
    create_time: datetime | None = None
    apply_time: datetime | None = None
    apply_rejected_at: datetime | None = None
    apply_note: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_primary(self) -> bool:
        """是否主管理员，前端据此禁用删除/降级入口"""
        return self.username == PRIMARY_ADMIN_USERNAME

    @computed_field  # type: ignore[prop-decorator]
    @property
    def apply_retry_at(self) -> datetime | None:
        """被拒绝后，下一次可申请的时间；为空表示现在就能申请"""
        if not self.apply_rejected_at or self.role == "admin":
            return None
        return self.apply_rejected_at + timedelta(days=APPLY_COOLDOWN_DAYS)


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(default="123", min_length=3, max_length=20)
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    # 只允许这两种角色，避免出现 role='root' 这类非法值（权限判断只认 admin）
    role: Literal["student", "admin"] = "student"
    status: int = 1


class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: Literal["student", "admin"] | None = None
    status: int | None = None


class PasswordUpdateRequest(BaseModel):
    """修改密码的请求参数"""

    old_password: str
    new_password: str


class AdminApplicationAuditRequest(BaseModel):
    """主管理员审核「注册为管理员」申请"""

    approve: bool = True


class AdminResetPasswordRequest(BaseModel):
    """管理员重置别人的密码（不填就自动生成一个）"""

    new_password: str | None = None
