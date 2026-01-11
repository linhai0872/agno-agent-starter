"""
Workflow 基础测试

运行测试:
    pytest tests/test_workflows.py -v

注意: 经典模板测试已迁移到 tests/workflows/ 目录
"""

from unittest.mock import MagicMock


class TestWorkflowConditions:
    """Workflow 条件判断测试"""

    def test_needs_fact_checking_with_statistics(self):
        """测试包含统计数据时需要事实核查"""
        step_input = MagicMock()
        step_input.previous_step_content = "According to the study, 75% of companies use AI."

        content = step_input.previous_step_content.lower()
        indicators = ["study shows", "according to", "percent", "%"]
        result = any(indicator in content for indicator in indicators)

        assert result is True

    def test_needs_fact_checking_without_statistics(self):
        """测试不包含统计数据时不需要事实核查"""
        step_input = MagicMock()
        step_input.previous_step_content = "This is a simple opinion piece."

        content = step_input.previous_step_content.lower()
        indicators = ["study shows", "according to", "percent", "%", "million", "billion"]
        result = any(indicator in content for indicator in indicators)

        assert result is False


class TestGetAllWorkflows:
    """Workflow 注册表测试"""

    def test_get_all_workflows_returns_list(self):
        """测试获取所有 Workflow 返回列表"""
        from app.workflows import get_all_workflows

        mock_db = MagicMock()
        workflows = get_all_workflows(mock_db)

        assert isinstance(workflows, list)
        # 现在应该包含 Customer Service Workflow
        assert len(workflows) >= 1


class TestStepDefinition:
    """Step 定义测试"""

    def test_step_import(self):
        """测试 Step 模块导入"""
        from agno.workflow import Step, Workflow
        from agno.workflow.condition import Condition

        assert Step is not None
        assert Workflow is not None
        assert Condition is not None
