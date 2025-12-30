"""
模型工厂

根据 ModelConfig 创建模型实例，支持多厂商路由。
"""

import logging
from typing import Any, Dict, Optional, Union

from app.models.config import (
    ModelConfig,
    ModelProvider,
    MultimodalConfig,
    ProjectConfig,
    ReasoningConfig,
    StructuredOutputConfig,
    WebSearchConfig,
)
from app.models.registry import MODEL_REGISTRY, ModelCapabilities

logger = logging.getLogger(__name__)


def get_model_info(model_id: str) -> Optional[ModelCapabilities]:
    """
    获取模型信息
    
    Args:
        model_id: 模型 ID
        
    Returns:
        模型能力信息，如果未注册则返回 None
    """
    return MODEL_REGISTRY.get(model_id)


def create_model(
    config: ModelConfig,
    project_config: Optional[ProjectConfig] = None,
) -> Any:
    """
    根据配置创建模型实例 (多厂商路由)
    
    支持的厂商:
    - OpenRouter: 统一网关，支持 100+ 模型
    - OpenAI: GPT-4o, o1/o3 系列
    - Google Gemini: Gemini 2.5 系列
    - Anthropic Claude: Claude Sonnet 4, Opus 4
    - DashScope: Qwen 系列
    - Volcengine: 豆包 Seed, DeepSeek
    - Ollama: 本地部署模型
    - LiteLLM: 统一网关
    
    API Key 三层优先级（从高到低）：
    1. Agent 级: config.api_key_env
    2. Project 级: project_config.api_key_env
    3. Global 级: 厂商默认环境变量
    
    Args:
        config: 模型配置
        project_config: 项目级配置（可选）
        
    Returns:
        模型实例 (Agno Model 或自定义适配器)
    """
    match config.provider:
        case ModelProvider.OPENROUTER:
            from app.models.providers.openrouter import create_openrouter_model
            return create_openrouter_model(config, project_config)
        
        case ModelProvider.OPENAI:
            from app.models.providers.openai import create_openai_model
            return create_openai_model(config, project_config)
        
        case ModelProvider.GOOGLE:
            from app.models.providers.google import create_google_model
            return create_google_model(config, project_config)
        
        case ModelProvider.ANTHROPIC:
            from app.models.providers.anthropic import create_anthropic_model
            return create_anthropic_model(config, project_config)
        
        case ModelProvider.DASHSCOPE:
            from app.models.providers.dashscope import create_dashscope_model
            return create_dashscope_model(config, project_config)
        
        case ModelProvider.VOLCENGINE:
            from app.models.providers.volcengine import create_volcengine_model
            return create_volcengine_model(config, project_config)
        
        case ModelProvider.OLLAMA:
            from app.models.providers.ollama import create_ollama_model
            return create_ollama_model(config, project_config)
        
        case ModelProvider.LITELLM:
            from app.models.providers.litellm import create_litellm_model
            return create_litellm_model(config, project_config)
        
        case _:
            raise ValueError(f"Unsupported model provider: {config.provider}")


def create_model_from_dict(config_dict: Dict[str, Any]) -> Any:
    """
    从字典创建模型（便于从配置文件加载）
    
    Args:
        config_dict: 配置字典
        
    Returns:
        模型实例
        
    示例:
        config = {
            "provider": "openai",
            "model_id": "gpt-4o",
            "temperature": 0.1,
            "reasoning": {
                "enabled": True,
                "effort": "medium"
            }
        }
        model = create_model_from_dict(config)
    """
    # 复制以避免修改原字典
    config_dict = config_dict.copy()
    
    # 处理 provider 枚举
    if "provider" in config_dict:
        provider_str = config_dict.pop("provider")
        if isinstance(provider_str, str):
            config_dict["provider"] = ModelProvider(provider_str)
    
    # 提取嵌套配置
    reasoning_dict = config_dict.pop("reasoning", {})
    web_search_dict = config_dict.pop("web_search", {})
    multimodal_dict = config_dict.pop("multimodal", {})
    structured_output_dict = config_dict.pop("structured_output", {})
    
    # 创建配置对象
    config = ModelConfig(
        **config_dict,
        reasoning=ReasoningConfig(**reasoning_dict) if reasoning_dict else ReasoningConfig(),
        web_search=WebSearchConfig(**web_search_dict) if web_search_dict else WebSearchConfig(),
        multimodal=MultimodalConfig(**multimodal_dict) if multimodal_dict else MultimodalConfig(),
        structured_output=StructuredOutputConfig(**structured_output_dict) if structured_output_dict else StructuredOutputConfig(),
    )
    
    return create_model(config)


