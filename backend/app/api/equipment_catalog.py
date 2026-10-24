from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.equipment_catalog import (
    EquipmentCatalogCreateRequest,
    EquipmentCatalogUpdateRequest,
)
from app.services import equipment_catalog_service

router = APIRouter(prefix="/equipment-catalog", tags=["设备库"])


@router.get("/list")
def list_catalog(
    keywords: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """设备库列表（登录后都能看，选设备时要用）"""
    return Response.success(
        data=equipment_catalog_service.list_catalog(db, keywords)
    )


@router.post("")
def create_catalog(
    data: EquipmentCatalogCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return Response.success(data=equipment_catalog_service.create_catalog(db, data))


@router.put("/{catalog_id}")
def update_catalog(
    catalog_id: int,
    data: EquipmentCatalogUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return Response.success(
        data=equipment_catalog_service.update_catalog(db, catalog_id, data)
    )


@router.delete("/{catalog_id}")
def delete_catalog(
    catalog_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    equipment_catalog_service.delete_catalog(db, catalog_id)
    return Response.success()
