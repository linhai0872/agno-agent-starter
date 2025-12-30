<p align="right">
  <a href="README.md">English</a>
</p>

# Agno Agent Starter

基于 [Agno](https://github.com/agno-agi/agno) + [AgentOS](https://docs.agno.com/agent-os/overview) 的生产级 AI Agent 编排框架脚手架。

**文档**: [Agno Docs](https://docs.agno.com) | [AgentOS](https://docs.agno.com/agent-os/overview) | [API Reference](https://docs.agno.com/reference)

## 特性

### 遵循 Agno 官方最佳实践
- 基于 **AgentOS Runtime**，标准化 API 自动生成
- 使用 **PostgresDb** 实现会话、记忆、知识库持久化
- Structured Output 采用 **Pydantic Schema** + `use_json_mode`
- **MCPTools** 官方协议集成

### 清晰的项目架构
- 模块化目录结构，**Agent/Team/Workflow** 分离
- 各模块独立 README，开发指南完整
- 示例代码开箱即用，复制即可开发

### 企业级功能支持
- **多厂商模型统一接口** - 支持 OpenRouter/OpenAI/Google/Anthropic/DashScope/Volcengine/Ollama/LiteLLM 8 大厂商
- **三层 API Key 管理** - Agent 级 > Project 级 > Global 级，计费隔离清晰
- **三层工具注册表** - Framework/Project/Agent 级别定制，灵活复用
- **内置安全护栏** - 内容安全检测、PII 过滤、输出验证 Hooks

### AI 辅助开发支持
- 内置 `.cursor/rules/` **Vibe Coding** 规则
- 提供 `AGENTS.md` 和 `CLAUDE.md` 开发规范
- 适配 Cursor、Claude Code 等 AI 编程工具

## Quick Start

```bash
# 1. 克隆并配置
git clone https://github.com/linhai0872/agno-agent-starter.git && cd agno-agent-starter
cp .env.example .env
# 编辑 .env 填入 OPENROUTER_API_KEY

# 2. 启动服务（开发模式，支持热重载）
docker compose up -d

# 3. 访问
# API 文档: http://localhost:7777/docs
# 健康检查: http://localhost:7777/health
```

### 生产部署

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 连接 Agent UI

Agno 官方提供了精美的 Web UI 来管理和使用你的 Agent。

1. 打开 [os.agno.com](https://os.agno.com) 并登录
2. 点击顶部导航栏的 **"Add new OS"**
3. 选择 **"Local"** 连接本地 AgentOS
4. 输入端点地址: `http://localhost:7777`
5. 点击 **"Connect"**

连接成功后，你可以：
- 与 Agents/Teams/Workflows 对话
- 查看会话历史和记忆
- 管理知识库
- 监控指标和追踪

## 开发流程

设计思想：**选架构 → 建目录 → 用组件 → 上生产**

```
Step 1: 选择编排模式
        根据业务场景选择 Agent / Team / Workflow

            ↓

Step 2: 创建业务目录
        在对应模块下创建独立目录，一个目录对应一个业务

            ↓

Step 3: 复用或扩展组件
        使用框架内置的 Models/Tools/Hooks，或针对业务额外开发

            ↓

Step 4: 注册并上线
        在 __init__.py 注册，通过 AgentOS 提供 API 服务
```

**示例：开发一个「客户研究」业务**
1. 需要研究员和写手协作 → 选择 **Team** 模式
2. 创建 `app/teams/customer_research/` 目录
3. 复用 `app/models/` 的 ModelConfig，按需添加自定义工具
4. 在 `app/teams/__init__.py` 注册，服务自动暴露 `/teams/customer-research/runs` API

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        AgentOS Runtime                          │
├─────────────────────────────────────────────────────────────────┤
│   Agents          │     Teams           │     Workflows         │
│   单 Agent 任务    │     多 Agent 协作    │     步骤流程控制       │
├─────────────────────────────────────────────────────────────────┤
│                      Abstraction Layers                         │
│   Models     │   Tools      │   Hooks      │   Knowledge        │
│   8 厂商统一  │   三层注册表  │   护栏系统    │   RAG 支持          │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure                             │
│              PostgreSQL + pgvector + Tracing                    │
└─────────────────────────────────────────────────────────────────┘
```

## 项目结构

```
agno-agent-starter/
├── app/
│   ├── main.py              # AgentOS 入口
│   ├── config.py            # 全局配置
│   ├── agents/              # Agent 实现
│   ├── teams/               # Team 实现
│   ├── workflows/           # Workflow 实现
│   ├── models/              # 模型配置
│   ├── tools/               # 工具注册表
│   └── hooks/               # Hooks/Guardrails
├── tests/                   # 单元测试
├── .cursor/rules/           # Vibe Coding Rules
├── docker-compose.yml       # 开发环境
├── docker-compose.prod.yml  # 生产环境
└── .env.example             # 环境变量模板
```

## 三种编排模式

| 模式 | 适用场景 | 说明 |
|------|----------|------|
| **Agent** | 单一任务 + 工具调用 | 90% 场景推荐，简单高效 |
| **Team** | 多角色协作 | 成员间自动协调 |
| **Workflow** | 严格步骤 + 条件分支 | 流程可控 |

详细开发指南:
- [Agents 开发指南](app/agents/README.md)
- [Teams 开发指南](app/teams/README.md)
- [Workflows 开发指南](app/workflows/README.md)
- [Models 配置指南](app/models/README.md)

## 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `OPENROUTER_API_KEY` | 是 | OpenRouter API Key |
| `DATABASE_URL` | 否 | PostgreSQL 连接（默认 Docker 提供） |
| `DEBUG_MODE` | 否 | 开发模式，启用热重载 |

完整配置见: [.env.example](.env.example)

## 测试

```bash
pytest tests/ -v
```

## License

MIT

