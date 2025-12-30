"""
Workflow 注册入口

统一管理所有 Workflow 的创建和注册。
Workflow 用于需要严格步骤控制、条件分支的场景。
"""

from typing import List

from agno.db.postgres import PostgresDb
from agno.workflow import Workflow


def get_all_workflows(db: PostgresDb) -> List[Workflow]:
    """
    获取所有 Workflow 实例

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        Workflow 实例列表
    """
    workflows = []

    # Content Pipeline (示例 - 取消注释以启用)
    # from app.workflows.content_pipeline.workflow import create_content_pipeline
    # workflows.append(create_content_pipeline(db))

    # 在此添加更多 Workflow...

    return workflows


__all__ = ["get_all_workflows"]

