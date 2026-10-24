from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.user import User
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["统计报表"])


@router.get("/overview")
def get_overview(
    days: int = 30,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """使用率 / 热门时段 / 违约情况（管理员）"""
    days = max(1, min(days, 365))
    return Response.success(data=stats_service.get_stats(db, days))
