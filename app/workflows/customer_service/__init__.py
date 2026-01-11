"""
Smart Customer Service Workflow 模块

展示 Agno Workflow 条件分支和知识库 RAG 的最佳实践。
"""

from app.workflows.customer_service.schemas import (
    ClassificationResult,
    CustomerQuery,
    QueryCategory,
    RetrievalResult,
    ServiceResponse,
)
from app.workflows.customer_service.workflow import create_customer_service_workflow

__all__ = [
    "create_customer_service_workflow",
    "CustomerQuery",
    "QueryCategory",
    "ClassificationResult",
    "RetrievalResult",
    "ServiceResponse",
]
