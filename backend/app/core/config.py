"""应用配置模块。

统一从环境变量或 backend/.env 文件中读取运行配置，
避免在业务代码中硬编码环境相关参数。
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# backend 目录的绝对路径，用于稳定定位 .env 文件。
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """DevFlow 应用配置。"""

    # 应用基础信息
    app_name: str = "DevFlow Platform"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "production"] = "local"
    debug: bool = False

    # API 版本统一前缀
    api_v1_prefix: str = "/api/v1"

    # JWT 认证配置
    jwt_secret_key: str = "local-development-secret-change-before-deploy"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # MySQL 数据库连接配置
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "devflow"
    mysql_password: str
    mysql_database: str = "devflow"

    # Redis 与 Celery 属于可选增强能力，核心 API 不在启动时强依赖它们。
    redis_url: str = "redis://127.0.0.1:6379/0"
    celery_broker_url: str = "redis://127.0.0.1:6379/1"
    celery_result_backend: str = "redis://127.0.0.1:6379/2"

    model_config = SettingsConfigDict(
        # 从 backend/.env 读取本地环境配置。
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",

        # 环境变量名称不区分大小写。
        case_sensitive=False,

        # 忽略暂未被 FastAPI 使用的环境变量。
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """获取应用配置单例。

    缓存配置对象，避免重复读取和解析环境变量。
    """

    return Settings()


# 提供全局配置实例，供应用初始化和基础设施模块使用。
settings = get_settings()
