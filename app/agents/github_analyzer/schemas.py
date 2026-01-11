"""
GitHub 仓库分析输出 Schema

定义 Agent 结构化输出的 Pydantic Model。
"""

from pydantic import BaseModel, Field


class GitHubRepoAnalysis(BaseModel):
    """GitHub 仓库分析结果"""

    repo_name: str = Field(
        ...,
        description="仓库名称，格式为 owner/repo",
    )

    description: str = Field(
        ...,
        description="仓库描述，简洁概括仓库用途",
    )

    tech_stack: list[str] = Field(
        default_factory=list,
        description="主要技术栈，如 Python、TypeScript、React 等",
    )

    stars: int = Field(
        default=0,
        description="Star 数量",
    )

    forks: int = Field(
        default=0,
        description="Fork 数量",
    )

    contributors: int = Field(
        default=0,
        description="贡献者数量",
    )

    activity_level: str = Field(
        default="unknown",
        description="活跃度：active（活跃）、moderate（中等）、low（较低）、inactive（不活跃）",
    )

    key_features: list[str] = Field(
        default_factory=list,
        description="核心功能特性，3-5 条",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="使用建议或注意事项，1-3 条",
    )
