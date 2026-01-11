"""
工具调用防护 (Tool Call Guard)

基于 Agno 框架官方最佳实践的多层防护机制，用于防止 Agent 工具调用无限循环。

机制说明:
- 软限制 (RetryAgentRun): 单工具调用过多时，跳过该工具并反馈给模型，Agent 继续运行
- 硬限制 (StopAgentRun): 达到安全阈值时强制终止 Agent，防止无限循环

使用示例:

```python
from app.hooks.builtin.tool_call_guard import ToolCallGuard

# 创建防护器实例
guard = ToolCallGuard(
    max_calls_per_tool=5,  # 单工具最多调用 5 次
    max_retries_per_tool=3,  # 单工具最多触发 3 次 RetryAgentRun
    max_total_calls=30,  # 总工具调用上限
)

# 应用到 Agent
agent = Agent(
    tools=[...],
    tool_hooks=[guard],  # 添加为 tool_hook
)
```

参考文档:
- https://docs.agno.com/basics/tools/tool-call-limit
- https://docs.agno.com/basics/tools/exceptions
- https://docs.agno.com/basics/tools/hooks
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agno.exceptions import RetryAgentRun, StopAgentRun

logger = logging.getLogger(__name__)


@dataclass
class ToolCallGuardConfig:
    """
    工具调用防护配置

    参数说明:
        max_calls_per_tool: 单个工具的最大调用次数，超过后触发 RetryAgentRun
        max_retries_per_tool: 单个工具触发 RetryAgentRun 的最大次数，超过后升级为 StopAgentRun
        max_total_calls: 所有工具的总调用次数上限，超过后触发 StopAgentRun
        retry_message_template: RetryAgentRun 消息模板
        stop_message_template: StopAgentRun 消息模板
    """

    # 单工具调用上限（软限制）
    max_calls_per_tool: int = 5

    # 单工具 retry 上限（升级为硬限制）
    max_retries_per_tool: int = 3

    # 总调用上限（硬限制）
    max_total_calls: int = 30

    # 是否启用
    enabled: bool = True

    # 自定义消息模板
    retry_message_template: str = (
        "⚠️ 工具 {tool_name} 已调用 {call_count} 次，超过单工具限制 ({limit})。\n"
        "请执行以下操作之一：\n"
        "1. 使用其他工具获取所需信息\n"
        "2. 基于已收集的数据生成最终输出\n"
        "禁止继续调用 {tool_name}！"
    )

    stop_message_template: str = "🛑 {reason}。\n请基于已收集的信息生成输出。"


class ToolCallGuard:
    """
    工具调用防护器

    实现 Agno tool_hooks 接口，提供多层防护：

    1. 软限制层 (RetryAgentRun):
       - 检测单工具调用次数过多
       - 跳过该工具，反馈给模型
       - Agent 继续运行，可使用其他工具

    2. 硬限制层 (StopAgentRun):
       - 单工具重试次数过多（模型未学会）
       - 总调用次数超限
       - 强制终止 Agent，Workflow 继续下一个节点

    使用示例:

    ```python
    guard = ToolCallGuard(max_calls_per_tool=5)

    agent = Agent(
        tools=[...],
        tool_hooks=[guard],
    )
    ```
    """

    def __init__(
        self,
        max_calls_per_tool: int = 5,
        max_retries_per_tool: int = 3,
        max_total_calls: int = 30,
        enabled: bool = True,
        config: ToolCallGuardConfig | None = None,
    ):
        """
        初始化工具调用防护器

        Args:
            max_calls_per_tool: 单工具最大调用次数
            max_retries_per_tool: 单工具最大重试次数
            max_total_calls: 总工具调用上限
            enabled: 是否启用防护
            config: 完整配置对象（覆盖其他参数）
        """
        if config:
            self.config = config
        else:
            self.config = ToolCallGuardConfig(
                max_calls_per_tool=max_calls_per_tool,
                max_retries_per_tool=max_retries_per_tool,
                max_total_calls=max_total_calls,
                enabled=enabled,
            )

        # 计数器
        self._call_counter: dict[str, int] = {}
        self._retry_counter: dict[str, int] = {}

    def reset(self) -> None:
        """
        重置计数器

        在每次 Agent run 开始时调用，清空所有计数。
        注意：Agno 框架会为每个 Agent run 创建新的 hook 实例，
        因此通常不需要手动调用此方法。
        """
        self._call_counter.clear()
        self._retry_counter.clear()
        logger.debug("ToolCallGuard counters reset")

    @property
    def call_counts(self) -> dict[str, int]:
        """获取当前工具调用计数（只读）"""
        return dict(self._call_counter)

    @property
    def total_calls(self) -> int:
        """获取总调用次数"""
        return sum(self._call_counter.values())

    def __call__(
        self,
        function_name: str,
        function_call: Callable[..., Any],
        arguments: dict[str, Any],
    ) -> Any:
        """
        tool_hooks 接口实现

        每次工具调用时由 Agno 框架调用此方法。

        Args:
            function_name: 工具函数名称
            function_call: 工具函数引用
            arguments: 调用参数

        Returns:
            工具执行结果

        Raises:
            RetryAgentRun: 单工具调用过多，反馈给模型
            StopAgentRun: 达到安全阈值，强制终止
        """
        if not self.config.enabled:
            return function_call(**arguments)

        # 更新调用计数
        self._call_counter[function_name] = self._call_counter.get(function_name, 0) + 1
        current_count = self._call_counter[function_name]
        total = self.total_calls

        logger.debug(
            "ToolCallGuard: %s (count=%d, total=%d)",
            function_name,
            current_count,
            total,
        )

        # 硬限制 1: 总调用次数超限
        if total > self.config.max_total_calls:
            reason = f"工具总调用次数 ({total}) 已超过上限 ({self.config.max_total_calls})"
            logger.warning("ToolCallGuard: %s - forcing stop", reason)
            raise StopAgentRun(self.config.stop_message_template.format(reason=reason))

        # 软限制: 单工具调用过多
        if current_count > self.config.max_calls_per_tool:
            self._retry_counter[function_name] = self._retry_counter.get(function_name, 0) + 1
            retry_count = self._retry_counter[function_name]

            # 硬限制 2: 重试次数过多（模型未学会）
            if retry_count > self.config.max_retries_per_tool:
                reason = (
                    f"工具 {function_name} 在 {self.config.max_retries_per_tool} 次"
                    f"提醒后仍被重复调用"
                )
                logger.warning("ToolCallGuard: %s - forcing stop", reason)
                raise StopAgentRun(self.config.stop_message_template.format(reason=reason))

            # 触发软限制
            logger.info(
                "ToolCallGuard: %s call limit reached (count=%d, retry=%d/%d)",
                function_name,
                current_count,
                retry_count,
                self.config.max_retries_per_tool,
            )
            raise RetryAgentRun(
                self.config.retry_message_template.format(
                    tool_name=function_name,
                    call_count=current_count,
                    limit=self.config.max_calls_per_tool,
                )
            )

        # 正常执行工具
        return function_call(**arguments)


# ============== 预配置实例（懒加载）==============

_default_guard: ToolCallGuard | None = None
_strict_guard: ToolCallGuard | None = None
_relaxed_guard: ToolCallGuard | None = None


def get_default_guard() -> ToolCallGuard:
    """获取默认配置的防护器实例（懒加载）"""
    global _default_guard
    if _default_guard is None:
        _default_guard = ToolCallGuard(
            max_calls_per_tool=5,
            max_retries_per_tool=3,
            max_total_calls=30,
        )
    return _default_guard


def get_strict_guard() -> ToolCallGuard:
    """获取严格配置的防护器实例（懒加载，适用于成本敏感场景）"""
    global _strict_guard
    if _strict_guard is None:
        _strict_guard = ToolCallGuard(
            max_calls_per_tool=3,
            max_retries_per_tool=2,
            max_total_calls=15,
        )
    return _strict_guard


def get_relaxed_guard() -> ToolCallGuard:
    """获取宽松配置的防护器实例（懒加载，适用于复杂任务）"""
    global _relaxed_guard
    if _relaxed_guard is None:
        _relaxed_guard = ToolCallGuard(
            max_calls_per_tool=10,
            max_retries_per_tool=5,
            max_total_calls=50,
        )
    return _relaxed_guard


def create_tool_call_guard(
    max_calls_per_tool: int = 5,
    max_retries_per_tool: int = 3,
    max_total_calls: int = 30,
) -> ToolCallGuard:
    """
    创建工具调用防护器实例

    工厂函数，用于为每个 Agent 创建独立的防护器实例。

    Args:
        max_calls_per_tool: 单工具最大调用次数
        max_retries_per_tool: 单工具最大重试次数
        max_total_calls: 总工具调用上限

    Returns:
        新的 ToolCallGuard 实例

    使用示例:

    ```python
    from app.hooks.builtin.tool_call_guard import create_tool_call_guard

    agent = Agent(
        tools=[...],
        tool_hooks=[create_tool_call_guard(max_calls_per_tool=10)],
    )
    ```
    """
    return ToolCallGuard(
        max_calls_per_tool=max_calls_per_tool,
        max_retries_per_tool=max_retries_per_tool,
        max_total_calls=max_total_calls,
    )
