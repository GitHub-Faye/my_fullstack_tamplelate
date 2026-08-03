import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from pathlib import Path

# 获取当前文件所在目录（app/core/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ======================== 工具函数 ========================
def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


# ======================== 应用配置类（Pydantic v2） ========================
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # ======================== API 配置 ========================
    API_V1_STR: str = "/v1"

    # ======================== 安全配置 ========================
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # ======================== CORS 跨域配置 ========================
    CORS_ALLOW_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.CORS_ALLOW_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    # ======================== 项目与监控配置 ========================
    PROJECT_NAME: str
    DOMAIN: str = "localhost"
    SENTRY_DSN: HttpUrl | None = None
    DEBUG: bool = True

    # ======================== MySQL 数据库配置 ========================
    DATABASE_URL: str = "mysql+asyncmy://hjc:hjc.123654@43.137.99.117:63697/xingdian"

    # ======================== SMTP 邮件配置 ========================
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

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

    EMAIL_TEST_USER: EmailStr = "test@example.com"

    # ======================== 初始超管账户 ========================
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # ======================== JWT 配置 ========================
    ALGORITHM: str = "HS256"
    BIND: str | None = None
    WORKERS: int | None = None

    # ======================== 文件上传配置 ========================
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    # ======================== 安全检查方法 ========================
    def _check_default_secret(self, var_name: str, value: str | None) -> None:
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
        self._check_default_secret("FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD)
        return self


# 创建单例
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()