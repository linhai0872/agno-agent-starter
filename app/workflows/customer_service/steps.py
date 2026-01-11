"""
Customer Service Workflow 步骤定义

包含分类、RAG 检索和响应生成步骤。
"""

import logging
from typing import TYPE_CHECKING

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.workflow.step import Step

from app.config import get_settings
from app.workflows.customer_service.schemas import (
    ClassificationResult,
    QueryCategory,
    ServiceResponse,
)

if TYPE_CHECKING:
    from agno.workflow.step import StepInput

logger = logging.getLogger(__name__)


def create_classifier_step() -> Step:
    """
    创建分类步骤

    使用 Agent 实现问题分类，返回 ClassificationResult
    """
    settings = get_settings()

    classifier_agent = Agent(
        name="Query Classifier",
        role="将客户问题分类为 billing、technical、general 或 other",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        instructions="""\
你是客服问题分类专家。分析用户问题并确定类别：

- **billing**: 账单、付款、订阅、退款、费用相关
- **technical**: 技术问题、故障、错误、使用方法、配置
- **general**: 一般咨询、产品信息、功能介绍
- **other**: 无法归入上述类别

返回分类结果，包含分类、置信度（0-1）和理由。
""",
        output_schema=ClassificationResult,
        use_json_mode=True,
        markdown=False,
    )

    return Step(
        name="classify_query",
        description="分类客户问题",
        agent=classifier_agent,
    )


def route_to_knowledge_base(step_input: "StepInput") -> bool:
    """
    条件评估器：决定是否需要查询知识库

    Args:
        step_input: 上一步的输出

    Returns:
        True 如果需要查询知识库
    """
    try:
        content = step_input.previous_step_content
        if isinstance(content, ClassificationResult):
            category = content.category
        elif isinstance(content, dict):
            category = content.get("category", "other")
        else:
            category = "other"

        return category in [
            QueryCategory.BILLING.value,
            QueryCategory.TECHNICAL.value,
            QueryCategory.GENERAL.value,
            "billing",
            "technical",
            "general",
        ]
    except Exception as e:
        logger.warning("路由评估失败: %s，默认查询知识库", e)
        return True


def create_rag_step(db_url: str) -> Step:
    """
    创建 RAG 检索步骤

    从知识库检索相关信息

    Args:
        db_url: 数据库连接 URL
    """
    settings = get_settings()

    try:
        from agno.knowledge.knowledge import Knowledge
        from agno.vectordb.pgvector import PgVector, SearchType

        knowledge_base = Knowledge(
            name="Customer Service Knowledge Base",
            description="客服知识库，包含账单、技术和常见问题解答",
            vector_db=PgVector(
                table_name="customer_service_kb",
                db_url=db_url,
                search_type=SearchType.hybrid,
            ),
        )

        rag_agent = Agent(
            name="Knowledge Retriever",
            role="从知识库检索相关信息",
            model=OpenRouter(
                id=settings.model_name,
                api_key=settings.openrouter_api_key,
            ),
            instructions="""\
你是知识库检索专家。根据用户问题：
1. 从知识库搜索相关信息
2. 整理最相关的答案
3. 如果未找到相关信息，明确说明

不要编造信息，只基于知识库内容回答。
""",
            knowledge=knowledge_base,
            search_knowledge=True,
            markdown=True,
        )
    except ImportError:
        logger.warning("PgVector 未安装，使用无知识库的 Agent")
        rag_agent = Agent(
            name="Knowledge Retriever",
            role="回答客户问题",
            model=OpenRouter(
                id=settings.model_name,
                api_key=settings.openrouter_api_key,
            ),
            instructions="基于上下文回答客户问题。如果无法回答，建议联系人工客服。",
            markdown=True,
        )

    return Step(
        name="retrieve_knowledge",
        description="从知识库检索相关信息",
        agent=rag_agent,
    )


def create_respond_step() -> Step:
    """
    创建响应生成步骤

    基于 RAG 结果生成最终回复
    """
    settings = get_settings()

    respond_agent = Agent(
        name="Response Generator",
        role="生成客户服务回复",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        instructions="""\
你是专业客服代表。基于前面步骤的信息生成回复：

1. 使用友好专业的语气
2. 提供清晰具体的解答
3. 如果信息不足，建议联系人工客服
4. 包含后续步骤（如有需要）

回复格式：
- 简短问候
- 直接回答问题
- 提供下一步建议（如需要）
""",
        output_schema=ServiceResponse,
        use_json_mode=True,
        markdown=False,
    )

    return Step(
        name="generate_response",
        description="生成客服回复",
        agent=respond_agent,
    )
