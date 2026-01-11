"""
内容生成工作流 - Content Pipeline

展示 Workflow 模式的完整功能：多步骤、条件分支、结构化输出。
"""

from app.workflows.content_pipeline.schemas import ArticleOutput, FactCheckItem
from app.workflows.content_pipeline.workflow import create_content_pipeline

__all__ = [
    "create_content_pipeline",
    "ArticleOutput",
    "FactCheckItem",
]
