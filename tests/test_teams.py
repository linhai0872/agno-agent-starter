"""
Team 基础测试

运行测试:
    pytest tests/test_teams.py -v

注意: 经典模板测试已迁移到 tests/teams/ 目录
"""

from unittest.mock import MagicMock


class TestGetAllTeams:
    """Team 注册表测试"""

    def test_get_all_teams_returns_list(self):
        """测试获取所有 Team 返回列表"""
        from app.teams import get_all_teams

        mock_db = MagicMock()
        teams = get_all_teams(mock_db)

        assert isinstance(teams, list)
        # 现在应该包含 Deep Research Team
        assert len(teams) >= 1


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
