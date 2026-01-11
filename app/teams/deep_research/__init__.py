"""
Deep Research Team 模块

展示 Agno Team 多智能体协作的最佳实践。
"""

from app.teams.deep_research.schemas import (
    ResearchFinding,
    ResearchReport,
    ResearchSource,
)
from app.teams.deep_research.team import create_deep_research_team

__all__ = [
    "create_deep_research_team",
    "ResearchReport",
    "ResearchFinding",
    "ResearchSource",
]
