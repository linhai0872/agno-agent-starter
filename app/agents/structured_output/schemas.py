"""
Structured Output Schema 定义

使用 Pydantic BaseModel 定义结构化输出格式。
Agno Agent 会确保输出严格符合 Schema 定义。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class MovieScript(BaseModel):
    """
    电影剧本结构化输出 - 官方示例
    
    展示完整的 Pydantic Schema 定义最佳实践：
    - 使用 Field 提供详细描述
    - 使用类型注解确保类型安全
    - 使用 Optional 标记可选字段
    """
    
    name: str = Field(
        ...,
        description="电影标题，应具有吸引力和记忆点",
    )
    
    genre: str = Field(
        ...,
        description="电影类型，如'科幻惊悚'、'浪漫喜剧'、'动作冒险'等",
    )
    
    setting: str = Field(
        ...,
        description="故事发生的地点和时代背景，包含氛围描述",
    )
    
    characters: List[str] = Field(
        ...,
        description="4-6个主要角色，格式：'角色名 - 简要描述'",
    )
    
    storyline: str = Field(
        ...,
        description="三句话剧情概要：背景设定、核心冲突、故事走向",
    )
    
    ending: str = Field(
        ...,
        description="电影结局，应与故事线呼应并带来情感冲击",
    )


class ResearchReport(BaseModel):
    """
    研究报告结构化输出
    
    适用于知识检索、信息整理等场景。
    """
    
    title: str = Field(
        ...,
        description="报告标题",
    )
    
    summary: str = Field(
        ...,
        description="执行摘要，200字以内",
    )
    
    key_findings: List[str] = Field(
        default_factory=list,
        description="核心发现列表，每项一句话",
    )
    
    analysis: str = Field(
        ...,
        description="详细分析内容",
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="建议措施列表",
    )
    
    sources: List[str] = Field(
        default_factory=list,
        description="参考来源列表",
    )
    
    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="分析置信度，0-1之间",
    )


class EntityInfo(BaseModel):
    """
    实体信息结构化输出
    
    适用于实体验证、信息抽取等场景。
    """
    
    name: str = Field(
        ...,
        description="实体名称",
    )
    
    type: str = Field(
        ...,
        description="实体类型：person/company/organization/location/product",
    )
    
    description: str = Field(
        default="",
        description="实体简要描述",
    )
    
    attributes: dict = Field(
        default_factory=dict,
        description="实体属性键值对",
    )
    
    verified: bool = Field(
        default=False,
        description="是否已验证",
    )
    
    sources: List[str] = Field(
        default_factory=list,
        description="信息来源",
    )

