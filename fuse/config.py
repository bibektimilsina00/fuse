import secrets
import warnings
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> Union[List[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return (
                f"http://{self.DOMAIN}:8000"
                if self.DOMAIN == "localhost"
                else f"http://{self.DOMAIN}"
            )
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[
        Union[List[str], str], BeforeValidator(parse_cors)
    ] = [
        "http://localhost:5678",
        "http://127.0.0.1:5678",
        "http://localhost:3000",  # For local frontend development
        "http://127.0.0.1:3000",
    ]

    PROJECT_NAME: str = "Fuse"
    SENTRY_DSN: Optional[HttpUrl] = None

    # Database configuration - defaults to SQLite for easy setup
    # Set POSTGRES_SERVER to use PostgreSQL instead
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = "changethis"
    POSTGRES_DB: str = "app"

    # SQLite database path (used when POSTGRES_SERVER is not set)
    SQLITE_DB_PATH: str = "fuse.db"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Returns the database URI. Uses SQLite by default for easy setup.
        Set POSTGRES_SERVER environment variable to use PostgreSQL instead.
        """
        if self.POSTGRES_SERVER:
            # Use PostgreSQL if configured
            return str(
                MultiHostUrl.build(
                    scheme="postgresql+psycopg",
                    username=self.POSTGRES_USER,
                    password=self.POSTGRES_PASSWORD,
                    host=self.POSTGRES_SERVER,
                    port=self.POSTGRES_PORT,
                    path=self.POSTGRES_DB,
                )
            )
        else:
            # Use SQLite by default
            return f"sqlite:///{self.SQLITE_DB_PATH}"

    # Redis & Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.REDIS_URL

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    # TODO: update type to EmailStr when sqlmodel supports it
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # TODO: update type to EmailStr when sqlmodel supports it
    EMAIL_TEST_USER: str = "test@example.com"
    # TODO: update type to EmailStr when sqlmodel supports it
    FIRST_SUPERUSER: str = "admin@fuse.io"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"

    # AI Service API Keys
    GOOGLE_AI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None

    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SLACK_CLIENT_ID: Optional[str] = None
    SLACK_CLIENT_SECRET: Optional[str] = None
    DISCORD_CLIENT_ID: Optional[str] = None
    DISCORD_CLIENT_SECRET: Optional[str] = None

    FRONTEND_URL: str = "http://localhost:3000"

    def _check_default_secret(self, var_name: str, value: Optional[str]) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        # Only check PostgreSQL password if using PostgreSQL
        if self.POSTGRES_SERVER:
            self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
