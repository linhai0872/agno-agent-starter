"""
GitHub 仓库分析 Agent

展示 Agno Agent 结构化输出的最佳实践。

使用示例:
    from agno.db.postgres import PostgresDb
    from app.agents.github_analyzer import create_github_analyzer_agent

    db = PostgresDb(db_url="...")
    agent = create_github_analyzer_agent(db)

    response = agent.run("分析 https://github.com/agno-agi/agno")
    print(response.content)  # GitHubRepoAnalysis 对象
"""

import logging

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools

from app.agents.github_analyzer.prompts import SYSTEM_PROMPT
from app.agents.github_analyzer.schemas import GitHubRepoAnalysis
from app.config import get_settings

logger = logging.getLogger(__name__)


def create_github_analyzer_agent(db: PostgresDb) -> Agent:
    """
    创建 GitHub 仓库分析 Agent

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        配置好的 Agent 实例

    特性:
        - 结构化输出: 使用 output_schema + use_json_mode
        - 搜索工具: DuckDuckGoTools（无需 API Key）
        - 错误处理: 搜索失败时返回部分结果
    """
    settings = get_settings()

    agent = Agent(
        name="GitHub Analyzer",
        description="分析 GitHub 仓库的技术栈、活跃度和核心功能",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        db=db,
        instructions=SYSTEM_PROMPT,
        tools=[DuckDuckGoTools()],
        output_schema=GitHubRepoAnalysis,
        use_json_mode=True,
        markdown=False,
        enable_user_memories=True,
        enable_session_summaries=True,
    )

    return agent
