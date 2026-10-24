from pydantic import BaseModel, ConfigDict, Field


class EquipmentCatalogResponse(BaseModel):
    id: int
    name: str
    spec: str | None = None
    category: str | None = None
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentCatalogCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    spec: str | None = None
    category: str | None = None
    description: str | None = None


class EquipmentCatalogUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    spec: str | None = None
    category: str | None = None
    description: str | None = None
