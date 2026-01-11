"""
工具注册表

实现三层工具优先级系统：
1. Framework 级：框架内置工具
2. Project 级：项目专属工具和覆盖配置
3. Agent 级：单个 Agent 的工具和覆盖配置

优先级规则（覆盖模式）：
- Agent 级完全覆盖 Project 级
- Project 级完全覆盖 Framework 级
- 同名工具：高优先级完全覆盖低优先级
"""

import functools
import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.tools.config import (
    UNSET,
    ProjectToolsConfig,
    ToolOverride,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """工具定义"""

    # 工具名称
    name: str

    # 工具描述
    description: str

    # 工具函数
    func: Callable

    # 参数信息
    parameters: dict[str, dict[str, Any]] = field(default_factory=dict)

    # 优先级层
    level: str = "framework"


class ToolRegistry:
    """
    三层工具注册表

    使用示例:

    ```python
    registry = get_tool_registry()

    # 注册框架级工具
    registry.register_framework_tool(company_enrichment)
    registry.register_framework_tool(tavily_search)

    # 注册项目级配置
    registry.register_project_config(
        ProjectToolsConfig(
            project_id="japan-sales",
            overrides=[
                ToolOverride(
                    tool_name="company_enrichment",
                    mode="inherit",
                    description="日本市场公司查询",
                ),
            ],
        )
    )

    # 获取 Agent 的最终工具列表
    tools = registry.get_tools_for_agent(
        agent_tools=[my_agent_tool],
        project_id="japan-sales",
    )
    ```
    """

    def __init__(self):
        # 框架级工具
        self._framework_tools: dict[str, ToolDefinition] = {}

        # 项目级配置
        self._project_configs: dict[str, ProjectToolsConfig] = {}

    def register_framework_tool(
        self,
        tool: Callable,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """
        注册框架级工具

        Args:
            tool: 工具函数
            name: 工具名称（默认使用函数名）
            description: 工具描述（默认使用 docstring）
        """
        tool_name = name or getattr(tool, "__name__", str(tool))
        tool_desc = description or (tool.__doc__ or "").strip().split("\n")[0]

        # 解析参数信息
        parameters = self._extract_parameters(tool)

        self._framework_tools[tool_name] = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            func=tool,
            parameters=parameters,
            level="framework",
        )

        logger.debug("Registered framework tool: %s", tool_name)

    def register_project_config(self, config: ProjectToolsConfig) -> None:
        """
        注册项目级配置

        Args:
            config: 项目工具配置
        """
        self._project_configs[config.project_id] = config
        logger.debug("Registered project config: %s", config.project_id)

    def get_tools_for_agent(
        self,
        agent_tools: list[Callable] | None = None,
        agent_overrides: list[ToolOverride] | None = None,
        project_id: str | None = None,
    ) -> list[Callable]:
        """
        获取 Agent 最终工具列表

        优先级（覆盖模式）：
        1. Agent 级 overrides/tools
        2. Project 级 overrides/tools
        3. Framework 级 tools

        同名工具：高优先级完全覆盖低优先级

        Args:
            agent_tools: Agent 专属工具
            agent_overrides: Agent 级覆盖配置
            project_id: 项目 ID（用于获取项目级配置）

        Returns:
            最终工具函数列表
        """
        # 收集所有工具名称和对应的工具
        final_tools: dict[str, Callable] = {}

        # 1. 首先添加框架级工具
        for name, tool_def in self._framework_tools.items():
            final_tools[name] = tool_def.func

        # 2. 应用项目级配置
        if project_id and project_id in self._project_configs:
            project_config = self._project_configs[project_id]

            # 禁用的工具
            for disabled_name in project_config.disabled_tools:
                final_tools.pop(disabled_name, None)

            # 应用项目级覆盖
            for override in project_config.overrides:
                if override.tool_name in self._framework_tools:
                    base_tool = self._framework_tools[override.tool_name]
                    final_tools[override.tool_name] = self._apply_override(base_tool, override)

            # 添加项目自定义工具
            for custom_tool in project_config.custom_tools:
                tool_name = getattr(custom_tool, "__name__", str(custom_tool))
                final_tools[tool_name] = custom_tool

        # 3. 应用 Agent 级覆盖
        if agent_overrides:
            for override in agent_overrides:
                if override.tool_name in self._framework_tools:
                    base_tool = self._framework_tools[override.tool_name]
                    final_tools[override.tool_name] = self._apply_override(base_tool, override)
                elif override.tool_name in final_tools:
                    # 覆盖项目级工具
                    # 需要从当前 final_tools 创建 ToolDefinition
                    current_func = final_tools[override.tool_name]
                    temp_def = ToolDefinition(
                        name=override.tool_name,
                        description=(current_func.__doc__ or "").strip().split("\n")[0],
                        func=current_func,
                        parameters=self._extract_parameters(current_func),
                        level="project",
                    )
                    final_tools[override.tool_name] = self._apply_override(temp_def, override)

        # 4. 添加 Agent 专属工具（完全覆盖同名工具）
        if agent_tools:
            for tool in agent_tools:
                tool_name = getattr(tool, "__name__", str(tool))
                final_tools[tool_name] = tool

        return list(final_tools.values())

    def _apply_override(
        self,
        base_tool: ToolDefinition,
        override: ToolOverride,
    ) -> Callable:
        """
        应用工具覆盖配置

        Args:
            base_tool: 基础工具定义
            override: 覆盖配置

        Returns:
            覆盖后的工具函数
        """
        if override.mode == "replace":
            return self._apply_replace(base_tool, override)
        elif override.mode == "wrap":
            return self._apply_wrap(base_tool, override)
        else:  # inherit
            return self._apply_inherit(base_tool, override)

    def _apply_replace(
        self,
        base_tool: ToolDefinition,
        override: ToolOverride,
    ) -> Callable:
        """替换模式：完全替换原工具"""
        if override.replacement is None:
            logger.warning(
                "Replace mode requires replacement function for tool: %s",
                override.tool_name,
            )
            return base_tool.func

        return override.replacement

    def _apply_wrap(
        self,
        base_tool: ToolDefinition,
        override: ToolOverride,
    ) -> Callable:
        """包装模式：在调用前后添加自定义逻辑"""
        original_func = base_tool.func
        pre_hook = override.pre_hook
        post_hook = override.post_hook

        if inspect.iscoroutinefunction(original_func):

            @functools.wraps(original_func)
            async def wrapped_async(*args, **kwargs):
                # 前置处理
                if pre_hook:
                    kwargs = pre_hook(kwargs)

                # 调用原函数
                result = await original_func(*args, **kwargs)

                # 后置处理
                if post_hook:
                    result = post_hook(result)

                return result

            return wrapped_async
        else:

            @functools.wraps(original_func)
            def wrapped_sync(*args, **kwargs):
                # 前置处理
                if pre_hook:
                    kwargs = pre_hook(kwargs)

                # 调用原函数
                result = original_func(*args, **kwargs)

                # 后置处理
                if post_hook:
                    result = post_hook(result)

                return result

            return wrapped_sync

    def _apply_inherit(
        self,
        base_tool: ToolDefinition,
        override: ToolOverride,
    ) -> Callable:
        """
        继承模式：仅修改指定属性

        修改工具的 __doc__ 和参数信息，但保持原函数逻辑。
        """
        original_func = base_tool.func

        # 创建包装函数
        if inspect.iscoroutinefunction(original_func):

            @functools.wraps(original_func)
            async def inherited_async(*args, **kwargs):
                # 处理隐藏参数（从 kwargs 中移除）
                for hidden in override.hidden_params:
                    kwargs.pop(hidden, None)

                # 处理新增参数的默认值
                for param in override.additional_params:
                    if param.name not in kwargs and param.default is not None:
                        kwargs[param.name] = param.default

                # 处理参数覆盖的默认值
                for param_name, param_override in override.param_overrides.items():
                    if param_name not in kwargs and param_override.default is not UNSET:
                        kwargs[param_name] = param_override.default

                return await original_func(*args, **kwargs)

            wrapper = inherited_async
        else:

            @functools.wraps(original_func)
            def inherited_sync(*args, **kwargs):
                # 处理隐藏参数
                for hidden in override.hidden_params:
                    kwargs.pop(hidden, None)

                # 处理新增参数的默认值
                for param in override.additional_params:
                    if param.name not in kwargs and param.default is not None:
                        kwargs[param.name] = param.default

                # 处理参数覆盖的默认值
                for param_name, param_override in override.param_overrides.items():
                    if param_name not in kwargs and param_override.default is not UNSET:
                        kwargs[param_name] = param_override.default

                return original_func(*args, **kwargs)

            wrapper = inherited_sync

        # 更新描述
        if override.description:
            wrapper.__doc__ = override.description

        return wrapper

    def _extract_parameters(self, func: Callable) -> dict[str, dict[str, Any]]:
        """从函数签名提取参数信息"""
        parameters = {}

        try:
            sig = inspect.signature(func)
            for name, param in sig.parameters.items():
                if name in ("self", "cls"):
                    continue

                param_info: dict[str, Any] = {
                    "name": name,
                    "required": param.default is inspect.Parameter.empty,
                }

                if param.default is not inspect.Parameter.empty:
                    param_info["default"] = param.default

                if param.annotation is not inspect.Parameter.empty:
                    param_info["type"] = param.annotation

                parameters[name] = param_info
        except (ValueError, TypeError):
            pass

        return parameters

    def list_framework_tools(self) -> list[str]:
        """列出所有框架级工具名称"""
        return list(self._framework_tools.keys())

    def list_project_ids(self) -> list[str]:
        """列出所有已注册的项目 ID"""
        return list(self._project_configs.keys())

    def get_tool_info(self, tool_name: str) -> ToolDefinition | None:
        """获取工具定义信息"""
        return self._framework_tools.get(tool_name)


# 全局单例
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表实例"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
