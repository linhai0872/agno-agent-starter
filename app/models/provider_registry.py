"""
Provider 注册表 (单例 + 字典缓存)

核心功能:
1. 加载内置 Adapter (代码定义)
2. 解析变体 (fast → 具体模型 ID)
3. 字典实例缓存 (provider + model_id + api_key_hash, max=100)
"""

import logging
from collections import OrderedDict
from typing import Any

from app.models.adapters.base import BaseModelAdapter
from app.models.adapters.dashscope import DashScopeAdapter
from app.models.adapters.gateway import GatewayAdapter
from app.models.adapters.native import NativeAdapter
from app.models.adapters.volcengine import VolcengineAdapter
from app.models.config import ModelConfig, ModelProvider, ProjectConfig
from app.models.variants import ModelVariant, resolve_variant

logger = logging.getLogger(__name__)

DEFAULT_CACHE_SIZE = 100


class LRUCache:
    """简单的 LRU 缓存实现"""

    def __init__(self, maxsize: int = 100):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> tuple[bool, Any]:
        """获取缓存项，返回 (命中, 值)"""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return True, self._cache[key]
        self._misses += 1
        return False, None

    def set(self, key: str, value: Any) -> None:
        """设置缓存项"""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            if len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)
            self._cache[key] = value


    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def cache_info(self) -> dict[str, int]:
        """获取缓存统计"""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "maxsize": self._maxsize,
        }


class ProviderRegistry:
    """Provider 注册表 (单例 + 字典缓存)"""

    _instance: "ProviderRegistry | None" = None
    _adapters: dict[str, BaseModelAdapter]
    _cache: LRUCache

    def __new__(cls, cache_size: int = DEFAULT_CACHE_SIZE) -> "ProviderRegistry":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._adapters = {}
            instance._cache = LRUCache(cache_size)
            instance._load_builtin_adapters()
            cls._instance = instance
        return cls._instance

    def _load_builtin_adapters(self) -> None:
        """加载内置 Adapter"""
        # Gateway (OpenRouter, LiteLLM)
        self._adapters["openrouter"] = GatewayAdapter("openrouter")
        self._adapters["litellm"] = GatewayAdapter("litellm")

        # Native (OpenAI, Google, Anthropic, Ollama)
        self._adapters["openai"] = NativeAdapter("openai")
        self._adapters["google"] = NativeAdapter("google")
        self._adapters["anthropic"] = NativeAdapter("anthropic")
        self._adapters["ollama"] = NativeAdapter("ollama")

        # Custom (DashScope, Volcengine)
        self._adapters["dashscope"] = DashScopeAdapter()
        self._adapters["volcengine"] = VolcengineAdapter()

        logger.debug("Loaded %d builtin adapters", len(self._adapters))

    def get_adapter(self, provider: ModelProvider) -> BaseModelAdapter:
        """获取指定 Provider 的 Adapter"""
        adapter = self._adapters.get(provider.value)
        if not adapter:
            raise ValueError(f"Unsupported provider: {provider}")
        return adapter

    def get_model(
        self,
        config: ModelConfig,
        project_config: ProjectConfig | None = None,
        variant: ModelVariant | None = None,
    ) -> Any:
        """获取模型实例 (带缓存和变体解析)"""
        # 解析变体
        model_id = config.model_id
        if variant:
            model_id = resolve_variant(config.provider.value, variant, model_id)
            config = self._with_model_id(config, model_id)

        # 获取 Adapter
        adapter = self.get_adapter(config.provider)

        # 获取 API Key 并生成缓存 Key
        api_key = adapter.get_api_key(config, project_config)

        # Ollama 不需要 API Key
        if config.provider != ModelProvider.OLLAMA and not api_key:
            raise ValueError(
                f"{adapter.provider_name} API Key not found. "
                f"Set: {adapter.default_env_var}"
            )

        # 生成缓存 Key
        cache_key = adapter.get_cache_key(config, api_key or "no-key")

        # 检查缓存
        hit, cached_model = self._cache.get(cache_key)
        if hit:
            logger.debug("Cache hit: %s", cache_key)
            return cached_model

        # 创建模型并缓存
        logger.debug("Cache miss, creating model: %s", cache_key)
        model = adapter.create_model(config, project_config)
        self._cache.set(cache_key, model)
        return model

    def _with_model_id(self, config: ModelConfig, model_id: str) -> ModelConfig:
        """创建带有新 model_id 的配置副本"""
        from dataclasses import replace

        return replace(config, model_id=model_id)

    def cache_info(self) -> dict[str, int]:
        """获取缓存统计信息"""
        return self._cache.cache_info()

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def list_adapters(self) -> list[str]:
        """列出所有已注册的 Adapter"""
        return list(self._adapters.keys())

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例 (仅用于测试)"""
        if cls._instance is not None:
            cls._instance.clear_cache()
            cls._instance = None


def get_registry(cache_size: int = DEFAULT_CACHE_SIZE) -> ProviderRegistry:
    """获取 ProviderRegistry 单例"""
    return ProviderRegistry(cache_size)

