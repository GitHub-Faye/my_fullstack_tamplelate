from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # CORS 配置
    cors_allow_origins: List[str] = [
        "http://localhost.tiangolo.com",
        "https://localhost.tiangolo.com",
        "http://localhost",
        "http://localhost:8080",
    ]
    
    # 其他常用配置示例
    app_name: str = "MY FULLSTACK TEMPLATE"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "postgresql+asyncpg://postgres:postgres123@localhost:5432/appdb"
    
    # JWT 配置
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",           # 自动加载 .env 文件
        env_file_encoding="utf-8",
        extra="ignore",            # 忽略多余的环境变量
        env_prefix="",             # 可选：加前缀如 "MYAPP_" 
        case_sensitive=False
    )

    # 如果想支持逗号分隔的环境变量字符串（更灵活）
    @property
    def cors_origins(self) -> List[str]:
        # 如果环境变量是字符串 "http://a.com,http://b.com"，就自动分割
        if isinstance(self.cors_allow_origins, str):
            return [origin.strip() for origin in self.cors_allow_origins.split(",")]
        return self.cors_allow_origins

# 创建单例（推荐用 lru_cache 缓存）
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()
