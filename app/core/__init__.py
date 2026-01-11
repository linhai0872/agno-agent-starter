"""
Core 抽象层

提供核心抽象基类，供 tools, hooks 等模块继承。

主要组件：
- PriorityRegistry[T]: 三层优先级注册表抽象基类
- RegistryConflictError: 同层级冲突异常
- RegistryLevel: 优先级层枚举
"""

from app.core.registry import (
    PriorityRegistry,
    RegistryConflictError,
    RegistryLevel,
)

__all__ = [
    "PriorityRegistry",
    "RegistryConflictError",
    "RegistryLevel",
]
