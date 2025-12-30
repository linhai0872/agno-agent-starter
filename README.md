<p align="right">
  <a href="README_CN.md">中文</a>
</p>

# Agno Agent Starter

Production-grade AI Agent orchestration framework scaffold based on [Agno](https://github.com/agno-agi/agno) + [AgentOS](https://docs.agno.com/agent-os/overview).

**Docs**: [Agno Docs](https://docs.agno.com) | [AgentOS](https://docs.agno.com/agent-os/overview) | [API Reference](https://docs.agno.com/reference)

## Features

### Following Agno Official Best Practices
- Based on **AgentOS Runtime**, with standardized API auto-generation.
- Persistence for sessions, memory, and knowledge base using **PostgresDb**.
- Structured Output using **Pydantic Schema** + `use_json_mode`.
- Official **MCPTools** protocol integration.

### Clean Architecture
- Modular directory structure separating **Agent/Team/Workflow**.
- Independent READMEs and complete development guides for each module.
- Ready-to-use boilerplate code for rapid development.

### Enterprise Support
- **Multi-provider Model Interface** - Supports 8 providers: OpenRouter/OpenAI/Google/Anthropic/DashScope/Volcengine/Ollama/LiteLLM.
- **Three-tier API Key Management** - Agent level > Project level > Global level for clear billing isolation.
- **Three-tier Tool Registry** - Customizable at Framework/Project/Agent levels for flexible reuse.
- **Built-in Guardrails** - Content safety, PII filtering, and output validation hooks.

### AI-Assisted Development
- Built-in `.cursor/rules/` for **Vibe Coding**.
- Development specifications provided in `AGENTS.md` and `CLAUDE.md`.
- Optimized for AI tools like Cursor and Claude Code.

## Quick Start

```bash
# 1. Clone and Configure
git clone https://github.com/linhai0872/agno-agent-starter.git && cd agno-agent-starter
cp .env.example .env
# Edit .env and fill in OPENROUTER_API_KEY

# 2. Start Service (Dev mode with Hot Reload)
docker compose up -d

# 3. Access
# API Docs: http://localhost:7777/docs
# Health Check: http://localhost:7777/health
```

### Production Deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Connect to Agent UI

Agno provides a beautiful official Web UI to manage and interact with your agents.

1. Open [os.agno.com](https://os.agno.com) and sign in
2. Click **"Add new OS"** in the top navigation
3. Select **"Local"** to connect to your local AgentOS
4. Enter your endpoint URL: `http://localhost:7777`
5. Click **"Connect"**

Once connected, you can:
- Chat with your Agents/Teams/Workflows
- View session history and memory
- Manage knowledge bases
- Monitor metrics and traces

## Development Flow

Philosophy: **Choose Architecture → Create Directory → Use Components → Deploy**

```
Step 1: Choose Orchestration Mode
        Choose Agent / Team / Workflow based on your use case.

            ↓

Step 2: Create Directory
        Create an independent directory under the corresponding module.

            ↓

Step 3: Reuse or Extend Components
        Use built-in Models/Tools/Hooks or develop custom ones.

            ↓

Step 4: Register and Go Live
        Register in __init__.py and serve via AgentOS.
```

**Example: Developing "Customer Research"**
1. Requires collaboration between researcher and writer → Choose **Team** mode.
2. Create `app/teams/customer_research/` directory.
3. Reuse `ModelConfig` from `app/models/`.
4. Register in `app/teams/__init__.py`, and `/teams/customer-research/runs` API is auto-exposed.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AgentOS Runtime                          │
├─────────────────────────────────────────────────────────────────┤
│   Agents          │     Teams           │     Workflows         │
│   Single Agent    │     Multi-Agent     │     Step-based Flow   │
├─────────────────────────────────────────────────────────────────┤
│                      Abstraction Layers                         │
│   Models     │   Tools      │   Hooks      │   Knowledge        │
│   8 Providers │   3-tier Reg │   Guardrails │   RAG Support      │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure                             │
│              PostgreSQL + pgvector + Tracing                    │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
agno-agent-starter/
├── app/
│   ├── main.py              # AgentOS Entrypoint
│   ├── config.py            # Global Config
│   ├── agents/              # Agent Implementations
│   ├── teams/               # Team Implementations
│   ├── workflows/           # Workflow Implementations
│   ├── models/              # Model Configurations
│   ├── tools/               # Tool Registry
│   └── hooks/               # Hooks/Guardrails
├── tests/                   # Unit Tests
├── .cursor/rules/           # Vibe Coding Rules
├── docker-compose.yml       # Dev Environment
├── docker-compose.prod.yml  # Prod Environment
└── .env.example             # Environment Template
```

## Orchestration Modes

| Mode | Use Case | Description |
|------|----------|-------------|
| **Agent** | Single task + Tool call | Recommended for 90% of cases, simple & efficient |
| **Team** | Multi-role collaboration | Automatic coordination among members |
| **Workflow** | Strict steps + Conditionals | Process control and state management |

Detailed development guides:
- [Agents Guide](app/agents/README_EN.md)
- [Teams Guide](app/teams/README_EN.md)
- [Workflows Guide](app/workflows/README_EN.md)
- [Models Guide](app/models/README_EN.md)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API Key |
| `DATABASE_URL` | No | PostgreSQL connection (Default provided by Docker) |
| `DEBUG_MODE` | No | Dev mode with Hot Reload |

Full configuration: [.env.example](.env.example)

## Testing

```bash
pytest tests/ -v
```

## License

MIT
