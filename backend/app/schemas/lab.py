from pydantic import BaseModel, ConfigDict, Field


class LabResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    img: str | None = None
    location: str | None = None
    capacity: int
    open_time: str | None = None
    close_time: str | None = None
    status: int
    # 实时状态（由服务层按当天预约计算，非数据库字段）
    busy_now: bool = False  # 当前时段是否被占用
    busy_until: str | None = None  # 占用到几点
    today_count: int = 0  # 今天该实验室的有效预约条数
    canceled_count: int = 0  # 关闭实验室时自动取消的预约条数（仅更新接口返回）

    model_config = ConfigDict(from_attributes=True)


class LabCreateRequest(BaseModel):
    name: str
    description: str | None = None
    img: str | None = None
    location: str | None = None
    capacity: int = 0
    open_time: str | None = None
    close_time: str | None = None
    status: int = 1


class LabUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    img: str | None = None
    location: str | None = None
    capacity: int | None = None
    open_time: str | None = None
    close_time: str | None = None
    status: int | None = None


class LabEquipmentItem(BaseModel):
    """实验室里的一个设备（新增时 id 为空，编辑时带上 id）"""

    id: int | None = None
    catalog_id: int | None = None
    name: str = Field(min_length=1, max_length=50)
    spec: str | None = None
    quantity: int = 1
    status: int = 1
    description: str | None = None


class LabEquipmentSaveRequest(BaseModel):
    """整份设备清单：前端提交完整列表，后端按 id 做增/改/删"""

    equipments: list[LabEquipmentItem] = []
