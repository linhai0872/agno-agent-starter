"""
Customer Service Workflow Schemas

定义客服工作流的输入输出格式。
"""

from enum import Enum

from pydantic import BaseModel, Field


class QueryCategory(str, Enum):
    """问题分类"""

    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"
    OTHER = "other"


class CustomerQuery(BaseModel):
    """客户查询输入"""

    message: str = Field(
        ...,
        description="客户的问题或请求",
    )

    user_id: str = Field(
        default="anonymous",
        description="用户 ID（可选）",
    )

    session_id: str = Field(
        default="",
        description="会话 ID（可选）",
    )


class ClassificationResult(BaseModel):
    """分类结果"""

    category: QueryCategory = Field(
        ...,
        description="问题分类",
    )

    confidence: float = Field(
        default=0.8,
        description="分类置信度 (0-1)",
    )

    reasoning: str = Field(
        default="",
        description="分类理由",
    )


class RetrievalResult(BaseModel):
    """知识库检索结果"""

    found: bool = Field(
        default=False,
        description="是否找到相关信息",
    )

    content: str = Field(
        default="",
        description="检索到的内容",
    )

    sources: list[str] = Field(
        default_factory=list,
        description="来源列表",
    )


class ServiceResponse(BaseModel):
    """客服响应"""

    answer: str = Field(
        ...,
        description="回复内容",
    )

    category: QueryCategory = Field(
        ...,
        description="问题分类",
    )

    confidence: float = Field(
        default=0.8,
        description="回答置信度",
    )

    sources: list[str] = Field(
        default_factory=list,
        description="参考来源",
    )

    requires_human: bool = Field(
        default=False,
        description="是否需要人工介入",
    )
