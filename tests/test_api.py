import unittest

from fastapi import HTTPException
from google.api_core.exceptions import PermissionDenied
from pydantic import ValidationError

from app.main import app, is_allowed_api_origin
from app.models import (
    ConversationMessage,
    ConversationReply,
    DiarySubmission,
    TomorrowPlan,
)
from app.repositories.conversations import ConversationContext
from app.repositories.diaries import FirestoreDiaryRepository
from app.routers.conversations import create_conversation_message
from app.routers.diaries import accept_diary
from app.routers.health import health_check
from app.services.conversation import OpenAIConversationService
from app.settings import parse_origins


class FakeDiaryRepository:
    def __init__(self) -> None:
        self.saved_submission = None

    def save(self, submission: DiarySubmission) -> str:
        self.saved_submission = submission
        return "diary-document-id"


class DeniedDiaryRepository:
    def save(self, submission: DiarySubmission) -> str:
        raise PermissionDenied("test permission failure")


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


def sample_reply() -> ConversationReply:
    return ConversationReply(
        angel="내일 가장 중요한 한 가지부터 정해 봐요.",
        devil="시작은 가볍게 하고 쉬는 시간도 챙겨요.",
        facilitator="이 계획으로 시작해 볼까요?",
        plan_ready=True,
        plan=TomorrowPlan(
            must_do="수업 자료 초안 만들기",
            nice_to_do=["책상 정리"],
            easy_first_step="문서 제목과 목차만 적기",
            recovery="저녁에 20분 산책하기",
            low_energy_alternative="목차 세 줄만 적기",
        ),
    )


class FakeConversationRepository:
    def __init__(self, context: ConversationContext | None) -> None:
        self.context = context
        self.saved_turn = None

    def get_context(self, diary_id: str) -> ConversationContext | None:
        return self.context

    def append_turn(self, diary_id, user_message, reply) -> None:
        self.saved_turn = (diary_id, user_message, reply)


class FakeConversationService:
    def __init__(self, reply: ConversationReply) -> None:
        self.reply = reply
        self.received = None

    def respond(self, context, message, energy_level) -> ConversationReply:
        self.received = (context, message, energy_level)
        return self.reply


class FakeResponses:
    def __init__(self, reply: ConversationReply) -> None:
        self.reply = reply
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        return type("ParsedResponse", (), {"output_parsed": self.reply})()


class FakeOpenAIClient:
    def __init__(self, reply: ConversationReply) -> None:
        self.responses = FakeResponses(reply)


class ApiTestCase(unittest.TestCase):
    def test_expected_routes_are_registered(self) -> None:
        route_paths = {route.path for route in app.routes}
        self.assertIn("/health", route_paths)
        self.assertIn("/api/v1/diaries", route_paths)
        self.assertIn(
            "/api/v1/conversations/{diary_id}/messages",
            route_paths,
        )

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

    def test_firestore_permission_error_is_safely_classified(self) -> None:
        submission = DiarySubmission(
            diary="오늘은 권한 오류 응답을 안전하게 확인했습니다.",
            today_tasks=[],
        )

        with self.assertRaises(HTTPException) as context:
            accept_diary(submission, DeniedDiaryRepository())

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(
            context.exception.detail["code"],
            "firestore_permission_denied",
        )
        self.assertNotIn(submission.diary, str(context.exception.detail))

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

    def test_conversation_reply_is_generated_and_persisted(self) -> None:
        context = ConversationContext(
            diary="오늘은 수업 자료를 정리하면서 보람을 느꼈다.",
            today_tasks=[{"text": "자료 정리", "complete": True}],
            history=[],
        )
        repository = FakeConversationRepository(context)
        service = FakeConversationService(sample_reply())
        request = ConversationMessage(
            message="내일은 무리하지 않고 초안을 만들고 싶어요.",
            energy_level="medium",
        )

        response = create_conversation_message(
            "aFbUvMCk3V2bGJK6cmMj",
            request,
            repository,
            service,
        )

        self.assertTrue(response.plan_ready)
        self.assertEqual(service.received, (context, request.message, "medium"))
        self.assertEqual(
            repository.saved_turn,
            ("aFbUvMCk3V2bGJK6cmMj", request.message, response),
        )

    def test_missing_diary_stops_before_model_call(self) -> None:
        repository = FakeConversationRepository(None)
        service = FakeConversationService(sample_reply())
        request = ConversationMessage(message="내일 계획을 세워 주세요.")

        with self.assertRaises(HTTPException) as context:
            create_conversation_message(
                "aFbUvMCk3V2bGJK6cmMj",
                request,
                repository,
                service,
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIsNone(service.received)
        self.assertIsNone(repository.saved_turn)

    def test_openai_request_uses_structured_output_without_storage(self) -> None:
        reply = sample_reply()
        client = FakeOpenAIClient(reply)
        service = OpenAIConversationService(client, "test-model")
        context = ConversationContext(
            diary="오늘은 계획 테스트를 위한 일기를 작성했다.",
            today_tasks=[],
            history=[],
        )

        response = service.respond(context, "내일 계획을 정해요.", "low")

        self.assertIs(response, reply)
        self.assertEqual(client.responses.kwargs["model"], "test-model")
        self.assertIs(
            client.responses.kwargs["text_format"],
            ConversationReply,
        )
        self.assertFalse(client.responses.kwargs["store"])
        self.assertIn("내일 계획을 정해요.", client.responses.kwargs["input"])

    def test_blank_conversation_message_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ConversationMessage(message="   ")

    def test_cors_origins_are_normalized_and_deduplicated(self) -> None:
        self.assertEqual(
            parse_origins(
                "https://1111webdiary.netlify.app/, "
                "https://1111webdiary.netlify.app"
            ),
            ("https://1111webdiary.netlify.app",),
        )

    def test_api_only_accepts_configured_frontend_origin(self) -> None:
        allowed_origins = ("https://1111webdiary.netlify.app",)
        self.assertTrue(
            is_allowed_api_origin(
                "/api/v1/diaries",
                "https://1111webdiary.netlify.app",
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
