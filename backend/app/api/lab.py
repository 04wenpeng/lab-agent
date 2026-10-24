from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.common.response import Response
from app.models.lab import Lab
from app.dependencies.auth import get_current_admin, get_current_user
from app.schemas.lab import (
    LabCreateRequest,
    LabEquipmentSaveRequest,
    LabUpdateRequest,
)
from app.services import lab_service
from app.database import get_db

router = APIRouter(prefix="/lab", tags=["实验室信息接口"])


@router.get("/list")
def get_lab_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    status: int | None = None,
    current_user: Lab = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = lab_service.get_lab_page_list(db, page, page_size, keywords, status)
    return Response.success(data=res)


@router.get("/{lab_id}")
def get_lab(
    lab_id: int,
    current_user: Lab = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = lab_service.get_lab(db, lab_id)
    return Response.success(data=res)


@router.post("")
def create_lab(
    data: LabCreateRequest,
    current_user: Lab = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = lab_service.create_lab(db, data)
    return Response.success(data=res)


@router.put("/{lab_id}")
def update_lab(
    lab_id: int,
    data: LabUpdateRequest,
    current_user: Lab = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = lab_service.update_lab(db, lab_id, data)
    message = "保存成功"
    if res.canceled_count:
        message = f"实验室已关闭，同时取消了 {res.canceled_count} 条后续预约"
    return Response.success(data=res, message=message)


@router.put("/{lab_id}/equipments")
def save_lab_equipments(
    lab_id: int,
    data: LabEquipmentSaveRequest,
    current_user: Lab = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """保存某个实验室的设备清单（增/改/删一次提交）"""
    res = lab_service.save_lab_equipments(db, lab_id, data.equipments)
    return Response.success(data=res)


@router.delete("/{lab_id}")
def delete_lab(
    lab_id: int,
    current_user: Lab = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    lab_service.delete_lab(db, lab_id)
    return Response.success()
