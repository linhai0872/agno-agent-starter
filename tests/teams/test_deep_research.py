"""
Deep Research Team 测试
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.teams.deep_research.schemas import (
    ResearchFinding,
    ResearchReport,
)


class TestResearchReportSchema:
    """Schema 验证测试"""

    def test_valid_report(self):
        # Arrange
        data = {
            "topic": "AI Agent 框架",
            "executive_summary": "研究发现 AI Agent 框架正在快速发展...",
            "findings": [
                {
                    "topic": "框架对比",
                    "summary": "主流框架各有特点",
                    "details": "详细分析...",
                    "confidence": "high",
                }
            ],
            "sources": [{"title": "Agno Docs", "url": "https://docs.agno.com", "type": "web"}],
            "recommendations": ["建议使用 Agno 框架"],
            "limitations": ["研究时间有限"],
        }

        # Act
        result = ResearchReport(**data)

        # Assert
        assert result.topic == "AI Agent 框架"
        assert len(result.findings) == 1
        assert result.findings[0].confidence == "high"

    def test_default_values(self):
        # Arrange
        data = {
            "topic": "Test Topic",
            "executive_summary": "Test summary",
        }

        # Act
        result = ResearchReport(**data)

        # Assert
        assert result.findings == []
        assert result.sources == []
        assert result.recommendations == []


class TestResearchFindingSchema:
    """研究发现 Schema 测试"""

    def test_valid_finding(self):
        # Arrange
        data = {
            "topic": "子主题",
            "summary": "核心发现",
            "details": "详细说明",
        }

        # Act
        result = ResearchFinding(**data)

        # Assert
        assert result.topic == "子主题"
        assert result.confidence == "medium"


class TestDeepResearchTeam:
    """Team 创建测试"""

    @patch("app.teams.deep_research.team.get_settings")
    @patch("app.teams.deep_research.agents.get_settings")
    @patch("agno.db.postgres.PostgresDb")
    def test_create_team(self, mock_db, mock_agents_settings, mock_team_settings):
        # Arrange
        settings_mock = MagicMock(
            model_name="gpt-4o",
            openrouter_api_key="test-key",
        )
        mock_team_settings.return_value = settings_mock
        mock_agents_settings.return_value = settings_mock
        mock_db_instance = MagicMock()

        # Act
        from app.teams.deep_research import create_deep_research_team

        team = create_deep_research_team(mock_db_instance)

        # Assert
        assert team.name == "Deep Research Team"
        assert len(team.members) == 4

    @patch("app.teams.deep_research.agents.get_settings")
    def test_researcher_has_tool_guard(self, mock_settings):
        # Arrange
        mock_settings.return_value = MagicMock(
            model_name="gpt-4o",
            openrouter_api_key="test-key",
        )

        # Act
        from app.teams.deep_research.agents import create_researcher_agent

        researcher = create_researcher_agent()

        # Assert
        assert researcher.name == "Researcher"
        assert len(researcher.tool_hooks) > 0


@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="需要 OPENROUTER_API_KEY 环境变量")
class TestDeepResearchE2E:
    """端到端测试（需要真实 API Key）"""

    @pytest.mark.asyncio
    async def test_research_topic(self):
        # 此测试需要真实 API Key，仅在 E2E 测试时运行
        pass
