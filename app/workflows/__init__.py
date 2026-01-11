"""
Workflow 注册入口

统一管理所有 Workflow 的创建和注册。
Workflow 用于需要严格步骤控制、条件分支的场景。
"""

from agno.db.postgres import PostgresDb
from agno.workflow import Workflow


def get_all_workflows(db: PostgresDb) -> list[Workflow]:
    """
    获取所有 Workflow 实例

    Args:
        db: PostgreSQL 数据库连接

    Returns:
        Workflow 实例列表
    """
    workflows = []

    # ============== 经典模板 Workflow ==============
    from app.workflows.customer_service import create_customer_service_workflow

    workflows.append(create_customer_service_workflow(db))

    # ============== 添加你的 Workflow ==============
    # from app.workflows.your_workflow.workflow import create_your_workflow
    # workflows.append(create_your_workflow(db))

    return workflows


__all__ = ["get_all_workflows"]
