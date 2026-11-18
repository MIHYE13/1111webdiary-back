from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Protocol

from google.cloud import firestore

from app.models import ConversationReply
from app.repositories.diaries import DIARIES_COLLECTION
from app.settings import load_settings


@dataclass(frozen=True)
class ConversationContext:
    diary: str
    today_tasks: list[dict[str, Any]]
    history: list[dict[str, Any]]


class ConversationRepository(Protocol):
    def get_context(self, diary_id: str) -> ConversationContext | None:
        """Load the private diary context for a conversation."""

    def append_turn(
        self,
        diary_id: str,
        user_message: str,
        reply: ConversationReply,
    ) -> None:
        """Persist one user message and its structured reply."""


class FirestoreConversationRepository:
    def __init__(
        self,
        client: firestore.Client,
        collection_name: str = DIARIES_COLLECTION,
    ) -> None:
        self._client = client
        self._collection_name = collection_name

    def get_context(self, diary_id: str) -> ConversationContext | None:
        document = self._client.collection(self._collection_name).document(
            diary_id
        )
        snapshot = document.get()
        if not snapshot.exists:
            return None

        data = snapshot.to_dict() or {}
        recent_turns = list(
            document.collection("conversation")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(6)
            .stream()
        )
        return ConversationContext(
            diary=str(data.get("diary", "")),
            today_tasks=list(data.get("today_tasks", [])),
            history=[
                turn.to_dict() or {} for turn in reversed(recent_turns)
            ],
        )

    def append_turn(
        self,
        diary_id: str,
        user_message: str,
        reply: ConversationReply,
    ) -> None:
        document = self._client.collection(self._collection_name).document(
            diary_id
        )
        turn = document.collection("conversation").document()
        updates: dict[str, Any] = {
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        if reply.plan_ready:
            updates["tomorrow_plan"] = reply.plan.model_dump()

        batch = self._client.batch()
        batch.set(
            turn,
            {
                "user_message": user_message,
                "reply": reply.model_dump(),
                "created_at": datetime.now(timezone.utc),
            },
        )
        batch.update(document, updates)
        batch.commit()


@lru_cache(maxsize=1)
def get_conversation_repository() -> FirestoreConversationRepository:
    settings = load_settings()
    client = firestore.Client(database=settings.firestore_database_id)
    return FirestoreConversationRepository(client)
