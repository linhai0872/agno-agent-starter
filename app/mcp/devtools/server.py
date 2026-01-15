"""
Agno DevTools MCP Server Entry Point.

Provides MCP tools for AI agents to test and debug Agno applications.

Usage:
    # Run with stdio transport (default, for IDE integration)
    python -m app.mcp.devtools.server

    # Test with MCP Inspector
    npx @anthropic-ai/mcp-inspector python -m app.mcp.devtools.server

Environment Variables:
    MCP_DEVTOOLS_API_URL: Agno REST API URL (default: http://127.0.0.1:7777)
    MCP_DEVTOOLS_DB_URL: PostgreSQL URL (default: postgresql+psycopg://ai:ai@localhost:5532/ai)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from psycopg_pool import AsyncConnectionPool

from app.mcp.devtools.config import get_config
from app.mcp.devtools.tools import (
    AppType,
    DetailLevel,
    RunResult,
    SessionsResult,
    agno_list,
    agno_run,
    agno_sessions,
    agno_trace,
)


class DevToolsContext:
    """Shared context for DevTools MCP server."""

    def __init__(self, http_client: httpx.AsyncClient, db_pool: AsyncConnectionPool):
        self.http_client = http_client
        self.db_pool = db_pool


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[DevToolsContext]:
    """
    Manage HTTP client and database connection pool lifecycle.

    Initializes resources on startup, yields context, and cleans up on shutdown.
    """
    import re

    config = get_config()

    # Normalize various PostgreSQL URL formats to psycopg-compatible format
    # Handles: postgresql+psycopg://, postgresql+asyncpg://, postgres://, postgresql://
    db_url = re.sub(r"^postgres(ql)?(\+\w+)?://", "postgresql://", config.db_url)

    http_client = httpx.AsyncClient(base_url=config.api_url)
    db_pool = AsyncConnectionPool(conninfo=db_url, min_size=1, max_size=config.db_pool_size)

    try:
        await db_pool.open()
        yield DevToolsContext(http_client=http_client, db_pool=db_pool)
    finally:
        await http_client.aclose()
        await db_pool.close()


mcp = FastMCP(
    name="agno-devtools",
    instructions=(
        "Agno DevTools provides tools to test and debug Agno applications. "
        "Use agno_list to discover available apps, agno_run to execute them, "
        "and agno_trace to check execution status and results. "
        "For long-running workflows, poll agno_trace until status is COMPLETED."
    ),
    lifespan=app_lifespan,
)


@mcp.tool
async def agno_list_tool(
    app_type: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """
    List registered Agno applications (agents, teams, workflows).

    Args:
        app_type: Optional filter - 'agent', 'team', or 'workflow'

    Returns:
        Dict with agents, teams, workflows arrays
    """
    devtools_ctx: DevToolsContext = ctx.request_context.lifespan_context

    type_filter = AppType(app_type) if app_type else None
    result = await agno_list(devtools_ctx.http_client, type_filter)
    return result.model_dump(exclude_none=True)


@mcp.tool
async def agno_run_tool(
    app_type: str,
    app_id: str,
    message: str,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """
    Run an Agno application (async mode).

    Does NOT wait for completion. Returns session_id immediately.
    Use agno_trace to poll for status and results.

    Args:
        app_type: Application type - 'agent', 'team', or 'workflow'
        app_id: Application identifier (e.g., 'customer-service')
        message: Input message (JSON string for structured input)

    Returns:
        Dict with session_id and status="SUBMITTED", or error
    """
    devtools_ctx: DevToolsContext = ctx.request_context.lifespan_context
    config = get_config()

    try:
        type_enum = AppType(app_type)
    except ValueError:
        return RunResult(status="ERROR", error=f"Invalid app_type: {app_type}").model_dump(
            exclude_none=True
        )

    result = await agno_run(
        devtools_ctx.http_client,
        type_enum,
        app_id,
        message,
        timeout=config.http_timeout,
    )
    return result.model_dump(exclude_none=True)


@mcp.tool
async def agno_trace_tool(
    session_id: str,
    detail_level: str = "summary",
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """
    Query session trace and execution details.

    Use this to check if a run is complete and get results.
    Poll until status is COMPLETED or FAILED.

    Args:
        session_id: Session identifier from agno_run
        detail_level: Amount of detail - 'summary', 'metrics', 'steps', 'content', 'full'

    Returns:
        Dict with status (RUNNING/COMPLETED/FAILED), metrics, steps, content
    """
    devtools_ctx: DevToolsContext = ctx.request_context.lifespan_context

    try:
        level = DetailLevel(detail_level)
    except ValueError:
        level = DetailLevel.SUMMARY

    result = await agno_trace(devtools_ctx.db_pool, session_id, level)
    return result.model_dump(exclude_none=True)


@mcp.tool
async def agno_sessions_tool(
    app_type: str | None = None,
    app_id: str | None = None,
    limit: int = 10,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """
    List historical sessions.

    Args:
        app_type: Optional filter - 'agent', 'team', or 'workflow'
        app_id: Optional filter by application ID
        limit: Maximum sessions to return (default 10)

    Returns:
        Dict with sessions array
    """
    devtools_ctx: DevToolsContext = ctx.request_context.lifespan_context

    type_filter = None
    if app_type:
        try:
            type_filter = AppType(app_type)
        except ValueError:
            return SessionsResult(error=f"Invalid app_type: {app_type}").model_dump(
                exclude_none=True
            )

    result = await agno_sessions(devtools_ctx.db_pool, type_filter, app_id, limit)
    return result.model_dump(exclude_none=True)


if __name__ == "__main__":
    mcp.run()
