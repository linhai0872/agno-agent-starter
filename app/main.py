"""
Agno Agent Service - AgentOS 入口

基于 AgentOS 的高性能智能体编排框架，支持：
- 标准化 Agent/Workflow API
- 会话管理
- 记忆管理
- 知识库管理
- 完整追踪和监控
"""

import logging
from pathlib import Path

from agno.db.postgres import PostgresDb
from agno.os import AgentOS

from app.config import get_settings
from app.agents import get_all_agents
from app.teams import get_all_teams
from app.workflows import get_all_workflows

logger = logging.getLogger(__name__)


def setup_tracing(settings) -> None:
    """配置 OpenTelemetry Tracing"""
    if not settings.enable_tracing:
        return
    
    try:
        from agno.tracing import setup_tracing as agno_setup_tracing
        
        tracing_db_url = settings.tracing_db_url or settings.database_url
        tracing_db = PostgresDb(
            id="agno-tracing-db",
            db_url=tracing_db_url,
        )
        
        agno_setup_tracing(
            db=tracing_db,
            max_export_batch_size=settings.tracing_batch_size,
        )
        
        logger.info("Tracing enabled with batch_size=%d", settings.tracing_batch_size)
    except ImportError:
        logger.warning("agno.tracing not available. Tracing disabled.")
    except Exception as e:
        logger.error("Failed to setup tracing: %s", str(e))


def create_app():
    """创建 AgentOS 应用"""
    settings = get_settings()

    # 配置日志级别
    log_level = logging.DEBUG if settings.debug_mode else logging.INFO
    logging.basicConfig(level=log_level)

    # 配置 Tracing
    setup_tracing(settings)

    # 配置文件路径
    config_path = Path(__file__).parent.parent / "configuration.yaml"

    # 数据库连接
    db = PostgresDb(
        id="agno-agent-db",
        db_url=settings.database_url,
    )

    # 获取所有组件
    agents = get_all_agents(db)
    teams = get_all_teams(db)
    workflows = get_all_workflows(db)

    # 构建 AgentOS 参数
    os_kwargs = {
        "id": "agno-agent-starter",
        "name": "Agno Agent Service",
        "description": "高性能智能体编排框架，支持实体验证、信息丰富等业务场景",
        "agents": agents,
        "teams": teams,
        "workflows": workflows,
    }
    
    if config_path.exists():
        os_kwargs["config"] = str(config_path)
    
    # MCP Server 配置
    if settings.enable_mcp_server:
        os_kwargs["enable_mcp_server"] = True
        logger.info("MCP Server enabled")

    # 创建 AgentOS
    agent_os = AgentOS(**os_kwargs)

    return agent_os


# 创建 AgentOS 实例
agent_os = create_app()

# 获取 FastAPI 应用
app = agent_os.get_app()


if __name__ == "__main__":
    settings = get_settings()

    agent_os.serve(
        app="app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=1 if settings.debug_mode else settings.workers,
        reload=settings.debug_mode,
    )
