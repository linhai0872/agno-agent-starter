<p align="right">
  <a href="README_EN.md">English</a>
</p>

# Team 开发指南

Team 用于多 Agent 协作场景，由 Leader 协调成员完成任务。

## 何时使用

| 场景 | 推荐 |
|------|------|
| 单一任务 + 工具调用 | Agent |
| 多角色协作 | Team |
| 严格步骤 + 条件分支 | Workflow |

## 目录结构

```
teams/
├── __init__.py       # 注册入口
└── my_team.py        # Team 实现
```

## Team 模板

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

## 注册

```python
# app/teams/__init__.py
from app.teams.my_team import create_my_team
teams.append(create_my_team(db))
```

## 关键参数

| 参数 | 说明 |
|------|------|
| id | Team ID，kebab-case |
| model | Leader 模型 |
| members | Agent 列表 |
| delegate_to_all_members | 并行委派所有成员 |
| share_member_interactions | 成员间共享交互历史 |
| show_members_responses | 显示成员响应 |

## API

Team 注册后自动生成:
- `POST /teams/{team_id}/runs` - 运行 Team
- API 文档: `http://localhost:7777/docs`
