"""
模型变体系统 (借鉴 OpenCode)

提供语义化的模型选择抽象，如 fast/balanced/creative/precise。
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ModelVariant(str, Enum):
    """模型变体"""

    FAST = "fast"
    BALANCED = "balanced"
    CREATIVE = "creative"
    PRECISE = "precise"


DEFAULT_VARIANT_MAPPINGS: dict[str, dict[str, str]] = {
    "openrouter": {
        "fast": "google/gemini-2.5-flash-lite-preview-09-2025",
        "balanced": "anthropic/claude-sonnet-4",
        "creative": "openai/gpt-4.1",
        "precise": "openai/o3",
    },
    "openai": {
        "fast": "gpt-4.1-nano",
        "balanced": "gpt-4.1",
        "creative": "gpt-4.1",
        "precise": "o3",
    },
    "google": {
        "fast": "gemini-2.5-flash-lite-preview-09-2025",
        "balanced": "gemini-2.5-flash-preview-09-2025",
        "creative": "gemini-2.5-pro-preview-09-2025",
        "precise": "gemini-2.5-pro-preview-09-2025",
    },
    "anthropic": {
        "fast": "claude-3-5-haiku-latest",
        "balanced": "claude-sonnet-4-20250514",
        "creative": "claude-sonnet-4-20250514",
        "precise": "claude-sonnet-4-20250514",
    },
    "dashscope": {
        "fast": "qwen-turbo",
        "balanced": "qwen-plus",
        "creative": "qwen-max",
        "precise": "qwen-max",
    },
    "volcengine": {
        "fast": "doubao-1-5-lite-32k-250115",
        "balanced": "doubao-1-5-pro-32k-250115",
        "creative": "doubao-1-5-pro-32k-250115",
        "precise": "doubao-1-5-thinking-pro-250415",
    },
    "ollama": {
        "fast": "llama3.2:latest",
        "balanced": "qwen2.5:14b",
        "creative": "qwen2.5:14b",
        "precise": "qwen2.5:32b",
    },
    "litellm": {
        "fast": "gpt-4.1-nano",
        "balanced": "gpt-4.1",
        "creative": "gpt-4.1",
        "precise": "o3",
    },
}


def resolve_variant(provider: str, variant: ModelVariant, fallback: str) -> str:
    """解析变体到具体模型 ID"""
    mappings = DEFAULT_VARIANT_MAPPINGS.get(provider, {})
    model_id = mappings.get(variant.value)

    if model_id:
        logger.debug("Resolved variant %s/%s -> %s", provider, variant.value, model_id)
        return model_id

    logger.debug("No mapping for %s/%s, using fallback: %s", provider, variant.value, fallback)
    return fallback


def get_available_variants(provider: str) -> list[str]:
    """获取指定 provider 支持的变体列表"""
    mappings = DEFAULT_VARIANT_MAPPINGS.get(provider, {})
    return list(mappings.keys())


def validate_variant_mappings() -> list[str]:
    """验证变体映射，返回可能无效的模型 ID 列表 (用于测试)"""
    from app.models.registry import MODEL_REGISTRY

    warnings: list[str] = []
    for provider, variants in DEFAULT_VARIANT_MAPPINGS.items():
        for variant_name, model_id in variants.items():
            if model_id not in MODEL_REGISTRY:
                warnings.append(f"{provider}/{variant_name}: {model_id} not in registry")
    return warnings
