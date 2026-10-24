"""�?sql/lab_agent.sql 的示例数据导入本�?SQLite，便于直接跑起来看效果�?""

import re
import sqlite3
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.database import Base, engine  # noqa: E402
from app.models import equipment, lab, reservation, user  # noqa: E402  (注册所有表)

Base.metadata.create_all(bind=engine)

SQL_FILE = BACKEND.parent / "sql" / "lab_agent.sql"
DB_FILE = BACKEND / "lab_agent.db"


def parse_tuples(text: str, start: int):
    """�?start（指�?'('）开始解�?VALUES 后面的行元组�?""
    rows, i, n = [], start, len(text)
    while i < n:
        if text[i] == "(":
            i += 1
            row = []
            buf = None  # None 表示不在字符串中
            while i < n:
                ch = text[i]
                if buf is not None:
                    if ch == "\\":
                        nxt = text[i + 1]
                        buf.append({"n": "\n", "r": "\r", "t": "\t", "0": "\0"}.get(nxt, nxt))
                        i += 2
                        continue
                    if ch == "'":
                        if i + 1 < n and text[i + 1] == "'":
                            buf.append("'")
                            i += 2
                            continue
                        row.append("".join(buf))
                        buf = None
                        i += 1
                        continue
                    buf.append(ch)
                    i += 1
                    continue
                if ch == "'":
                    buf = []
                    i += 1
                    continue
                if ch == ")":
                    i += 1
                    break
                if ch == ",":
                    i += 1
                    continue
                # 未加引号的字面量：数�?/ NULL
                j = i
                while j < n and text[j] not in ",)":
                    j += 1
                token = text[i:j].strip()
                row.append(None if token.upper() == "NULL" else int(token) if token.lstrip("-").isdigit() else token)
                i = j
            rows.append(row)
            continue
        i += 1
    return rows


def main():
    sql = SQL_FILE.read_text(encoding="utf-8")
    con = sqlite3.connect(DB_FILE)
    con.execute("PRAGMA foreign_keys=OFF")
    cur = con.cursor()

    for table in ("users", "labs", "equipments", "reservations"):
        create = re.search(rf"CREATE TABLE `{table}` \((.*?)\n\) ENGINE", sql, re.S)
        columns = re.findall(r"^\s*`(\w+)`", create.group(1), re.M)
        columns = [c for c in columns if c != "id"]
        body = re.search(rf"INSERT INTO `{table}` VALUES (.*?);\n", sql, re.S).group(1)
        rows = parse_tuples(body, 0)
        full = ["id"] + columns
        placeholders = ",".join("?" * len(full))
        cols = ",".join(f'"{c}"' for c in full)
        cur.execute(f'DELETE FROM "{table}"')
        cur.executemany(f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})', [r for r in rows if len(r) == len(full)])
        print(f"{table}: {cur.rowcount} rows (from {len(rows)} parsed)")

    from app.utils.password import hash_password

    now = "2026-10-22 10:00:00"

    def add_user(username, password, name, role, email="", phone=""):
        cur.execute(
            'INSERT INTO users (username,password,name,role,email,phone,avatar,status,create_time,update_time) '
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (username, hash_password(password), name, role, email, phone, "", 1, now, now),
        )
        print(f"user added: {username}/{password} ({role})")

    # 初始管理员：空库时的默认管理员，与后�?user_service.ensure_initial_admin 保持一�?    if not cur.execute("SELECT 1 FROM users WHERE username='123456'").fetchone():
        add_user("123456", "123456", "初始管理�?, "admin")
    if not cur.execute("SELECT 1 FROM users WHERE username='demo'").fetchone():
        add_user("demo", "demo123", "演示管理�?, "admin", "demo@lab.local", "13800000000")
    if not cur.execute("SELECT 1 FROM users WHERE username='stu'").fetchone():
        add_user("stu", "stu123", "演示学生", "student", "stu@lab.local", "13800000001")

    con.commit()
    for table in ("users", "labs", "equipments", "reservations"):
        print(table, cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0], "rows")
    con.close()


if __name__ == "__main__":
    main()
