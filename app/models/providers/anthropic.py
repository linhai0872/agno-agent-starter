"""
Anthropic Claude 模型适配器

使用 Agno 原生 Anthropic 集成。
支持: Claude Sonnet 4, Claude Opus 4, Claude 3.5 系列
特性: 扩展思考, 长上下文
"""

import logging
import os
from typing import TYPE_CHECKING

from app.models.config import PROVIDER_DEFAULT_ENV_VARS, ModelConfig, ModelProvider, ProjectConfig

if TYPE_CHECKING:
    from agno.models.anthropic import Claude

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
    default_env = PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.ANTHROPIC)
    if default_env:
        return os.environ.get(default_env)

    return None


def create_anthropic_model(
    config: ModelConfig,
    project_config: ProjectConfig | None = None,
) -> "Claude":
    """
    创建 Anthropic Claude 模型实例

    Args:
        config: 模型配置
        project_config: 项目级配置

    Returns:
        Agno Claude 模型实例
    """
    try:
        from agno.models.anthropic import Claude
    except ImportError:
        raise ImportError("anthropic package not found. Install with: pip install anthropic")

    api_key = _get_api_key(config, project_config)

    if not api_key:
        raise ValueError(
            "Anthropic API Key not found. Please set one of: "
            f"config.api_key_env, project_config.api_key_env, or {PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.ANTHROPIC)}"
        )

    # 构建参数
    params = {"id": config.model_id}

    # 通用参数
    if config.temperature is not None:
        params["temperature"] = config.temperature
    if config.max_tokens is not None:
        params["max_tokens"] = config.max_tokens
    if config.top_p is not None:
        params["top_p"] = config.top_p
    if config.top_k is not None:
        params["top_k"] = config.top_k
    if config.stop:
        params["stop_sequences"] = config.stop

    # Extended Thinking (Anthropic 扩展思考)
    if config.reasoning.enabled:
        thinking_config = {
            "type": config.reasoning.anthropic_thinking_type,
            "budget_tokens": config.reasoning.max_tokens or 1024,
        }
        params["thinking"] = thinking_config

    logger.info("Creating Anthropic Claude model: %s", config.model_id)

    return Claude(api_key=api_key, **params)
