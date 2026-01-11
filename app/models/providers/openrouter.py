"""
OpenRouter 模型适配器

OpenRouter 是统一网关，支持 100+ 模型厂商。
使用 Agno 原生 OpenRouter 集成。
"""

import logging
import os
from typing import TYPE_CHECKING

from app.models.config import PROVIDER_DEFAULT_ENV_VARS, ModelConfig, ModelProvider, ProjectConfig

if TYPE_CHECKING:
    from agno.models.openrouter import OpenRouter

logger = logging.getLogger(__name__)


def _get_api_key(
    config: ModelConfig,
    project_config: ProjectConfig | None,
) -> str | None:
    """
    三层 API Key 优先级获取

    1. Agent 级: config.api_key_env
    2. Project 级: project_config.api_key_env
    3. Global 级: OPENROUTER_API_KEY
    """
    # 1. Agent 级
    if config.api_key_env:
        api_key = os.environ.get(config.api_key_env)
        if api_key:
            logger.debug("Using Agent-level API Key from %s", config.api_key_env)
            return api_key

    # 2. Project 级
    if project_config and project_config.api_key_env:
        api_key = os.environ.get(project_config.api_key_env)
        if api_key:
            logger.debug("Using Project-level API Key from %s", project_config.api_key_env)
            return api_key

    # 3. Global 级
    default_env = PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.OPENROUTER)
    if default_env:
        api_key = os.environ.get(default_env)
        if api_key:
            logger.debug("Using Global API Key from %s", default_env)
            return api_key

    return None


def create_openrouter_model(
    config: ModelConfig,
    project_config: ProjectConfig | None = None,
) -> "OpenRouter":
    """
    创建 OpenRouter 模型实例

    Args:
        config: 模型配置
        project_config: 项目级配置（用于共享 API Key）

    Returns:
        Agno OpenRouter 模型实例
    """
    try:
        from agno.models.openrouter import OpenRouter
    except ImportError:
        raise ImportError("agno package not found. Install with: pip install agno")

    api_key = _get_api_key(config, project_config)

    if not api_key:
        raise ValueError(
            "OpenRouter API Key not found. Please set one of: "
            f"config.api_key_env, project_config.api_key_env, or {PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.OPENROUTER)}"
        )

    # 获取 Agno 参数
    params = config.to_agno_params()

    logger.info("Creating OpenRouter model: %s", params.get("id"))

    return OpenRouter(api_key=api_key, **params)
