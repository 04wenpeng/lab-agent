from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str
    # 登录入口类型：普通登录按学生校验，管理员登录按管理员校验；不传则不做限制
    role: Literal["student", "admin"] | None = None


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str | None = None
    # student：直接注册成学生；admin：提交管理员申请，等主管理员审核
    role: Literal["student", "admin"] = "student"
    # 申请管理员时必填，主管理员审核时会看到
    apply_note: str | None = Field(default=None, max_length=500)


class ApplyAdminRequest(BaseModel):
    """已登录学生申请成为管理员时提交的说明"""

    note: str = Field(min_length=5, max_length=500, description="申请说明，至少 5 个字")
