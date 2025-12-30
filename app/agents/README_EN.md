<p align="right">
  <a href="README.md">中文</a>
</p>

# Agent Development Guide

Agents are the most basic units, suitable for single tasks + tool call scenarios.

## Directory Structure

```
agents/
├── __init__.py              # Registration entrypoint
├── {agent_name}/
│   ├── __init__.py
│   ├── agent.py             # Agent definition + ModelConfig
│   ├── prompts.py           # System Prompt
│   ├── schemas.py           # Pydantic Schema (Optional)
│   └── tools.py             # Tool functions (Optional)
```

## Quick Start

```bash
mkdir -p app/agents/my_agent
touch app/agents/my_agent/{__init__,agent,prompts}.py
```

## Agent Template

```python
# agent.py
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from app.models import ModelConfig, create_model
from .prompts import SYSTEM_PROMPT

AGENT_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
    max_tokens=8192,
)

def create_my_agent(db: PostgresDb) -> Agent:
    return Agent(
        id="my-agent",
        name="My Agent",
        model=create_model(AGENT_MODEL_CONFIG),
        db=db,
        instructions=SYSTEM_PROMPT,
        tools=[...],
        markdown=True,
    )
```

```python
# prompts.py
SYSTEM_PROMPT = """You are a professional assistant.

## Task
Complete the task based on user input.

## Output Format
Answer concisely and accurately.
"""
```

## Structured Output

```python
from pydantic import BaseModel, Field

class MyOutput(BaseModel):
    result: str = Field(..., description="The result")
    confidence: float = Field(..., ge=0, le=1)

agent = Agent(
    output_schema=MyOutput,
    use_json_mode=True,
)
```

## Registration

```python
# app/agents/__init__.py
from app.agents.my_agent.agent import create_my_agent
agents.append(create_my_agent(db))
```

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| id        | Agent ID, kebab-case, determines API URL |
| model     | Model instance, use create_model() |
| db        | PostgresDb connection |
| instructions | System Prompt |
| tools     | List of tool functions |
| output_schema | Pydantic Model (Optional) |
| use_json_mode | Enable JSON mode (with output_schema) |

## API

After registration, the following APIs are auto-generated:
- `POST /agents/{agent_id}/runs` - Run Agent
- API Docs: `http://localhost:7777/docs`

