# Hooks 开发指南

三层护栏系统，支持内容安全、PII 过滤、输出验证、工具调用防护。

## 目录结构

```
hooks/
├── __init__.py       # 导出接口
├── config.py         # 配置定义
├── registry.py       # 三层注册表
└── builtin/          # 内置护栏
    ├── content_safety.py    # 内容安全
    ├── pii_filter.py        # PII 过滤
    ├── output_validator.py  # 输出验证
    └── tool_call_guard.py   # 工具调用防护 (防止无限循环)
```

## 内置护栏

### 工具调用防护 (推荐)

防止 Agent 工具调用无限循环，基于 Agno 官方 `RetryAgentRun` + `StopAgentRun` 机制。

```python
from app.hooks.builtin.tool_call_guard import create_tool_call_guard

# 创建防护器
guard = create_tool_call_guard(
    max_calls_per_tool=5,      # 单工具最多调用 5 次 (超过触发 RetryAgentRun)
    max_retries_per_tool=3,    # 单工具最多提醒 3 次 (超过升级为 StopAgentRun)
    max_total_calls=30,        # 总调用上限 (超过触发 StopAgentRun)
)

# 应用到 Agent
agent = Agent(
    tools=[...],
    tool_hooks=[guard],  # 添加为 tool_hook
)
```

预配置实例：

```python
from app.hooks.builtin.tool_call_guard import default_guard, strict_guard, relaxed_guard

# default_guard: 标准配置 (max_calls=5, max_retries=3, max_total=30)
# strict_guard:  严格配置 (max_calls=3, max_retries=2, max_total=15)
# relaxed_guard: 宽松配置 (max_calls=10, max_retries=5, max_total=50)
```

### 内容安全

```python
from app.hooks.builtin.content_safety import content_safety_check

# 检查输出内容安全
content_safety_check(output, level="moderate")  # strict/moderate/permissive
```

### PII 过滤

```python
from app.hooks.builtin.pii_filter import pii_filter_check

# 检测个人信息
pii_filter_check(output, pii_types=["email", "phone", "ssn"])
```

### 输出验证

```python
from app.hooks.builtin.output_validator import quality_check

# 验证输出质量
quality_check(output, min_length=10)
```

## 配置护栏

```python
from app.hooks import HooksConfig

config = HooksConfig(
    enable_content_safety=True,
    content_safety_level="strict",
    enable_pii_filter=True,
    pii_types=["email", "phone"],
)
```

## 自定义 Hook

```python
from app.hooks import HookConfig

def my_validator(output):
    if len(output.content) < 10:
        raise ValueError("Output too short")

hook = HookConfig(
    name="my_validator",
    hook_fn=my_validator,
    hook_type="post",
    on_failure="raise",  # raise/warn/ignore
)
```

## 三层优先级

执行顺序:
- Pre-Hooks: Framework -> Project -> Agent
- Post-Hooks: Agent -> Project -> Framework

覆盖规则:
- 同名 Hook 高优先级覆盖低优先级
- `enable_xxx=False` 可禁用低层级护栏

## Hook 覆盖

```python
from app.hooks import HookOverride

override = HookOverride(
    hook_name="content_safety",
    mode="disable",  # disable/replace/wrap
)
```

## 冲突检测

同层级注册同名 Hook 会抛出 `RegistryConflictError`：

```python
from app.hooks import HooksRegistry, HooksConfig, HookConfig, RegistryConflictError

registry = HooksRegistry()

# 首次注册成功
registry.register_framework_hooks(HooksConfig(
    pre_hooks=[HookConfig(name="my_hook", hook_fn=my_fn, hook_type="pre")]
))

# 再次注册同名 Hook 会抛出异常
try:
    registry.register_framework_hooks(HooksConfig(
        pre_hooks=[HookConfig(name="my_hook", hook_fn=other_fn, hook_type="pre")]
    ))
except RegistryConflictError as e:
    print(f"冲突: {e}")  # 'my_hook' already registered at framework level
```

**注意**: 跨层级同名是允许的（Agent 级覆盖 Project 级覆盖 Framework 级）。
