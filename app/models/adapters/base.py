"""
模型适配器基类

统一 API Key 获取逻辑，消除 9 处重复代码。
"""

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from app.models.config import (
    PROVIDER_DEFAULT_ENV_VARS,
    ModelConfig,
    ModelProvider,
    ProjectConfig,
)

logger = logging.getLogger(__name__)


class BaseModelAdapter(ABC):
    """模型适配器基类 - 统一 _get_api_key 实现，消除重复代码"""

    provider_id: str
    provider_name: str
    default_env_var: str | None = None

    def __init__(
        self,
        provider_id: str,
        provider_name: str,
        default_env_var: str | None = None,
    ):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.default_env_var = default_env_var or PROVIDER_DEFAULT_ENV_VARS.get(
            ModelProvider(provider_id)
        )

    def get_api_key(
        self,
        config: ModelConfig,
        project_config: ProjectConfig | None = None,
    ) -> str | None:
        """获取 API Key (三层优先级) - 统一实现，消除 9 处重复"""
        # 1. Agent 级
        if config.api_key_env:
            api_key = os.environ.get(config.api_key_env)
            if api_key:
                logger.debug("Using Agent-level API Key from %s", config.api_key_env)
                return api_key

        # 2. Project 级
        if project_config and project_config.api_key_env:
            api_key = os.environ.get(project_config.api_key_env)
            if api_key:
                logger.debug(
                    "Using Project-level API Key from %s", project_config.api_key_env
                )
                return api_key

        # 3. Global 级
        if self.default_env_var:
            api_key = os.environ.get(self.default_env_var)
            if api_key:
                logger.debug("Using Global API Key from %s", self.default_env_var)
                return api_key

        return None

    def get_cache_key(self, config: ModelConfig, api_key: str) -> str:
        """生成缓存 Key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        return f"{self.provider_id}:{config.model_id}:{key_hash}"

    @abstractmethod
    def create_model(
        self,
        config: ModelConfig,
        project_config: ProjectConfig | None = None,
    ) -> Any:
        """创建模型实例"""
        ...
