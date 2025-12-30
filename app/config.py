"""
Agno Agent Service - 配置模块

AgentOS 标准化配置，通过环境变量管理：
- API Keys（模型和工具）
- 数据库连接
- 服务配置

注意：模型参数（temperature, max_tokens, reasoning 等）
现在通过 app/models/ModelConfig 在各 Agent 中独立配置。
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类，从环境变量加载配置"""

    # ----------------- API Keys -----------------

    # OpenRouter API Key（主要模型提供商）
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    
    # 备用模型提供商 API Keys
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # 外部工具 API Keys（按需添加）
    # 示例：常用工具 API Key
    # tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    # serper_api_key: str = Field(default="", alias="SERPER_API_KEY")

    # ----------------- 数据库配置 -----------------

    # 数据库连接 URL
    database_url: str = Field(
        default="postgresql+psycopg://ai:ai@localhost:5532/ai",
        alias="DATABASE_URL"
    )

    # ----------------- 服务配置 -----------------

    # AgentOS 端口 (默认 7777)
    api_port: int = Field(default=7777, alias="API_PORT")

    # AgentOS Host
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")

    # 服务版本
    service_version: str = Field(default="2.0.0", alias="SERVICE_VERSION")

    # 是否启用调试模式（热重载）
    debug_mode: bool = Field(default=False, alias="DEBUG_MODE")

    # Worker 数量（生产模式）
    workers: int = Field(default=4, alias="WORKERS")

    # AgentOS 安全密钥（可选）
    os_security_key: Optional[str] = Field(default=None, alias="OS_SECURITY_KEY")

    # ----------------- Tracing 配置 -----------------

    # 是否启用 OpenTelemetry Tracing
    enable_tracing: bool = Field(default=False, alias="ENABLE_TRACING")

    # Tracing 数据库 URL（默认复用主数据库）
    tracing_db_url: Optional[str] = Field(default=None, alias="TRACING_DB_URL")

    # Tracing 批量导出大小
    tracing_batch_size: int = Field(default=256, alias="TRACING_BATCH_SIZE")

    # ----------------- MCP 配置 -----------------

    # 是否启用 MCP Server（暴露工具给外部 Agent）
    enable_mcp_server: bool = Field(default=False, alias="ENABLE_MCP_SERVER")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
