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

    # ============== 经典模板 Team ==============
    from app.teams.deep_research import create_deep_research_team

    teams.append(create_deep_research_team(db))

    # ============== 添加你的 Team ==============
    # from app.teams.your_team.team import create_your_team
    # teams.append(create_your_team(db))

    return teams


__all__ = ["get_all_teams"]
