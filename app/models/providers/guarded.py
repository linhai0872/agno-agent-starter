"""
迭代防护模型包装 (Guarded Model Wrapper)

提供 LLM 调用层面的迭代次数限制，防止无限循环。

原理:
- 包装 agno Model 的 invoke/ainvoke 方法
- 在每次 LLM 调用时计数
- 达到限制时抛出 StopAgentRun 强制终止 Agent

使用示例:

```python
from app.models.providers.guarded import create_guarded_openrouter_model

model = create_guarded_openrouter_model(
    config=ModelConfig(...),
    project_config=PROJECT_CONFIG,
    max_iterations=50,
)

agent = Agent(model=model, ...)
```

参考:
- agno StopAgentRun: https://docs.agno.com/basics/tools/exceptions
"""

import logging
import os
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Any

from agno.exceptions import StopAgentRun
from agno.models.openrouter import OpenRouter
from agno.models.response import ModelResponse

from app.models.config import PROVIDER_DEFAULT_ENV_VARS, ModelConfig, ModelProvider, ProjectConfig

logger = logging.getLogger(__name__)


@dataclass
class GuardedOpenRouter(OpenRouter):
    """
    带迭代防护的 OpenRouter 模型

    在 LLM 调用层面限制迭代次数，防止 Agent 无限循环。
    当迭代次数超过 max_iterations 时，抛出 StopAgentRun 强制终止。

    Attributes:
        max_iterations: LLM 最大调用次数（默认 50）
        guard_enabled: 是否启用迭代防护（默认 True）

    使用示例:

    ```python
    # 推荐使用工厂函数
    from app.models.providers.guarded import create_guarded_openrouter_model

    model = create_guarded_openrouter_model(
        config=ModelConfig(...),
        project_config=PROJECT_CONFIG,
        max_iterations=50,
    )
    ```
    """

    # 迭代防护配置
    max_iterations: int = 50
    guard_enabled: bool = True

    # 内部计数器（不参与 dataclass 初始化）
    _iteration_count: int = field(default=0, init=False, repr=False)
    _warn_logged: bool = field(default=False, init=False, repr=False)

    def _check_iteration_limit(self) -> None:
        """
        检查迭代次数限制

        Raises:
            StopAgentRun: 当迭代次数超过限制时
        """
        if not self.guard_enabled:
            return

        self._iteration_count += 1
        warn_threshold = int(self.max_iterations * 0.8)

        # 警告日志（只记录一次）
        if self._iteration_count >= warn_threshold and not self._warn_logged:
            logger.warning(
                "GuardedOpenRouter: LLM 迭代次数接近上限 (%d/%d)",
                self._iteration_count,
                self.max_iterations,
            )
            self._warn_logged = True

        # 超过限制，强制终止
        if self._iteration_count > self.max_iterations:
            logger.error(
                "GuardedOpenRouter: LLM 迭代次数超限 (%d > %d)，强制终止 Agent",
                self._iteration_count,
                self.max_iterations,
            )
            raise StopAgentRun(
                f"LLM 迭代次数 ({self._iteration_count}) 超过限制 ({self.max_iterations})，"
                f"已强制终止以防止无限循环。请基于已收集的信息生成输出。"
            )

        logger.debug(
            "GuardedOpenRouter: LLM 调用 %d/%d",
            self._iteration_count,
            self.max_iterations,
        )

    def reset_iteration_count(self) -> None:
        """
        重置迭代计数器

        在每次 Agent run 开始时可调用此方法重置计数。
        注意：agno 框架会为每个 Agent run 创建新的 model 实例，
        因此通常不需要手动调用此方法。
        """
        self._iteration_count = 0
        self._warn_logged = False
        logger.debug("GuardedOpenRouter: 迭代计数器已重置")

    @property
    def iteration_count(self) -> int:
        """获取当前迭代次数"""
        return self._iteration_count

    def invoke(self, *args: Any, **kwargs: Any) -> ModelResponse:
        """
        同步 LLM 调用（带迭代防护）
        """
        self._check_iteration_limit()
        return super().invoke(*args, **kwargs)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> ModelResponse:
        """
        异步 LLM 调用（带迭代防护）
        """
        self._check_iteration_limit()
        return await super().ainvoke(*args, **kwargs)

    def invoke_stream(self, *args: Any, **kwargs: Any) -> Iterator[ModelResponse]:
        """
        同步流式 LLM 调用（带迭代防护）
        """
        self._check_iteration_limit()
        return super().invoke_stream(*args, **kwargs)

    async def ainvoke_stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[ModelResponse]:
        """
        异步流式 LLM 调用（带迭代防护）
        """
        self._check_iteration_limit()
        return super().ainvoke_stream(*args, **kwargs)


