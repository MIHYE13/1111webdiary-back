from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TodayTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=80)
    complete: bool = False

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("할 일은 공백만 입력할 수 없습니다.")
        return normalized


class DiarySubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diary: str = Field(min_length=10, max_length=2000)
    today_tasks: list[TodayTask] = Field(default_factory=list, max_length=50)

    @field_validator("diary")
    @classmethod
    def normalize_diary(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("일기는 공백을 제외하고 10자 이상이어야 합니다.")
        return normalized


class DiaryAcceptance(BaseModel):
    request_id: str
    status: Literal["accepted"] = "accepted"
    message: str
    persisted: bool = False
    agent_status: Literal["not_connected"] = "not_connected"


class IntegrationStatus(BaseModel):
    agent: Literal["not_connected"] = "not_connected"
    firestore: Literal["not_connected"] = "not_connected"


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["webdiary-api"] = "webdiary-api"
    integrations: IntegrationStatus = Field(default_factory=IntegrationStatus)
