<p align="right">
  <a href="README_CN.md">中文</a>
</p>

<div align="center">

# Agno Agent Starter

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Agno](https://img.shields.io/badge/Built%20with-Agno-orange.svg)](https://github.com/agno-agi/agno)

**Production-grade AI Agent scaffold with batteries included**

*Build, deploy, and scale intelligent agents in minutes, not weeks.*

[📖 Docs](https://docs.agno.com) · [🍳 Cookbook](https://docs.agno.com/cookbook) · [💬 Discord](https://discord.gg/agno) · [🐛 Issues](https://github.com/linhai0872/agno-agent-starter/issues)

</div>

---

## Why Agno Agent Starter?

- 🚀 **Zero to Production in 3 Steps** — Clone, configure, `docker compose up`
- 🔌 **Unified Model Layer** — One `ModelConfig` for all providers, switch with one line
- 🛡️ **Enterprise-Ready** — 3-tier API key management, built-in guardrails, full tracing
- 🤖 **AI-Optimized** — Cursor rules, AGENTS.md, Claude Code ready

---

## Quick Start

### Option A: npx (Recommended)

```bash
# Create a new project
npx create-agno-agent my-agent
cd my-agent

# Configure & Start
cp .env.example .env  # Add OPENROUTER_API_KEY
docker compose up -d

# Done! Open http://localhost:7777/docs
```

### Option B: Git Clone

```bash
git clone https://github.com/linhai0872/agno-agent-starter.git && cd agno-agent-starter
cp .env.example .env
docker compose up -d
```

### Try It

```python
from app.agents.github_analyzer import create_github_analyzer_agent
from agno.db.postgres import PostgresDb

db = PostgresDb(db_url="postgresql://...")
agent = create_github_analyzer_agent(db)
response = agent.run("Analyze https://github.com/agno-agi/agno")
# Returns: GitHubRepoAnalysis (structured output)
```

### Production Deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Connect to Agent UI

1. Open [os.agno.com](https://os.agno.com) → Sign in
2. Click **"Add new OS"** → Select **"Local"**
3. Enter: `http://localhost:7777` → **Connect**

---

## Core Philosophy

1. **AgentOS First** — Use AgentOS standard APIs, never write FastAPI routes manually
2. **Single Agent Preferred** — 90% of cases can be solved with one Agent + Tools
3. **Config over Code** — Model parameters use `ModelConfig`, no hardcoding

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AgentOS Runtime                          │
├─────────────────────────────────────────────────────────────────┤
│   Agents          │     Teams           │     Workflows         │
│   Single task     │     Multi-agent     │     Step-based flow   │
├─────────────────────────────────────────────────────────────────┤
│                      Core Abstractions                          │
│   Models     │   Tools      │   Hooks      │   Registry         │
│   Unified    │   3-tier Reg │   Guardrails │   PriorityRegistry │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure                             │
│              PostgreSQL + pgvector + Tracing                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Classic Templates

| Template             | Type     | Description            | Key Features                  |
| -------------------- | -------- | ---------------------- | ----------------------------- |
| **GitHub Analyzer**  | Agent    | Analyze GitHub repos   | Structured Output, DuckDuckGo |
| **Deep Research**    | Team     | Multi-agent research   | session_state, ToolCallGuard  |
| **Customer Service** | Workflow | Smart support with RAG | Condition routing, pgvector   |

**Guides:**
[Agents](app/agents/README_EN.md) · [Teams](app/teams/README_EN.md) · [Workflows](app/workflows/README_EN.md) · [Models](app/models/README_EN.md)

---

## Project Structure

```
agno-agent-starter/
├── app/
│   ├── main.py              # AgentOS entrypoint
│   ├── config.py            # 3-tier config loader
│   ├── agents/              # ✏️ Agent implementations
│   ├── teams/               # ✏️ Team implementations
│   ├── workflows/           # ✏️ Workflow implementations
│   ├── models/              # Model abstraction (8 providers)
│   ├── tools/               # 3-tier tool registry
│   ├── hooks/               # Guardrails & lifecycle hooks
│   └── core/                # Registry abstractions
├── api/                     # OpenAPI spec (auto-generated)
├── tests/                   # Unit tests
└── .cursor/rules/           # Vibe Coding rules
```

*✏️ = User extension points*

---

## Orchestration Modes

| Mode         | Use Case                  | Description                         |
| ------------ | ------------------------- | ----------------------------------- |
| **Agent**    | Single task + Tools       | 90% recommended, simple & efficient |
| **Team**     | Multi-role collaboration  | Auto-coordination between members   |
| **Workflow** | Strict steps + Conditions | Process control & state management  |

---

## Environment Variables

| Variable             | Required | Description                      |
| -------------------- | -------- | -------------------------------- |
| `OPENROUTER_API_KEY` | Yes      | OpenRouter API Key               |
| `DATABASE_URL`       | No       | PostgreSQL (default from Docker) |
| `DEBUG_MODE`         | No       | Hot reload for dev               |

Full config: [.env.example](.env.example)

---

## API Reference

- **Interactive Docs**: http://localhost:7777/docs
- **OpenAPI Spec**: [api/openapi.json](api/openapi.json)

```bash
# Export latest spec
python scripts/export_openapi.py
```

---

## Contributing

Issues and PRs are welcome! Please read [AGENTS.md](AGENTS.md) for development guidelines.

---

## License

[MIT](LICENSE)
