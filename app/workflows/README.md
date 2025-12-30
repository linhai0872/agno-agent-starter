<p align="right">
  <a href="README_EN.md">English</a>
</p>

# Workflow 开发指南

Workflow 用于需要严格步骤控制、条件分支的场景。

## 何时使用

| 场景 | 推荐 |
|------|------|
| 单一任务 + 工具调用 | Agent |
| 多角色协作 | Team |
| 严格步骤 + 条件分支 | Workflow |

## 目录结构

```
workflows/
├── __init__.py          # 注册入口
└── my_workflow.py       # Workflow 实现
```

## Workflow 模板

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.workflow import Workflow
from agno.workflow.step import Step
from app.models import ModelConfig, create_model

WORKFLOW_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
)

def create_my_workflow(db: PostgresDb) -> Workflow:
    researcher = Agent(
        name="Researcher",
        model=create_model(WORKFLOW_MODEL_CONFIG),
    )
    
    writer = Agent(
        name="Writer",
        model=create_model(WORKFLOW_MODEL_CONFIG),
    )
    
    return Workflow(
        id="my-workflow",
        db=db,
        steps=[
            Step(name="research", agent=researcher),
            Step(name="write", agent=writer),
        ],
    )
```

## 条件分支

```python
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput

def needs_review(step_input: StepInput) -> bool:
    content = step_input.previous_step_content or ""
    return "statistics" in content.lower()

workflow = Workflow(
    steps=[
        research_step,
        Condition(
            name="review_condition",
            evaluator=needs_review,
            steps=[review_step],
        ),
        write_step,
    ],
)
```

## 注册

```python
# app/workflows/__init__.py
from app.workflows.my_workflow import create_my_workflow
workflows.append(create_my_workflow(db))
```

## 关键组件

| 组件 | 说明 |
|------|------|
| Step | 单个步骤，包含 Agent 或 Team |
| Condition | 条件分支，evaluator 返回 bool |
| Parallel | 并行执行多个步骤 |

## API

Workflow 注册后自动生成:
- `POST /workflows/{workflow_id}/runs` - 运行 Workflow
- API 文档: `http://localhost:7777/docs`
