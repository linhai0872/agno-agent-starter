"""
Gateway 适配器 (OpenRouter / LiteLLM)

通过 Agno SDK 调用统一网关，支持 100+ 模型厂商。
"""

import logging
import os
from typing import TYPE_CHECKING

from app.models.adapters.base import BaseModelAdapter
from app.models.config import ModelConfig, ModelProvider, ProjectConfig

if TYPE_CHECKING:
    from agno.models.base import Model

logger = logging.getLogger(__name__)


class GatewayAdapter(BaseModelAdapter):
    """
    Gateway 适配器 - 通过 Agno SDK 调用 OpenRouter / LiteLLM

    GatewayType:
    - openrouter: 使用 agno.models.openrouter.OpenRouter
    - litellm: 使用 agno.models.litellm.LiteLLM
    """

    def __init__(
        self,
        gateway_type: str = "openrouter",
    ):
        provider_id = gateway_type
        provider_name = "OpenRouter" if gateway_type == "openrouter" else "LiteLLM"
        super().__init__(provider_id, provider_name)
        self.gateway_type = gateway_type

    def create_model(
        self,
        config: ModelConfig,
        project_config: ProjectConfig | None = None,
    ) -> "Model":
        """创建 Gateway 模型实例"""
        api_key = self.get_api_key(config, project_config)

        if self.gateway_type == "openrouter":
            return self._create_openrouter(config, api_key)
        elif self.gateway_type == "litellm":
            return self._create_litellm(config, api_key)
        else:
            raise ValueError(f"Unsupported gateway type: {self.gateway_type}")

    def _create_openrouter(self, config: ModelConfig, api_key: str | None) -> "Model":
        """创建 OpenRouter 模型"""
        try:
            from agno.models.openrouter import OpenRouter
        except ImportError as e:
            raise ImportError("agno package not found. Install with: pip install agno") from e

        if not api_key:
            raise ValueError(f"OpenRouter API Key not found. Set: {self.default_env_var}")

        params = config.to_agno_params()
        logger.info("Creating OpenRouter model: %s", params.get("id"))
        return OpenRouter(api_key=api_key, **params)

    def _create_litellm(self, config: ModelConfig, api_key: str | None) -> "Model":
        """创建 LiteLLM 模型"""
        try:
            from agno.models.litellm import LiteLLM
        except ImportError as e:
            raise ImportError("litellm package not found. Install with: pip install litellm") from e

        params = {"id": config.model_id}
        if api_key:
            params["api_key"] = api_key

        # API Base URL
        api_base = self._get_litellm_api_base(config)
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

        # 结构化输出
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

    def _get_litellm_api_base(self, config: ModelConfig) -> str | None:
        """获取 LiteLLM API Base URL"""
        if config.litellm_api_base_env:
            api_base = os.environ.get(config.litellm_api_base_env)
            if api_base:
                return api_base

        if config.litellm_api_base:
            return config.litellm_api_base

        return os.environ.get("LITELLM_API_BASE")


def create_gateway_adapter(provider: ModelProvider) -> GatewayAdapter:
    """工厂函数：根据 Provider 创建 Gateway 适配器"""
    if provider == ModelProvider.OPENROUTER:
        return GatewayAdapter("openrouter")
    elif provider == ModelProvider.LITELLM:
        return GatewayAdapter("litellm")
    else:
        raise ValueError(f"Provider {provider} is not a gateway type")
