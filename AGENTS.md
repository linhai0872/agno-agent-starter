# Agno Agent Service 开发规范

_AI 工具主规范文档。所有 AI 辅助开发工具（Cursor、Claude Code 等）应参考本文档。_

---

## 核心哲学

1. **AgentOS First** — 使用 AgentOS 标准 API，不手写 FastAPI 路由
2. **Single Agent 优先** — 90% 场景用单 Agent + 工具解决，避免过度使用 Team/Workflow
3. **配置与代码分离** — 模型参数用 `ModelConfig` 配置，不硬编码

---

## 项目结构概览

```
agno-agent-starter/
├── app/                     # 应用代码（User Code 区域）
│   ├── main.py              # AgentOS 入口（脚手架核心，慎改）
│   ├── config.py            # 三层配置加载器（脚手架核心）
│   ├── agents/              # ✏️ Agent 实现（用户扩展区）
│   ├── teams/               # ✏️ Team 实现（用户扩展区）
│   ├── workflows/           # ✏️ Workflow 实现（用户扩展区）
│   ├── models/              # 模型抽象层（脚手架提供）
│   ├── tools/               # 三层工具注册表
│   │   ├── framework/       # 框架级工具（脚手架提供）
│   │   ├── project/         # ✏️ 项目级工具（用户扩展区）
│   │   └── user/            # Agent 专用工具
│   ├── hooks/               # 护栏与生命周期钩子
│   └── mcp/                 # MCP Server（AI Agent 开发工具）
├── api/                     # OpenAPI 规格（自动生成）
├── tests/                   # 单元测试（镜像 app/ 结构）
├── scripts/                 # 脚本工具（含 agno CLI）
└── .cursor/rules/           # Vibe Coding 规则
```

**User Code vs Scaffold Core:**
- ✏️ 标记 = 用户扩展区，自由修改
- 无标记 = 脚手架核心，谨慎修改

---

## 开发规范

### 命名规则

| 元素      | 规则               | 示例                 |
| --------- | ------------------ | -------------------- |
| Agent ID  | `kebab-case`       | `github-analyzer`    |
| 文件名    | `snake_case.py`    | `github_analyzer.py` |
| 类名      | `PascalCase`       | `GitHubAnalyzer`     |
| 函数/变量 | `snake_case`       | `analyze_repo`       |
| 常量      | `UPPER_SNAKE_CASE` | `MAX_RETRIES`        |

### 性能要求

- **禁止**在循环中创建 Agent，Agent 实例是重量级对象
- 创建一次，复用多次
- 异步操作使用 `async def`

### 代码风格

- **禁止**在 print/log 中使用 emoji
- 工具函数返回 `str`，让模型处理
- 每个模块必须在 `__init__.py` 注册

---

## 模型配置

### 基础用法

```python
from app.models import ModelConfig, create_model

AGENT_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.1,
    max_tokens=16384,
)

model = create_model(AGENT_MODEL_CONFIG)
```

### API Key 优先级

```
优先级（高 → 低）：
1. Agent 级: ModelConfig(api_key_env="MY_AGENT_KEY")
2. Project 级: ProjectConfig(api_key_env="MY_PROJECT_KEY")
3. Global 级: OPENROUTER_API_KEY 环境变量
```

### 高级配置

```python
from app.models import ReasoningConfig, WebSearchConfig

# 启用思考模式
config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    reasoning=ReasoningConfig(enabled=True, effort="medium"),
)

# 启用网络搜索
config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    web_search=WebSearchConfig(enabled=True),
)
```

---

## 常见任务

### 创建新 Agent

1. **创建目录**
   ```bash
   mkdir -p app/agents/my_agent
   ```

2. **实现 Agent**
   ```python
   # app/agents/my_agent/agent.py
   from agno.agent import Agent
   from agno.db.postgres import PostgresDb
   from app.models import ModelConfig, create_model

   AGENT_MODEL_CONFIG = ModelConfig(
       model_id="google/gemini-2.5-flash-preview-09-2025",
       temperature=0.2,
       max_tokens=8192,
   )

   SYSTEM_PROMPT = """你是一个专业的助手..."""

   def create_my_agent(db: PostgresDb) -> Agent:
       return Agent(
           id="my-agent",              # kebab-case
           name="My Agent",
           model=create_model(AGENT_MODEL_CONFIG),
           db=db,
           instructions=SYSTEM_PROMPT,
           tools=[],
           markdown=True,
       )
   ```

