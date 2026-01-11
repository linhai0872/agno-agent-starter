"""
LLM 调用防护 (符合 Agno Post-Hook 设计)

替代原有的 GuardedOpenRouter (Model 层状态违反 Agno 设计原则)。
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


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


class LLMInvocationGuard:
    """
    LLM 调用防护 (符合 Agno Post-Hook 设计)

    使用示例:

    ```python
    from app.agents.guards import LLMInvocationGuard

    guard = LLMInvocationGuard(max_invocations=50)
    agent = Agent(model=model, post_hooks=[guard])

    # 每次新会话
    guard.reset()
    agent.run("...")
    ```
    """

    def __init__(self, max_invocations: int = 50, warn_threshold: float = 0.8):
        self.max_invocations = max_invocations
        self.warn_threshold = warn_threshold
        self._count = 0

    def __call__(self, run_response: Any) -> None:
        """Post-hook: 每次 LLM 响应后调用"""
        self._count += 1

        warn_at = int(self.max_invocations * self.warn_threshold)
        if self._count >= warn_at:
            logger.warning(
                "LLM invocation approaching limit (%d/%d)",
                self._count,
                self.max_invocations,
            )

        if self._count > self.max_invocations:
            stop_exception = _get_stop_exception()
            raise stop_exception(
                f"LLM invocation count ({self._count}) exceeded limit "
                f"({self.max_invocations}), terminated"
            )

    def reset(self) -> None:
        """重置计数 (每次新会话调用)"""
        self._count = 0

    @property
    def count(self) -> int:
        """当前调用次数"""
        return self._count

    @property
    def remaining(self) -> int:
        """剩余调用次数"""
        return max(0, self.max_invocations - self._count)


class TokenBudgetGuard:
    """
    Token 预算防护

    跟踪累计 Token 使用量，超过预算时终止。

    使用示例:

    ```python
    guard = TokenBudgetGuard(max_tokens=100000)
    agent = Agent(model=model, post_hooks=[guard])
    ```
    """

    def __init__(self, max_tokens: int = 100000, warn_threshold: float = 0.8):
        self.max_tokens = max_tokens
        self.warn_threshold = warn_threshold
        self._total_tokens = 0

    def __call__(self, run_response: Any) -> None:
        """Post-hook: 每次 LLM 响应后调用"""
        tokens_used = self._extract_tokens(run_response)
        if tokens_used > 0:
            self._total_tokens += tokens_used

        warn_at = int(self.max_tokens * self.warn_threshold)
        if self._total_tokens >= warn_at:
            logger.warning(
                "Token usage approaching budget (%d/%d)",
                self._total_tokens,
                self.max_tokens,
            )

        if self._total_tokens > self.max_tokens:
            stop_exception = _get_stop_exception()
            raise stop_exception(
                f"Token usage ({self._total_tokens}) exceeded budget "
                f"({self.max_tokens}), terminated"
            )

    def _extract_tokens(self, run_response: Any) -> int:
        """从 RunResponse 提取 token 使用量 (兼容多种 Agno 版本)"""
        # 尝试多种路径获取 token
        if hasattr(run_response, "metrics") and run_response.metrics:
            metrics = run_response.metrics
            # Agno RunResponse.metrics 可能是 dict 或 object
            if isinstance(metrics, dict):
                return metrics.get("total_tokens", 0) or 0
            return getattr(metrics, "total_tokens", 0) or 0

        # 尝试从 response_usage 获取 (某些 Agno 版本)
        if hasattr(run_response, "response_usage"):
            usage = run_response.response_usage
            if usage:
                return getattr(usage, "total_tokens", 0) or 0

        # 尝试从 messages 最后一条获取
        if hasattr(run_response, "messages") and run_response.messages:
            last_msg = run_response.messages[-1]
            if hasattr(last_msg, "usage"):
                usage = last_msg.usage
                if usage:
                    return getattr(usage, "total_tokens", 0) or 0

        return 0

    def reset(self) -> None:
        """重置累计 Token"""
        self._total_tokens = 0

    @property
    def total_tokens(self) -> int:
        """累计 Token 使用量"""
        return self._total_tokens

    @property
    def remaining(self) -> int:
        """剩余 Token 预算"""
        return max(0, self.max_tokens - self._total_tokens)

