<p align="right">
  <a href="README.md">中文</a>
</p>

# Team Development Guide

Teams are used for multi-agent collaboration, where a Leader coordinates members to complete tasks.

## When to Use

| Scenario | Recommendation |
|----------|----------------|
| Single task + Tool calls | Agent |
| Multi-role collaboration | Team |
| Strict steps + Conditionals | Workflow |

## Directory Structure

```
teams/
├── __init__.py       # Registration entrypoint
└── my_team.py        # Team implementation
```

## Team Template

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.team import Team
from app.models import ModelConfig, ProjectConfig, create_model

PROJECT_CONFIG = ProjectConfig(api_key_env="MY_TEAM_KEY")
TEAM_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.3,
)

def create_my_team(db: PostgresDb) -> Team:
    researcher = Agent(
        name="Researcher",
        role="Research information",
        model=create_model(TEAM_MODEL_CONFIG, PROJECT_CONFIG),
    )
    
    writer = Agent(
        name="Writer",
        role="Write content",
        model=create_model(TEAM_MODEL_CONFIG, PROJECT_CONFIG),
    )
    
    return Team(
        id="my-team",
        model=create_model(TEAM_MODEL_CONFIG, PROJECT_CONFIG),
        members=[researcher, writer],
        db=db,
        instructions=["First research, then write."],
        show_members_responses=True,
    )
```

## Registration

```python
# app/teams/__init__.py
from app.teams.my_team import create_my_team
teams.append(create_my_team(db))
```

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| id        | Team ID, kebab-case |
| model     | Leader model |
| members   | List of Agents |
| delegate_to_all_members | Parallel delegation to all members |
| share_member_interactions | Shared interaction history among members |
| show_members_responses | Show responses from members |

## API

After registration, the following APIs are auto-generated:
- `POST /teams/{team_id}/runs` - Run Team
- API Docs: `http://localhost:7777/docs`

