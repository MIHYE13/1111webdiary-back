from typing import Annotated, Literal

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
    persisted: Literal[True] = True


class IntegrationStatus(BaseModel):
    firestore: Literal["configured"] = "configured"


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["webdiary-api"] = "webdiary-api"
    integrations: IntegrationStatus = Field(default_factory=IntegrationStatus)


EnergyLevel = Literal["low", "medium", "high"]


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=500)
    energy_level: EnergyLevel = "medium"

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("메시지는 공백만 입력할 수 없습니다.")
        return normalized


class TomorrowPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    must_do: str = Field(max_length=200)
    nice_to_do: list[Annotated[str, Field(max_length=200)]] = Field(
        max_length=2
    )
    easy_first_step: str = Field(max_length=200)
    recovery: str = Field(max_length=200)
    low_energy_alternative: str = Field(max_length=200)


class ConversationReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    angel: str = Field(min_length=1, max_length=240)
    devil: str = Field(min_length=1, max_length=240)
    facilitator: str = Field(min_length=1, max_length=240)
    plan_ready: bool
    plan: TomorrowPlan | None = None
