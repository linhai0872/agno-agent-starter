"""
Customer Service Workflow 测试
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.workflows.customer_service.schemas import (
    ClassificationResult,
    QueryCategory,
    ServiceResponse,
)
from app.workflows.customer_service.steps import route_to_knowledge_base


class TestQueryCategoryEnum:
    """分类枚举测试"""

    def test_category_values(self):
        # Assert
        assert QueryCategory.BILLING.value == "billing"
        assert QueryCategory.TECHNICAL.value == "technical"
        assert QueryCategory.GENERAL.value == "general"
        assert QueryCategory.OTHER.value == "other"


class TestClassificationResultSchema:
    """分类结果 Schema 测试"""

    def test_valid_classification(self):
        # Arrange
        data = {
            "category": "billing",
            "confidence": 0.95,
            "reasoning": "问题涉及账单",
        }

        # Act
        result = ClassificationResult(**data)

        # Assert
        assert result.category == QueryCategory.BILLING
        assert result.confidence == 0.95


class TestServiceResponseSchema:
    """服务响应 Schema 测试"""

    def test_valid_response(self):
        # Arrange
        data = {
            "answer": "您好！请访问账单页面查看。",
            "category": "billing",
            "confidence": 0.9,
            "sources": ["billing-faq.md"],
            "requires_human": False,
        }

        # Act
        result = ServiceResponse(**data)

        # Assert
        assert result.answer.startswith("您好")
        assert result.requires_human is False


class TestRouteToKnowledgeBase:
    """路由评估器测试"""

    def test_route_billing_query(self):
        # Arrange
        mock_step_input = MagicMock()
        mock_step_input.previous_step_content = ClassificationResult(
            category=QueryCategory.BILLING,
            confidence=0.9,
            reasoning="账单相关",
        )

        # Act
        result = route_to_knowledge_base(mock_step_input)

        # Assert
        assert result is True

    def test_route_other_query(self):
        # Arrange
        mock_step_input = MagicMock()
        mock_step_input.previous_step_content = {"category": "other"}

        # Act
        result = route_to_knowledge_base(mock_step_input)

        # Assert
        assert result is False

    def test_route_with_none_content(self):
        # Arrange
        mock_step_input = MagicMock()
        mock_step_input.previous_step_content = None

        # Act
        result = route_to_knowledge_base(mock_step_input)

        # Assert - None 会进入 else 分支，category="other"，返回 False
        assert result is False


class TestCustomerServiceWorkflow:
    """Workflow 创建测试"""

    @patch("app.workflows.customer_service.workflow.get_settings")
    @patch("app.workflows.customer_service.steps.get_settings")
    @patch("agno.db.postgres.PostgresDb")
    def test_create_workflow(self, mock_db, mock_steps_settings, mock_workflow_settings):
        # Arrange
        settings_mock = MagicMock(
            model_name="gpt-4o",
            openrouter_api_key="test-key",
            database_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        )
        mock_workflow_settings.return_value = settings_mock
        mock_steps_settings.return_value = settings_mock
        mock_db_instance = MagicMock()

        # Act
        from app.workflows.customer_service import create_customer_service_workflow

        workflow = create_customer_service_workflow(mock_db_instance)

        # Assert
        assert workflow.name == "Smart Customer Service"
        assert len(workflow.steps) == 3


@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"), reason="需要 OPENROUTER_API_KEY 环境变量"
)
class TestCustomerServiceE2E:
    """端到端测试（需要真实 API Key）"""

    @pytest.mark.asyncio
    async def test_billing_query(self):
        # 此测试需要真实 API Key，仅在 E2E 测试时运行
        pass
