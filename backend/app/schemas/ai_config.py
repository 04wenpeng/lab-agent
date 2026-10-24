from pydantic import BaseModel, Field


class AIConfigPayload(BaseModel):
    """新建/修改配置时提交的内容。api_key 不传表示沿用原来的。"""

    name: str | None = None
    base_url: str = Field(min_length=4, max_length=255)
    model: str = Field(min_length=1, max_length=100)
    api_key: str | None = Field(default=None, max_length=500)


class AIConfigResponse(BaseModel):
    """对外的配置视图：只告诉前端「有没有配 Key」，永远不回传明文或密文。"""

    id: int
    owner_id: int | None = None
    owner_name: str | None = None
    name: str
    base_url: str
    model: str
    has_key: bool = False
    api_key_masked: str = ""
    is_default: bool = False
    status: int = 1


class MyAIConfigResponse(BaseModel):
    """「我的配置」页需要一次性拿到：自己的配置 + 当前实际生效的来源。"""

    my_config: AIConfigResponse | None = None
    default_config: AIConfigResponse | None = None
    # mine / default / env / none
    effective_source: str = "none"
    effective_model: str | None = None
    effective_base_url: str | None = None
