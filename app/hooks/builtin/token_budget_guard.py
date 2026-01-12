"""
Token 预算防护 (Token Budget Guard) - V2

基于 Agno post_hooks 机制，防止 Token 使用超出预算。

V2 重构亮点:
- 使用 Agno 原生 run_context.session_state 存储累计 Token
- 天然请求级别隔离，无跨请求状态累积问题
- 完全兼容 Agno post_hooks 接口

设计来源:
- Agno: run_context.session_state 存储 + StopAgentRun 异常
- Dify: Layer 模式 (on_event 检查 + 优雅停止)
- 需求: 请求级别隔离 + 成本控制

使用示例:

```python
from app.hooks.builtin.token_budget_guard import TokenBudgetGuard

guard = TokenBudgetGuard(max_tokens=100000)
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

_GUARD_STATE_PREFIX = "_token_budget_guard"


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
class TokenBudgetGuardConfig:
    """
    Token 预算防护配置

    参数说明:
        max_tokens: Token 预算上限，超过后触发 StopAgentRun
        warn_threshold: 警告阈值 (0.0-1.0)，达到后开始记录警告日志
        enabled: 是否启用防护
    """

    max_tokens: int = 100000
    warn_threshold: float = 0.8
    enabled: bool = True

    stop_message_template: str = (
        "🛑 Token 使用量 ({total}) 已超过预算 ({limit})。\n请基于已收集的信息生成输出。"
    )


class TokenBudgetGuard:
    """
    Token 预算防护器 (V2 - 请求级别隔离)

    使用 Agno 原生 run_context.session_state 存储累计 Token，
    实现请求级别隔离，无需额外配置即可解决跨请求状态累积问题。

    实现 Agno post_hooks 接口:
    - 每次 LLM 响应后由框架调用
    - 从 run_output 提取 token 使用量
    - 达到警告阈值时记录日志
    - 超过预算时抛出 StopAgentRun 终止 Agent

    使用示例:

    ```python
    guard = TokenBudgetGuard(max_tokens=100000)

    agent = Agent(
        model=model,
        post_hooks=[guard],
    )
    ```
    """

    def __init__(
        self,
        max_tokens: int = 100000,
        warn_threshold: float = 0.8,
        enabled: bool = True,
        config: TokenBudgetGuardConfig | None = None,
    ):
        """
        初始化 Token 预算防护器

        Args:
            max_tokens: Token 预算上限
            warn_threshold: 警告阈值 (0.0-1.0)
            enabled: 是否启用防护
            config: 完整配置对象（覆盖其他参数）
        """
        if config:
            self.config = config
        else:
            self.config = TokenBudgetGuardConfig(
                max_tokens=max_tokens,
                warn_threshold=warn_threshold,
                enabled=enabled,
            )

        self._guard_id = f"{_GUARD_STATE_PREFIX}_{id(self)}"

    def _get_state(self, run_context: RunContext) -> dict[str, int]:
        """
        获取当前请求的 Token 累计状态

        使用 run_context.session_state 存储，天然请求隔离。

        Args:
            run_context: Agno 运行上下文

        Returns:
            包含 total_tokens 的字典
        """
        if run_context.session_state is None:
            run_context.session_state = {}

        if self._guard_id not in run_context.session_state:
            run_context.session_state[self._guard_id] = {"total_tokens": 0}

        return run_context.session_state[self._guard_id]

    def _extract_tokens(self, run_output: Any) -> int:
        """
        从 RunOutput 提取 token 使用量 (兼容多种 Agno 版本)

        Args:
            run_output: Agent 输出对象

        Returns:
            本次调用的 token 使用量
        """
        # 尝试多种路径获取 token
        if hasattr(run_output, "metrics") and run_output.metrics:
            metrics = run_output.metrics
            if isinstance(metrics, dict):
                return metrics.get("total_tokens", 0) or 0
            return getattr(metrics, "total_tokens", 0) or 0

        if hasattr(run_output, "response_usage"):
            usage = run_output.response_usage
            if usage:
                return getattr(usage, "total_tokens", 0) or 0

        if hasattr(run_output, "messages") and run_output.messages:
            last_msg = run_output.messages[-1]
            if hasattr(last_msg, "usage"):
                usage = last_msg.usage
                if usage:
                    return getattr(usage, "total_tokens", 0) or 0

        return 0

    def get_total_tokens(self, run_context: RunContext) -> int:
        """获取当前请求的累计 Token 使用量"""
        state = self._get_state(run_context)
        return state.get("total_tokens", 0)

    def get_remaining(self, run_context: RunContext) -> int:
        """获取当前请求的剩余 Token 预算"""
        return max(0, self.config.max_tokens - self.get_total_tokens(run_context))

    def reset(self, run_context: RunContext) -> None:
        """
        重置当前请求的 Token 累计

        通常不需要手动调用，因为每个请求有独立的 session_state。
        仅在特殊场景（如同一请求内多次 Agent 调用）使用。
        """
        if run_context.session_state and self._guard_id in run_context.session_state:
            del run_context.session_state[self._guard_id]
        logger.debug("TokenBudgetGuard counters reset for guard_id=%s", self._guard_id)

    def __call__(
        self,
        run_output: Any,
        run_context: RunContext,
    ) -> None:
        """
        post_hooks 接口实现 (V2 - 支持 run_context)

        每次 LLM 响应后由 Agno 框架调用此方法。

        Args:
            run_output: Agent 输出对象（包含 metrics/usage）
            run_context: Agno 运行上下文（包含 session_state）

        Raises:
            StopAgentRun: 超过 Token 预算时强制终止
        """
        if not self.config.enabled:
            return

        tokens_used = self._extract_tokens(run_output)
        if tokens_used <= 0:
            return

        state = self._get_state(run_context)
        state["total_tokens"] = state.get("total_tokens", 0) + tokens_used
        total = state["total_tokens"]

        logger.debug(
            "TokenBudgetGuard: +%d tokens, total=%d/%d, guard=%s",
            tokens_used,
            total,
            self.config.max_tokens,
            self._guard_id,
        )

        warn_at = int(self.config.max_tokens * self.config.warn_threshold)
        if total >= warn_at and total <= self.config.max_tokens:
            logger.warning(
                "Token usage approaching budget (%d/%d)",
                total,
                self.config.max_tokens,
            )

        if total > self.config.max_tokens:
            stop_exception = _get_stop_exception()
            message = self.config.stop_message_template.format(
                total=total,
                limit=self.config.max_tokens,
            )
            logger.warning("TokenBudgetGuard: %s - forcing stop", message)
            raise stop_exception(message)


# ============== 工厂函数 ==============


def create_token_budget_guard(
    max_tokens: int = 100000,
    warn_threshold: float = 0.8,
) -> TokenBudgetGuard:
    """
    创建 Token 预算防护器实例

    工厂函数，用于为每个 Agent 创建独立的防护器实例。

    注意：V2 版本使用 run_context.session_state 存储累计 Token，
    即使多个 Agent 共享同一个 Guard 实例，每个请求的 Token 累计也是隔离的。

    Args:
        max_tokens: Token 预算上限
        warn_threshold: 警告阈值 (0.0-1.0)

    Returns:
        新的 TokenBudgetGuard 实例

    使用示例:

    ```python
    from app.hooks.builtin.token_budget_guard import create_token_budget_guard

    agent = Agent(
        model=model,
        post_hooks=[create_token_budget_guard(max_tokens=50000)],
    )
    ```
    """
    return TokenBudgetGuard(
        max_tokens=max_tokens,
        warn_threshold=warn_threshold,
    )


# ============== 预配置工厂 ==============


def get_default_guard() -> TokenBudgetGuard:
    """获取默认配置的防护器实例 (max=100000, warn=0.8)"""
    return TokenBudgetGuard(max_tokens=100000, warn_threshold=0.8)


def get_strict_guard() -> TokenBudgetGuard:
    """获取严格配置的防护器实例 (max=30000, warn=0.7)"""
    return TokenBudgetGuard(max_tokens=30000, warn_threshold=0.7)


def get_relaxed_guard() -> TokenBudgetGuard:
    """获取宽松配置的防护器实例 (max=500000, warn=0.9)"""
    return TokenBudgetGuard(max_tokens=500000, warn_threshold=0.9)


__all__ = [
    "TokenBudgetGuard",
    "TokenBudgetGuardConfig",
    "create_token_budget_guard",
    "get_default_guard",
    "get_strict_guard",
    "get_relaxed_guard",
]
