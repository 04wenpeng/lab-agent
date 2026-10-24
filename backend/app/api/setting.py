from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.setting import ReservationRules
from app.services import setting_service

router = APIRouter(prefix="/setting", tags=["系统设置"])


@router.get("/reservation-rules")
def get_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """预约规则（所有人可读，前端提交预约时用来提示/预校验）"""
    return Response.success(data=setting_service.get_reservation_rules(db))


@router.put("/reservation-rules")
def update_rules(
    data: ReservationRules,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """修改预约规则（管理员）"""
    return Response.success(data=setting_service.update_reservation_rules(db, data))
