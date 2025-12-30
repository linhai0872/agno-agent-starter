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
from typing import Callable, Dict, List, Optional, Tuple

from app.hooks.config import HookConfig, HookOverride, HooksConfig

logger = logging.getLogger(__name__)


class HooksRegistry:
    """
    三层 Hooks 注册表
    
    使用示例:
    
    ```python
    registry = get_hooks_registry()
    
    # 注册框架级护栏
    registry.register_framework_hooks(HooksConfig(
        enable_content_safety=True,
    ))
    
    # 注册项目级配置
    registry.register_project_hooks("ecommerce", HooksConfig(
        enable_pii_filter=True,
        post_hooks=[price_validation_hook],
    ))
    
    # 获取 Agent 的最终 Hooks
    pre_hooks, post_hooks = registry.get_hooks_for_agent(
        agent_hooks=HooksConfig(enable_pii_filter=False),
        project_id="ecommerce",
    )
    ```
    """
    
    def __init__(self):
        # 框架级配置
        self._framework_hooks: HooksConfig = HooksConfig()
        
        # 项目级配置
        self._project_hooks: Dict[str, HooksConfig] = {}
        
        # 内置护栏函数（懒加载）
        self._builtin_hooks: Dict[str, Callable] = {}
    
    def register_framework_hooks(self, config: HooksConfig) -> None:
        """
        注册框架级 Hooks 配置
        
        Args:
            config: 框架级 Hooks 配置
        """
        self._framework_hooks = config
        logger.debug("Registered framework hooks config")
    
    def register_project_hooks(self, project_id: str, config: HooksConfig) -> None:
        """
        注册项目级 Hooks 配置
        
        Args:
            project_id: 项目 ID
            config: 项目级 Hooks 配置
        """
        self._project_hooks[project_id] = config
        logger.debug("Registered project hooks config: %s", project_id)
    
    def get_hooks_for_agent(
        self,
        agent_hooks: Optional[HooksConfig] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[List[Callable], List[Callable]]:
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
        pre_hooks: List[Callable] = []
        post_hooks: List[Callable] = []
        
        # 收集所有层级的 Hooks
        framework_config = self._framework_hooks
        project_config = self._project_hooks.get(project_id) if project_id else None
        
        # 收集所有覆盖配置
        all_overrides: Dict[str, HookOverride] = {}
        if project_config:
            for override in project_config.overrides:
                all_overrides[override.hook_name] = override
        if agent_hooks:
            for override in agent_hooks.overrides:
                all_overrides[override.hook_name] = override
        
        # 确定最终的内置护栏状态
        final_content_safety = self._resolve_bool_flag(
            framework_config.enable_content_safety,
            project_config.enable_content_safety if project_config else None,
            agent_hooks.enable_content_safety if agent_hooks else None,
        )
        
        final_pii_filter = self._resolve_bool_flag(
            framework_config.enable_pii_filter,
            project_config.enable_pii_filter if project_config else None,
            agent_hooks.enable_pii_filter if agent_hooks else None,
        )
        
        final_quality_check = self._resolve_bool_flag(
            framework_config.enable_quality_check,
            project_config.enable_quality_check if project_config else None,
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
        
        # 添加自定义 Pre-Hooks（Framework -> Project -> Agent）
        pre_hooks.extend(self._collect_hooks(
            framework_config.pre_hooks,
            project_config.pre_hooks if project_config else [],
            agent_hooks.pre_hooks if agent_hooks else [],
            all_overrides,
        ))
        
        # 添加自定义 Post-Hooks（Agent -> Project -> Framework）
        agent_post = agent_hooks.post_hooks if agent_hooks else []
        project_post = project_config.post_hooks if project_config else []
        framework_post = framework_config.post_hooks
        
        # 反转顺序：Agent -> Project -> Framework
        post_hooks.extend(self._collect_hooks(
            [],  # 先添加自定义 hooks
            [],
            agent_post,
            all_overrides,
        ))
        post_hooks.extend(self._collect_hooks(
            [],
            project_post,
            [],
            all_overrides,
        ))
        post_hooks.extend(self._collect_hooks(
            framework_post,
            [],
            [],
            all_overrides,
        ))
        
        return pre_hooks, post_hooks
    
    def _resolve_bool_flag(
        self,
        framework: bool,
        project: Optional[bool],
        agent: Optional[bool],
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
    
    def _collect_hooks(
        self,
        framework_hooks: List[HookConfig],
        project_hooks: List[HookConfig],
        agent_hooks: List[HookConfig],
        overrides: Dict[str, HookOverride],
    ) -> List[Callable]:
        """收集并合并 Hooks"""
        result = []
        
        all_hooks = framework_hooks + project_hooks + agent_hooks
        
        for hook in all_hooks:
            if not hook.enabled:
                continue
            
            # 检查是否被覆盖
            if hook.name in overrides:
                override = overrides[hook.name]
                if override.mode == "disable":
                    continue
                elif override.mode == "replace" and override.replacement:
                    result.append(override.replacement)
                    continue
                elif override.mode == "wrap" and override.wrapper:
                    # 包装原函数
                    wrapped = self._create_wrapper(hook.hook_fn, override.wrapper)
                    result.append(wrapped)
                    continue
            
            result.append(hook.hook_fn)
        
        return result
    
    def _create_wrapper(
        self,
        original: Callable,
        wrapper: Callable,
    ) -> Callable:
        """创建包装函数"""
        def wrapped_hook(*args, **kwargs):
            return wrapper(original, *args, **kwargs)
        return wrapped_hook
    
    def _get_builtin_hook(self, name: str) -> Optional[Callable]:
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
    
    def list_project_ids(self) -> List[str]:
        """列出所有已注册的项目 ID"""
        return list(self._project_hooks.keys())


# 全局单例
_registry: Optional[HooksRegistry] = None


def get_hooks_registry() -> HooksRegistry:
    """获取全局 Hooks 注册表实例"""
    global _registry
    if _registry is None:
        _registry = HooksRegistry()
    return _registry


