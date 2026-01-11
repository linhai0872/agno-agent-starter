"""
Ollama 模型适配器

使用 Agno 原生 Ollama 集成。
支持: Llama 3.2, Qwen2.5, DeepSeek 等本地部署模型
特性: 本地部署, 无需 API Key
"""

import logging
import os
from typing import TYPE_CHECKING

from app.models.config import ModelConfig, ProjectConfig

if TYPE_CHECKING:
    from agno.models.ollama import Ollama

logger = logging.getLogger(__name__)


def _get_host(
    config: ModelConfig,
    project_config: ProjectConfig | None,
) -> str:
    """
    三层 Host 优先级获取

    1. Agent 级: config.ollama_host_env
    2. Project 级: 暂不支持
    3. Global 级: OLLAMA_HOST 或 config.ollama_host
    """
    # 1. Agent 级
    if config.ollama_host_env:
        host = os.environ.get(config.ollama_host_env)
        if host:
            return host

    # 2. Global 级 (环境变量)
    host = os.environ.get("OLLAMA_HOST")
    if host:
        return host

    # 3. 默认配置
    return config.ollama_host


def create_ollama_model(
    config: ModelConfig,
    project_config: ProjectConfig | None = None,
) -> "Ollama":
    """
    创建 Ollama 模型实例

    Args:
        config: 模型配置
        project_config: 项目级配置（Ollama 不使用）

    Returns:
        Agno Ollama 模型实例
    """
    try:
        from agno.models.ollama import Ollama
    except ImportError:
        raise ImportError("ollama package not found. Install with: pip install ollama")

    host = _get_host(config, project_config)

    # 构建参数
    params = {"id": config.model_id, "host": host}

    # 通用参数
    if config.temperature is not None:
        params["options"] = params.get("options", {})
        params["options"]["temperature"] = config.temperature
    if config.top_p is not None:
        params["options"] = params.get("options", {})
        params["options"]["top_p"] = config.top_p
    if config.top_k is not None:
        params["options"] = params.get("options", {})
        params["options"]["top_k"] = config.top_k
    if config.stop:
        params["stop"] = config.stop

    # 结构化输出 (Ollama 通过 format 参数支持)
    if config.structured_output.enabled:
        params["format"] = "json"
        if config.structured_output.json_schema:
            params["format"] = config.structured_output.json_schema

    logger.info("Creating Ollama model: %s at %s", config.model_id, host)

    return Ollama(**params)
