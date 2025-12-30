# Hooks 开发指南

三层护栏系统，支持内容安全、PII 过滤、输出验证。

## 目录结构

```
hooks/
├── __init__.py       # 导出接口
├── config.py         # 配置定义
├── registry.py       # 三层注册表
└── builtin/          # 内置护栏
    ├── content_safety.py
    ├── pii_filter.py
    └── output_validator.py
```

## 内置护栏

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

