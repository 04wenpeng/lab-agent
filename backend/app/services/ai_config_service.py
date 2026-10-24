"""AI 模型配置的业务逻辑。

规则：
- 每个人可以维护一条自己的配置（写进来自动覆盖）；
- 主管理员可以维护一条「系统默认配置」，并管理所有人的配置（停用 / 删除 / 设为默认）；
- API Key 一律加密保存，任何接口都只回 `has_key`，不回明文；
- 对话时按「我的配置 → 系统默认 → .env」的顺序取第一条可用配置。
"""

from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.config import settings
from app.models.ai_config import AIConfig
from app.models.user import User
from app.schemas.ai_config import (
    AIConfigPayload,
    AIConfigResponse,
    MyAIConfigResponse,
)
from app.schemas.user import PRIMARY_ADMIN_USERNAME
from app.utils.crypto import decrypt_key, encrypt_key

MASKED_KEY = "••••••••"


def _is_primary(user: User) -> bool:
    return user.username == PRIMARY_ADMIN_USERNAME


def _to_response(cfg: AIConfig | None) -> AIConfigResponse | None:
    if cfg is None:
        return None
    has_key = bool(cfg.api_key_enc)
    return AIConfigResponse(
        id=cfg.id,
        owner_id=cfg.owner_id,
        owner_name=cfg.owner.name if cfg.owner else "系统默认",
        name=cfg.name,
        base_url=cfg.base_url,
        model=cfg.model,
        has_key=has_key,
        api_key_masked=MASKED_KEY if has_key else "",
        is_default=bool(cfg.is_default),
        status=cfg.status,
    )


def _get_default(db: Session) -> AIConfig | None:
    return db.query(AIConfig).filter(AIConfig.is_default.is_(True)).first()


def _get_mine(db: Session, user: User) -> AIConfig | None:
    return db.query(AIConfig).filter(AIConfig.owner_id == user.id).first()


def resolve_config(db: Session, user: User) -> SimpleNamespace:
    """返回当前用户实际生效的模型配置。"""
    mine = _get_mine(db, user)
    if mine and mine.status == 1:
        key = decrypt_key(mine.api_key_enc)
        if key:
            return SimpleNamespace(
                base_url=mine.base_url,
                model=mine.model,
                api_key=key,
                source="mine",
            )

    default = _get_default(db)
    if default and default.status == 1:
        key = decrypt_key(default.api_key_enc)
        if key:
            return SimpleNamespace(
                base_url=default.base_url,
                model=default.model,
                api_key=key,
                source="default",
            )

    if settings.LLM_API_KEY:
        return SimpleNamespace(
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            source="env",
        )

    raise BusinessException(
        message="还没有可用的模型配置：请联系主管理员配置系统默认模型，或在「模型配置」里添加自己的 API Key"
    )


def get_my_config(db: Session, user: User) -> MyAIConfigResponse:
    mine = _get_mine(db, user)
    default = _get_default(db)
    effective = resolve_config(db, user)
    return MyAIConfigResponse(
        my_config=_to_response(mine),
        default_config=_to_response(default),
        effective_source=effective.source,
        effective_model=effective.model,
        effective_base_url=effective.base_url,
    )


def save_my_config(db: Session, user: User, data: AIConfigPayload) -> AIConfigResponse:
    cfg = _get_mine(db, user)
    if cfg is None:
        cfg = AIConfig(owner_id=user.id, name=data.name or "我的配置")
        db.add(cfg)
    if data.name:
        cfg.name = data.name
    cfg.base_url = data.base_url.strip()
    cfg.model = data.model.strip()
    if data.api_key:
        cfg.api_key_enc = encrypt_key(data.api_key.strip())
    if not cfg.api_key_enc:
        raise BusinessException(message="API Key 不能为空")
    cfg.status = 1
    db.commit()
    db.refresh(cfg)
    return _to_response(cfg)


def delete_my_config(db: Session, user: User):
    cfg = _get_mine(db, user)
    if cfg is None:
        raise BusinessException(message="你还没有配置")
    db.delete(cfg)
    db.commit()


def _ensure_primary(user: User, action: str):
    if not _is_primary(user):
        raise BusinessException(message=f"只有主管理员可以{action}")


def list_configs(db: Session, current_user: User) -> list[AIConfigResponse]:
    """主管理员看全部；其他人只能看到自己那条（以及只读的默认配置）。"""
    if _is_primary(current_user):
        rows = (
            db.query(AIConfig)
            .order_by(AIConfig.is_default.desc(), AIConfig.id.desc())
            .all()
        )
        return [_to_response(row) for row in rows]
    rows = [
        cfg
        for cfg in (_get_mine(db, current_user), _get_default(db))
        if cfg is not None
    ]
    return [_to_response(row) for row in rows]


def save_default(
    db: Session, current_user: User, data: AIConfigPayload
) -> AIConfigResponse:
    _ensure_primary(current_user, "修改系统默认配置")
    cfg = _get_default(db)
    if cfg is None:
        cfg = AIConfig(owner_id=None, is_default=True, name=data.name or "系统默认")
        db.add(cfg)
    cfg.base_url = data.base_url.strip()
    cfg.model = data.model.strip()
    if data.api_key:
        cfg.api_key_enc = encrypt_key(data.api_key.strip())
    if not cfg.api_key_enc:
        raise BusinessException(message="API Key 不能为空")
    cfg.status = 1
    db.commit()
    db.refresh(cfg)
    return _to_response(cfg)


def promote_to_default(
    db: Session, current_user: User, config_id: int
) -> AIConfigResponse:
    """把某条配置复制成系统默认（Key 在服务端内部复制，不会回显）。"""
    _ensure_primary(current_user, "设置默认配置")
    src = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not src:
        raise BusinessException(message="配置不存在")
    if src.is_default:
        return _to_response(src)
    cfg = _get_default(db)
    if cfg is None:
        cfg = AIConfig(owner_id=None, is_default=True, name="系统默认")
        db.add(cfg)
    cfg.base_url = src.base_url
    cfg.model = src.model
    cfg.api_key_enc = src.api_key_enc
    cfg.status = 1
    db.commit()
    db.refresh(cfg)
    return _to_response(cfg)


def set_config_status(
    db: Session, current_user: User, config_id: int, status: int
) -> AIConfigResponse:
    _ensure_primary(current_user, "管理配置")
    if status not in (0, 1):
        raise BusinessException(message="状态只能是 0 或 1")
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise BusinessException(message="配置不存在")
    cfg.status = status
    db.commit()
    db.refresh(cfg)
    return _to_response(cfg)


def delete_config(db: Session, current_user: User, config_id: int):
    _ensure_primary(current_user, "删除别人的配置")
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise BusinessException(message="配置不存在")
    if cfg.is_default:
        raise BusinessException(message="系统默认配置不能直接删除，可以先改掉它")
    db.delete(cfg)
    db.commit()
