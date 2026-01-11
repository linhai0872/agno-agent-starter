"""
Team 注册入口

统一管理所有 Team 的创建和注册。
Team 用于多智能体协作场景，让多个 Agent 共同完成复杂任务。
"""

from agno.db.postgres import PostgresDb
from agno.team import Team


def get_all_teams(db: PostgresDb) -> list[Team]:
    """
    获取所有 Team 实例

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        Team 实例列表
    """
    teams = []

    # Research Team (示例 - 取消注释以启用)
    # from app.teams.research_team.team import create_research_team
    # teams.append(create_research_team(db))

    # 在此添加更多 Team...

    return teams


__all__ = ["get_all_teams"]
