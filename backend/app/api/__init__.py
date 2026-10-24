from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.files import router as files_router
from app.api.lab import router as lab_router
from app.api.equipment import router as equipment_router
from app.api.reservation import router as reservation_router
from app.api.ai import router as ai_router
from app.api.ai_config import router as ai_config_router
from app.api.notification import router as notification_router
from app.api.equipment_catalog import router as equipment_catalog_router
from app.api.announcement import router as announcement_router
from app.api.setting import router as setting_router
from app.api.stats import router as stats_router
from app.api.log import router as log_router

api = APIRouter(prefix="/api")

api.include_router(auth_router)
api.include_router(user_router)
api.include_router(files_router)
api.include_router(lab_router)
api.include_router(equipment_router)
api.include_router(reservation_router)
api.include_router(ai_router)
api.include_router(ai_config_router)
api.include_router(notification_router)
api.include_router(equipment_catalog_router)
api.include_router(announcement_router)
api.include_router(setting_router)
api.include_router(stats_router)
api.include_router(log_router)
