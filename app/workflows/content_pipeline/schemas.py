"""
内容生成工作流 - 数据结构定义
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class FactCheckItem(BaseModel):
    """事实核查项"""
    
    claim: str = Field(..., description="待核查的声明")
    verified: bool = Field(..., description="是否验证通过")
    source: Optional[str] = Field(None, description="验证来源")
    note: Optional[str] = Field(None, description="备注")


class ArticleOutput(BaseModel):
    """文章输出结构"""
    
    title: str = Field(..., description="文章标题")
    summary: str = Field(..., description="摘要")
    content: str = Field(..., description="正文内容")
    key_points: List[str] = Field(default_factory=list, description="要点列表")
    sources: List[str] = Field(default_factory=list, description="参考来源")
    word_count: int = Field(..., description="字数统计")

