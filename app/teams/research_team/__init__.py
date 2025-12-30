"""
研究团队 - Research Team

多 Agent 协作示例，展示 Team 模式的最佳实践。
"""

from app.teams.research_team.schemas import ResearchFinding, ResearchReport
from app.teams.research_team.team import create_research_team

__all__ = [
    "create_research_team",
    "ResearchFinding",
    "ResearchReport",
]

