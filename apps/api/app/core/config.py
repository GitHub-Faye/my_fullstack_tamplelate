import secrets
import warnings
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import (
    BeforeValidator,
    EmailStr,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取当前文件所在目录（app/core/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ======================== 工具函数 ========================
def parse_cors(v: Any) -> list[str] | str:
    """
    解析 CORS 源列表。
    
    支持两种格式：
    1. 字符串（逗号分隔）："http://localhost,http://localhost:5173" -> ["http://localhost", "http://localhost:5173"]
    2. 列表：["http://localhost", "http://localhost:5173"]
    
    此函数用作 BeforeValidator，在 Pydantic 字段验证前转换输入。
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


# ======================== 应用配置类（Pydantic v2） ========================
class Settings(BaseSettings):
    """
    应用全局配置类。
    
    基于 Pydantic v2 的 BaseSettings，自动从 .env 文件和环境变量加载配置。
    所有属性都可通过环境变量覆盖（遵循环境变量名称约定）。
    """
    
    # Pydantic v2 配置字典
    model_config = SettingsConfigDict(
        # 从 apps/api/.env 文件加载
        env_file=BASE_DIR / ".env",
        # 忽略空值环境变量
        env_ignore_empty=True,
        # 忽略额外字段（不在模型中定义的环境变量）
        extra="ignore",
    )
    
    # ======================== API 配置 ========================
    API_V1_STR: str = "/v1"  # API 版本前缀
    
    # ======================== 安全配置 ========================
    # ⚠️ 生产环境必须设置为强随机字符串，不能为 "changethis"
    # 默认值：动态生成 32 字节的 URL 安全随机字符串
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # 访问令牌过期时间（分钟）
    # 60 分钟 × 24 小时 × 8 天 = 8 天
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # 前端应用 URL（用于生成邮件链接）
    FRONTEND_HOST: str = "http://localhost:5173"
    
    # 运行环境：本地开发、预发布、生产
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # ======================== CORS 跨域配置 ========================
    # CORS_ALLOW_ORIGINS：后端允许的跨域源列表
    # 使用 BeforeValidator 将字符串自动转换为列表
    # 本地开发可用 ["*"] 允许所有来源（注意：AnyUrl 无法表示 "*"，故使用 str）
    CORS_ALLOW_ORIGINS: Annotated[
        list[str] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """
        Pydantic v2 计算属性：返回所有 CORS 源（包含前端 URL）。

        组合：
        1. CORS_ALLOW_ORIGINS 中的所有源
        2. FRONTEND_HOST（自动追加）

        返回值为规范化的字符串列表（移除末尾 /）。
        """
        # 允许所有来源时直接透传 "*"
        # （不要追加 FRONTEND_HOST，避免破坏通配符语义，也不要去尾斜杠）
        if self.CORS_ALLOW_ORIGINS == ["*"]:
            return ["*"]
        return [str(origin).rstrip("/") for origin in self.CORS_ALLOW_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    # ======================== 项目与监控配置 ========================
    PROJECT_NAME: str  # 项目名称
    
    # 域名配置
    DOMAIN: str = "localhost"
    
    # Sentry 错误追踪服务 DSN（可选）
    # 用于生产环境的异常监控和告警
    SENTRY_DSN: HttpUrl | None = None

    DEBUG: bool = True  # 调试模式开关（生产环境应设置为 False）

    # ======================== 数据库配置 ========================
    # 优先使用 DATABASE_URL（支持任意 SQLAlchemy 异步方言，如 SQLite / MySQL / PostgreSQL）
    # 未设置 DATABASE_URL 时，回退到 PostgreSQL 环境变量；两者都未配置则默认本地 SQLite 文件库
    DATABASE_URL: str | None = None

    # PostgreSQL 配置（可选：仅在未设置 DATABASE_URL 时生效）
    POSTGRES_SERVER: str | None = None  # 数据库服务器地址
    POSTGRES_PORT: int = 5432  # 数据库端口（默认 5432）
    POSTGRES_USER: str | None = None  # 数据库用户名
    POSTGRES_PASSWORD: str | None = None  # 数据库密码（⚠️ 生产必改）
    POSTGRES_DB: str | None = None  # 数据库名称

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Pydantic v2 计算属性：生成 SQLAlchemy 数据库连接 URI。

        优先级：
        1. DATABASE_URL（.env 中显式指定，例如 sqlite+aiosqlite:///./app.db）
        2. PostgreSQL 环境变量（postgresql+asyncpg://user:password@host:port/dbname）
        3. 默认本地 SQLite 文件库（无需外部数据库即可启动）
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if self.POSTGRES_SERVER and self.POSTGRES_USER and self.POSTGRES_DB:
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD or ''}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

        return f"sqlite+aiosqlite:///{BASE_DIR / 'app.db'}"

    # ======================== SMTP 邮件配置 ========================
    SMTP_TLS: bool = True  # 是否使用 STARTTLS（通常为 True）
    SMTP_SSL: bool = False  # 是否使用 SSL/TLS 加密连接（通常为 False）
    SMTP_PORT: int = 587  # SMTP 端口（587 用于 STARTTLS，465 用于 SSL）
    SMTP_HOST: str | None = None  # SMTP 服务器地址
    SMTP_USER: str | None = None  # SMTP 账户用户名
    SMTP_PASSWORD: str | None = None  # SMTP 账户密码
    EMAILS_FROM_EMAIL: EmailStr | None = None  # 发送邮件的地址
    EMAILS_FROM_NAME: str | None = None  # 发送邮件的名称

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        """
        Pydantic v2 模型验证器（mode='after'）：在模型验证完成后执行。
        
        作用：若 EMAILS_FROM_NAME 未配置，默认使用 PROJECT_NAME。
        """
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48  # 密码重置令牌有效期（小时）

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        """
        Pydantic v2 计算属性：检查邮件服务是否启用。
        
        条件：SMTP_HOST 和 EMAILS_FROM_EMAIL 都配置了。
        """
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # 邮件测试账户
    
    # ======================== 初始超管账户 ========================
    FIRST_SUPERUSER: EmailStr  # 首个超管邮箱
    FIRST_SUPERUSER_PASSWORD: str  # 首个超管密码（⚠️ 生产必改）
    
    # ======================== JWT 配置 ========================
    ALGORITHM: str = "HS256"  # JWT 签名算法
    BIND: str | None = None  # Gunicorn 绑定地址（可通过环境变量覆盖）
    WORKERS: int | None = None  # Gunicorn worker 数量（可通过

    # ======================== 安全检查方法 ========================
    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        """
        检查关键密钥是否使用了默认值 "changethis"。
        
        - 本地开发：发出 warning（不阻止启动）
        - 生产环境：抛出 ValueError（拒绝启动）
        """
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
        """
        Pydantic v2 模型验证器：在模型验证完成后检查所有关键密钥。
        
        检查项：
        1. SECRET_KEY：JWT 签名密钥
        2. POSTGRES_PASSWORD：数据库密码
        3. FIRST_SUPERUSER_PASSWORD：超管密码
        
        这是安全最佳实践：防止生产环境意外使用默认密钥。
        """
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self

# 创建单例（推荐用 lru_cache 缓存）
from functools import lru_cache


@lru_cache
def get_settings() -> Settings:
    return Settings()