# ============== 便捷函数 (OpenRouter) ==============

def create_gemini_flash(
    temperature: float = 0.1,
    max_tokens: int = 16384,
    reasoning_enabled: bool = False,
    reasoning_effort: str = "medium",
) -> Any:
    """创建 Gemini 2.5 Flash 模型 (via OpenRouter)"""
    config = ModelConfig(
        model_id="google/gemini-2.5-flash-preview-09-2025",
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning=ReasoningConfig(
            enabled=reasoning_enabled,
            effort=reasoning_effort,
        ),
    )
    return create_model(config)


def create_gemini_pro(
    temperature: float = 0.3,
    max_tokens: int = 32768,
    reasoning_enabled: bool = True,
    reasoning_effort: str = "high",
) -> Any:
    """创建 Gemini 3 Pro 模型 (via OpenRouter)"""
    config = ModelConfig(
        model_id="google/gemini-3-pro-preview",
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning=ReasoningConfig(
            enabled=reasoning_enabled,
            effort=reasoning_effort,
        ),
    )
    return create_model(config)


def create_claude_sonnet(
    temperature: float = 0.2,
    max_tokens: int = 8192,
    reasoning_enabled: bool = False,
) -> Any:
    """创建 Claude Sonnet 4 模型 (via OpenRouter)"""
    config = ModelConfig(
        model_id="anthropic/claude-sonnet-4",
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning=ReasoningConfig(enabled=reasoning_enabled),
    )
    return create_model(config)


def create_gpt_4_1(
    temperature: float = 0.2,
    max_tokens: int = 8192,
    web_search_enabled: bool = False,
) -> Any:
    """创建 GPT-4.1 模型 (via OpenRouter)"""
    config = ModelConfig(
        model_id="openai/gpt-4.1",
        temperature=temperature,
        max_tokens=max_tokens,
        web_search=WebSearchConfig(enabled=web_search_enabled),
    )
    return create_model(config)


# ============== 便捷函数 (直连) ==============

def create_openai_gpt4o(
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> Any:
    """创建 OpenAI GPT-4o 模型 (直连)"""
    config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o",
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return create_model(config)


def create_google_gemini(
    model_id: str = "gemini-2.5-flash",
    temperature: float = 0.2,
    max_tokens: int = 8192,
    web_search_enabled: bool = False,
) -> Any:
    """创建 Google Gemini 模型 (直连)"""
    config = ModelConfig(
        provider=ModelProvider.GOOGLE,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        web_search=WebSearchConfig(enabled=web_search_enabled),
    )
    return create_model(config)


def create_anthropic_claude(
    model_id: str = "claude-sonnet-4-20250514",
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> Any:
    """创建 Anthropic Claude 模型 (直连)"""
    config = ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return create_model(config)


def create_dashscope_qwen(
    model_id: str = "qwen-plus",
    temperature: float = 0.2,
    max_tokens: int = 8192,
    web_search_enabled: bool = False,
) -> Any:
    """创建阿里云 Qwen 模型 (直连)"""
    config = ModelConfig(
        provider=ModelProvider.DASHSCOPE,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        web_search=WebSearchConfig(enabled=web_search_enabled),
    )
    return create_model(config)


def create_volcengine_doubao(
    model_id: str = "doubao-seed-1-6-251015",
    temperature: float = 0.2,
    max_tokens: int = 8192,
    reasoning_enabled: bool = False,
) -> Any:
    """创建火山方舟豆包模型 (直连)"""
    config = ModelConfig(
        provider=ModelProvider.VOLCENGINE,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning=ReasoningConfig(enabled=reasoning_enabled),
    )
    return create_model(config)


def create_ollama_local(
    model_id: str = "llama3.2:latest",
    host: str = "http://localhost:11434",
    temperature: float = 0.7,
) -> Any:
    """创建 Ollama 本地模型"""
    config = ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id=model_id,
        ollama_host=host,
        temperature=temperature,
    )
    return create_model(config)
