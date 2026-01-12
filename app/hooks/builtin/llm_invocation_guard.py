"""
LLM 调用防护 (LLM Invocation Guard) - V2

基于 Agno post_hooks 机制，防止 LLM 无限调用循环。

V2 重构亮点:
- 使用 Agno 原生 run_context.session_state 存储计数器
- 天然请求级别隔离，无跨请求状态累积问题
- 完全兼容 Agno post_hooks 接口

设计来源:
- Agno: run_context.session_state 存储 + StopAgentRun 异常
- Dify: Layer 模式 (on_event 检查 + 优雅停止)
- 需求: 请求级别隔离 + 优雅降级

使用示例:

```python
from app.hooks.builtin.llm_invocation_guard import LLMInvocationGuard

guard = LLMInvocationGuard(max_invocations=50)
agent = Agent(model=model, post_hooks=[guard])
```

参考文档:
- https://docs.agno.com/basics/hooks/overview
- https://docs.agno.com/basics/tools/exceptions
"""

import logging
from dataclasses import dataclass
from typing import Any

from agno.run import RunContext

logger = logging.getLogger(__name__)

_GUARD_STATE_PREFIX = "_llm_invocation_guard"


class StopAgentRunFallback(Exception):
    """Agno StopAgentRun 的降级异常"""

    pass


def _get_stop_exception() -> type:
    """获取 StopAgentRun 异常类，支持降级"""
    try:
        from agno.exceptions import StopAgentRun

        return StopAgentRun
    except ImportError:
        return StopAgentRunFallback


@dataclass
class LLMInvocationGuardConfig:
    """
    LLM 调用防护配置

    参数说明:
        max_invocations: LLM 最大调用次数，超过后触发 StopAgentRun
        warn_threshold: 警告阈值 (0.0-1.0)，达到后开始记录警告日志
        enabled: 是否启用防护
    """

    max_invocations: int = 50
    warn_threshold: float = 0.8
    enabled: bool = True

    stop_message_template: str = (
        "🛑 LLM 调用次数 ({count}) 已超过上限 ({limit})。\n请基于已收集的信息生成输出。"
    )


