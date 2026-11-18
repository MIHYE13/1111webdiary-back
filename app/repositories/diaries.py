from functools import lru_cache
from typing import Protocol

from google.cloud import firestore

from app.models import DiarySubmission
from app.settings import load_settings


DIARIES_COLLECTION = "diary_entries"


class DiaryRepository(Protocol):
    def save(self, submission: DiarySubmission) -> str:
        """Persist a diary and return its document identifier."""


class FirestoreDiaryRepository:
    def __init__(
        self,
        client: firestore.Client,
        collection_name: str = DIARIES_COLLECTION,
    ) -> None:
        self._client = client
        self._collection_name = collection_name

    def save(self, submission: DiarySubmission) -> str:
        document = self._client.collection(self._collection_name).document()
        document.set(
            {
                "diary": submission.diary,
                "today_tasks": [
                    task.model_dump() for task in submission.today_tasks
                ],
                "created_at": firestore.SERVER_TIMESTAMP,
                "schema_version": 1,
            }
        )
        return document.id


@lru_cache(maxsize=1)
def get_diary_repository() -> FirestoreDiaryRepository:
    settings = load_settings()
    client = firestore.Client(
        project=settings.firebase_project_id,
        database=settings.firestore_database_id,
    )
    return FirestoreDiaryRepository(client)
