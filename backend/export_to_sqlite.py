"""把 MySQL 里的数据导出成 SQLite 文件（给「独立部署包」用）。

用法：cd E:\\lab-agent\\backend && python export_to_sqlite.py [输出路径]
默认输出到 E:\\lab-agent\\backend\\lab_agent_standalone.db
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, ".pylibs"))

from sqlalchemy import create_engine, text  # noqa: E402

from app.database import Base  # noqa: E402
from app.models.user import User  # noqa: F401,E402
from app.models.lab import Lab  # noqa: F401,E402
from app.models.equipment import Equipment  # noqa: F401,E402
from app.models.equipment_catalog import EquipmentCatalog  # noqa: F401,E402
from app.models.reservation import Reservation  # noqa: F401,E402
from app.models.notification import Notification  # noqa: F401,E402
from app.models.ai_config import AIConfig  # noqa: F401,E402
from app.models.announcement import Announcement  # noqa: F401,E402
from app.models.setting import SystemSetting  # noqa: F401,E402
from app.models.operation_log import OperationLog  # noqa: F401,E402

MYSQL_URL = "mysql+pymysql://lab:lab123456@127.0.0.1:3307/lab_agent?charset=utf8mb4"
out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "lab_agent_standalone.db")
if os.path.exists(out_path):
    os.remove(out_path)
SQLITE_URL = "sqlite:///" + out_path.replace("\\", "/")

TABLES = [
    "labs",
    "equipment_catalog",
    "equipments",
    "users",
    "reservations",
    "notifications",
    "ai_configs",
    "announcements",
    "system_settings",
    "operation_logs",
]

src = create_engine(MYSQL_URL, future=True)
dst = create_engine(SQLITE_URL, future=True)
Base.metadata.create_all(bind=dst)

total = 0
for table in TABLES:
    with src.connect() as sconn:
        rows = sconn.execute(text(f"SELECT * FROM `{table}`")).mappings().all()
    if not rows:
        print(f"{table}: 0")
        continue
    cols = list(rows[0].keys())
    col_sql = ", ".join(f'"{c}"' for c in cols)
    val_sql = ", ".join(f":{c}" for c in cols)
    with dst.begin() as dconn:
        dconn.execute(text(f'INSERT INTO "{table}" ({col_sql}) VALUES ({val_sql})'), [dict(r) for r in rows])
    total += len(rows)
    print(f"{table}: {len(rows)}")

print(f"完成，共 {total} 行 -> {out_path}")
