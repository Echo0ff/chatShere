"""
ChatSphere 应用配置
"""
import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用设置"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"  # 忽略额外字段
    )

    # 环境配置
    environment: str = "development"

    # 应用基础配置
    app_name: str = "ChatSphere API"
    app_version: str = "2.0.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # 安全配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS配置
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://49.232.202.209:8999",
        "http://frontend:8080",
    ]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = True

    # 数据库配置
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "chatsphere"
    postgres_echo: bool = False

    # 添加 DATABASE_URL 环境变量支持
    database_url_env: Optional[str] = Field(None, alias="DATABASE_URL")

    @property
    def database_url(self) -> str:
        # 优先使用环境变量中的 DATABASE_URL
        if self.database_url_env:
            return self.database_url_env.replace("postgresql://", "postgresql+asyncpg://")
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_expire_seconds: int = 3600

    # 添加 REDIS_URL 环境变量支持
    redis_url_env: Optional[str] = Field(None, alias="REDIS_URL")

    @property
    def redis_url(self) -> str:
        # 优先使用环境变量中的 REDIS_URL
        if self.redis_url_env:
            return self.redis_url_env
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # OAuth2配置
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None

    # WebSocket配置
    websocket_heartbeat_interval: int = 30
    websocket_timeout: int = 60
    max_connections_per_user: int = 5

    # 消息配置
    max_message_length: int = 1000
    max_file_size_mb: int = 10
    offline_message_retention_days: int = 30

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 速率限制
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds


# 创建全局设置实例
settings = Settings()


# 环境检测
def is_development() -> bool:
    return settings.environment == "development"


def is_production() -> bool:
    return settings.environment == "production"


def is_testing() -> bool:
    return settings.environment == "testing"
