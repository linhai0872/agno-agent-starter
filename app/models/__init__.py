"""
模型配置模块 (多厂商支持)

提供统一的多厂商模型配置接口，支持：
- OpenRouter: 统一网关
- OpenAI: GPT-4o, o1/o3 系列
- Google Gemini: Gemini 2.5 系列
- Anthropic Claude: Claude Sonnet 4, Opus 4
- DashScope: 阿里云百炼 Qwen 系列
- Volcengine: 火山方舟豆包系列
- Ollama: 本地部署模型
- LiteLLM: 统一网关
"""

from app.models.config import (
    PROVIDER_DEFAULT_ENV_VARS,
    KnowledgeConfig,
    MemoryConfig,
    ModelConfig,
    ModelProvider,
    MultimodalConfig,
    ProjectConfig,
    ReasoningConfig,
    StructuredOutputConfig,
    WebSearchConfig,
)
from app.models.factory import (
    create_anthropic_claude,
    create_claude_sonnet,
    create_dashscope_qwen,
    create_gemini_flash,
    create_gemini_pro,
    create_google_gemini,
    create_gpt_4_1,
    create_model,
    create_model_from_dict,
    create_ollama_local,
    create_openai_gpt4o,
    create_volcengine_doubao,
    get_model_info,
)
from app.models.features import ModelFeature
from app.models.pricing import ModelPricing
from app.models.provider_registry import ProviderRegistry, get_registry
from app.models.registry import MODEL_REGISTRY, ModelCapabilities
from app.models.variants import ModelVariant

__all__ = [
    # 配置类
    "ModelConfig",
    "ModelProvider",
    "ReasoningConfig",
    "WebSearchConfig",
    "MultimodalConfig",
    "StructuredOutputConfig",
    "ProjectConfig",
    "MemoryConfig",
    "KnowledgeConfig",
    "PROVIDER_DEFAULT_ENV_VARS",
    # 新增: 能力/变体/定价
    "ModelFeature",
    "ModelVariant",
    "ModelPricing",
    # 工厂函数
    "create_model",
    "create_model_from_dict",
    "get_model_info",
    # OpenRouter 便捷函数
    "create_gemini_flash",
    "create_gemini_pro",
    "create_claude_sonnet",
    "create_gpt_4_1",
    # 直连便捷函数
    "create_openai_gpt4o",
    "create_google_gemini",
    "create_anthropic_claude",
    "create_dashscope_qwen",
    "create_volcengine_doubao",
    "create_ollama_local",
    # 注册表
    "MODEL_REGISTRY",
    "ModelCapabilities",
    "ProviderRegistry",
    "get_registry",
]

