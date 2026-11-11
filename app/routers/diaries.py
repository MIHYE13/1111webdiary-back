from uuid import uuid4

from fastapi import APIRouter, status

from app.models import DiaryAcceptance, DiarySubmission


router = APIRouter(prefix="/diaries", tags=["diaries"])


@router.post(
    "",
    response_model=DiaryAcceptance,
    status_code=status.HTTP_202_ACCEPTED,
    summary="일기 입력 검증",
)
def accept_diary(submission: DiarySubmission) -> DiaryAcceptance:
    # 민감한 일기 원문을 로그, 응답 또는 저장소에 남기지 않는다.
    # submission은 현재 요청의 유효성 확인에만 사용한다.
    del submission

    return DiaryAcceptance(
        request_id=str(uuid4()),
        message="일기 형식을 확인했습니다. 에이전트 연결은 아직 준비되지 않았습니다.",
    )
