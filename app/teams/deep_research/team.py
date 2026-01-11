"""
Deep Research Team

展示 Agno Team 多智能体协作的最佳实践。

使用示例:
    from agno.db.postgres import PostgresDb
    from app.teams.deep_research import create_deep_research_team

    db = PostgresDb(db_url="...")
    team = create_deep_research_team(db)

    response = team.run("研究 AI Agent 框架的发展趋势")
    print(response.content)
"""

import logging

from agno.db.postgres import PostgresDb
from agno.models.openrouter import OpenRouter
from agno.team import Team

from app.config import get_settings
from app.teams.deep_research.agents import (
    create_analyst_agent,
    create_planner_agent,
    create_researcher_agent,
    create_writer_agent,
)
from app.teams.deep_research.schemas import ResearchReport

logger = logging.getLogger(__name__)


def create_deep_research_team(db: PostgresDb) -> Team:
    """
    创建深度研究 Team

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        配置好的 Team 实例

    特性:
        - 多智能体协作: Planner -> Researcher -> Analyst -> Writer
        - 状态管理: session_state 共享研究发现
        - 迭代控制: ToolCallGuard 限制搜索次数
    """
    settings = get_settings()

    planner = create_planner_agent()
    researcher = create_researcher_agent()
    analyst = create_analyst_agent()
    writer = create_writer_agent()

    team = Team(
        name="Deep Research Team",
        description="多智能体协作完成深度研究任务",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        members=[planner, researcher, analyst, writer],
        db=db,
        session_state={
            "findings": [],
            "topics_searched": [],
            "sources": [],
        },
        enable_agentic_state=True,
        add_session_state_to_context=True,
        share_member_interactions=True,
        instructions="""\
你是深度研究团队的协调者。管理研究流程：

1. **规划阶段**: 让 Planner 分解研究主题
2. **搜索阶段**: 让 Researcher 按计划搜索信息
3. **分析阶段**: 让 Analyst 综合分析结果
4. **撰写阶段**: 让 Writer 生成最终报告

session_state 说明:
- findings: 累积的研究发现
- topics_searched: 已搜索的主题
- sources: 来源列表

确保最终输出是结构化的研究报告。
""",
        output_schema=ResearchReport,
        markdown=True,
    )

    return team
