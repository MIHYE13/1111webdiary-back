from fastapi import APIRouter, Depends, HTTPException, status
from google.api_core.exceptions import (
    FailedPrecondition,
    GoogleAPIError,
    NotFound,
    PermissionDenied,
)
from google.auth.exceptions import DefaultCredentialsError

from app.models import DiaryAcceptance, DiarySubmission
from app.repositories.diaries import DiaryRepository, get_diary_repository


router = APIRouter(prefix="/diaries", tags=["diaries"])


def storage_unavailable(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": code, "message": message},
    )


@router.post(
    "",
    response_model=DiaryAcceptance,
    status_code=status.HTTP_202_ACCEPTED,
    summary="일기 입력 검증",
)
def accept_diary(
    submission: DiarySubmission,
    repository: DiaryRepository = Depends(get_diary_repository),
) -> DiaryAcceptance:
    try:
        document_id = repository.save(submission)
    except PermissionDenied as error:
        raise storage_unavailable(
            "firestore_permission_denied",
            "Firestore 서비스 계정 권한을 확인해 주세요.",
        ) from error
    except (NotFound, FailedPrecondition) as error:
        raise storage_unavailable(
            "firestore_database_unavailable",
            "Firestore 데이터베이스 생성 및 모드를 확인해 주세요.",
        ) from error
    except DefaultCredentialsError as error:
        raise storage_unavailable(
            "firestore_credentials_unavailable",
            "Cloud Run 런타임 서비스 계정을 확인해 주세요.",
        ) from error
    except GoogleAPIError as error:
        raise storage_unavailable(
            "firestore_service_error",
            "Firestore 서비스 연결을 잠시 후 다시 시도해 주세요.",
        ) from error

    return DiaryAcceptance(
        request_id=document_id,
        message="오늘의 기록을 안전하게 저장했습니다.",
    )
