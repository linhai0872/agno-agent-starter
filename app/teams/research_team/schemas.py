"""
研究团队 - 数据结构定义
"""

from typing import List

from pydantic import BaseModel, Field


class ResearchFinding(BaseModel):
    """研究发现"""
    
    topic: str = Field(..., description="研究主题")
    summary: str = Field(..., description="发现摘要")
    sources: List[str] = Field(default_factory=list, description="信息来源")
    confidence: float = Field(..., ge=0, le=1, description="置信度")


class ResearchReport(BaseModel):
    """研究报告"""
    
    title: str = Field(..., description="报告标题")
    abstract: str = Field(..., description="摘要")
    findings: List[ResearchFinding] = Field(
        default_factory=list,
        description="研究发现列表"
    )
    conclusion: str = Field(..., description="结论")
    recommendations: List[str] = Field(
        default_factory=list,
        description="建议"
    )

