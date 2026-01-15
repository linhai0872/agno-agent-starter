"""
Agno DevTools MCP Server - Tool Implementations.

Provides 4 MCP tools for AI agents to test and debug Agno applications:
    - agno_list: List registered agents, teams, and workflows
    - agno_run: Run an application (async, returns session_id immediately)
    - agno_trace: Query session trace and execution details
    - agno_sessions: List historical sessions
"""

from enum import Enum
from typing import Any, Literal

import httpx
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field


class AppType(str, Enum):
    """Agno application types."""

    AGENT = "agent"
    TEAM = "team"
    WORKFLOW = "workflow"


class DetailLevel(str, Enum):
    """Trace detail levels."""

    SUMMARY = "summary"
    METRICS = "metrics"
    STEPS = "steps"
    CONTENT = "content"
    FULL = "full"


class SessionStatus(str, Enum):
    """Session execution status."""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NOT_FOUND = "NOT_FOUND"


class RunResult(BaseModel):
    """Result from agno_run tool."""

    session_id: str | None = None
    status: Literal["SUBMITTED", "ERROR"] = "SUBMITTED"
    error: str | None = None


class TraceResult(BaseModel):
    """Result from agno_trace tool."""

    session_id: str
    status: SessionStatus
    metrics: dict[str, Any] | None = None
    steps: list[dict[str, Any]] | None = None
    content: str | None = None
    error: str | None = None


class ListResult(BaseModel):
    """Result from agno_list tool."""

    agents: list[dict[str, str]] = Field(default_factory=list)
    teams: list[dict[str, str]] = Field(default_factory=list)
    workflows: list[dict[str, str]] = Field(default_factory=list)
    error: str | None = None


class SessionInfo(BaseModel):
    """Session information for agno_sessions tool."""

    session_id: str
    app_id: str
    app_type: str
    created_at: str


class SessionsResult(BaseModel):
    """Result from agno_sessions tool."""

    sessions: list[SessionInfo] = Field(default_factory=list)
    error: str | None = None


