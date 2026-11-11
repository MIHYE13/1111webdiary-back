from fastapi import FastAPI

from app.routers import diaries, health


def create_app() -> FastAPI:
    app = FastAPI(
        title="다음 장 API",
        version="0.1.0",
        description=(
            "오늘의 일기를 받아 다음 단계로 전달하기 위한 백엔드입니다. "
            "현재는 OpenAI 에이전트와 Firestore에 연결하지 않습니다."
        ),
    )
    app.include_router(health.router)
    app.include_router(diaries.router, prefix="/api/v1")
    return app


app = create_app()
