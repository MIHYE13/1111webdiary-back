from fastapi import APIRouter, Depends, status

from app.models import DiaryAcceptance, DiarySubmission
from app.repositories.diaries import DiaryRepository, get_diary_repository


router = APIRouter(prefix="/diaries", tags=["diaries"])


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
    document_id = repository.save(submission)
    return DiaryAcceptance(
        request_id=document_id,
        message="오늘의 기록을 안전하게 저장했습니다.",
    )
