"""
GitHub 仓库分析 Agent 模块

展示 Agno Agent 结构化输出的最佳实践。
"""

from app.agents.github_analyzer.agent import create_github_analyzer_agent
from app.agents.github_analyzer.schemas import GitHubRepoAnalysis

__all__ = ["create_github_analyzer_agent", "GitHubRepoAnalysis"]