3. **注册**
   ```python
   # app/agents/__init__.py
   from app.agents.my_agent.agent import create_my_agent
   agents.append(create_my_agent(db))
   ```

4. **API 自动暴露**: `POST /agents/my-agent/runs`

### 创建新 Team

1. **创建目录**: `mkdir -p app/teams/my_team`

2. **实现 Team**
   ```python
   # app/teams/my_team/team.py
   from agno.team import Team
   from agno.db.postgres import PostgresDb

   def create_my_team(db: PostgresDb) -> Team:
       return Team(
           id="my-team",
           name="My Team",
           members=[agent_a, agent_b],
           db=db,
       )
   ```

3. **注册**: 在 `app/teams/__init__.py` 添加

### 创建新 Workflow

1. **创建目录**: `mkdir -p app/workflows/my_workflow`

2. **实现 Workflow**
   ```python
   # app/workflows/my_workflow/workflow.py
   from agno.workflow import Workflow

   class MyWorkflow(Workflow):
       def run(self, message: str) -> str:
           # 实现步骤逻辑
           return f"Processed: {message}"
   ```

3. **注册**: 在 `app/workflows/__init__.py` 添加

---

## 注册表使用

工具和 Hooks 使用三层优先级注册表 (`PriorityRegistry`)：

```
优先级（覆盖模式）：
1. Agent 级 — 最高优先级，完全覆盖
2. Project 级 — 中间优先级
3. Framework 级 — 最低优先级，提供默认值
```

### 注册工具

```python
from app.tools import get_tool_registry

registry = get_tool_registry()

# Framework 级（脚手架提供）
registry.register_framework_tool(search_tool, name="search")

# Project 级（项目通用）
registry.register_project_tool(my_tool, name="my_tool")

# Agent 级（覆盖同名工具）
tools = registry.get_tools_for_agent(agent_tools=[custom_search])
```

### 冲突检测

**同层级**注册同名项目会抛出 `RegistryConflictError`：

```python
registry.register_framework_tool(tool_a, name="search")
registry.register_framework_tool(tool_b, name="search")
# → RegistryConflictError: 'search' already registered at framework level
```

**跨层级**同名是允许的（这是优先级覆盖的设计意图）。

---

## API 规格

- **交互式文档**: http://localhost:7777/docs
- **OpenAPI 规格**: [api/openapi.json](api/openapi.json)

### API 调用规范

- **先查后做**: 调用 API 前先查 `/openapi.json` 确认端点和参数格式
- **Content-Type**: AgentOS 使用 `application/x-www-form-urlencoded`，不是 JSON
- **导出规格**: `python scripts/export_openapi.py`

---

## 常见错误

| 错误                              | 正确做法                                       |
| --------------------------------- | ---------------------------------------------- |
| 手写 FastAPI 路由                 | 让 AgentOS 自动生成                            |
| 环境变量配置模型参数              | 代码中用 `ModelConfig`                         |
| 用 Team 解决单 Agent 能处理的任务 | 优先 Single Agent                              |
| 忘记在 `__init__.py` 注册         | 每次新建都要注册                               |
| 循环中创建 Agent                  | 创建一次，复用多次                             |
| 同层级重复注册工具                | 检查是否已存在，或捕获 `RegistryConflictError` |

---

## 相关文档

- [Agents 开发指南](app/agents/README.md)
- [Teams 开发指南](app/teams/README.md)
- [Workflows 开发指南](app/workflows/README.md)
- [Models 配置指南](app/models/README.md)
- [Agno CLI](scripts/AGNO_CLI.md) - 终端测试与调试工具
- [MCP DevTools](app/mcp/devtools/README.md) - AI Agent 测试工具
- [API 规格](api/README_CN.md)
