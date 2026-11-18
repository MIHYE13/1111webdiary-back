from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from google.api_core.exceptions import GoogleAPIError
from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError

from app.models import ConversationMessage, ConversationReply
from app.repositories.conversations import (
    ConversationRepository,
    get_conversation_repository,
)
from app.services.conversation import (
    ConversationService,
    get_conversation_service,
)


router = APIRouter(prefix="/conversations", tags=["conversations"])


def service_unavailable(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": code, "message": message},
    )


@router.post(
    "/{diary_id}/messages",
    response_model=ConversationReply,
    summary="천사와 악마 관점으로 내일 계획 대화하기",
)
def create_conversation_message(
    diary_id: Annotated[str, Path(pattern=r"^[A-Za-z0-9]{20}$")],
    request: ConversationMessage,
    repository: ConversationRepository = Depends(get_conversation_repository),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationReply:
    try:
        context = repository.get_context(diary_id)
    except GoogleAPIError as error:
        raise service_unavailable(
            "conversation_storage_failed",
            "대화 기록을 불러오지 못했습니다.",
        ) from error

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "diary_not_found", "message": "기록을 찾지 못했습니다."},
        )

    try:
        reply = service.respond(context, request.message, request.energy_level)
        repository.append_turn(diary_id, request.message, reply)
        return reply
    except AuthenticationError as error:
        raise service_unavailable(
            "openai_authentication_failed",
            "OpenAI API 키 설정을 확인해 주세요.",
        ) from error
    except RateLimitError as error:
        raise service_unavailable(
            "openai_rate_limited",
            "대화 요청이 많습니다. 잠시 후 다시 시도해 주세요.",
        ) from error
    except APIConnectionError as error:
        raise service_unavailable(
            "openai_connection_failed",
            "AI 서비스 연결을 잠시 후 다시 시도해 주세요.",
        ) from error
    except APIError as error:
        raise service_unavailable(
            "openai_service_error",
            "AI 응답을 생성하지 못했습니다.",
        ) from error
    except GoogleAPIError as error:
        raise service_unavailable(
            "conversation_storage_failed",
            "대화 저장을 잠시 후 다시 시도해 주세요.",
        ) from error
    except RuntimeError as error:
        raise service_unavailable(
            "openai_invalid_response",
            "AI 응답 형식을 확인하지 못했습니다.",
        ) from error
