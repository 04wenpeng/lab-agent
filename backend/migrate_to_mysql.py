"""把 SQLite 里的数据迁移到 MySQL（一次性脚本）。

用法（在 E:\\lab-agent\\backend 目录下）：
    python migrate_to_mysql.py
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, ".pylibs"))

from sqlalchemy import create_engine, text  # noqa: E402

# 先把所有模型 import 进来，Base.metadata 才完整
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

SQLITE_URL = "sqlite:///" + os.path.join(BASE, "lab_agent.db").replace("\\", "/")
MYSQL_URL = "mysql+pymysql://lab:lab123456@127.0.0.1:3307/lab_agent?charset=utf8mb4"

TABLE_ORDER = [
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

src = create_engine(SQLITE_URL, future=True)
dst = create_engine(MYSQL_URL, future=True, pool_pre_ping=True)

print("1) 在 MySQL 里建表 ...")
Base.metadata.create_all(bind=dst)

print("2) 从 SQLite 读取数据 ...")
data = {}
for table in TABLE_ORDER:
    with src.connect() as sconn:
        rows = sconn.execute(text(f"SELECT * FROM {table}")).mappings().all()
    data[table] = [dict(r) for r in rows]
    print(f"   {table}: {len(data[table])} 行")

print("3) 写入 MySQL（临时关闭外键检查，老库里可能有孤儿数据）...")
with dst.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for table in reversed(TABLE_ORDER):
        try:
            conn.execute(text(f"DELETE FROM `{table}`"))
        except Exception:
            pass
    total = 0
    for table in TABLE_ORDER:
        rows = data[table]
        if not rows:
            continue
        columns = list(rows[0].keys())
        col_sql = ", ".join(f"`{c}`" for c in columns)
        val_sql = ", ".join(f":{c}" for c in columns)
        stmt = text(f"INSERT INTO `{table}` ({col_sql}) VALUES ({val_sql})")
        conn.execute(stmt, rows)
        total += len(rows)
        print(f"   {table}: 写入 {len(rows)} 行")
    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

print(f"4) 完成，共写入 {total} 行")

print("5) 校验两边行数 ...")
with src.connect() as sconn, dst.connect() as dconn:
    ok = True
    for table in TABLE_ORDER:
        a = sconn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        b = dconn.execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar()
        if a != b:
            ok = False
            print(f"   {table}: sqlite={a} mysql={b} 不一致")
        else:
            print(f"   {table}: {a} 行 OK")

print("6) 检查孤儿预约（引用了已删除用户/实验室）...")
with dst.connect() as dconn:
    orphan_user = dconn.execute(
        text("SELECT COUNT(*) FROM reservations r LEFT JOIN users u ON u.id=r.user_id WHERE u.id IS NULL")
    ).scalar()
    orphan_lab = dconn.execute(
        text("SELECT COUNT(*) FROM reservations r LEFT JOIN labs l ON l.id=r.lab_id WHERE l.id IS NULL")
    ).scalar()
print(f"   用户不存在: {orphan_user} 条；实验室不存在: {orphan_lab} 条")

print("全部一致 ✅" if ok else "有表数量不一致，请检查 ⚠️")
