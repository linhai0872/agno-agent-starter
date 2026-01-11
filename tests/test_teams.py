"""
Team 基础测试

运行测试:
    pytest tests/test_teams.py -v
"""

from unittest.mock import MagicMock, patch


class TestTeamSchemas:
    """Team Schema 单元测试"""

    def test_research_finding_schema(self):
        """测试研究发现 Schema"""
        from app.teams.research_team.schemas import ResearchFinding

        finding = ResearchFinding(
            topic="AI 发展趋势",
            summary="人工智能正在快速发展...",
            sources=["来源1", "来源2"],
            confidence=0.85,
        )

        assert finding.topic == "AI 发展趋势"
        assert finding.confidence == 0.85
        assert len(finding.sources) == 2

    def test_research_report_schema(self):
        """测试研究报告 Schema"""
        from app.teams.research_team.schemas import ResearchFinding, ResearchReport

        finding = ResearchFinding(
            topic="测试主题",
            summary="测试摘要",
            sources=[],
            confidence=0.9,
        )

        report = ResearchReport(
            title="测试报告",
            abstract="报告摘要",
            findings=[finding],
            conclusion="结论内容",
            recommendations=["建议1", "建议2"],
        )

        assert report.title == "测试报告"
        assert len(report.findings) == 1
        assert len(report.recommendations) == 2


class TestTeamCreation:
    """Team 创建测试"""

    def test_research_team_creation(self):
        """测试研究团队创建"""
        from app.teams.research_team.team import create_research_team

        mock_db = MagicMock()

        with patch("app.teams.research_team.team.Team") as MockTeam:
            mock_team_instance = MagicMock()
            MockTeam.return_value = mock_team_instance

            with patch("app.teams.research_team.team.create_model") as mock_create_model:
                mock_create_model.return_value = "mock-model"

                with patch("app.teams.research_team.team.Agent") as MockAgent:
                    MockAgent.return_value = MagicMock()

                    create_research_team(mock_db)

                    # 验证 Team 创建参数
                    call_kwargs = MockTeam.call_args[1]
                    assert call_kwargs["id"] == "research-team"
                    assert call_kwargs["name"] == "Research Team"
                    assert len(call_kwargs["members"]) == 2
                    assert call_kwargs["db"] == mock_db

    def test_team_config(self):
        """测试 Team 配置"""
        from app.models import ModelProvider
        from app.teams.research_team.team import (
            PROJECT_CONFIG,
            RESEARCHER_MODEL_CONFIG,
            TEAM_MODEL_CONFIG,
            WRITER_MODEL_CONFIG,
        )

        # 验证项目配置
        assert PROJECT_CONFIG.api_key_env == "RESEARCH_TEAM_KEY"

        # 验证模型配置
        assert TEAM_MODEL_CONFIG.provider == ModelProvider.OPENROUTER
        assert RESEARCHER_MODEL_CONFIG.temperature == 0.2
        assert WRITER_MODEL_CONFIG.temperature == 0.5


class TestGetAllTeams:
    """Team 注册表测试"""

    def test_get_all_teams_empty(self):
        """测试获取所有 Team（默认为空）"""
        from app.teams import get_all_teams

        mock_db = MagicMock()
        teams = get_all_teams(mock_db)

        # 默认情况下示例 Team 被注释，返回空列表
        assert isinstance(teams, list)


class TestProjectConfig:
    """项目配置测试"""

    def test_project_config_api_key(self):
        """测试项目级 API Key 配置"""
        from app.models import ProjectConfig

        config = ProjectConfig(api_key_env="MY_PROJECT_KEY")

        assert config.api_key_env == "MY_PROJECT_KEY"

    def test_project_config_defaults(self):
        """测试项目配置默认值"""
        from app.models import ProjectConfig

        config = ProjectConfig()

        assert config.api_key_env is None
