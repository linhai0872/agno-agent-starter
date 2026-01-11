"""
OpenAI 模型适配器

使用 Agno 原生 OpenAI 集成。
支持: GPT-4o, GPT-4.1, o1/o3 系列
"""

import logging
import os
from typing import TYPE_CHECKING

from app.models.config import PROVIDER_DEFAULT_ENV_VARS, ModelConfig, ModelProvider, ProjectConfig

if TYPE_CHECKING:
    from agno.models.openai import OpenAIChat

logger = logging.getLogger(__name__)


def _get_api_key(
    config: ModelConfig,
    project_config: ProjectConfig | None,
) -> str | None:
    """三层 API Key 优先级获取"""
    # 1. Agent 级
    if config.api_key_env:
        api_key = os.environ.get(config.api_key_env)
        if api_key:
            return api_key

    # 2. Project 级
    if project_config and project_config.api_key_env:
        api_key = os.environ.get(project_config.api_key_env)
        if api_key:
            return api_key

    # 3. Global 级
    default_env = PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.OPENAI)
    if default_env:
        return os.environ.get(default_env)

    return None


def create_openai_model(
    config: ModelConfig,
    project_config: ProjectConfig | None = None,
) -> "OpenAIChat":
    """
    创建 OpenAI 模型实例

    Args:
        config: 模型配置
        project_config: 项目级配置

    Returns:
        Agno OpenAI 模型实例
    """
    try:
        from agno.models.openai import OpenAIChat
    except ImportError:
        raise ImportError("agno package not found. Install with: pip install agno")

    api_key = _get_api_key(config, project_config)

    if not api_key:
        raise ValueError(
            "OpenAI API Key not found. Please set one of: "
            f"config.api_key_env, project_config.api_key_env, or {PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.OPENAI)}"
        )

    # 构建参数
    params = {"id": config.model_id}

    # 通用参数
    common_params = config.get_common_params()
    params.update(common_params)

    # Reasoning (o1/o3/gpt-5 系列)
    if config.reasoning.enabled and config.reasoning.effort != "none":
        params["reasoning_effort"] = config.reasoning.effort

    # Structured Output
    if config.structured_output.enabled:
        structured_params = config.structured_output.to_provider_params(ModelProvider.OPENAI)
        params.update(structured_params)

    logger.info("Creating OpenAI model: %s", config.model_id)

    return OpenAIChat(api_key=api_key, **params)
