# Hooks 开发指南

三层护栏系统，支持内容安全、PII 过滤、输出验证、执行防护。

## 目录结构

```
hooks/
├── __init__.py       # 导出接口
├── config.py         # 配置定义
├── registry.py       # 三层注册表
└── builtin/          # 内置护栏
    ├── content_safety.py       # 内容安全
    ├── pii_filter.py           # PII 过滤
    ├── output_validator.py     # 输出验证
    ├── tool_call_guard.py      # 工具调用防护 (tool_hooks)
    ├── llm_invocation_guard.py # LLM 调用防护 (post_hooks)
    └── token_budget_guard.py   # Token 预算防护 (post_hooks)
```

## 内置护栏

### 工具调用防护 (推荐) - V2

防止 Agent 工具调用无限循环，基于 Agno 官方 `RetryAgentRun` + `StopAgentRun` 机制。

**V2 架构亮点**:
- 使用 Agno 原生 `run_context.session_state` 存储计数器
- 天然请求级别隔离，无跨请求状态累积
- 完全兼容 Agno `tool_hooks` 接口

```python
from app.hooks.builtin import create_tool_call_guard

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

**为什么需要 ToolCallGuard？**

Agno 官方的 `tool_call_limit` 只能限制总调用次数，无法:
- 限制单个工具的调用次数（防止对某工具死循环）
- 提供软警告机制（让 LLM 知道应该换工具）
- 分层升级（先警告，多次后强制停止）

**工厂函数**：

```python
from app.hooks.builtin import get_default_tool_guard, get_strict_tool_guard, get_relaxed_tool_guard

# get_default_tool_guard(): 标准配置 (max_calls=5, max_retries=3, max_total=30)
# get_strict_tool_guard():  严格配置 (max_calls=3, max_retries=2, max_total=15)
# get_relaxed_tool_guard(): 宽松配置 (max_calls=10, max_retries=5, max_total=50)
```

### LLM 调用防护 - V2 (post_hooks)

防止 Agent LLM 调用无限循环，基于 Agno `post_hooks` 机制。

**V2 架构亮点**:
- 使用 Agno 原生 `run_context.session_state` 存储计数器
- 天然请求级别隔离，无跨请求状态累积
- 完全兼容 Agno `post_hooks` 接口

```python
from app.hooks.builtin.llm_invocation_guard import create_llm_invocation_guard

# 创建防护器
guard = create_llm_invocation_guard(
    max_invocations=50,   # LLM 最大调用次数
    warn_threshold=0.8,   # 警告阈值 (80%时开始警告)
)

# 应用到 Agent
agent = Agent(
    model=model,
    post_hooks=[guard],  # 添加为 post_hook
)
```

**工厂函数**：

```python
from app.hooks.builtin import get_default_llm_guard, get_strict_llm_guard, get_relaxed_llm_guard

# get_default_llm_guard(): 标准配置 (max=50, warn=0.8)
# get_strict_llm_guard():  严格配置 (max=20, warn=0.7)
# get_relaxed_llm_guard(): 宽松配置 (max=100, warn=0.9)
```

### Token 预算防护 - V2 (post_hooks)

防止 Agent Token 使用超出预算，基于 Agno `post_hooks` 机制。

**V2 架构亮点**:
- 使用 Agno 原生 `run_context.session_state` 存储累计 Token
- 天然请求级别隔离，无跨请求状态累积
- 自动从 `run_output` 提取 token 使用量

```python
from app.hooks.builtin.token_budget_guard import create_token_budget_guard

# 创建防护器
guard = create_token_budget_guard(
    max_tokens=100000,    # Token 预算上限
    warn_threshold=0.8,   # 警告阈值 (80%时开始警告)
)

# 应用到 Agent
agent = Agent(
    model=model,
    post_hooks=[guard],  # 添加为 post_hook
)
```

**工厂函数**：

```python
from app.hooks.builtin import get_default_token_guard, get_strict_token_guard, get_relaxed_token_guard

# get_default_token_guard(): 标准配置 (max=100000, warn=0.8)
# get_strict_token_guard():  严格配置 (max=30000, warn=0.7)
# get_relaxed_token_guard(): 宽松配置 (max=500000, warn=0.9)
```

### 执行防护组合使用

推荐在复杂 Agent 中同时使用多种防护：

```python
from app.hooks.builtin import (
    create_tool_call_guard,
    create_llm_invocation_guard,
    create_token_budget_guard,
)

agent = Agent(
    model=model,
    tools=[...],
    # 工具调用防护 (tool_hooks)
    tool_hooks=[
        create_tool_call_guard(max_calls_per_tool=5, max_total_calls=30),
    ],
    # LLM 调用 + Token 预算防护 (post_hooks)
    post_hooks=[
        create_llm_invocation_guard(max_invocations=50),
        create_token_budget_guard(max_tokens=100000),
    ],
)
```

**三层防护体系：**
1. **ToolCallGuard** - 防止单工具死循环
2. **LLMInvocationGuard** - 防止 LLM 无限推理
3. **TokenBudgetGuard** - 控制成本上限

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
