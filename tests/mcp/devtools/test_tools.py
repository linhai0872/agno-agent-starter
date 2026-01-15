"""
Unit tests for Agno DevTools MCP tools.

Tests use mocked httpx and psycopg to verify tool behavior without real connections.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.mcp.devtools.tools import (
    AppType,
    DetailLevel,
    SessionStatus,
    agno_list,
    agno_run,
    agno_sessions,
    agno_trace,
)


class TestAgnoList:
    """Tests for agno_list tool."""

    @pytest.mark.asyncio
    async def test_list_all_types_success(self):
        # Arrange
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(
            side_effect=[
                MagicMock(
                    json=lambda: [{"id": "agent-1", "name": "Test Agent"}],
                    raise_for_status=lambda: None,
                ),
                MagicMock(
                    json=lambda: [{"id": "team-1", "name": "Test Team"}],
                    raise_for_status=lambda: None,
                ),
                MagicMock(
                    json=lambda: [{"id": "wf-1", "name": "Test Workflow"}],
                    raise_for_status=lambda: None,
                ),
            ]
        )

        # Act
        result = await agno_list(mock_client)

        # Assert
        assert len(result.agents) == 1
        assert result.agents[0]["id"] == "agent-1"
        assert len(result.teams) == 1
        assert len(result.workflows) == 1
        assert result.error is None

    @pytest.mark.asyncio
    async def test_list_single_type(self):
        # Arrange
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(
            return_value=MagicMock(
                json=lambda: [{"id": "wf-1", "name": "My Workflow"}],
                raise_for_status=lambda: None,
            )
        )

        # Act
        result = await agno_list(mock_client, AppType.WORKFLOW)

        # Assert
        assert len(result.workflows) == 1
        assert result.workflows[0]["id"] == "wf-1"
        assert result.agents == []
        assert result.teams == []

    @pytest.mark.asyncio
    async def test_list_timeout_error(self):
        # Arrange
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        # Act
        result = await agno_list(mock_client, AppType.AGENT)

        # Assert
        assert result.error is not None
        assert "Timeout" in result.error


class TestAgnoRun:
    """Tests for agno_run tool."""

    @pytest.mark.asyncio
    async def test_run_success(self):
        # Arrange
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(
            return_value=MagicMock(
                json=lambda: {"session_id": "sess-123", "status": "completed"},
                raise_for_status=lambda: None,
            )
        )

        # Act
        result = await agno_run(
            mock_client,
            AppType.WORKFLOW,
            "customer-service",
            '{"input": "test"}',
        )

        # Assert
        assert result.session_id == "sess-123"
        assert result.status == "SUBMITTED"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_not_found(self):
        # Arrange
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.status_code = 404
        response.text = "Not found"
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("404", request=None, response=response)
        )

        # Act
        result = await agno_run(
            mock_client,
            AppType.WORKFLOW,
            "invalid-id",
            "{}",
        )

        # Assert
        assert result.status == "ERROR"
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_timeout(self):
        # Arrange
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        # Act
        result = await agno_run(
            mock_client,
            AppType.AGENT,
            "test-agent",
            "{}",
            timeout=5.0,
        )

        # Assert
        assert result.status == "ERROR"
        assert "timeout" in result.error.lower()


class TestAgnoTrace:
    """Tests for agno_trace tool."""

    @pytest.mark.asyncio
    async def test_trace_completed_session(self):
        # Arrange
        runs_data = [
            {
                "status": "completed",
                "metrics": {"duration": 10.5, "total_tokens": 1000},
                "step_results": [{"step_name": "step1", "status": "completed"}],
                "content": "Final output",
            }
        ]

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(runs_data,))
        mock_conn.cursor = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_cursor), __aexit__=AsyncMock()
            )
        )
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()
            )
        )

        # Act
        result = await agno_trace(mock_pool, "sess-123", DetailLevel.SUMMARY)

        # Assert
        assert result.status == SessionStatus.COMPLETED
        assert result.metrics is not None
        assert result.steps is not None

    @pytest.mark.asyncio
    async def test_trace_not_found(self):
        # Arrange
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn.cursor = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_cursor), __aexit__=AsyncMock()
            )
        )
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()
            )
        )

        # Act
        result = await agno_trace(mock_pool, "invalid-sess")

        # Assert
        assert result.status == SessionStatus.NOT_FOUND
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_trace_running_session(self):
        # Arrange
        runs_data = [{"run_id": "run-1"}]

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(runs_data,))
        mock_conn.cursor = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_cursor), __aexit__=AsyncMock()
            )
        )
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()
            )
        )

        # Act
        result = await agno_trace(mock_pool, "sess-456")

        # Assert
        assert result.status == SessionStatus.RUNNING


class TestAgnoSessions:
    """Tests for agno_sessions tool."""

    @pytest.mark.asyncio
    async def test_sessions_list_all(self):
        # Arrange
        rows = [
            ("sess-1", "wf-1", "workflow", "2026-01-12 10:00:00+00"),
            ("sess-2", "agent-1", "agent", "2026-01-12 09:00:00+00"),
        ]

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=rows)
        mock_conn.cursor = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_cursor), __aexit__=AsyncMock()
            )
        )
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()
            )
        )

        # Act
        result = await agno_sessions(mock_pool)

        # Assert
        assert len(result.sessions) == 2
        assert result.sessions[0].session_id == "sess-1"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_sessions_filter_by_type(self):
        # Arrange
        rows = [("sess-1", "wf-1", "workflow", "2026-01-12 10:00:00+00")]

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=rows)
        mock_cursor.execute = AsyncMock()
        mock_conn.cursor = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_cursor), __aexit__=AsyncMock()
            )
        )
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()
            )
        )

        # Act
        result = await agno_sessions(mock_pool, AppType.WORKFLOW)

        # Assert
        assert len(result.sessions) == 1
        assert result.sessions[0].app_type == "workflow"

    @pytest.mark.asyncio
    async def test_sessions_db_error(self):
        # Arrange
        mock_pool = MagicMock()
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(side_effect=Exception("Connection failed")),
                __aexit__=AsyncMock(),
            )
        )

        # Act
        result = await agno_sessions(mock_pool)

        # Assert
        assert result.error is not None
        assert "connection failed" in result.error.lower()
