"""
Smart Customer Service Workflow

展示 Agno Workflow 条件分支和知识库 RAG 的最佳实践。

使用示例:
    from agno.db.postgres import PostgresDb
    from app.workflows.customer_service import create_customer_service_workflow

    db = PostgresDb(db_url="...")
    workflow = create_customer_service_workflow(db)

    response = workflow.run("如何查看我的账单？")
    print(response.content)
"""

import logging

from agno.db.postgres import PostgresDb
from agno.workflow import Condition, Workflow

from app.config import get_settings
from app.workflows.customer_service.steps import (
    create_classifier_step,
    create_rag_step,
    create_respond_step,
    route_to_knowledge_base,
)

logger = logging.getLogger(__name__)


def create_customer_service_workflow(db: PostgresDb) -> Workflow:
    """
    创建智能客服 Workflow

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        配置好的 Workflow 实例

    特性:
        - 问题分类: Agent 工具调用模式
        - 条件路由: 根据分类决定是否查询知识库
        - 知识库 RAG: PgVector 混合搜索
        - 结构化输出: ServiceResponse Schema
    """
    settings = get_settings()

    classify_step = create_classifier_step()
    rag_step = create_rag_step(settings.database_url)
    respond_step = create_respond_step()

    workflow = Workflow(
        name="Smart Customer Service",
        description="智能客服工作流：分类 -> 知识库检索 -> 响应生成",
        db=db,
        steps=[
            classify_step,
            Condition(
                name="route_by_category",
                description="根据分类决定是否查询知识库",
                evaluator=route_to_knowledge_base,
                steps=[rag_step],
            ),
            respond_step,
        ],
    )

    return workflow
