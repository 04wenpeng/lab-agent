"""设备库：全局设备清单，实验室里加设备时从这里选。"""

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.database import SessionLocal
from app.models.equipment import Equipment
from app.models.equipment_catalog import EquipmentCatalog
from app.schemas.equipment_catalog import (
    EquipmentCatalogCreateRequest,
    EquipmentCatalogResponse,
    EquipmentCatalogUpdateRequest,
)


def list_catalog(db: Session, keywords: str | None = None):
    query = db.query(EquipmentCatalog)
    if keywords:
        query = query.filter(EquipmentCatalog.name.ilike(f"%{keywords}%"))
    items = query.order_by(EquipmentCatalog.id.desc()).all()
    return [EquipmentCatalogResponse.model_validate(item) for item in items]


def create_catalog(db: Session, data: EquipmentCatalogCreateRequest):
    name = data.name.strip()
    exist = db.query(EquipmentCatalog).filter(EquipmentCatalog.name == name).first()
    if exist:
        raise BusinessException(message=f"设备库里已经有「{name}」了")
    item = EquipmentCatalog(
        name=name,
        spec=data.spec,
        category=data.category,
        description=data.description,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return EquipmentCatalogResponse.model_validate(item)


def update_catalog(db: Session, catalog_id: int, data: EquipmentCatalogUpdateRequest):
    item = db.query(EquipmentCatalog).filter(EquipmentCatalog.id == catalog_id).first()
    if not item:
        raise BusinessException(message="设备库中没有这个设备")
    payload = data.model_dump(exclude_none=True)
    if "name" in payload:
        name = payload["name"].strip()
        exist = (
            db.query(EquipmentCatalog)
            .filter(EquipmentCatalog.name == name, EquipmentCatalog.id != catalog_id)
            .first()
        )
        if exist:
            raise BusinessException(message=f"设备库里已经有「{name}」了")
        item.name = name
        payload.pop("name")
    for field, value in payload.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return EquipmentCatalogResponse.model_validate(item)


def delete_catalog(db: Session, catalog_id: int):
    item = db.query(EquipmentCatalog).filter(EquipmentCatalog.id == catalog_id).first()
    if not item:
        raise BusinessException(message="设备库中没有这个设备")
    used = db.query(Equipment).filter(Equipment.catalog_id == catalog_id).count()
    if used:
        raise BusinessException(
            message=f"「{item.name}」已经被 {used} 个实验室设备记录引用，不能删除"
        )
    db.delete(item)
    db.commit()


def seed_from_equipments() -> int:
    """设备库为空时，用现有设备名初始化一批，免得一开始是空的。"""
    db = SessionLocal()
    try:
        if db.query(EquipmentCatalog).count() > 0:
            return 0
        rows = db.query(Equipment).all()
        seen = set()
        added = 0
        for row in rows:
            name = (row.name or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            db.add(EquipmentCatalog(name=name, spec=row.spec))
            added += 1
        if added:
            db.commit()
            print(f"[catalog] 已用现有设备初始化设备库 {added} 条")
        return added
    finally:
        db.close()
