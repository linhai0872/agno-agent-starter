"""
Native 适配器 (OpenAI / Google / Anthropic / Ollama)

通过 Agno SDK 调用各厂商原生 API。
"""

import logging
import os
from typing import TYPE_CHECKING, Any

from app.models.adapters.base import BaseModelAdapter
from app.models.config import ModelConfig, ModelProvider, ProjectConfig

if TYPE_CHECKING:
    from agno.models.base import Model

logger = logging.getLogger(__name__)


class NativeAdapter(BaseModelAdapter):
    """
    Native 适配器 - 通过 Agno SDK 调用原生 API

    支持的 Provider:
    - openai: agno.models.openai.OpenAIChat
    - google: agno.models.google.Gemini
    - anthropic: agno.models.anthropic.Claude
    - ollama: agno.models.ollama.Ollama
    """

    def __init__(self, native_type: str):
        provider_names = {
            "openai": "OpenAI",
            "google": "Google Gemini",
            "anthropic": "Anthropic Claude",
            "ollama": "Ollama",
        }
        super().__init__(native_type, provider_names.get(native_type, native_type))
        self.native_type = native_type

    def create_model(
        self,
        config: ModelConfig,
        project_config: ProjectConfig | None = None,
    ) -> "Model":
        """创建 Native 模型实例"""
        api_key = self.get_api_key(config, project_config)

        if self.native_type == "openai":
            return self._create_openai(config, api_key)
        elif self.native_type == "google":
            return self._create_google(config, api_key)
        elif self.native_type == "anthropic":
            return self._create_anthropic(config, api_key)
        elif self.native_type == "ollama":
            return self._create_ollama(config, project_config)
        else:
            raise ValueError(f"Unsupported native type: {self.native_type}")

    def _create_openai(self, config: ModelConfig, api_key: str | None) -> "Model":
        """创建 OpenAI 模型"""
        try:
            from agno.models.openai import OpenAIChat
        except ImportError as e:
            raise ImportError("agno package not found. Install with: pip install agno") from e

        if not api_key:
            raise ValueError(f"OpenAI API Key not found. Set: {self.default_env_var}")

        params: dict[str, Any] = {"id": config.model_id}
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

    def _create_google(self, config: ModelConfig, api_key: str | None) -> "Model":
        """创建 Google Gemini 模型"""
        try:
            from agno.models.google import Gemini
        except ImportError as e:
            raise ImportError(
                "google-genai package not found. Install with: pip install google-genai"
            ) from e

        if not api_key:
            raise ValueError(f"Google API Key not found. Set: {self.default_env_var}")

        params: dict[str, Any] = {"id": config.model_id}

        # 通用参数
        if config.temperature is not None:
            params["temperature"] = config.temperature
        if config.max_tokens is not None:
            params["max_output_tokens"] = config.max_tokens
        if config.top_p is not None:
            params["top_p"] = config.top_p
        if config.top_k is not None:
            params["top_k"] = config.top_k
        if config.stop:
            params["stop_sequences"] = config.stop

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

    def _create_anthropic(self, config: ModelConfig, api_key: str | None) -> "Model":
        """创建 Anthropic Claude 模型"""
        try:
            from agno.models.anthropic import Claude
        except ImportError as e:
            raise ImportError(
                "anthropic package not found. Install with: pip install anthropic"
            ) from e

        if not api_key:
            raise ValueError(f"Anthropic API Key not found. Set: {self.default_env_var}")

        params: dict[str, Any] = {"id": config.model_id}

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

    def _create_ollama(self, config: ModelConfig, project_config: ProjectConfig | None) -> "Model":
        """创建 Ollama 模型"""
        try:
            from agno.models.ollama import Ollama
        except ImportError as e:
            raise ImportError("ollama package not found. Install with: pip install ollama") from e

        host = self._get_ollama_host(config)
        params: dict[str, Any] = {"id": config.model_id, "host": host}

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

        # 结构化输出
        if config.structured_output.enabled:
            params["format"] = "json"
            if config.structured_output.json_schema:
                params["format"] = config.structured_output.json_schema

        logger.info("Creating Ollama model: %s at %s", config.model_id, host)
        return Ollama(**params)

    def _get_ollama_host(self, config: ModelConfig) -> str:
        """获取 Ollama Host"""
        if config.ollama_host_env:
            host = os.environ.get(config.ollama_host_env)
            if host:
                return host

        host = os.environ.get("OLLAMA_HOST")
        if host:
            return host

        return config.ollama_host


def create_native_adapter(provider: ModelProvider) -> NativeAdapter:
    """工厂函数：根据 Provider 创建 Native 适配器"""
    native_types = {
        ModelProvider.OPENAI: "openai",
        ModelProvider.GOOGLE: "google",
        ModelProvider.ANTHROPIC: "anthropic",
        ModelProvider.OLLAMA: "ollama",
    }
    native_type = native_types.get(provider)
    if not native_type:
        raise ValueError(f"Provider {provider} is not a native type")
    return NativeAdapter(native_type)