class LLMInvocationGuard:
    """
    LLM 调用防护器 (V2 - 请求级别隔离)

    使用 Agno 原生 run_context.session_state 存储计数器，
    实现请求级别隔离，无需额外配置即可解决跨请求状态累积问题。

    实现 Agno post_hooks 接口:
    - 每次 LLM 响应后由框架调用
    - 达到警告阈值时记录日志
    - 超过上限时抛出 StopAgentRun 终止 Agent

    使用示例:

    ```python
    guard = LLMInvocationGuard(max_invocations=50)

    agent = Agent(
        model=model,
        post_hooks=[guard],
    )
    ```
    """

    def __init__(
        self,
        max_invocations: int = 50,
        warn_threshold: float = 0.8,
        enabled: bool = True,
        config: LLMInvocationGuardConfig | None = None,
    ):
        """
        初始化 LLM 调用防护器

        Args:
            max_invocations: LLM 最大调用次数
            warn_threshold: 警告阈值 (0.0-1.0)
            enabled: 是否启用防护
            config: 完整配置对象（覆盖其他参数）
        """
        if config:
            self.config = config
        else:
            self.config = LLMInvocationGuardConfig(
                max_invocations=max_invocations,
                warn_threshold=warn_threshold,
                enabled=enabled,
            )

        self._guard_id = f"{_GUARD_STATE_PREFIX}_{id(self)}"

    def _get_state(self, run_context: RunContext) -> dict[str, int]:
        """
        获取当前请求的计数器状态

        使用 run_context.session_state 存储，天然请求隔离。

        Args:
            run_context: Agno 运行上下文

        Returns:
            包含 count 的字典
        """
        if run_context.session_state is None:
            run_context.session_state = {}

        if self._guard_id not in run_context.session_state:
            run_context.session_state[self._guard_id] = {"count": 0}

        return run_context.session_state[self._guard_id]

    def get_count(self, run_context: RunContext) -> int:
        """获取当前请求的 LLM 调用次数"""
        state = self._get_state(run_context)
        return state.get("count", 0)

    def get_remaining(self, run_context: RunContext) -> int:
        """获取当前请求的剩余调用次数"""
        return max(0, self.config.max_invocations - self.get_count(run_context))

    def reset(self, run_context: RunContext) -> None:
        """
        重置当前请求的计数器

        通常不需要手动调用，因为每个请求有独立的 session_state。
        仅在特殊场景（如同一请求内多次 Agent 调用）使用。
        """
        if run_context.session_state and self._guard_id in run_context.session_state:
            del run_context.session_state[self._guard_id]
        logger.debug("LLMInvocationGuard counters reset for guard_id=%s", self._guard_id)

    def __call__(
        self,
        run_output: Any,
        run_context: RunContext,
    ) -> None:
        """
        post_hooks 接口实现 (V2 - 支持 run_context)

        每次 LLM 响应后由 Agno 框架调用此方法。

        Args:
            run_output: Agent 输出对象
            run_context: Agno 运行上下文（包含 session_state）

        Raises:
            StopAgentRun: 超过调用上限时强制终止
        """
        if not self.config.enabled:
            return

        state = self._get_state(run_context)
        state["count"] = state.get("count", 0) + 1
        count = state["count"]

        logger.debug(
            "LLMInvocationGuard: count=%d/%d, guard=%s",
            count,
            self.config.max_invocations,
            self._guard_id,
        )

        warn_at = int(self.config.max_invocations * self.config.warn_threshold)
        if count >= warn_at and count <= self.config.max_invocations:
            logger.warning(
                "LLM invocation approaching limit (%d/%d)",
                count,
                self.config.max_invocations,
            )

        if count > self.config.max_invocations:
            stop_exception = _get_stop_exception()
            message = self.config.stop_message_template.format(
                count=count,
                limit=self.config.max_invocations,
            )
            logger.warning("LLMInvocationGuard: %s - forcing stop", message)
            raise stop_exception(message)


# ============== 工厂函数 ==============


def create_llm_invocation_guard(
    max_invocations: int = 50,
    warn_threshold: float = 0.8,
) -> LLMInvocationGuard:
    """
    创建 LLM 调用防护器实例

    工厂函数，用于为每个 Agent 创建独立的防护器实例。

    注意：V2 版本使用 run_context.session_state 存储计数器，
    即使多个 Agent 共享同一个 Guard 实例，每个请求的计数器也是隔离的。

    Args:
        max_invocations: LLM 最大调用次数
        warn_threshold: 警告阈值 (0.0-1.0)

    Returns:
        新的 LLMInvocationGuard 实例

    使用示例:

    ```python
    from app.hooks.builtin.llm_invocation_guard import create_llm_invocation_guard

    agent = Agent(
        model=model,
        post_hooks=[create_llm_invocation_guard(max_invocations=30)],
    )
    ```
    """
    return LLMInvocationGuard(
        max_invocations=max_invocations,
        warn_threshold=warn_threshold,
    )


# ============== 预配置工厂 ==============


def get_default_guard() -> LLMInvocationGuard:
    """获取默认配置的防护器实例 (max=50, warn=0.8)"""
    return LLMInvocationGuard(max_invocations=50, warn_threshold=0.8)


def get_strict_guard() -> LLMInvocationGuard:
    """获取严格配置的防护器实例 (max=20, warn=0.7)"""
    return LLMInvocationGuard(max_invocations=20, warn_threshold=0.7)


def get_relaxed_guard() -> LLMInvocationGuard:
    """获取宽松配置的防护器实例 (max=100, warn=0.9)"""
    return LLMInvocationGuard(max_invocations=100, warn_threshold=0.9)


__all__ = [
    "LLMInvocationGuard",
    "LLMInvocationGuardConfig",
    "create_llm_invocation_guard",
    "get_default_guard",
    "get_strict_guard",
    "get_relaxed_guard",
]
