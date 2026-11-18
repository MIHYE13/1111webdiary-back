from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import diaries, health
from app.settings import load_settings, normalize_origin


def is_allowed_api_origin(
    path: str,
    origin: str | None,
    allowed_origins: Sequence[str],
) -> bool:
    if not path.startswith("/api/"):
        return True
    if not origin:
        return False
    try:
        return normalize_origin(origin) in allowed_origins
    except ValueError:
        return False


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(
        title="다음 장 API",
        version="0.1.0",
        description=(
            "오늘의 일기와 오늘 할 일을 Firestore에 저장하는 백엔드입니다."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def enforce_api_origin(request: Request, call_next):
        if not is_allowed_api_origin(
            request.url.path,
            request.headers.get("origin"),
            settings.cors_origins,
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "Origin is not allowed"},
            )
        return await call_next(request)

    app.include_router(health.router)
    app.include_router(diaries.router, prefix="/api/v1")
    return app


app = create_app()
