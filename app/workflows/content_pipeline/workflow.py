"""
内容生成工作流 - Workflow 创建

展示 Workflow 的完整功能：
- 多步骤顺序执行
- 条件分支判断
- 结构化输出
- 项目级 API Key 管理

流程: Research -> Summarize -> Conditional Fact Check -> Write Article
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.workflow import Workflow
from agno.workflow.condition import Condition
from agno.workflow.step import Step
from agno.workflow.types import StepInput

from app.models import ModelConfig, ProjectConfig, create_model

# ============== 项目级配置 ==============

PROJECT_CONFIG = ProjectConfig(
    api_key_env="CONTENT_PIPELINE_KEY",
)


# ============== 模型配置 ==============

STANDARD_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
    max_tokens=8192,
)

CREATIVE_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.6,
    max_tokens=12288,
)


def create_content_pipeline(db: PostgresDb) -> Workflow:
    """
    创建内容生成工作流

    流程:
    1. Research: 研究主题，收集信息
    2. Summarize: 整理研究发现
    3. Fact Check (条件): 如果包含数据/统计，进行事实核查
    4. Write: 撰写最终文章

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        配置好的 Workflow 实例
    """
    # ============== 定义 Agents ==============
    # 注意：Workflow 内的 Agent 是无状态的，不需要传 db 参数
    # 如需 Session/Memory 持久化，可添加 db=db 参数

    researcher = Agent(
        name="Researcher",
        model=create_model(STANDARD_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a research specialist.",
            "When given a topic, thoroughly research and gather information.",
            "Include:",
            "- Key facts and statistics",
            "- Expert opinions and quotes",
            "- Recent developments and trends",
            "- Credible sources",
            "Format your findings clearly with sections and bullet points.",
        ],
    )

    summarizer = Agent(
        name="Summarizer",
        model=create_model(STANDARD_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a summarization expert.",
            "Create a concise but comprehensive summary of the research.",
            "Organize information into:",
            "- Main findings",
            "- Key statistics",
            "- Important quotes",
            "- Areas for fact-checking",
            "Flag any claims that need verification.",
        ],
    )

    fact_checker = Agent(
        name="FactChecker",
        model=create_model(STANDARD_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a fact-checking specialist.",
            "Your job is to verify claims and statistics.",
            "For each significant claim:",
            "1. Identify the source",
            "2. Verify accuracy",
            "3. Note any discrepancies",
            "4. Suggest corrections if needed",
            "Be thorough but efficient.",
        ],
    )

    writer = Agent(
        name="Writer",
        model=create_model(CREATIVE_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a professional content writer.",
            "Write a compelling article based on the research and verification.",
            "Guidelines:",
            "- Use clear, engaging language",
            "- Structure with introduction, body, conclusion",
            "- Include relevant quotes and statistics",
            "- Cite sources appropriately",
            "- Aim for ~1000 words unless specified otherwise",
        ],
    )

    # ============== 定义 Steps ==============

    research_step = Step(
        name="research",
        description="Research the topic and gather information",
        agent=researcher,
    )

    summarize_step = Step(
        name="summarize",
        description="Summarize and organize research findings",
        agent=summarizer,
    )

    fact_check_step = Step(
        name="fact_check",
        description="Verify facts, statistics, and claims",
        agent=fact_checker,
    )

    write_step = Step(
        name="write_article",
        description="Write the final article",
        agent=writer,
    )

    # ============== 条件判断 ==============

    def needs_fact_checking(step_input: StepInput) -> bool:
        """
        判断是否需要事实核查

        触发条件：内容包含数据、统计或引用
        """
        content = step_input.previous_step_content or ""
        content_lower = content.lower()

        # 需要核查的指标词
        fact_indicators = [
            "study shows",
            "research indicates",
            "according to",
            "statistics",
            "data shows",
            "survey",
            "report",
            "percent",
            "%",
            "million",
            "billion",
            "increased by",
            "decreased by",
        ]

        # 任一指标词出现则需要核查
        return any(indicator in content_lower for indicator in fact_indicators)

    # ============== 创建 Workflow ==============

    workflow = Workflow(
        id="content-pipeline",
        name="Content Pipeline",
        description="End-to-end content generation: Research -> Summarize -> Fact Check -> Write",
        db=db,
        steps=[
            research_step,
            summarize_step,
            Condition(
                name="fact_check_condition",
                description="Check if content contains claims that need verification",
                evaluator=needs_fact_checking,
                steps=[fact_check_step],
            ),
            write_step,
        ],
    )

    return workflow


# ============== 使用示例 ==============
#
# Workflow API 调用:
# POST /workflows/content-pipeline/runs
# {
#   "message": "Write an article about the impact of AI on healthcare in 2025"
# }
#
# 响应包含每个步骤的输出和最终文章
