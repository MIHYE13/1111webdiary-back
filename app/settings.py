import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from dotenv import load_dotenv


VALID_APP_ENVIRONMENTS = {"development", "test", "production"}


def normalize_origin(value: str) -> str:
    origin = value.strip().rstrip("/")
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"Invalid CORS origin: {value!r}")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def parse_origins(raw_value: str) -> tuple[str, ...]:
    origins = tuple(
        dict.fromkeys(
            normalize_origin(value)
            for value in raw_value.split(",")
            if value.strip()
        )
    )
    if "*" in origins:
        raise ValueError("Wildcard CORS origins are not allowed")
    return origins


@dataclass(frozen=True)
class Settings:
    app_env: str
    cors_origins: tuple[str, ...]
    firestore_database_id: str
    openai_model: str


def load_settings() -> Settings:
    load_dotenv(override=False)

    app_env = os.getenv("APP_ENV", "development").strip().lower()
    if app_env not in VALID_APP_ENVIRONMENTS:
        raise ValueError(
            "APP_ENV must be one of: development, test, production"
        )

    cors_origins = parse_origins(os.getenv("CORS_ORIGINS", ""))
    if app_env == "production" and not cors_origins:
        raise ValueError("CORS_ORIGINS is required when APP_ENV=production")

    firestore_database_id = os.getenv(
        "FIRESTORE_DATABASE_ID", "(default)"
    ).strip()
    if not firestore_database_id:
        raise ValueError("FIRESTORE_DATABASE_ID cannot be empty")

    openai_model = os.getenv("OPENAI_MODEL", "gpt-6-luna").strip()
    if not openai_model:
        raise ValueError("OPENAI_MODEL cannot be empty")

    return Settings(
        app_env=app_env,
        cors_origins=cors_origins,
        firestore_database_id=firestore_database_id,
        openai_model=openai_model,
    )
