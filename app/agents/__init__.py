"""
Agent 注册入口

统一管理所有 Agent 的创建和注册。
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb


def get_all_agents(db: PostgresDb) -> list[Agent]:
    """
    获取所有 Agent 实例

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        Agent 实例列表
    """
    agents = []

    # ============== 经典模板 Agent ==============
    from app.agents.github_analyzer import create_github_analyzer_agent

    agents.append(create_github_analyzer_agent(db))

    # ============== 添加你的 Agent ==============
    # from app.agents.your_agent.agent import create_your_agent
    # agents.append(create_your_agent(db))

    return agents


__all__ = ["get_all_agents"]
