"""系统设置：目前只有「预约规则」一项。"""

import json

from sqlalchemy.orm import Session

from app.models.setting import SystemSetting
from app.schemas.setting import ReservationRules

RULES_KEY = "reservation_rules"


def get_reservation_rules(db: Session) -> ReservationRules:
    item = db.query(SystemSetting).filter(SystemSetting.key == RULES_KEY).first()
    if not item:
        return ReservationRules()
    try:
        data = json.loads(item.value)
    except (TypeError, json.JSONDecodeError):
        return ReservationRules()
    # 老配置缺字段时用默认值兜底
    merged = {**ReservationRules().model_dump(), **{k: v for k, v in data.items() if v is not None}}
    try:
        return ReservationRules(**merged)
    except Exception:
        return ReservationRules()


def update_reservation_rules(db: Session, data: ReservationRules) -> ReservationRules:
    payload = data.model_dump()
    item = db.query(SystemSetting).filter(SystemSetting.key == RULES_KEY).first()
    if item:
        item.value = json.dumps(payload, ensure_ascii=False)
    else:
        db.add(SystemSetting(key=RULES_KEY, value=json.dumps(payload, ensure_ascii=False)))
    db.commit()
    return data
