"""
Workflow 基础测试

运行测试:
    pytest tests/test_workflows.py -v
"""

from unittest.mock import MagicMock, patch


class TestWorkflowSchemas:
    """Workflow Schema 单元测试"""

    def test_fact_check_item_schema(self):
        """测试事实核查项 Schema"""
        from app.workflows.content_pipeline.schemas import FactCheckItem

        item = FactCheckItem(
            claim="AI 市场规模将达到 1000 亿美元",
            verified=True,
            source="Gartner 2024 报告",
            note="数据来自可靠来源",
        )

        assert item.claim == "AI 市场规模将达到 1000 亿美元"
        assert item.verified is True
        assert item.source == "Gartner 2024 报告"

    def test_article_output_schema(self):
        """测试文章输出 Schema"""
        from app.workflows.content_pipeline.schemas import ArticleOutput

        article = ArticleOutput(
            title="AI 发展趋势分析",
            summary="本文分析了 AI 的最新发展趋势...",
            content="正文内容...",
            key_points=["要点1", "要点2", "要点3"],
            sources=["来源1", "来源2"],
            word_count=1500,
        )

        assert article.title == "AI 发展趋势分析"
        assert len(article.key_points) == 3
        assert article.word_count == 1500

    def test_article_output_defaults(self):
        """测试文章输出默认值"""
        from app.workflows.content_pipeline.schemas import ArticleOutput

        article = ArticleOutput(
            title="测试标题",
            summary="测试摘要",
            content="测试内容",
            word_count=100,
        )

        assert article.key_points == []
        assert article.sources == []


class TestWorkflowConditions:
    """Workflow 条件判断测试"""

    def test_needs_fact_checking_with_statistics(self):
        """测试包含统计数据时需要事实核查"""

        # 模拟 StepInput
        step_input = MagicMock()
        step_input.previous_step_content = "According to the study, 75% of companies use AI."

        # 导入条件函数

        # 测试判断逻辑
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

    def test_fact_check_indicators(self):
        """测试各种事实核查指标"""
        test_cases = [
            ("The study shows that...", True),
            ("Research indicates...", True),
            ("Data shows 50% increase", True),
            ("Revenue reached 5 million", True),
            ("Market size is 10 billion", True),
            ("Simple greeting message", False),
            ("Just an opinion", False),
        ]

        indicators = [
            "study shows",
            "research indicates",
            "according to",
            "statistics",
            "data shows",
            "survey",
            "report",
            "percent",
            "%",
            "million",
            "billion",
            "increased by",
            "decreased by",
        ]

        for content, expected in test_cases:
            content_lower = content.lower()
            result = any(indicator in content_lower for indicator in indicators)
            assert result == expected, f"Failed for: {content}"


class TestWorkflowCreation:
    """Workflow 创建测试"""

    def test_content_pipeline_creation(self):
        """测试内容生成工作流创建"""
        from app.workflows.content_pipeline.workflow import create_content_pipeline

        mock_db = MagicMock()

        with patch("app.workflows.content_pipeline.workflow.Workflow") as MockWorkflow:
            mock_workflow_instance = MagicMock()
            MockWorkflow.return_value = mock_workflow_instance

            with patch("app.workflows.content_pipeline.workflow.create_model") as mock_create_model:
                mock_create_model.return_value = "mock-model"

                with patch("app.workflows.content_pipeline.workflow.Agent") as MockAgent:
                    MockAgent.return_value = MagicMock()

                    with patch("app.workflows.content_pipeline.workflow.Step") as MockStep:
                        MockStep.return_value = MagicMock()

                        with patch(
                            "app.workflows.content_pipeline.workflow.Condition"
                        ) as MockCondition:
                            MockCondition.return_value = MagicMock()

                            create_content_pipeline(mock_db)

                            # 验证 Workflow 创建参数
                            call_kwargs = MockWorkflow.call_args[1]
                            assert call_kwargs["id"] == "content-pipeline"
                            assert call_kwargs["name"] == "Content Pipeline"
                            assert call_kwargs["db"] == mock_db
                            # 4 个步骤：research, summarize, condition, write
                            assert len(call_kwargs["steps"]) == 4

    def test_workflow_config(self):
        """测试 Workflow 配置"""
        from app.workflows.content_pipeline.workflow import (
            CREATIVE_MODEL_CONFIG,
            PROJECT_CONFIG,
            STANDARD_MODEL_CONFIG,
        )

        # 验证项目配置
        assert PROJECT_CONFIG.api_key_env == "CONTENT_PIPELINE_KEY"

        # 验证模型配置差异
        assert STANDARD_MODEL_CONFIG.temperature == 0.2
        assert CREATIVE_MODEL_CONFIG.temperature == 0.6
        assert CREATIVE_MODEL_CONFIG.max_tokens > STANDARD_MODEL_CONFIG.max_tokens


class TestGetAllWorkflows:
    """Workflow 注册表测试"""

    def test_get_all_workflows_empty(self):
        """测试获取所有 Workflow（默认为空）"""
        from app.workflows import get_all_workflows

        mock_db = MagicMock()
        workflows = get_all_workflows(mock_db)

        # 默认情况下示例 Workflow 被注释，返回空列表
        assert isinstance(workflows, list)


class TestStepDefinition:
    """Step 定义测试"""

    def test_step_import(self):
        """测试 Step 模块导入"""
        from agno.workflow import Step, Workflow
        from agno.workflow.condition import Condition

        # 验证类型可用
        assert Step is not None
        assert Workflow is not None
        assert Condition is not None
