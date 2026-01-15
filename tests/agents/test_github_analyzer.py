"""
GitHub Analyzer Agent 测试
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.agents.github_analyzer.schemas import GitHubRepoAnalysis


class TestGitHubRepoAnalysisSchema:
    """Schema 验证测试"""

    def test_valid_schema(self):
        # Arrange
        data = {
            "repo_name": "agno-agi/agno",
            "description": "Multi-agent framework",
            "tech_stack": ["Python", "FastAPI"],
            "stars": 12000,
            "forks": 800,
            "contributors": 50,
            "activity_level": "active",
            "key_features": ["Multi-agent", "RAG"],
            "recommendations": ["Use with AgentOS"],
        }

        # Act
        result = GitHubRepoAnalysis(**data)

        # Assert
        assert result.repo_name == "agno-agi/agno"
        assert result.stars == 12000
        assert "Python" in result.tech_stack

    def test_default_values(self):
        # Arrange
        data = {
            "repo_name": "test/repo",
            "description": "Test repo",
        }

        # Act
        result = GitHubRepoAnalysis(**data)

        # Assert
        assert result.stars == 0
        assert result.forks == 0
        assert result.activity_level == "unknown"
        assert result.tech_stack == []


class TestGitHubAnalyzerAgent:
    """Agent 创建测试"""

    @patch("app.agents.github_analyzer.agent.get_settings")
    @patch("agno.db.postgres.PostgresDb")
    def test_create_agent(self, mock_db, mock_settings):
        # Arrange
        mock_settings.return_value = MagicMock(
            model_name="gpt-4o",
            openrouter_api_key="test-key",
        )
        mock_db_instance = MagicMock()

        # Act
        from app.agents.github_analyzer import create_github_analyzer_agent

        agent = create_github_analyzer_agent(mock_db_instance)

        # Assert
        assert agent.name == "GitHub Analyzer"
        assert agent.output_schema == GitHubRepoAnalysis


@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="需要 OPENROUTER_API_KEY 环境变量")
class TestGitHubAnalyzerE2E:
    """端到端测试（需要真实 API Key）"""

    @pytest.mark.asyncio
    async def test_analyze_repository(self):
        # 此测试需要真实 API Key，仅在 E2E 测试时运行
        pass
