<p align="right">
  <a href="README.md">中文</a>
</p>

# Workflow Development Guide

Workflows are used for scenarios requiring strict step control and conditional branching.

## When to Use

| Scenario | Recommendation |
|----------|----------------|
| Single task + Tool calls | Agent |
| Multi-role collaboration | Team |
| Strict steps + Conditionals | Workflow |

## Directory Structure

```
workflows/
├── __init__.py          # Registration entrypoint
└── my_workflow.py       # Workflow implementation
```

## Workflow Template

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

## Conditional Branching

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

## Registration

```python
# app/workflows/__init__.py
from app.workflows.my_workflow import create_my_workflow
workflows.append(create_my_workflow(db))
```

## Key Components

| Component | Description |
|-----------|-------------|
| Step      | A single step, containing an Agent or Team |
| Condition | Conditional branching, evaluator returns bool |
| Parallel  | Execute multiple steps in parallel |

## API

After registration, the following APIs are auto-generated:
- `POST /workflows/{workflow_id}/runs` - Run Workflow
- API Docs: `http://localhost:7777/docs`

