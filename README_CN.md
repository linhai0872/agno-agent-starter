<p align="right">
  <a href="README.md">English</a>
</p>

<div align="center">

# Agno Agent Starter

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Agno](https://img.shields.io/badge/Built%20with-Agno-orange.svg)](https://github.com/agno-agi/agno)

**生产级 AI Agent 脚手架，开箱即用**

*分钟级构建、部署、扩展智能体，而非数周。*

[📖 文档](https://docs.agno.com) · [🍳 Cookbook](https://docs.agno.com/cookbook) · [💬 Discord](https://discord.gg/agno) · [🐛 Issues](https://github.com/linhai0872/agno-agent-starter/issues)

</div>

---

## 为什么选择 Agno Agent Starter？

- 🚀 **3 步上生产** — Clone、配置、`docker compose up`
- 🔌 **统一模型层** — 一个 `ModelConfig` 通吃所有厂商，一行代码切换
- 🛡️ **企业就绪** — 三层 API Key 管理、内置护栏、完整追踪
- 🤖 **AI 编程优化** — Cursor rules、AGENTS.md、Claude Code 就绪

---

## 快速启动

### 方式 A: npx (推荐)

```bash
# 创建新项目
npx create-agno-agent my-agent
cd my-agent

# 配置并启动
cp .env.example .env  # 添加 OPENROUTER_API_KEY
docker compose up -d

# 完成！打开 http://localhost:7777/docs
```

### 方式 B: Git Clone

```bash
git clone https://github.com/linhai0872/agno-agent-starter.git && cd agno-agent-starter
cp .env.example .env
docker compose up -d
```

### 试一试

```python
from app.agents.github_analyzer import create_github_analyzer_agent
from agno.db.postgres import PostgresDb

db = PostgresDb(db_url="postgresql://...")
agent = create_github_analyzer_agent(db)
response = agent.run("分析 https://github.com/agno-agi/agno")
# 返回: GitHubRepoAnalysis (结构化输出)
```

### 生产部署

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 连接 Agent UI

1. 打开 [os.agno.com](https://os.agno.com) → 登录
2. 点击 **"Add new OS"** → 选择 **"Local"**
3. 输入: `http://localhost:7777` → **Connect**

---

## 核心哲学

1. **AgentOS First** — 使用 AgentOS 标准 API，不手写 FastAPI 路由
2. **Single Agent 优先** — 90% 场景用单 Agent + 工具解决
3. **配置与代码分离** — 模型参数用 `ModelConfig`，不硬编码

---

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        AgentOS Runtime                          │
├─────────────────────────────────────────────────────────────────┤
│   Agents          │     Teams           │     Workflows         │
│   单 Agent 任务    │     多 Agent 协作    │     步骤流程控制       │
├─────────────────────────────────────────────────────────────────┤
│                      Core Abstractions                          │
│   Models     │   Tools      │   Hooks      │   Registry         │
│   统一接口    │   三层注册表  │   护栏系统    │   PriorityRegistry │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure                             │
│              PostgreSQL + pgvector + Tracing                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 经典模板

| 模板                 | 类型     | 说明              | 关键特性                      |
| -------------------- | -------- | ----------------- | ----------------------------- |
| **GitHub Analyzer**  | Agent    | 分析 GitHub 仓库  | Structured Output, DuckDuckGo |
| **Deep Research**    | Team     | 多 Agent 协作研究 | session_state, ToolCallGuard  |
| **Customer Service** | Workflow | 智能客服 + RAG    | 条件路由, pgvector            |

**开发指南:**
[Agents](app/agents/README.md) · [Teams](app/teams/README.md) · [Workflows](app/workflows/README.md) · [Models](app/models/README.md)

---

## 项目结构

```
agno-agent-starter/
├── app/
│   ├── main.py              # AgentOS 入口
│   ├── config.py            # 三层配置加载器
│   ├── agents/              # ✏️ Agent 实现
│   ├── teams/               # ✏️ Team 实现
│   ├── workflows/           # ✏️ Workflow 实现
│   ├── models/              # 模型抽象层 (8 厂商)
│   ├── tools/               # 三层工具注册表
│   ├── hooks/               # 护栏与生命周期钩子
│   └── core/                # 注册表抽象层
├── api/                     # OpenAPI 规格 (自动生成)
├── tests/                   # 单元测试
└── .cursor/rules/           # Vibe Coding 规则
```

*✏️ = 用户扩展点*

---

## 三种编排模式

| 模式         | 适用场景        | 说明               |
| ------------ | --------------- | ------------------ |
| **Agent**    | 单任务 + 工具   | 90% 推荐，简单高效 |
| **Team**     | 多角色协作      | 成员间自动协调     |
| **Workflow** | 严格步骤 + 条件 | 流程可控           |

---

## 环境变量

| 变量                 | 必需 | 说明                         |
| -------------------- | ---- | ---------------------------- |
| `OPENROUTER_API_KEY` | 是   | OpenRouter API Key           |
| `DATABASE_URL`       | 否   | PostgreSQL (Docker 默认提供) |
| `DEBUG_MODE`         | 否   | 开发热重载                   |

完整配置: [.env.example](.env.example)

---

## API 参考

- **交互式文档**: http://localhost:7777/docs
- **OpenAPI 规格**: [api/openapi.json](api/openapi.json)

```bash
# 导出最新规格
python scripts/export_openapi.py
```

---

## 贡献

欢迎提交 Issues 和 PRs！请先阅读 [AGENTS.md](AGENTS.md) 了解开发规范。

---

## License

[MIT](LICENSE)
