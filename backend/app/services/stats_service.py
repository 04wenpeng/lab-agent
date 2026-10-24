"""统计报表：实验室使用率、热门时段、违约情况。"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User


def _hours(start: str, end: str) -> float:
    try:
        h1, m1 = map(int, start.split(":"))
        h2, m2 = map(int, end.split(":"))
        return max(0.0, ((h2 * 60 + m2) - (h1 * 60 + m1)) / 60)
    except (ValueError, AttributeError):
        return 0.0


def get_stats(db: Session, days: int = 30):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    since = (now - timedelta(days=days)).strftime("%Y-%m-%d")

    items = db.query(Reservation).filter(Reservation.date >= since).all()
    all_items = db.query(Reservation).all()

    approved = [x for x in items if x.status == 1]
    no_show = [x for x in items if x.no_show == 1]
    checked = [x for x in items if x.checked_in == 1]

    summary = {
        "range_days": days,
        "total": len(items),
        "pending": len([x for x in items if x.status == 0]),
        "approved": len(approved),
        "rejected": len([x for x in items if x.status == 2]),
        "cancelled": len([x for x in items if x.status == 3]),
        "today": len([x for x in all_items if x.date == today]),
        "checked_in": len(checked),
        "no_show": len(no_show),
        # 已结束的通过预约里，签到的比例
        "check_in_rate": round(len(checked) / len(approved) * 100, 1) if approved else 0.0,
    }

    # 实验室使用率：近 N 天「已通过」预约的总小时 / (N 天 × 每天开放小时)
    labs = db.query(Lab).all()
    lab_rows = []
    for lab in labs:
        lab_items = [x for x in approved if x.lab_id == lab.id]
        used_hours = sum(_hours(x.start_time, x.end_time) for x in lab_items)
        try:
            open_hours = _hours(lab.open_time or "08:00", lab.close_time or "18:00")
        except Exception:
            open_hours = 10
        capacity_hours = open_hours * days
        rate = round(used_hours / capacity_hours * 100, 1) if capacity_hours > 0 else 0.0
        lab_rows.append(
            {
                "lab_id": lab.id,
                "lab_name": lab.name,
                "count": len(lab_items),
                "hours": round(used_hours, 1),
                "rate": rate,
            }
        )
    lab_rows.sort(key=lambda x: x["hours"], reverse=True)

    # 热门时段：按开始小时统计（近 N 天，有效预约）
    hour_map: dict[int, int] = {}
    for item in items:
        if item.status not in (0, 1):
            continue
        try:
            hour = int(item.start_time.split(":")[0])
        except (ValueError, AttributeError):
            continue
        hour_map[hour] = hour_map.get(hour, 0) + 1
    hour_rows = [
        {"hour": f"{h:02d}:00", "count": hour_map.get(h, 0)} for h in range(8, 22)
    ]

    # 违约排行
    user_map: dict[int, int] = {}
    for item in no_show:
        user_map[item.user_id] = user_map.get(item.user_id, 0) + 1
    users = {
        u.id: u.name
        for u in db.query(User).filter(User.id.in_(list(user_map.keys()) or [-1])).all()
    }
    no_show_rows = [
        {"user_id": uid, "user_name": users.get(uid, f"用户{uid}"), "count": cnt}
        for uid, cnt in sorted(user_map.items(), key=lambda kv: kv[1], reverse=True)
    ]

    # 违约明细：具体是哪几条预约没签到
    no_show_list = [
        {
            "id": x.id,
            "user_id": x.user_id,
            "user_name": (x.user.name if x.user else users.get(x.user_id, f"用户{x.user_id}")),
            "lab_name": x.lab.name if x.lab else f"实验室{x.lab_id}",
            "equipment_name": x.equipment.name if x.equipment else None,
            "date": x.date,
            "start_time": x.start_time,
            "end_time": x.end_time,
            "people": x.people or 1,
            "remark": x.remark,
            "status": x.status,
        }
        for x in sorted(no_show, key=lambda r: (r.date, r.start_time), reverse=True)
    ]

    return {
        "summary": summary,
        "labs": lab_rows,
        "hours": hour_rows,
        "no_show_users": no_show_rows,
        "no_show_list": no_show_list,
    }
