"""
火山方舟适配器

使用 volcenginesdkarkruntime 官方 SDK。
支持: 豆包 Seed 系列, DeepSeek 系列
特性: 联网搜索, 深度思考, 多模态
"""

import logging
from collections.abc import Iterator
from typing import Any

from app.models.adapters.base import BaseModelAdapter
from app.models.config import ModelConfig, ProjectConfig

logger = logging.getLogger(__name__)


class VolcengineModel:
    """
    火山方舟模型适配器

    特性:
    - 联网搜索: tools=[{"type": "web_search"}]
    - 深度思考: thinking.type = "auto" | "enabled"
    - 多模态: 支持图片 URL
    - 结构化输出: response_format
    """

    def __init__(
        self,
        model_id: str,
        api_key: str,
        config: ModelConfig,
    ):
        try:
            from volcenginesdkarkruntime import Ark
        except ImportError as e:
            raise ImportError(
                "volcenginesdkarkruntime package not found. "
                "Install with: pip install volcengine-python-sdk[ark]"
            ) from e

        self.client = Ark(
            api_key=api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            timeout=1800,
        )
        self.model_id = model_id
        self.config = config

    def _build_params(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """构建火山方舟 API 参数"""
        params: dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
        }

        # 通用参数
        if self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            params["max_tokens"] = self.config.max_tokens
        if self.config.top_p is not None:
            params["top_p"] = self.config.top_p
        if self.config.frequency_penalty is not None:
            params["frequency_penalty"] = self.config.frequency_penalty
        if self.config.presence_penalty is not None:
            params["presence_penalty"] = self.config.presence_penalty
        if self.config.stop:
            params["stop"] = self.config.stop

        # 深度思考 (豆包 Seed 系列)
        if self.config.reasoning.enabled:
            params["thinking"] = {"type": self.config.reasoning.volcengine_thinking_type}

        # 结构化输出
        if self.config.structured_output.enabled:
            if self.config.structured_output.response_type == "json_object":
                params["response_format"] = {"type": "json_object"}
            elif self.config.structured_output.json_schema:
                params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": self.config.structured_output.schema_name,
                        "schema": self.config.structured_output.json_schema,
                        "strict": self.config.structured_output.strict,
                    },
                }

        # 多模态图片限制
        if (
            self.config.multimodal.volcengine_max_pixels
            or self.config.multimodal.volcengine_min_pixels
        ):
            image_limit: dict[str, int] = {}
            if self.config.multimodal.volcengine_max_pixels:
                image_limit["max_pixels"] = self.config.multimodal.volcengine_max_pixels
            if self.config.multimodal.volcengine_min_pixels:
                image_limit["min_pixels"] = self.config.multimodal.volcengine_min_pixels
            params["image_pixel_limit"] = image_limit

        return params

    def _build_web_search_tools(self) -> list[dict[str, Any]]:
        """构建联网搜索工具"""
        if not self.config.web_search.enabled:
            return []

        tool: dict[str, Any] = {
            "type": "web_search",
            "web_search": {
                "enable": True,
            },
        }

        if self.config.web_search.volcengine_max_keyword != 3:
            tool["web_search"]["max_keyword"] = self.config.web_search.volcengine_max_keyword
        if self.config.web_search.volcengine_limit != 10:
            tool["web_search"]["limit"] = self.config.web_search.volcengine_limit
        if self.config.web_search.volcengine_sources:
            tool["web_search"]["sources"] = self.config.web_search.volcengine_sources

        return [tool]

    def chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | Iterator[dict[str, Any]]:
        """发送聊天请求"""
        params = self._build_params(messages)

        all_tools = self._build_web_search_tools()
        if tools:
            all_tools.extend(tools)
        if all_tools:
            params["tools"] = all_tools

        if stream:
            params["stream"] = True
            response = self.client.chat.completions.create(**params)
            return self._handle_stream(response)
        else:
            response = self.client.chat.completions.create(**params)
            return self._handle_response(response)

    def _handle_response(self, response: Any) -> dict[str, Any]:
        """处理非流式响应"""
        choice = response.choices[0]

        result: dict[str, Any] = {
            "content": choice.message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "raw": response,
        }

        if hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
            result["reasoning"] = choice.message.reasoning_content

        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            result["tool_calls"] = choice.message.tool_calls

        return result

    def _handle_stream(self, response: Any) -> Iterator[dict[str, Any]]:
        """处理流式响应"""
        for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            result: dict[str, Any] = {
                "content": delta.content or "",
                "raw": chunk,
            }

            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                result["reasoning"] = delta.reasoning_content

            yield result


class VolcengineAdapter(BaseModelAdapter):
    """火山方舟适配器"""

    def __init__(self):
        super().__init__("volcengine", "火山方舟")

    def create_model(
        self,
        config: ModelConfig,
        project_config: ProjectConfig | None = None,
    ) -> VolcengineModel:
        """创建火山方舟模型实例"""
        api_key = self.get_api_key(config, project_config)

        if not api_key:
            raise ValueError(f"Volcengine Ark API Key not found. Set: {self.default_env_var}")

        logger.info("Creating Volcengine model: %s", config.model_id)

        return VolcengineModel(
            model_id=config.model_id,
            api_key=api_key,
            config=config,
        )
