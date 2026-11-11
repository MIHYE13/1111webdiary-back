import unittest

from pydantic import ValidationError

from app.main import app
from app.models import DiarySubmission
from app.routers.diaries import accept_diary
from app.routers.health import health_check


class ApiTestCase(unittest.TestCase):
    def test_expected_routes_are_registered(self) -> None:
        route_paths = {route.path for route in app.routes}
        self.assertIn("/health", route_paths)
        self.assertIn("/api/v1/diaries", route_paths)

    def test_health_reports_unconnected_integrations(self) -> None:
        response = health_check()
        self.assertEqual(
            response.model_dump(),
            {
                "status": "ok",
                "service": "webdiary-api",
                "integrations": {
                    "agent": "not_connected",
                    "firestore": "not_connected",
                },
            },
        )

    def test_diary_is_validated_but_not_echoed_or_persisted(self) -> None:
        diary_text = "오늘은 수업 자료를 차분히 정리해서 뿌듯했다."
        submission = DiarySubmission(
            diary=diary_text,
            today_tasks=[{"text": "수업 자료 정리", "complete": True}],
        )
        response = accept_diary(submission)

        payload = response.model_dump()
        self.assertEqual(payload["status"], "accepted")
        self.assertFalse(payload["persisted"])
        self.assertEqual(payload["agent_status"], "not_connected")
        self.assertNotIn(diary_text, response.model_dump_json())

    def test_short_diary_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            DiarySubmission(diary="짧은 일기", today_tasks=[])

    def test_unknown_fields_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            DiarySubmission.model_validate(
                {
                "diary": "오늘의 기록은 열 글자를 충분히 넘습니다.",
                    "unexpected": True,
                }
            )


if __name__ == "__main__":
    unittest.main()
