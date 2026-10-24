from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_name: str | None = None
    is_primary_author: bool = False
    can_delete: bool = False
    can_edit: bool = False
    create_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AnnouncementCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=1000)


class AnnouncementUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=100)
    content: str | None = Field(default=None, max_length=1000)
