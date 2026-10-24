from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.ai_config import AIConfigPayload
from app.services import ai_config_service

router = APIRouter(prefix="/ai/config", tags=["AI模型配置"])


@router.get("/me")
def get_my_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我自己的配置 + 当前实际生效的来源（mine / default / env / none）"""
    return Response.success(data=ai_config_service.get_my_config(db, current_user))


@router.put("/me")
def save_my_config(
    data: AIConfigPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新增或覆盖我自己的模型配置；api_key 不传表示沿用原来的"""
    return Response.success(data=ai_config_service.save_my_config(db, current_user, data))


@router.delete("/me")
def delete_my_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ai_config_service.delete_my_config(db, current_user)
    return Response.success()


@router.get("/list")
def list_configs(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """主管理员看全部；其他管理员只能看到自己那条和默认配置（Key 一律不回传）"""
    return Response.success(data=ai_config_service.list_configs(db, current_user))


@router.post("/default")
def save_default(
    data: AIConfigPayload,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """主管理员设置系统默认模型"""
    return Response.success(data=ai_config_service.save_default(db, current_user, data))


@router.post("/{config_id}/promote")
def promote_to_default(
    config_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """主管理员把某条配置复制成系统默认"""
    return Response.success(
        data=ai_config_service.promote_to_default(db, current_user, config_id)
    )


@router.put("/{config_id}/status")
def set_config_status(
    config_id: int,
    status: int = Query(..., ge=0, le=1),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return Response.success(
        data=ai_config_service.set_config_status(db, current_user, config_id, status)
    )


@router.delete("/{config_id}")
def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ai_config_service.delete_config(db, current_user, config_id)
    return Response.success()
