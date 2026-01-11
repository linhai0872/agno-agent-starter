# Agno Agent Service 开发规范

## 核心哲学

1. **AgentOS First** - 使用 AgentOS 标准 API，不自己写 FastAPI 路由
2. **Single Agent 优先** - 90% 场景用单 Agent + 工具解决，避免过度使用 Team/Workflow
3. **配置与代码分离** - 模型参数用 ModelConfig 配置，不硬编码

## 关键规则

### 性能
- 禁止在循环中创建 Agent，Agent 实例是重量级对象
- 创建一次，复用多次

### 模型配置
- 使用 `app/models/ModelConfig` 统一接口
- OpenRouter 是主要模型提供商
- 思考模式用 ReasoningConfig，网络搜索用 WebSearchConfig
- 切换模型只需修改 MODEL_CONFIG

### API Key 优先级
1. Agent 级: `ModelConfig(api_key_env="XXX_KEY")`
2. Project 级: `ProjectConfig(api_key_env="XXX_KEY")`
3. Global 级: `OPENROUTER_API_KEY` 环境变量

### 命名规范
- Agent ID 使用 kebab-case: `my-agent`
- Agent ID 决定 API URL: `/agents/{agent_id}/runs`

### 数据库
- 生产环境必须用 PostgresDb
- 开发可用 SqliteDb

### 代码风格
- 禁止在 print/log 中使用 emoji
- 工具函数返回 str，让模型处理
- 新 Agent 必须在 `app/agents/__init__.py` 注册

## 常见错误

- 自己写 FastAPI 路由（应让 AgentOS 自动生成）
- 在环境变量里配置模型参数（应在代码中用 ModelConfig）
- 使用 Team 解决单 Agent 能处理的任务
- 忘记在 `__init__.py` 注册新 Agent

## 快速参考

```python
# Agent 模板
from app.models import ModelConfig, create_model

AGENT_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.1,
    max_tokens=16384,
)

def create_my_agent(db: PostgresDb) -> Agent:
    return Agent(
        id="my-agent",
        model=create_model(AGENT_MODEL_CONFIG),
        db=db,
        instructions=SYSTEM_PROMPT,
        tools=[...],
    )
```

## 注册表使用

工具和 Hooks 使用三层优先级注册表 (`PriorityRegistry`)：

```
优先级（覆盖模式）：
1. Agent 级 - 最高优先级，完全覆盖
2. Project 级 - 中间优先级
3. Framework 级 - 最低优先级，提供默认值
```

### 冲突检测

**同层级**注册同名项目会抛出 `RegistryConflictError`：

```python
from app.tools import get_tool_registry, RegistryConflictError

registry = get_tool_registry()
registry.register_framework_tool(tool_a, name="search")

# 同层级冲突 → 抛出异常
registry.register_framework_tool(tool_b, name="search")
# RegistryConflictError: 'search' already registered at framework level
```

**跨层级**同名是允许的（这是优先级覆盖的设计意图）：

```python
# Framework 级有 "search"
registry.register_framework_tool(framework_search, name="search")

# Agent 级可以覆盖同名
tools = registry.get_tools_for_agent(agent_tools=[agent_search])
# agent_search 覆盖 framework_search
```

### 常见错误

- 在同一层级重复注册同名工具/Hook
- 忘记捕获 `RegistryConflictError`
