from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import operation_log_service

router = APIRouter(prefix="/log", tags=["操作日志"])


def _ensure_primary(current_user: User):
    from app.common.exceptions import BusinessException

    if current_user.username != "123456":
        raise BusinessException(message="只有主管理员可以查看操作日志", code=403)


@router.get("/list")
def list_logs(
    page: int = 1,
    page_size: int = 20,
    keywords: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_primary(current_user)
    return Response.success(
        data=operation_log_service.list_logs(db, page, page_size, keywords)
    )
