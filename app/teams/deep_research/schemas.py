"""
Deep Research Team 输出 Schema

定义研究报告的结构化输出格式。
"""

from pydantic import BaseModel, Field


class ResearchFinding(BaseModel):
    """单条研究发现"""

    topic: str = Field(
        ...,
        description="发现相关的子主题",
    )

    summary: str = Field(
        ...,
        description="发现的核心内容，一句话概括",
    )

    details: str = Field(
        ...,
        description="详细说明，包含具体数据或引用",
    )

    confidence: str = Field(
        default="medium",
        description="可信度: high（多源验证）、medium（单一可靠来源）、low（需进一步验证）",
    )


class ResearchSource(BaseModel):
    """研究来源"""

    title: str = Field(
        ...,
        description="来源标题",
    )

    url: str = Field(
        default="",
        description="来源 URL（如有）",
    )

    type: str = Field(
        default="web",
        description="来源类型: web、paper、report、news",
    )


class ResearchReport(BaseModel):
    """完整研究报告"""

    topic: str = Field(
        ...,
        description="研究主题",
    )

    executive_summary: str = Field(
        ...,
        description="执行摘要，200-300 字概括全文核心观点",
    )

    findings: list[ResearchFinding] = Field(
        default_factory=list,
        description="研究发现列表，3-7 条",
    )

    sources: list[ResearchSource] = Field(
        default_factory=list,
        description="参考来源列表",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="行动建议，1-3 条",
    )

    limitations: list[str] = Field(
        default_factory=list,
        description="研究局限性或不确定性，1-3 条",
    )
