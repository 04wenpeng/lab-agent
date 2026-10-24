from pydantic import BaseModel, Field


class ReservationRules(BaseModel):
    """预约规则（管理员可调）"""

    advance_days: int = Field(default=30, ge=1, le=365, description="最多提前几天预约")
    max_hours: int = Field(default=4, ge=1, le=24, description="单次最长几小时")
    daily_limit: int = Field(default=2, ge=1, le=20, description="每人每天最多预约几次")
    no_show_limit: int = Field(
        default=3, ge=1, le=10, description="违约几次后自动禁用账号"
    )
    modify_limit: int = Field(
        default=2, ge=0, le=10, description="学生自己最多能改几次预约（0 = 不允许改）"
    )
    modify_before_days: int = Field(
        default=0,
        ge=0,
        le=30,
        description="预约开始前多少天内不再允许修改（0 = 不限制）",
    )
    modify_window_days: int = Field(
        default=0,
        ge=0,
        le=30,
        description="提交预约后多少天内可以修改（0 = 不限制）",
    )
    cancel_before_days: int = Field(
        default=0,
        ge=0,
        le=30,
        description="预约开始前多少天内不再允许自己取消（0 = 不限制）",
    )
