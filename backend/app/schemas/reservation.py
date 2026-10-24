from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReservationCreateRequest(BaseModel):
    lab_id: int
    equipment_id: int | None = None
    date: str
    start_time: str
    end_time: str
    people: int = 1
    remark: str | None = None


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    lab_id: int
    lab_name: str | None = None
    equipment_id: int | None = None
    equipment_name: str | None = None
    type: str | None = None
    date: str
    start_time: str
    end_time: str
    people: int = 1
    remark: str | None = None
    status: int
    # 审核留痕
    audit_by: int | None = None
    audit_by_name: str | None = None
    audit_time: datetime | None = None
    audit_source: str | None = "admin"
    checked_in: int = 0
    check_in_time: datetime | None = None
    no_show: int = 0
    modify_count: int = 0
    create_time: datetime | None = None
    cancel_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AuditReservationRequest(BaseModel):
    status: int  #  1 | 2


class AdminCancelRequest(BaseModel):
    reason: str | None = None


class AdminRescheduleRequest(BaseModel):
    date: str
    start_time: str
    end_time: str
    remark: str | None = None
    reason: str | None = None


class ModifyReservationRequest(BaseModel):
    """学生自己改预约（只能改没开始的）"""

    date: str
    start_time: str
    end_time: str
    people: int | None = None
    remark: str | None = None