async def agno_list(
    http_client: httpx.AsyncClient,
    app_type: AppType | None = None,
) -> ListResult:
    """
    List registered Agno applications.

    Args:
        http_client: Async HTTP client for API calls
        app_type: Optional filter by application type

    Returns:
        ListResult with agents, teams, and workflows
    """
    result = ListResult()

    types_to_fetch = [app_type] if app_type else [AppType.AGENT, AppType.TEAM, AppType.WORKFLOW]

    for t in types_to_fetch:
        endpoint = f"/{t.value}s"
        try:
            response = await http_client.get(endpoint, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            items = [{"id": item.get("id", ""), "name": item.get("name", "")} for item in data]

            if t == AppType.AGENT:
                result.agents = items
            elif t == AppType.TEAM:
                result.teams = items
            elif t == AppType.WORKFLOW:
                result.workflows = items

        except httpx.TimeoutException:
            result.error = f"Timeout fetching {t.value}s"
        except httpx.HTTPStatusError as e:
            result.error = f"HTTP error fetching {t.value}s: {e.response.status_code}"
        except Exception as e:
            result.error = f"Error fetching {t.value}s: {e!s}"

    return result


async def agno_run(
    http_client: httpx.AsyncClient,
    app_type: AppType,
    app_id: str,
    message: str,
    timeout: float = 30.0,
) -> RunResult:
    """
    Run an Agno application (async mode).

    Does NOT wait for completion. Returns session_id immediately.
    Use agno_trace to poll for status and results.

    Args:
        http_client: Async HTTP client for API calls
        app_type: Application type (agent, team, workflow)
        app_id: Application identifier
        message: Input message (JSON string for structured input)
        timeout: Request timeout in seconds (default 30s for cold start)

    Returns:
        RunResult with session_id or error
    """
    endpoint = f"/{app_type.value}s/{app_id}/runs"

    try:
        response = await http_client.post(
            endpoint,
            data={"message": message, "stream": "false"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()

        session_id = data.get("session_id")
        if not session_id:
            return RunResult(status="ERROR", error="No session_id in response")

        return RunResult(session_id=session_id, status="SUBMITTED")

    except httpx.TimeoutException:
        return RunResult(
            status="ERROR",
            error=f"Request timeout after {timeout}s. The application may still be running.",
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return RunResult(
                status="ERROR",
                error=f"{app_type.value.capitalize()} not found: {app_id}",
            )
        return RunResult(status="ERROR", error=f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        return RunResult(status="ERROR", error=f"Request failed: {e!s}")


async def agno_trace(
    db_pool: AsyncConnectionPool,
    session_id: str,
    detail_level: DetailLevel = DetailLevel.SUMMARY,
) -> TraceResult:
    """
    Query session trace and execution details.

    Args:
        db_pool: Async database connection pool
        session_id: Session identifier to query
        detail_level: Amount of detail to return

    Returns:
        TraceResult with status, metrics, steps, and/or content
    """
    query = """
        SELECT runs
        FROM ai.agno_sessions
        WHERE session_id = %s
    """

    try:
        async with db_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(query, (session_id,))
            row = await cur.fetchone()

            if not row or not row[0]:
                return TraceResult(
                    session_id=session_id,
                    status=SessionStatus.NOT_FOUND,
                    error=f"Session not found: {session_id}",
                )

            runs = row[0]
            return _parse_trace_result(session_id, runs, detail_level)

    except Exception as e:
        return TraceResult(
            session_id=session_id,
            status=SessionStatus.FAILED,
            error=f"Database connection failed: {e!s}",
        )


def _parse_trace_result(
    session_id: str,
    runs: list[dict[str, Any]],
    detail_level: DetailLevel,
) -> TraceResult:
    """Parse runs JSONB into TraceResult based on detail level."""
    if not runs:
        return TraceResult(session_id=session_id, status=SessionStatus.RUNNING)

    run = runs[0]

    status = _determine_status(run)
    result = TraceResult(session_id=session_id, status=status)

    if detail_level == DetailLevel.FULL:
        result.metrics = run.get("metrics")
        result.steps = run.get("step_results") or run.get("messages")
        result.content = run.get("content")
        return result

    if detail_level in (DetailLevel.SUMMARY, DetailLevel.METRICS, DetailLevel.FULL):
        metrics = run.get("metrics")
        if metrics:
            result.metrics = {
                "duration": metrics.get("duration"),
                "total_tokens": metrics.get("total_tokens"),
                "cost": metrics.get("cost"),
            }
            result.metrics = {k: v for k, v in (result.metrics or {}).items() if v is not None}

    if detail_level in (DetailLevel.SUMMARY, DetailLevel.STEPS, DetailLevel.FULL):
        step_results = run.get("step_results")
        if step_results:
            result.steps = [
                {"step": s.get("step_name"), "status": s.get("status")} for s in step_results
            ]
        else:
            messages = run.get("messages")
            if messages:
                result.steps = [{"info": f"Agent: {len(messages)} messages"}]

    if detail_level in (DetailLevel.CONTENT, DetailLevel.FULL):
        result.content = run.get("content")

    return result


def _determine_status(run: dict[str, Any]) -> SessionStatus:
    """
    Determine session status from run data.

    Rules:
        - COMPLETED: run.status == "completed" OR run has content
        - FAILED: run.status == "failed" OR run contains error
        - RUNNING: otherwise
    """
    run_status = run.get("status", "").lower()

    if run_status == "completed" or run.get("content"):
        return SessionStatus.COMPLETED

    if run_status == "failed" or run.get("error"):
        return SessionStatus.FAILED

    return SessionStatus.RUNNING


async def agno_sessions(
    db_pool: AsyncConnectionPool,
    app_type: AppType | None = None,
    app_id: str | None = None,
    limit: int = 10,
) -> SessionsResult:
    """
    List historical sessions.

    Args:
        db_pool: Async database connection pool
        app_type: Optional filter by application type
        app_id: Optional filter by application ID
        limit: Maximum number of sessions to return

    Returns:
        SessionsResult with session list
    """
    where_clauses = []
    params: list[Any] = []

    if app_type and app_id:
        column = f"{app_type.value}_id"
        where_clauses.append(f"{column} = %s")
        params.append(app_id)
    elif app_type:
        column = f"{app_type.value}_id"
        where_clauses.append(f"{column} IS NOT NULL")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT
            session_id,
            COALESCE(agent_id, team_id, workflow_id) AS app_id,
            session_type,
            to_timestamp(created_at)::text AS created
        FROM ai.agno_sessions
        {where_sql}
        ORDER BY created_at DESC
        LIMIT %s
    """
    params.append(limit)

    try:
        async with db_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()

            sessions = [
                SessionInfo(
                    session_id=row[0],
                    app_id=row[1] or "",
                    app_type=row[2] or "",
                    created_at=row[3] or "",
                )
                for row in rows
            ]

            return SessionsResult(sessions=sessions)

    except Exception as e:
        return SessionsResult(error=f"Database connection failed: {e!s}")
