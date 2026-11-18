import unittest

from pydantic import ValidationError

from app.main import app, is_allowed_api_origin
from app.models import DiarySubmission
from app.repositories.diaries import FirestoreDiaryRepository
from app.routers.diaries import accept_diary
from app.routers.health import health_check
from app.settings import parse_origins


class FakeDiaryRepository:
    def __init__(self) -> None:
        self.saved_submission = None

    def save(self, submission: DiarySubmission) -> str:
        self.saved_submission = submission
        return "diary-document-id"


class FakeDocument:
    id = "firestore-document-id"

    def __init__(self) -> None:
        self.payload = None

    def set(self, payload) -> None:
        self.payload = payload


class FakeCollection:
    def __init__(self, document: FakeDocument) -> None:
        self._document = document

    def document(self) -> FakeDocument:
        return self._document


class FakeFirestoreClient:
    def __init__(self) -> None:
        self.document = FakeDocument()
        self.collection_name = None

    def collection(self, name: str) -> FakeCollection:
        self.collection_name = name
        return FakeCollection(self.document)


class ApiTestCase(unittest.TestCase):
    def test_expected_routes_are_registered(self) -> None:
        route_paths = {route.path for route in app.routes}
        self.assertIn("/health", route_paths)
        self.assertIn("/api/v1/diaries", route_paths)

    def test_health_reports_firestore_configuration(self) -> None:
        response = health_check()
        self.assertEqual(
            response.model_dump(),
            {
                "status": "ok",
                "service": "webdiary-api",
                "integrations": {
                    "firestore": "configured",
                },
            },
        )

    def test_diary_is_saved_but_not_echoed(self) -> None:
        diary_text = "오늘은 수업 자료를 차분히 정리해서 뿌듯했다."
        submission = DiarySubmission(
            diary=diary_text,
            today_tasks=[{"text": "수업 자료 정리", "complete": True}],
        )
        repository = FakeDiaryRepository()
        response = accept_diary(submission, repository)

        payload = response.model_dump()
        self.assertEqual(payload["status"], "accepted")
        self.assertTrue(payload["persisted"])
        self.assertEqual(payload["request_id"], "diary-document-id")
        self.assertIs(repository.saved_submission, submission)
        self.assertNotIn(diary_text, response.model_dump_json())

    def test_firestore_repository_writes_expected_document(self) -> None:
        client = FakeFirestoreClient()
        repository = FirestoreDiaryRepository(client)
        submission = DiarySubmission(
            diary="오늘은 파이어스토어 저장 테스트를 진행했습니다.",
            today_tasks=[{"text": "저장 테스트", "complete": True}],
        )

        document_id = repository.save(submission)

        self.assertEqual(document_id, "firestore-document-id")
        self.assertEqual(client.collection_name, "diary_entries")
        self.assertEqual(
            client.document.payload["today_tasks"],
            [{"text": "저장 테스트", "complete": True}],
        )
        self.assertEqual(client.document.payload["schema_version"], 1)

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

    def test_cors_origins_are_normalized_and_deduplicated(self) -> None:
        self.assertEqual(
            parse_origins(
                "https://smwu261111.netlify.app/, "
                "https://smwu261111.netlify.app"
            ),
            ("https://smwu261111.netlify.app",),
        )

    def test_api_only_accepts_configured_frontend_origin(self) -> None:
        allowed_origins = ("https://smwu261111.netlify.app",)
        self.assertTrue(
            is_allowed_api_origin(
                "/api/v1/diaries",
                "https://smwu261111.netlify.app",
                allowed_origins,
            )
        )
        self.assertFalse(
            is_allowed_api_origin(
                "/api/v1/diaries",
                "https://example.com",
                allowed_origins,
            )
        )
        self.assertFalse(
            is_allowed_api_origin("/api/v1/diaries", None, allowed_origins)
        )
        self.assertTrue(is_allowed_api_origin("/health", None, allowed_origins))


if __name__ == "__main__":
    unittest.main()
