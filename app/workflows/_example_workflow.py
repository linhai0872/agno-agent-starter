"""
示例 Workflow - 内容生成工作流

此文件以 _ 开头，不会被自动加载。
仅作为创建新 Workflow 的参考模板。

使用时：
1. 复制此文件并重命名（去掉 _ 前缀）
2. 修改 Workflow 配置
3. 在 __init__.py 中注册

API Key 配置：
- 在 .env 中添加项目专用 Key: CONTENT_PIPELINE_KEY=sk-xxx
- 通过 ProjectConfig 统一管理，所有 Agent 共享同一个 Key
- 特定 Agent 可通过 ModelConfig.api_key_env 覆盖
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.workflow import Workflow
from agno.workflow.condition import Condition
from agno.workflow.step import Step
from agno.workflow.types import StepInput

from app.models import ModelConfig, ProjectConfig, create_model


# ============== 项目级配置 ==============
# 整个 Workflow 内的所有 Agent 共用此 API Key
# 在 .env 中添加: CONTENT_PIPELINE_KEY=sk-xxx

PROJECT_CONFIG = ProjectConfig(
    api_key_env="CONTENT_PIPELINE_KEY",  # 不设置则使用全局 OPENROUTER_API_KEY
)


# ============== Workflow 模型配置 ==============

WORKFLOW_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
    max_tokens=8192,
)

# 高级 Agent 使用独立 API Key（覆盖项目配置）
PREMIUM_MODEL_CONFIG = ModelConfig(
    model_id="anthropic/claude-sonnet-4",
    api_key_env="PREMIUM_MODEL_KEY",  # Agent 级覆盖
    temperature=0.3,
    max_tokens=16384,
)


def create_content_pipeline(db: PostgresDb) -> Workflow:
    """
    创建内容生成工作流

    流程: Research -> Summarize -> Conditional Fact Check -> Write Article

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        配置好的 Workflow 实例
    """
    # ============== 定义 Agents ==============
    # 所有 Agent 共用 PROJECT_CONFIG 的 API Key
    # 特定 Agent 可通过 ModelConfig.api_key_env 覆盖

    researcher = Agent(
        name="Researcher",
        model=create_model(WORKFLOW_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a research specialist.",
            "Research the given topic and provide detailed findings.",
            "Include relevant facts, statistics, and sources.",
        ],
    )

    summarizer = Agent(
        name="Summarizer",
        model=create_model(WORKFLOW_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a summarization expert.",
            "Create a clear and concise summary of the research findings.",
            "Highlight key points and main conclusions.",
        ],
    )

    fact_checker = Agent(
        name="FactChecker",
        model=create_model(WORKFLOW_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a fact-checking specialist.",
            "Verify the accuracy of facts and claims.",
            "Flag any unverified or questionable statements.",
        ],
    )

    # Writer 使用高级模型和独立 API Key（覆盖项目配置）
    writer = Agent(
        name="Writer",
        model=create_model(PREMIUM_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a professional content writer.",
            "Write a comprehensive article based on the research and verification.",
            "Use clear, engaging language suitable for the target audience.",
        ],
    )

    # ============== 定义 Steps ==============

    research_step = Step(
        name="research",
        description="Research the topic thoroughly",
        agent=researcher,
    )

    summarize_step = Step(
        name="summarize",
        description="Summarize the research findings",
        agent=summarizer,
    )

    fact_check_step = Step(
        name="fact_check",
        description="Verify facts and claims",
        agent=fact_checker,
    )

    write_step = Step(
        name="write_article",
        description="Write the final article",
        agent=writer,
    )

    # ============== 条件判断函数 ==============

    def needs_fact_checking(step_input: StepInput) -> bool:
        """判断是否需要事实核查"""
        content = step_input.previous_step_content or ""

        # 包含这些关键词时需要事实核查
        fact_indicators = [
            "study shows",
            "research indicates",
            "according to",
            "statistics",
            "data shows",
            "percent",
            "%",
            "million",
            "billion",
        ]

        return any(indicator in content.lower() for indicator in fact_indicators)

    # ============== 创建 Workflow ==============

    workflow = Workflow(
        name="content-pipeline",
        description="Research -> Summarize -> Conditional Fact Check -> Write Article",
        db=db,
        steps=[
            research_step,
            summarize_step,
            Condition(
                name="fact_check_condition",
                description="Check if fact-checking is needed",
                evaluator=needs_fact_checking,
                steps=[fact_check_step],
            ),
            write_step,
        ],
    )

    return workflow


# ============== 注册示例 ==============
#
# 在 app/workflows/__init__.py 中添加：
#
# from app.workflows.content_pipeline import create_content_pipeline
# workflows.append(create_content_pipeline(db))

