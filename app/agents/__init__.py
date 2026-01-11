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

    # ============== 示例 Agent ==============

    # Structured Output Agent - 电影剧本（官方推荐的结构化输出模式）
    from app.agents.structured_output.agent import create_movie_script_agent

    agents.append(create_movie_script_agent(db))

    # Structured Output Agent - 研究报告
    # from app.agents.structured_output.agent import create_research_report_agent
    # agents.append(create_research_report_agent(db))

    # Knowledge RAG Agent
    # from app.agents.knowledge_rag.agent import create_knowledge_rag_agent
    # agents.append(create_knowledge_rag_agent(db))

    # ============== 添加你的 Agent ==============
    # from app.agents.your_agent.agent import create_your_agent
    # agents.append(create_your_agent(db))

    return agents


__all__ = ["get_all_agents"]
