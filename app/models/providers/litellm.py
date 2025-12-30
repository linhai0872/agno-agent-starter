"""
LiteLLM 模型适配器

使用 Agno 原生 LiteLLM 集成。
LiteLLM 是统一网关，支持 100+ 模型厂商。
特性: 统一接口, 透传底层能力
"""

import logging
import os
from typing import TYPE_CHECKING, Optional

from app.models.config import ModelConfig, ModelProvider, ProjectConfig, PROVIDER_DEFAULT_ENV_VARS

if TYPE_CHECKING:
    from agno.models.litellm import LiteLLM

logger = logging.getLogger(__name__)


def _get_api_key(
    config: ModelConfig,
    project_config: Optional[ProjectConfig],
) -> Optional[str]:
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
    default_env = PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.LITELLM)
    if default_env:
        return os.environ.get(default_env)
    
    return None


def _get_api_base(config: ModelConfig) -> Optional[str]:
    """获取 API Base URL"""
    # 环境变量优先
    if config.litellm_api_base_env:
        api_base = os.environ.get(config.litellm_api_base_env)
        if api_base:
            return api_base
    
    # 直接配置
    if config.litellm_api_base:
        return config.litellm_api_base
    
    # 全局环境变量
    return os.environ.get("LITELLM_API_BASE")


def create_litellm_model(
    config: ModelConfig,
    project_config: Optional[ProjectConfig] = None,
) -> "LiteLLM":
    """
    创建 LiteLLM 模型实例
    
    LiteLLM 支持的模型格式:
    - openai/gpt-4o
    - anthropic/claude-3-sonnet
    - azure/gpt-4
    - bedrock/anthropic.claude-3
    
    Args:
        config: 模型配置
        project_config: 项目级配置
    
    Returns:
        Agno LiteLLM 模型实例
    """
    try:
        from agno.models.litellm import LiteLLM
    except ImportError:
        raise ImportError(
            "litellm package not found. Install with: pip install litellm"
        )
    
    api_key = _get_api_key(config, project_config)
    api_base = _get_api_base(config)
    
    # 构建参数
    params = {"id": config.model_id}
    
    if api_key:
        params["api_key"] = api_key
    
    if api_base:
        params["api_base"] = api_base
    
    # 通用参数
    if config.temperature is not None:
        params["temperature"] = config.temperature
    if config.max_tokens is not None:
        params["max_tokens"] = config.max_tokens
    if config.top_p is not None:
        params["top_p"] = config.top_p
    if config.frequency_penalty is not None:
        params["frequency_penalty"] = config.frequency_penalty
    if config.presence_penalty is not None:
        params["presence_penalty"] = config.presence_penalty
    if config.seed is not None:
        params["seed"] = config.seed
    if config.stop:
        params["stop"] = config.stop
    
    # 结构化输出 (LiteLLM 透传给底层模型)
    if config.structured_output.enabled:
        if config.structured_output.response_type == "json_object":
            params["response_format"] = {"type": "json_object"}
        elif config.structured_output.json_schema:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": config.structured_output.schema_name,
                    "schema": config.structured_output.json_schema,
                    "strict": config.structured_output.strict,
                },
            }
    
    logger.info("Creating LiteLLM model: %s", config.model_id)
    
    return LiteLLM(**params)

