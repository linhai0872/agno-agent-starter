"""
Hooks 配置数据类

定义 Hooks/Guardrails 的配置和覆盖相关的数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Literal, Optional


@dataclass
class HookConfig:
    """
    单个 Hook 配置
    
    用于配置输入验证、输出验证、安全检查等护栏功能。
    
    使用示例:
    
    ```python
    hook = HookConfig(
        name="content_safety",
        hook_fn=content_safety_check,
        hook_type="post",
        level="framework",
        on_failure="raise",
    )
    ```
    """
    
    # Hook 名称
    name: str
    
    # Hook 函数
    # Pre-Hook: (input: str) -> str  或  (input: str) -> None
    # Post-Hook: (output: RunOutput) -> None  或  (output: RunOutput) -> RunOutput
    hook_fn: Callable
    
    # Hook 类型: pre (输入验证) / post (输出验证)
    hook_type: Literal["pre", "post"] = "post"
    
    # 优先级层: framework / project / agent
    level: Literal["framework", "project", "agent"] = "agent"
    
    # 是否启用
    enabled: bool = True
    
    # 失败时行为
    # - raise: 抛出异常，终止执行
    # - warn: 记录警告，继续执行
    # - ignore: 静默忽略
    on_failure: Literal["raise", "warn", "ignore"] = "raise"
    
    # 描述信息
    description: str = ""


@dataclass
class HookOverride:
    """
    Hook 覆盖配置 - 类似 ToolOverride
    
    用于在项目级或 Agent 级覆盖框架级 Hook。
    
    使用示例:
    
    ```python
    # 禁用框架级护栏
    override = HookOverride(
        hook_name="content_safety",
        mode="disable",
    )
    
    # 替换为自定义实现
    override = HookOverride(
        hook_name="pii_filter",
        mode="replace",
        replacement=my_pii_filter,
    )
    ```
    """
    
    # 目标 Hook 名称
    hook_name: str
    
    # 覆盖模式
    # - disable: 禁用此 Hook
    # - replace: 完全替换实现
    # - wrap: 包装原 Hook
    mode: Literal["disable", "replace", "wrap"] = "disable"
    
    # 替换函数（replace 模式）
    replacement: Optional[Callable] = None
    
    # 包装函数（wrap 模式）
    wrapper: Optional[Callable] = None


@dataclass
class HooksConfig:
    """
    Hooks 配置集合 - 支持三层覆盖
    
    使用示例:
    
    ```python
    # 项目级配置
    config = HooksConfig(
        enable_content_safety=True,
        content_safety_level="strict",
        enable_pii_filter=True,
        post_hooks=[
            HookConfig(
                name="price_validation",
                hook_fn=validate_price,
                level="project",
            ),
        ],
    )
    
    # Agent 级覆盖
    agent_hooks = HooksConfig(
        enable_pii_filter=False,  # 禁用项目级 PII 过滤
    )
    ```
    """
    
    # ============== 自定义 Hooks ==============
    
    # 前置钩子（输入验证，按 Framework -> Project -> Agent 顺序执行）
    pre_hooks: List[HookConfig] = field(default_factory=list)
    
    # 后置钩子（输出验证，按 Agent -> Project -> Framework 顺序执行）
    post_hooks: List[HookConfig] = field(default_factory=list)
    
    # Hook 覆盖配置
    overrides: List[HookOverride] = field(default_factory=list)
    
    # ============== 内置护栏开关 ==============
    
    # 内容安全检查
    enable_content_safety: bool = False
    content_safety_level: Literal["strict", "moderate", "permissive"] = "moderate"
    
    # PII 过滤
    enable_pii_filter: bool = False
    pii_types: List[str] = field(
        default_factory=lambda: ["email", "phone", "ssn", "credit_card"]
    )
    
    # 输出长度限制
    max_output_length: Optional[int] = None
    
    # 输出质量检查
    enable_quality_check: bool = False
    min_quality_score: float = 0.6
    
    def to_agent_params(self) -> dict:
        """转换为 Agno Agent 参数"""
        params = {}
        
        # 收集所有 post_hooks
        all_post_hooks = []
        
        for hook in self.post_hooks:
            if hook.enabled:
                all_post_hooks.append(hook.hook_fn)
        
        if all_post_hooks:
            params["output_checks"] = all_post_hooks
        
        return params