# ============== 工厂函数（复用项目封装逻辑）==============


def _get_api_key(
    config: ModelConfig,
    project_config: ProjectConfig | None,
) -> str | None:
    """
    三层 API Key 优先级获取（复用自 openrouter.py）

    1. Agent 级: config.api_key_env
    2. Project 级: project_config.api_key_env
    3. Global 级: OPENROUTER_API_KEY
    """
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
            logger.debug("Using Project-level API Key from %s", project_config.api_key_env)
            return api_key

    # 3. Global 级
    default_env = PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.OPENROUTER)
    if default_env:
        api_key = os.environ.get(default_env)
        if api_key:
            logger.debug("Using Global API Key from %s", default_env)
            return api_key

    return None


def create_guarded_openrouter_model(
    config: ModelConfig,
    project_config: ProjectConfig | None = None,
    max_iterations: int = 50,
    guard_enabled: bool = True,
) -> GuardedOpenRouter:
    """
    创建带迭代防护的 OpenRouter 模型实例

    基于项目的三层 API Key 优先级和 to_agno_params() 参数转换，
    在此基础上添加 LLM 迭代次数防护。

    Args:
        config: 模型配置（ModelConfig）
        project_config: 项目级配置（用于共享 API Key）
        max_iterations: LLM 最大调用次数（默认 50）
        guard_enabled: 是否启用迭代防护（默认 True）

    Returns:
        GuardedOpenRouter 模型实例

    使用示例:

    ```python
    from app.models import ModelConfig, ProjectConfig
    from app.models.providers.guarded import create_guarded_openrouter_model

    config = ModelConfig(
        model_id="google/gemini-2.5-flash-preview-05-20",
        temperature=0.2,
        max_tokens=16384,
    )

    model = create_guarded_openrouter_model(
        config=config,
        project_config=PROJECT_CONFIG,
        max_iterations=50,
    )

    agent = Agent(model=model, tools=[...])
    ```
    """
    api_key = _get_api_key(config, project_config)

    if not api_key:
        raise ValueError(
            "OpenRouter API Key not found. Please set one of: "
            f"config.api_key_env, project_config.api_key_env, or "
            f"{PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.OPENROUTER)}"
        )

    # 获取 Agno 参数（复用 config.to_agno_params()）
    params = config.to_agno_params()

    logger.info(
        "Creating GuardedOpenRouter model: %s (max_iterations=%d)",
        params.get("id"),
        max_iterations,
    )

    return GuardedOpenRouter(
        api_key=api_key,
        max_iterations=max_iterations,
        guard_enabled=guard_enabled,
        **params,
    )


# 保留简单工厂函数（向后兼容）
def create_guarded_openrouter(
    model_id: str,
    api_key: str | None = None,
    max_iterations: int = 50,
    max_tokens: int = 16384,
    **kwargs: Any,
) -> GuardedOpenRouter:
    """
    创建带迭代防护的 OpenRouter 模型（简单版）

    直接指定参数创建，不使用 ModelConfig。
    推荐使用 create_guarded_openrouter_model 以复用项目配置体系。

    Args:
        model_id: 模型 ID
        api_key: API Key（可选）
        max_iterations: LLM 最大调用次数
        max_tokens: 最大输出 token 数
    """
    return GuardedOpenRouter(
        id=model_id,
        api_key=api_key,
        max_iterations=max_iterations,
        max_tokens=max_tokens,
        **kwargs,
    )
