"""
Agno Agent Service - 配置模块

三层配置优先级系统:
  Layer 3: Agent 参数     ← 运行时覆盖 (最高，通过函数参数传递)
  Layer 2: .env           ← 敏感凭证 (环境变量)
  Layer 1: configuration.yaml  ← 业务配置 (可提交)
  Defaults: 代码中的默认值

AgentOS 标准化配置，管理：
- API Keys（模型和工具）
- 数据库连接
- 服务配置

YAML 配置说明:
  configuration.yaml 同时服务于两个目的：
  1. AgentOS 配置 - 嵌套结构如 chat.quick_prompts, memory.dbs 等
  2. Settings 配置 - 顶级 key 如 model_name, debug_mode 等

  本模块只读取 YAML 的顶级 key 来填充 Settings 字段。
  如需通过 YAML 配置 Settings，请添加顶级 key：

  示例 configuration.yaml:
    # Settings 配置 (顶级 key)
    model_name: gpt-4o

    # AgentOS 配置 (嵌套结构，由 AgentOS 读取)
    chat:
      quick_prompts: {}
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """YAML 配置源 - 从 configuration.yaml 加载配置"""

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        self._yaml_data: dict[str, Any] = {}
        self._load_yaml()

    def _load_yaml(self) -> None:
        yaml_path = Path(__file__).parent.parent / "configuration.yaml"
        if yaml_path.exists():
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    self._yaml_data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError):
                self._yaml_data = {}

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        field_value = self._yaml_data.get(field_name)
        return field_value, field_name, False

    def __call__(self) -> dict[str, Any]:
        return {
            field_name: self._yaml_data.get(field_name)
            for field_name in self.settings_cls.model_fields
            if field_name in self._yaml_data
        }


class Settings(BaseSettings):
    """应用配置类 - 三层优先级加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ----------------- API Keys -----------------

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # ----------------- 数据库配置 -----------------

    database_url: str = Field(
        default="postgresql+psycopg://ai:ai@localhost:5532/ai", alias="DATABASE_URL"
    )

    # ----------------- 服务配置 -----------------

    api_port: int = Field(default=7777, alias="API_PORT")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    service_version: str = Field(default="2.0.0", alias="SERVICE_VERSION")
    debug_mode: bool = Field(default=False, alias="DEBUG_MODE")
    workers: int = Field(default=4, alias="WORKERS")
    os_security_key: str | None = Field(default=None, alias="OS_SECURITY_KEY")

    # ----------------- 从 YAML 加载的业务配置 -----------------

    model_name: str = Field(default="gpt-4o", alias="MODEL_NAME")

    # ----------------- Tracing 配置 -----------------

    enable_tracing: bool = Field(default=False, alias="ENABLE_TRACING")
    tracing_db_url: str | None = Field(default=None, alias="TRACING_DB_URL")
    tracing_batch_size: int = Field(default=256, alias="TRACING_BATCH_SIZE")

    # ----------------- MCP 配置 -----------------

    enable_mcp_server: bool = Field(default=False, alias="ENABLE_MCP_SERVER")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        配置优先级 (从高到低):
        1. init_settings: 实例化时传入的参数 (Agent 参数)
        2. env_settings: 环境变量
        3. dotenv_settings: .env 文件
        4. yaml_settings: configuration.yaml 文件
        5. file_secret_settings: 密钥文件
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
