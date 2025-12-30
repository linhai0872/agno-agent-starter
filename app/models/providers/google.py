"""
Google Gemini 模型适配器

使用 Agno 原生 Google 集成。
支持: Gemini 2.5 Flash/Pro, Gemini 2.0
特性: 原生搜索, 思考模式
"""

import logging
import os
from typing import TYPE_CHECKING, Optional

from app.models.config import ModelConfig, ModelProvider, ProjectConfig, PROVIDER_DEFAULT_ENV_VARS

if TYPE_CHECKING:
    from agno.models.google import Gemini

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
    default_env = PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.GOOGLE)
    if default_env:
        return os.environ.get(default_env)
    
    return None


def create_google_model(
    config: ModelConfig,
    project_config: Optional[ProjectConfig] = None,
) -> "Gemini":
    """
    创建 Google Gemini 模型实例
    
    Args:
        config: 模型配置
        project_config: 项目级配置
    
    Returns:
        Agno Gemini 模型实例
    """
    try:
        from agno.models.google import Gemini
    except ImportError:
        raise ImportError(
            "google-genai package not found. Install with: pip install google-genai"
        )
    
    api_key = _get_api_key(config, project_config)
    
    if not api_key:
        raise ValueError(
            "Google API Key not found. Please set one of: "
            f"config.api_key_env, project_config.api_key_env, or {PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.GOOGLE)}"
        )
    
    # 构建参数
    params = {"id": config.model_id}
    
    # 通用参数
    if config.temperature is not None:
        params["temperature"] = config.temperature
    if config.max_tokens is not None:
        params["max_output_tokens"] = config.max_tokens  # Google 使用 max_output_tokens
    if config.top_p is not None:
        params["top_p"] = config.top_p
    if config.top_k is not None:
        params["top_k"] = config.top_k
    if config.stop:
        params["stop_sequences"] = config.stop  # Google 使用 stop_sequences
    
    # Reasoning (Gemini 思考模式)
    if config.reasoning.enabled:
        if config.reasoning.max_tokens:
            params["thinking_budget"] = config.reasoning.max_tokens
        if config.reasoning.google_thinking_level:
            params["thinking_level"] = config.reasoning.google_thinking_level
        if config.reasoning.include_reasoning:
            params["include_thoughts"] = True
    
    # Web Search (Google 原生支持)
    if config.web_search.enabled:
        params["search"] = True
    
    # Structured Output
    if config.structured_output.enabled:
        params["response_mime_type"] = "application/json"
        if config.structured_output.json_schema:
            params["response_schema"] = config.structured_output.json_schema
    
    logger.info("Creating Google Gemini model: %s", config.model_id)
    
    return Gemini(api_key=api_key, **params)

