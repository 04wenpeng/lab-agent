from operator import or_
from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.equipment import Equipment
from app.models.equipment_catalog import EquipmentCatalog
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.schemas.equipment import (
    EquipmentResponse,
    EquipmentCreateRequest,
    EquipmentUpdateRequest,
)
from sqlalchemy.orm import Session


def get_equipment_page_list(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    lab_id: int | None = None,
):
    """分页模糊查询列表"""
    # select * from equipment where name like '%计算机%';
    query = db.query(Equipment)
    if lab_id:
        query = query.filter(Equipment.lab_id == lab_id)
    if keywords:
        query = query.filter(Equipment.name.ilike(f"%{keywords}%"))
    total = query.count()
    items = (
        query.order_by(Equipment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        res = EquipmentResponse.model_validate(item)
        res.lab_name = item.lab.name if item.lab else None
        result.append(res)
    return PageResponse(list=result, total=total)


def create_equipment(db: Session, data: EquipmentCreateRequest):
    """新增（同一实验室内设备名不能重复，不同实验室可以重名）"""
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")

    payload = data.model_dump()
    catalog = None
    if data.catalog_id:
        catalog = (
            db.query(EquipmentCatalog)
            .filter(EquipmentCatalog.id == data.catalog_id)
            .first()
        )
        if not catalog:
            raise BusinessException(message="设备库里没有这个设备")
        payload["name"] = catalog.name
        if not payload.get("spec"):
            payload["spec"] = catalog.spec

    name = (payload.get("name") or "").strip()
    if not name:
        raise BusinessException(message="请先选择设备（设备库）")
    payload["name"] = name
    exist = (
        db.query(Equipment)
        .filter(Equipment.lab_id == data.lab_id, Equipment.name == name)
        .first()
    )
    if exist:
        raise BusinessException(message="同一个实验室不能存在同名的设备")
    equipment = Equipment(**payload)
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return res


def update_equipment(db: Session, equipment_id: int, data: EquipmentUpdateRequest):
    """更新"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise BusinessException(message="实验室设备不存在")
    payload = data.model_dump(exclude_none=True)

    # 换了设备库条目 → 名称/规格跟着设备库走
    if payload.get("catalog_id"):
        catalog = (
            db.query(EquipmentCatalog)
            .filter(EquipmentCatalog.id == payload["catalog_id"])
            .first()
        )
        if not catalog:
            raise BusinessException(message="设备库里没有这个设备")
        payload["name"] = catalog.name
        if not payload.get("spec"):
            payload["spec"] = catalog.spec

    lab_id = payload.get("lab_id", equipment.lab_id)
    name = payload.get("name", equipment.name)
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    exist = (
        db.query(Equipment)
        .filter(
            Equipment.lab_id == lab_id,
            Equipment.name == name,
            Equipment.id != equipment.id,
        )
        .first()
    )
    if exist:
        raise BusinessException(message="同一个实验室不能存在同名的设备")

    for filed, value in payload.items():
        setattr(equipment, filed, value)

    db.commit()
    db.refresh(equipment)
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return res


def delete_equipment(db: Session, equipment_id: int):
    """删除（有预约记录的设备不允许删，避免留下孤儿预约）"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise BusinessException(message="实验室设备不存在")
    used = db.query(Reservation).filter(Reservation.equipment_id == equipment_id).count()
    if used:
        raise BusinessException(
            message=f"设备「{equipment.name}」还有 {used} 条预约记录，不能删除"
        )
    db.delete(equipment)
    db.commit()
