"""
研究团队 - Team 创建

多 Agent 协作示例：
- Researcher: 负责信息检索和研究
- Writer: 负责内容撰写
- Team Leader: 协调成员完成任务

API Key 配置：
- 通过 ProjectConfig 统一管理项目级 API Key
- 在 .env 中添加: RESEARCH_TEAM_KEY=sk-xxx
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.team import Team

from app.models import ModelConfig, ProjectConfig, create_model

# ============== 项目级配置 ==============
# 整个 Team 内的所有 Agent 共用此 API Key

PROJECT_CONFIG = ProjectConfig(
    api_key_env="RESEARCH_TEAM_KEY",
)


# ============== Team 模型配置 ==============

TEAM_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.3,
    max_tokens=8192,
)

RESEARCHER_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
    max_tokens=4096,
)

WRITER_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.5,
    max_tokens=8192,
)


def create_research_team(db: PostgresDb) -> Team:
    """
    创建研究团队

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        配置好的 Team 实例
    """
    # 创建 Researcher Agent
    researcher = Agent(
        name="Researcher",
        role="Research and gather information on any topic",
        model=create_model(RESEARCHER_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a research specialist with expertise in finding and analyzing information.",
            "When given a topic, search thoroughly for relevant information.",
            "Always cite your sources and indicate the reliability of information.",
            "Focus on facts and data, avoid speculation.",
            "Provide structured findings that can be used by the writer.",
        ],
        add_datetime_to_context=True,
    )

    # 创建 Writer Agent
    writer = Agent(
        name="Writer",
        role="Write clear, well-structured content based on research",
        model=create_model(WRITER_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a professional content writer.",
            "Create clear, engaging, and well-organized content.",
            "Use appropriate formatting: headings, bullet points, etc.",
            "Maintain a professional yet accessible tone.",
            "Ensure all claims are based on the provided research.",
        ],
    )

    # 创建 Team
    team = Team(
        id="research-team",
        name="Research Team",
        description="A collaborative team for research and content creation",
        model=create_model(TEAM_MODEL_CONFIG, PROJECT_CONFIG),
        members=[researcher, writer],
        db=db,
        instructions=[
            "You are the leader of a research team.",
            "Your team consists of a Researcher and a Writer.",
            "",
            "## Workflow",
            "1. First, delegate research tasks to the Researcher",
            "2. Review the research findings",
            "3. Then, delegate writing tasks to the Writer",
            "4. Review and finalize the content",
            "",
            "## Guidelines",
            "- Ensure research is thorough before writing begins",
            "- Provide clear instructions to each team member",
            "- Synthesize the final output from team contributions",
        ],
        # Team 配置
        show_members_responses=True,
        get_member_information_tool=True,
        add_member_tools_to_context=True,
        share_member_interactions=True,  # 成员间共享交互历史
        markdown=True,
        # Structured Output（可选）
        # output_schema=ResearchReport,
        # use_json_mode=True,
    )

    return team


# ============== 使用示例 ==============
#
# Team API 调用:
# POST /teams/research-team/runs
# {
#   "message": "Research the latest trends in AI agents and create a summary report"
# }
