import asyncio
from contextlib import asynccontextmanager
from traceback import print_exc
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR, BASE_DIR
from app.database import SessionLocal
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.models.ai_config import AIConfig
from app.models.notification import Notification
from app.models.equipment_catalog import EquipmentCatalog
from app.models.announcement import Announcement
from app.models.setting import SystemSetting
from app.models.operation_log import OperationLog
from app.database import Base, engine
from app.utils.jwt import decode_access_token
from app.api import api
from starlette.middleware.cors import CORSMiddleware
from app.common.exceptions import (
    BusinessException,
    bussiness_excpetion_hadler,
    http_excpetion_hadler,
    validation_excpetion_hadler,
    global_excpetion_hadler,
)
from app.services import (
    equipment_catalog_service,
    kb_service,
    operation_log_service,
    reservation_service,
    user_service,
)

Base.metadata.create_all(bind=engine)  # 自动帮我们创数据库表


def _ensure_schema():
    """给老库补字段：create_all 只建新表，不会给已存在的表加列。

    这里用「执行失败就忽略」的方式做最小迁移，SQLite / MySQL 都适用。
    """
    from sqlalchemy import text

    ddl_list = [
        "ALTER TABLE reservations ADD COLUMN audit_by INTEGER",
        "ALTER TABLE reservations ADD COLUMN audit_time DATETIME",
        "ALTER TABLE reservations ADD COLUMN cancel_reason VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN pending_admin INTEGER",
        "UPDATE users SET pending_admin = 0 WHERE pending_admin IS NULL",
        "ALTER TABLE notifications ADD COLUMN link VARCHAR(200)",
        "ALTER TABLE notifications ADD COLUMN ref_user_id INTEGER",
        "ALTER TABLE users ADD COLUMN apply_time DATETIME",
        "ALTER TABLE users ADD COLUMN apply_rejected_at DATETIME",
        "ALTER TABLE users ADD COLUMN apply_note VARCHAR(500)",
        "ALTER TABLE equipments ADD COLUMN catalog_id INTEGER",
        "ALTER TABLE reservations ADD COLUMN audit_source VARCHAR(20)",
        "UPDATE reservations SET audit_source = 'admin' WHERE audit_source IS NULL",
        "ALTER TABLE reservations ADD COLUMN people INTEGER",
        "UPDATE reservations SET people = 1 WHERE people IS NULL",
        "ALTER TABLE reservations ADD COLUMN checked_in INTEGER",
        "UPDATE reservations SET checked_in = 0 WHERE checked_in IS NULL",
        "ALTER TABLE reservations ADD COLUMN check_in_time DATETIME",
        "ALTER TABLE reservations ADD COLUMN no_show INTEGER",
        "UPDATE reservations SET no_show = 0 WHERE no_show IS NULL",
        "ALTER TABLE reservations ADD COLUMN modify_count INTEGER",
        "UPDATE reservations SET modify_count = 0 WHERE modify_count IS NULL",
    ]
    for ddl in ddl_list:
        try:
            with engine.begin() as conn:
                conn.execute(text(ddl))
            print(f"[schema] {ddl}")
        except Exception:
            pass  # 字段已存在


_ensure_schema()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 一个管理员都没有时兜底创建初始管理员 123456/123456
    try:
        await asyncio.to_thread(user_service.ensure_initial_admin)
    except Exception:
        traceback.print_exc()
    # 设备库为空时用现有设备初始化一下
    try:
        await asyncio.to_thread(equipment_catalog_service.seed_from_equipments)
    except Exception:
        traceback.print_exc()
    try:
        await asyncio.to_thread(kb_service.warmup)
    except Exception:
        traceback.print_exc()
    # 启动项目开启异步的扫描任务
    task = asyncio.create_task(reservation_service.run_expire_scan())
    try:
        yield
    finally:
        task.cancel()  # 关闭项目同时取消异步任务
        await asyncio.gather(
            task, return_exceptions=True
        )  # 取消任务不再把 CanceledError 抛给 lifespan


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源，不要直接写 ["*"]
    allow_credentials=True,  # ✅ 关键：允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
)

app.include_router(api)


@app.middleware("http")
async def record_operation_log(request: Request, call_next):
    """记录写操作（POST/PUT/DELETE）：谁、什么时候、改了什么"""
    response = await call_next(request)
    try:
        path = request.url.path
        method = request.method
        if method in ("POST", "PUT", "DELETE", "PATCH") and path.startswith("/api"):
            action = operation_log_service.describe_action(method, path)
            if action and response.status_code < 400:
                user = None
                auth = request.headers.get("authorization") or ""
                if auth.lower().startswith("bearer "):
                    try:
                        payload = decode_access_token(auth[7:])
                        uid = payload.get("user_id")
                        if uid:
                            db = SessionLocal()
                            try:
                                user = db.query(User).filter(User.id == uid).first()
                            finally:
                                db.close()
                    except Exception:
                        user = None
                db = SessionLocal()
                try:
                    operation_log_service.record(
                        db,
                        user,
                        action,
                        method,
                        path,
                        response.status_code,
                        detail=request.url.query or None,
                        ip=request.client.host if request.client else None,
                    )
                finally:
                    db.close()
    except Exception:
        traceback.print_exc()
    return response


# 注册异常处理器
app.add_exception_handler(BusinessException, bussiness_excpetion_hadler)
app.add_exception_handler(HTTPException, http_excpetion_hadler)
app.add_exception_handler(RequestValidationError, validation_excpetion_hadler)
# 全局的异常兜底，必须放在最后注册！！
app.add_exception_handler(Exception, global_excpetion_hadler)

# 挂载静态的文件目录  http://127.0.0.1:8000/uploads/xxx.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def api_health():
    return {"message": "FastAPI工程正在运行中"}


# ===== 独立部署模式：如果同目录下有 web/（前端构建产物），直接由后端托管 =====
# 开发时（前端跑 5173）没有这个目录，走原来的方式，互不影响。
WEB_DIR = BASE_DIR.parent / "web"
if WEB_DIR.is_dir():
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        target = (WEB_DIR / full_path).resolve()
        # 防止 ../ 跳出目录
        if str(target).startswith(str(WEB_DIR.resolve())) and target.is_file():
            return FileResponse(target)
        return FileResponse(WEB_DIR / "index.html")


@app.get("/")
def root():
    if (WEB_DIR / "index.html").is_file():
        from fastapi.responses import FileResponse

        return FileResponse(WEB_DIR / "index.html")
    return {"message": "FastAPI工程正在运行中"}
