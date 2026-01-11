"""
框架级内置护栏

这些护栏在框架级别注册，可被所有项目和 Agent 使用。
项目和 Agent 可以通过 HookOverride 对这些护栏进行定制。
"""

from app.hooks.builtin.content_safety import content_safety_check
from app.hooks.builtin.output_validator import length_check, quality_check
from app.hooks.builtin.pii_filter import pii_filter_check
from app.hooks.builtin.tool_call_guard import (
    ToolCallGuard,
    ToolCallGuardConfig,
    create_tool_call_guard,
    get_default_guard,
    get_relaxed_guard,
    get_strict_guard,
)

__all__ = [
    # 内容安全
    "content_safety_check",
    # PII 过滤
    "pii_filter_check",
    # 输出验证
    "quality_check",
    "length_check",
    # 工具调用防护
    "ToolCallGuard",
    "ToolCallGuardConfig",
    "create_tool_call_guard",
    "get_default_guard",
    "get_strict_guard",
    "get_relaxed_guard",
]
