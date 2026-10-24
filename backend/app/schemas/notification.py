from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    title: str
    content: str
    reservation_id: int | None = None
    link: str | None = None
    is_read: int = 0
    create_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    # 注意：字段名叫 list，类型必须用 typing.List，否则会拿到类属性自己
    list: List[NotificationResponse] = []
    total: int = 0
    unread: int = 0
