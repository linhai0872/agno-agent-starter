"""
示例 Team - 研究团队

此文件以 _ 开头，不会被自动加载。
仅作为创建新 Team 的参考模板。

使用时：
1. 复制此文件并重命名（去掉 _ 前缀）
2. 修改 Team 配置
3. 在 __init__.py 中注册

API Key 配置：
- 在 .env 中添加项目专用 Key: RESEARCH_TEAM_KEY=sk-xxx
- 通过 ProjectConfig 统一管理，所有成员 Agent 共享同一个 Key
- 特定成员可通过 ModelConfig.api_key_env 覆盖
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.team import Team

from app.models import ModelConfig, ProjectConfig, create_model

# ============== 项目级配置 ==============
# 整个 Team 内的所有 Agent 共用此 API Key
# 在 .env 中添加: RESEARCH_TEAM_KEY=sk-xxx

PROJECT_CONFIG = ProjectConfig(
    api_key_env="RESEARCH_TEAM_KEY",  # 不设置则使用全局 OPENROUTER_API_KEY
)


# ============== Team 模型配置 ==============
# Team Leader 和成员使用的模型配置

TEAM_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.3,
    max_tokens=8192,
)


def create_research_team(db: PostgresDb, agents: list[Agent]) -> Team:
    """
    创建研究团队

    Args:
        db: PostgreSQL 数据库连接
        agents: 已注册的 Agent 列表

    Returns:
        配置好的 Team 实例
    """
    # 创建 Team 成员
    # 所有成员共用 PROJECT_CONFIG 的 API Key
    researcher = Agent(
        name="Researcher",
        role="Research and gather information",
        model=create_model(TEAM_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a research specialist.",
            "Find relevant information about the given topic.",
            "Provide detailed findings with sources.",
        ],
    )

    writer = Agent(
        name="Writer",
        role="Write clear and concise content",
        model=create_model(TEAM_MODEL_CONFIG, PROJECT_CONFIG),
        instructions=[
            "You are a content writer.",
            "Create well-structured content based on research.",
            "Use clear and engaging language.",
        ],
    )

    # 创建 Team
    # Team Leader 也共用项目 API Key
    team = Team(
        name="research-team",
        model=create_model(TEAM_MODEL_CONFIG, PROJECT_CONFIG),
        members=[researcher, writer],
        db=db,
        instructions=[
            "You are a research team leader.",
            "Coordinate the researcher and writer to complete tasks.",
            "First, use the researcher to gather information.",
            "Then, use the writer to create content based on the research.",
        ],
        show_members_responses=True,
        get_member_information_tool=True,
        add_member_tools_to_context=True,
        markdown=True,
    )

    return team


# ============== 注册示例 ==============
#
# 在 app/teams/__init__.py 中添加：
#
# from app.teams.research_team import create_research_team
# teams.append(create_research_team(db, agents))
