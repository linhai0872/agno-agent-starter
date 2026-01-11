"""
多厂商模型适配器

支持的厂商:
- OpenRouter: 统一网关
- OpenAI: 原生直连
- Google Gemini: 原生直连
- Anthropic Claude: 原生直连
- DashScope: 阿里云百炼
- Volcengine: 火山方舟
- Ollama: 本地部署
- LiteLLM: 统一网关

注意: 使用延迟导入避免在加载时检测所有 SDK 依赖
"""

__all__ = [
    "create_openrouter_model",
    "create_openai_model",
    "create_google_model",
    "create_anthropic_model",
    "create_dashscope_model",
    "create_volcengine_model",
    "create_ollama_model",
    "create_litellm_model",
]


def __getattr__(name: str):
    """延迟导入，仅在实际使用时加载对应模块"""
    if name == "create_openrouter_model":
        from app.models.providers.openrouter import create_openrouter_model

        return create_openrouter_model
    elif name == "create_openai_model":
        from app.models.providers.openai import create_openai_model

        return create_openai_model
    elif name == "create_google_model":
        from app.models.providers.google import create_google_model

        return create_google_model
    elif name == "create_anthropic_model":
        from app.models.providers.anthropic import create_anthropic_model

        return create_anthropic_model
    elif name == "create_dashscope_model":
        from app.models.providers.dashscope import create_dashscope_model

        return create_dashscope_model
    elif name == "create_volcengine_model":
        from app.models.providers.volcengine import create_volcengine_model

        return create_volcengine_model
    elif name == "create_ollama_model":
        from app.models.providers.ollama import create_ollama_model

        return create_ollama_model
    elif name == "create_litellm_model":
        from app.models.providers.litellm import create_litellm_model

        return create_litellm_model
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
