"""
框架级内置护栏

这些护栏在框架级别注册，可被所有项目和 Agent 使用。
项目和 Agent 可以通过 HookOverride 对这些护栏进行定制。

护栏类型:
- tool_hooks: 工具调用防护 (ToolCallGuard)
- post_hooks: LLM 调用防护 (LLMInvocationGuard), Token 预算防护 (TokenBudgetGuard)
"""

from app.hooks.builtin.content_safety import content_safety_check
from app.hooks.builtin.llm_invocation_guard import (
    LLMInvocationGuard,
    LLMInvocationGuardConfig,
    create_llm_invocation_guard,
)
from app.hooks.builtin.llm_invocation_guard import (
    get_default_guard as get_default_llm_guard,
)
from app.hooks.builtin.llm_invocation_guard import (
    get_relaxed_guard as get_relaxed_llm_guard,
)
from app.hooks.builtin.llm_invocation_guard import (
    get_strict_guard as get_strict_llm_guard,
)
from app.hooks.builtin.output_validator import length_check, quality_check
from app.hooks.builtin.pii_filter import pii_filter_check
from app.hooks.builtin.token_budget_guard import (
    TokenBudgetGuard,
    TokenBudgetGuardConfig,
    create_token_budget_guard,
)
from app.hooks.builtin.token_budget_guard import (
    get_default_guard as get_default_token_guard,
)
from app.hooks.builtin.token_budget_guard import (
    get_relaxed_guard as get_relaxed_token_guard,
)
from app.hooks.builtin.token_budget_guard import (
    get_strict_guard as get_strict_token_guard,
)
from app.hooks.builtin.tool_call_guard import (
    ToolCallGuard,
    ToolCallGuardConfig,
    create_tool_call_guard,
)
from app.hooks.builtin.tool_call_guard import (
    get_default_guard as get_default_tool_guard,
)
from app.hooks.builtin.tool_call_guard import (
    get_relaxed_guard as get_relaxed_tool_guard,
)
from app.hooks.builtin.tool_call_guard import (
    get_strict_guard as get_strict_tool_guard,
)

__all__ = [
    # 内容安全
    "content_safety_check",
    # PII 过滤
    "pii_filter_check",
    # 输出验证
    "quality_check",
    "length_check",
    # 工具调用防护 (tool_hooks)
    "ToolCallGuard",
    "ToolCallGuardConfig",
    "create_tool_call_guard",
    "get_default_tool_guard",
    "get_strict_tool_guard",
    "get_relaxed_tool_guard",
    # LLM 调用防护 (post_hooks)
    "LLMInvocationGuard",
    "LLMInvocationGuardConfig",
    "create_llm_invocation_guard",
    "get_default_llm_guard",
    "get_strict_llm_guard",
    "get_relaxed_llm_guard",
    # Token 预算防护 (post_hooks)
    "TokenBudgetGuard",
    "TokenBudgetGuardConfig",
    "create_token_budget_guard",
    "get_default_token_guard",
    "get_strict_token_guard",
    "get_relaxed_token_guard",
]
