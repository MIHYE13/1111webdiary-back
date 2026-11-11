from fastapi import APIRouter

from app.models import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="서버 상태 확인")
def health_check() -> HealthResponse:
    return HealthResponse()
