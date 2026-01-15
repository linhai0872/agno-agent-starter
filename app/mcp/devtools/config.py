"""
Agno DevTools MCP Server - Configuration Module.

Provides configuration for MCP DevTools using pydantic-settings.

**零配置设计**: 自动从项目已有环境变量派生默认值
- API_PORT -> api_url (http://127.0.0.1:{port})
- DATABASE_URL -> db_url

开发者无需配置 MCP_DEVTOOLS_* 变量，即可开箱即用。
如需覆盖，可设置 MCP_DEVTOOLS_API_URL 或 MCP_DEVTOOLS_DB_URL。
"""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _derive_api_url() -> str:
    """从 API_PORT 环境变量派生 API URL，默认 7777"""
    port = os.getenv("API_PORT", "7777")
    return f"http://127.0.0.1:{port}"


def _derive_db_url() -> str:
    """从 DATABASE_URL 环境变量派生数据库 URL，默认使用脚手架标准配置"""
    return os.getenv("DATABASE_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")


class DevToolsConfig(BaseSettings):
    """DevTools MCP Server configuration.
    
    自动从项目环境变量派生配置，真正零配置开箱即用。
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_DEVTOOLS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_url: str = Field(
        default_factory=_derive_api_url,
        description="Agno REST API base URL (auto-derived from API_PORT)",
    )

    db_url: str = Field(
        default_factory=_derive_db_url,
        description="PostgreSQL database URL (auto-derived from DATABASE_URL)",
    )

    db_pool_size: int = Field(
        default=5,
        description="Database connection pool size",
        ge=1,
        le=20,
    )

    http_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds (includes cold start)",
        ge=5.0,
        le=300.0,
    )


_config: DevToolsConfig | None = None


def get_config() -> DevToolsConfig:
    """Get DevTools configuration singleton."""
    global _config
    if _config is None:
        _config = DevToolsConfig()
    return _config
