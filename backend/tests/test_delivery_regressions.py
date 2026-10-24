"""运行：在 backend 下执行 python -m unittest discover -s tests -v。

使用内存 SQLite 与模拟模型响应，不读取 .env、不连接外部数据库或模型服务。
"""
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
config = types.ModuleType("app.config")
config.settings = SimpleNamespace(
    DATABASE_URL="sqlite://",
    JWT_SECRET_KEY="delivery-regression-tests-only-32-characters",
    JWT_EXPIRE_HOURS=1,
    JWT_ALGORITHM="HS256",
    LLM_API_KEY="unused",
    LLM_MODEL="mock-model",
    LLM_BASE_URL="http://127.0.0.1/unused",
)
sys.modules["app.config"] = config
kb = types.ModuleType("app.services.kb_service")
kb.search = lambda **kwargs: ""
sys.modules["app.services.kb_service"] = kb

from fastapi import HTTPException
from app.common.exceptions import BusinessException
from app.database import Base, SessionLocal, engine
from app.dependencies.auth import get_current_user, oauth2_scheme
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from app.schemas.reservation import ReservationCreateRequest
from app.services import ai_service, reservation_service
from app.utils.jwt import create_access_token


class DeliveryRegressions(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.db = SessionLocal()
        self.user = User(username="student", password="unused", name="student", role="student", status=1)
        self.lab = Lab(name="lab", status=1)
        self.db.add_all([self.user, self.lab])
        self.db.commit()
        self.devices = [Equipment(lab_id=self.lab.id, name=str(i), status=1) for i in range(2)]
        self.db.add_all(self.devices)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(engine)

    def reserve(self, device=None):
        request = ReservationCreateRequest(
            lab_id=self.lab.id, equipment_id=device,
            date="2099-01-01", start_time="10:00", end_time="11:00",
        )
        reservation_service.create_reservation(self.db, self.user, request)
        return self.db.query(Reservation).order_by(Reservation.id.desc()).first()

    def test_deleted_user_with_valid_token_gets_401(self):
        token = create_access_token(self.user.id)
        self.db.delete(self.user)
        self.db.commit()
        with self.assertRaises(HTTPException) as error:
            get_current_user(token, self.db)
        self.assertEqual(error.exception.status_code, 401)

    def test_login_documentation_url(self):
        self.assertEqual(oauth2_scheme.model.flows.password.tokenUrl, "/api/auth/login")

    def test_only_pending_own_reservations_can_be_cancelled(self):
        item = self.reserve()
        reservation_service.cancel_reservation(self.db, self.user, item.id)
        self.assertEqual(item.status, 3)
        for value in (1, 2, 3):
            item.status = value
            self.db.commit()
            with self.assertRaises(BusinessException):
                reservation_service.cancel_reservation(self.db, self.user, item.id)
            self.assertEqual(item.status, value)
        item.status = 0
        self.db.commit()
        with self.assertRaises(BusinessException) as error:
            reservation_service.cancel_reservation(self.db, SimpleNamespace(id=self.user.id + 1), item.id)
        self.assertEqual(error.exception.code, 403)
        self.assertEqual(item.status, 0)

    def test_lab_and_devices_use_independent_conflict_checks(self):
        self.reserve(self.devices[0].id)
        self.reserve()
        self.reserve(self.devices[1].id)
        self.assertEqual(self.db.query(Reservation).count(), 3)
        for device in (None, self.devices[0].id, self.devices[1].id):
            with self.assertRaises(BusinessException):
                self.reserve(device)

    def run_chat(self, final_content="answer", final_error=None, tool_rounds=3):
        calls = []
        tool = SimpleNamespace(id="call-1", function=SimpleNamespace(name="list_open_labs", arguments="{}"))

        def create(**kwargs):
            calls.append(kwargs)
            final = len(calls) > tool_rounds
            if final and final_error:
                raise final_error
            msg = SimpleNamespace(tool_calls=[] if final else [tool], content=final_content if final else None)
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        request = ChatRequest(messages=[ChatMessage(role="user", content="list labs")])
        with patch.object(ai_service, "get_client", return_value=client), \
             patch.object(ai_service, "run_tool", return_value="{}") as run_tool, \
             patch.object(ai_service.traceback, "print_exc"):
            if final_error or not final_content.strip():
                with self.assertRaises(BusinessException):
                    ai_service.chat(self.db, request)
            else:
                content = ai_service.chat(self.db, request)
                self.assertEqual(ChatMessage(role="assistant", content=content).content, final_content)
            self.assertEqual(run_tool.call_count, tool_rounds)
        self.assertEqual(len(calls), tool_rounds + 1)
        if tool_rounds == 3:
            self.assertEqual(calls[-1]["tool_choice"], "none")
            self.assertEqual([m["role"] for m in calls[-1]["messages"][-6:]], ["assistant", "tool"] * 3)

    def test_three_tool_rounds_produce_final_answer(self):
        self.run_chat()

    def test_normal_answer_returns_without_extra_call(self):
        self.run_chat(tool_rounds=0)

    def test_empty_final_answer_is_reported(self):
        self.run_chat(final_content=" ")

    def test_final_model_failure_is_reported(self):
        self.run_chat(final_error=RuntimeError("simulated model failure"))

    def test_knowledge_matches_reservation_rules(self):
        directory = Path(__file__).resolve().parents[1] / "data" / "kb"
        booking = (directory / "预约规则.md").read_text(encoding="utf-8")
        equipment = (directory / "设备使用.md").read_text(encoding="utf-8")
        self.assertIn("本人只能取消待审核", booking)
        self.assertIn("分别判断时段冲突，互不占用", equipment)
        self.assertEqual(len(list(directory.glob("*.md"))), 4)


if __name__ == "__main__":
    unittest.main()
