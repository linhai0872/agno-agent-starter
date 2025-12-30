<p align="right">
  <a href="README_EN.md">English</a>
</p>

# Agent 开发指南

Agent 是最基础的智能体单元，适用于单一任务 + 工具调用场景。

## 目录结构

```
agents/
├── __init__.py              # 注册入口
├── {agent_name}/
│   ├── __init__.py
│   ├── agent.py             # Agent 定义 + ModelConfig
│   ├── prompts.py           # System Prompt
│   ├── schemas.py           # Pydantic Schema（可选）
│   └── tools.py             # 工具函数（可选）
```

## 快速创建

```bash
mkdir -p app/agents/my_agent
touch app/agents/my_agent/{__init__,agent,prompts}.py
```

## Agent 模板

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
SYSTEM_PROMPT = """你是一个专业助手。

## 任务
根据用户输入完成任务。

## 输出格式
简洁准确地回答。
"""
```

## Structured Output

```python
from pydantic import BaseModel, Field

class MyOutput(BaseModel):
    result: str = Field(..., description="结果")
    confidence: float = Field(..., ge=0, le=1)

agent = Agent(
    output_schema=MyOutput,
    use_json_mode=True,
)
```

## 注册

```python
# app/agents/__init__.py
from app.agents.my_agent.agent import create_my_agent
agents.append(create_my_agent(db))
```

## 关键参数

| 参数 | 说明 |
|------|------|
| id | Agent ID，kebab-case，决定 API URL |
| model | 模型实例，使用 create_model() |
| db | PostgresDb 连接 |
| instructions | System Prompt |
| tools | 工具函数列表 |
| output_schema | Pydantic Model（可选） |
| use_json_mode | 启用 JSON 模式（配合 output_schema） |

## API

Agent 注册后自动生成:
- `POST /agents/{agent_id}/runs` - 运行 Agent
- API 文档: `http://localhost:7777/docs`
