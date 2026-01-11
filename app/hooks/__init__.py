"""
Hooks/Guardrails 抽象层

提供三层 Hooks 优先级系统，支持：
- Framework 级：框架内置护栏
- Project 级：项目专属护栏和覆盖配置
- Agent 级：单个 Agent 的护栏和覆盖配置

执行顺序：
- Pre-Hooks: Framework -> Project -> Agent（外到内）
- Post-Hooks: Agent -> Project -> Framework（内到外）
"""

from app.core.registry import RegistryConflictError
from app.hooks.config import (
    HookConfig,
    HookOverride,
    HooksConfig,
)
from app.hooks.registry import HooksRegistry, get_hooks_registry

__all__ = [
    # 配置类
    "HookConfig",
    "HookOverride",
    "HooksConfig",
    # 注册表
    "HooksRegistry",
    "get_hooks_registry",
    "RegistryConflictError",
]
