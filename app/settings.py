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

    return Settings(app_env=app_env, cors_origins=cors_origins)
