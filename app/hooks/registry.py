"""
Hooks 注册表

实现三层 Hooks 优先级系统：
1. Framework 级：框架内置护栏
2. Project 级：项目专属护栏和覆盖配置
3. Agent 级：单个 Agent 的护栏和覆盖配置

执行顺序：
- Pre-Hooks: Framework -> Project -> Agent（外到内）
- Post-Hooks: Agent -> Project -> Framework（内到外）
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from app.core.registry import (
    PriorityRegistry,
    RegistryLevel,
)
from app.hooks.config import HookConfig, HookOverride, HooksConfig

logger = logging.getLogger(__name__)


@dataclass
class BuiltinFlags:
    """内置护栏开关状态"""

    enable_content_safety: bool = False
    content_safety_level: str = "moderate"
    enable_pii_filter: bool = False
    pii_types: list[str] = field(default_factory=lambda: ["email", "phone", "ssn", "credit_card"])
    enable_quality_check: bool = False
    min_quality_score: float = 0.6
    max_output_length: int | None = None


class HooksRegistry(PriorityRegistry[HookConfig]):
    """
    三层 Hooks 注册表

    内部存储使用 dict[str, HookConfig] 模式，与 ToolRegistry 保持一致。
    公开 API 保持向后兼容。

    使用示例:

    ```python
    registry = get_hooks_registry()

    # 注册框架级护栏
    registry.register_framework_hooks(
        HooksConfig(
            enable_content_safety=True,
        )
    )

    # 注册项目级配置
    registry.register_project_hooks(
        "ecommerce",
        HooksConfig(
            enable_pii_filter=True,
            post_hooks=[price_validation_hook],
        ),
    )

    # 获取 Agent 的最终 Hooks
    pre_hooks, post_hooks = registry.get_hooks_for_agent(
        agent_hooks=HooksConfig(enable_pii_filter=False),
        project_id="ecommerce",
    )
    ```
    """

    def __init__(self):
        super().__init__()

        # 使用基类的 _framework_items 存储 Framework 级自定义 hooks
        # dict[str, HookConfig] where key is hook name
        self._framework_hooks = self._framework_items

        # 使用基类的 _project_items 存储 Project 级自定义 hooks
        # dict[project_id, dict[str, HookConfig]]
        self._project_hooks = self._project_items

        # 内置护栏开关（分层存储）
        self._framework_flags: BuiltinFlags = BuiltinFlags()
        self._project_flags: dict[str, BuiltinFlags] = {}

        # Hook 覆盖配置（分层存储）
        self._framework_overrides: dict[str, HookOverride] = {}
        self._project_overrides: dict[str, dict[str, HookOverride]] = {}

        # 内置护栏函数（懒加载）
        self._builtin_hooks: dict[str, Callable] = {}

        # 跟踪 pre/post 类型（避免重构后丢失类型信息）
        self._hook_types: dict[str, str] = {}  # hook_name -> "pre" | "post"

    def register_framework_hooks(self, config: HooksConfig) -> None:
        """
        注册框架级 Hooks 配置

        将 HooksConfig 解析为内部 dict 存储模式。

        Args:
            config: 框架级 Hooks 配置

        Raises:
            RegistryConflictError: 如果同名自定义 Hook 已在 Framework 级注册
        """
        # 注册自定义 pre_hooks
        for hook in config.pre_hooks:
            self._check_conflict(self._framework_hooks, hook.name, RegistryLevel.FRAMEWORK)
            self._framework_hooks[hook.name] = hook
            self._hook_types[hook.name] = "pre"

        # 注册自定义 post_hooks
        for hook in config.post_hooks:
            self._check_conflict(self._framework_hooks, hook.name, RegistryLevel.FRAMEWORK)
            self._framework_hooks[hook.name] = hook
            self._hook_types[hook.name] = "post"

        # 存储内置开关
        self._framework_flags = BuiltinFlags(
            enable_content_safety=config.enable_content_safety,
            content_safety_level=config.content_safety_level,
            enable_pii_filter=config.enable_pii_filter,
            pii_types=list(config.pii_types),
            enable_quality_check=config.enable_quality_check,
            min_quality_score=config.min_quality_score,
            max_output_length=config.max_output_length,
        )

        # 存储覆盖配置
        for override in config.overrides:
            self._framework_overrides[override.hook_name] = override

        logger.debug("Registered framework hooks config")

    def register_project_hooks(self, project_id: str, config: HooksConfig) -> None:
        """
        注册项目级 Hooks 配置

        Args:
            project_id: 项目 ID
            config: 项目级 Hooks 配置

        Raises:
            RegistryConflictError: 如果同名自定义 Hook 已在该 Project 级注册
        """
        # 初始化项目级存储
        if project_id not in self._project_hooks:
            self._project_hooks[project_id] = {}

        project_hooks = self._project_hooks[project_id]

        # 注册自定义 pre_hooks
        for hook in config.pre_hooks:
            self._check_conflict(project_hooks, hook.name, RegistryLevel.PROJECT)
            project_hooks[hook.name] = hook
            self._hook_types[hook.name] = "pre"

        # 注册自定义 post_hooks
        for hook in config.post_hooks:
            self._check_conflict(project_hooks, hook.name, RegistryLevel.PROJECT)
            project_hooks[hook.name] = hook
            self._hook_types[hook.name] = "post"

        # 存储内置开关
        self._project_flags[project_id] = BuiltinFlags(
            enable_content_safety=config.enable_content_safety,
            content_safety_level=config.content_safety_level,
            enable_pii_filter=config.enable_pii_filter,
            pii_types=list(config.pii_types),
            enable_quality_check=config.enable_quality_check,
            min_quality_score=config.min_quality_score,
            max_output_length=config.max_output_length,
        )

        # 存储覆盖配置
        if project_id not in self._project_overrides:
            self._project_overrides[project_id] = {}
        for override in config.overrides:
            self._project_overrides[project_id][override.hook_name] = override

        logger.debug("Registered project hooks config: %s", project_id)

    def get_hooks_for_agent(
        self,
        agent_hooks: HooksConfig | None = None,
        project_id: str | None = None,
    ) -> tuple[list[Callable], list[Callable]]:
        """
        获取 Agent 最终的 pre_hooks 和 post_hooks

        执行顺序：
        - pre_hooks: Framework -> Project -> Agent（外到内）
        - post_hooks: Agent -> Project -> Framework（内到外）

        覆盖规则：
        - 同名 Hook 高优先级覆盖低优先级
        - enable_xxx = False 可禁用低层级的内置护栏

        Args:
            agent_hooks: Agent 级 Hooks 配置
            project_id: 项目 ID

        Returns:
            (pre_hooks, post_hooks) 函数列表元组
        """
        pre_hooks: list[Callable] = []
        post_hooks: list[Callable] = []

        # 获取各层级 flags
        framework_flags = self._framework_flags
        project_flags = self._project_flags.get(project_id) if project_id else None

        # 收集所有覆盖配置
        all_overrides: dict[str, HookOverride] = dict(self._framework_overrides)
        if project_id and project_id in self._project_overrides:
            all_overrides.update(self._project_overrides[project_id])
        if agent_hooks:
            for override in agent_hooks.overrides:
                all_overrides[override.hook_name] = override

        # 确定最终的内置护栏状态
        final_content_safety = self._resolve_bool_flag(
            framework_flags.enable_content_safety,
            project_flags.enable_content_safety if project_flags else None,
            agent_hooks.enable_content_safety if agent_hooks else None,
        )

        final_pii_filter = self._resolve_bool_flag(
            framework_flags.enable_pii_filter,
            project_flags.enable_pii_filter if project_flags else None,
            agent_hooks.enable_pii_filter if agent_hooks else None,
        )

        final_quality_check = self._resolve_bool_flag(
            framework_flags.enable_quality_check,
            project_flags.enable_quality_check if project_flags else None,
            agent_hooks.enable_quality_check if agent_hooks else None,
        )

        # 添加内置护栏（Post-Hooks）
        if final_content_safety and "content_safety" not in all_overrides:
            content_safety_hook = self._get_builtin_hook("content_safety")
            if content_safety_hook:
                post_hooks.append(content_safety_hook)

        if final_pii_filter and "pii_filter" not in all_overrides:
            pii_filter_hook = self._get_builtin_hook("pii_filter")
            if pii_filter_hook:
                post_hooks.append(pii_filter_hook)

        if final_quality_check and "quality_check" not in all_overrides:
            quality_hook = self._get_builtin_hook("quality_check")
            if quality_hook:
                post_hooks.append(quality_hook)

        # 收集 Pre-Hooks（Framework -> Project -> Agent）
        pre_hooks.extend(
            self._collect_hooks_by_type(
                "pre",
                project_id,
                agent_hooks.pre_hooks if agent_hooks else [],
                all_overrides,
            )
        )

        # 收集 Post-Hooks（Agent -> Project -> Framework）
        post_hooks.extend(
            self._collect_post_hooks(
                project_id,
                agent_hooks.post_hooks if agent_hooks else [],
                all_overrides,
            )
        )

        return pre_hooks, post_hooks

    def _collect_hooks_by_type(
        self,
        hook_type: str,
        project_id: str | None,
        agent_hooks: list[HookConfig],
        overrides: dict[str, HookOverride],
    ) -> list[Callable]:
        """收集指定类型的 Hooks（Framework -> Project -> Agent 顺序）"""
        result = []

        # Framework 级
        for name, hook in self._framework_hooks.items():
            if self._hook_types.get(name) == hook_type:
                fn = self._apply_hook(hook, overrides)
                if fn:
                    result.append(fn)

        # Project 级
        if project_id and project_id in self._project_hooks:
            for name, hook in self._project_hooks[project_id].items():
                if self._hook_types.get(name) == hook_type:
                    fn = self._apply_hook(hook, overrides)
                    if fn:
                        result.append(fn)

        # Agent 级
        for hook in agent_hooks:
            fn = self._apply_hook(hook, overrides)
            if fn:
                result.append(fn)

        return result

    def _collect_post_hooks(
        self,
        project_id: str | None,
        agent_hooks: list[HookConfig],
        overrides: dict[str, HookOverride],
    ) -> list[Callable]:
        """收集 Post-Hooks（Agent -> Project -> Framework 顺序）"""
        result = []

        # Agent 级
        for hook in agent_hooks:
            fn = self._apply_hook(hook, overrides)
            if fn:
                result.append(fn)

        # Project 级
        if project_id and project_id in self._project_hooks:
            for name, hook in self._project_hooks[project_id].items():
                if self._hook_types.get(name) == "post":
                    fn = self._apply_hook(hook, overrides)
                    if fn:
                        result.append(fn)

        # Framework 级
        for name, hook in self._framework_hooks.items():
            if self._hook_types.get(name) == "post":
                fn = self._apply_hook(hook, overrides)
                if fn:
                    result.append(fn)

        return result

    def _apply_hook(
        self,
        hook: HookConfig,
        overrides: dict[str, HookOverride],
    ) -> Callable | None:
        """应用覆盖配置后返回最终 hook 函数"""
        if not hook.enabled:
            return None

        if hook.name in overrides:
            override = overrides[hook.name]
            if override.mode == "disable":
                return None
            elif override.mode == "replace" and override.replacement:
                return override.replacement
            elif override.mode == "wrap" and override.wrapper:
                return self._create_wrapper(hook.hook_fn, override.wrapper)

        return hook.hook_fn

    def _resolve_bool_flag(
        self,
        framework: bool,
        project: bool | None,
        agent: bool | None,
    ) -> bool:
        """
        解析布尔标志（高优先级覆盖低优先级）

        优先级: Agent > Project > Framework
        """
        if agent is not None:
            return agent
        if project is not None:
            return project
        return framework

    def _create_wrapper(
        self,
        original: Callable,
        wrapper: Callable,
    ) -> Callable:
        """创建包装函数"""

        def wrapped_hook(*args, **kwargs):
            return wrapper(original, *args, **kwargs)

        return wrapped_hook

    def _get_builtin_hook(self, name: str) -> Callable | None:
        """获取内置护栏函数"""
        if name not in self._builtin_hooks:
            try:
                if name == "content_safety":
                    from app.hooks.builtin.content_safety import content_safety_check

                    self._builtin_hooks[name] = content_safety_check
                elif name == "pii_filter":
                    from app.hooks.builtin.pii_filter import pii_filter_check

                    self._builtin_hooks[name] = pii_filter_check
                elif name == "quality_check":
                    from app.hooks.builtin.output_validator import quality_check

                    self._builtin_hooks[name] = quality_check
            except ImportError as e:
                logger.warning("Failed to load builtin hook %s: %s", name, e)
                return None

        return self._builtin_hooks.get(name)

    def list_framework_hooks(self) -> list[str]:
        """列出所有 Framework 级自定义 Hook 名称"""
        return self.list_framework_items()

    def list_project_ids(self) -> list[str]:
        """列出所有已注册的项目 ID"""
        return list(self._project_hooks.keys())

    def get_hook_info(self, hook_name: str) -> HookConfig | None:
        """获取 Hook 配置信息"""
        return self._framework_hooks.get(hook_name)


# 全局单例
_registry: HooksRegistry | None = None


def get_hooks_registry() -> HooksRegistry:
    """获取全局 Hooks 注册表实例"""
    global _registry
    if _registry is None:
        _registry = HooksRegistry()
    return _registry
