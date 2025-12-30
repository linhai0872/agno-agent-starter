"""
Tools 抽象层

提供三层工具优先级系统，支持：
- Framework 级：框架内置工具
- Project 级：项目专属工具和覆盖配置
- Agent 级：单个 Agent 的工具和覆盖配置

支持三种定制模式：
- inherit: 继承原工具，仅修改指定属性
- wrap: 包装原工具，在调用前后添加自定义逻辑
- replace: 完全替换原工具实现
"""

from app.tools.config import (
    MCPConfig,
    MCPServerConfig,
    ParamConfig,
    ParamOverride,
    ProjectToolsConfig,
    ToolConfig,
    ToolOverride,
    UNSET,
)
from app.tools.registry import ToolRegistry, get_tool_registry

__all__ = [
    # 配置类
    "ToolConfig",
    "ToolOverride",
    "ParamOverride",
    "ParamConfig",
    "ProjectToolsConfig",
    "MCPConfig",
    "MCPServerConfig",
    "UNSET",
    # 注册表
    "ToolRegistry",
    "get_tool_registry",
]


