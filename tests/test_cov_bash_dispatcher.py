"""Tests for bash_dispatcher - 100% coverage target."""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import dataclass

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)


@dataclass
class FakeAgent:
    agent_id: str
    platform: str = "linux"
    hostname: str = "host"
    port: int = 50051
    capabilities: list = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class FakeTaskResult:
    success: bool
    stdout: str = ""
    stderr: str = ""


class TestDispatchTool:
    """Test dispatch_tool function."""

    @pytest.mark.asyncio
    async def test_execute_no_agent_id(self):
        from services.bash_dispatcher import dispatch_tool

        result = await dispatch_tool("execute", {"command": "ls"})
        assert result["success"] is False
        assert "No agent_id" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_no_command(self):
        from services.bash_dispatcher import dispatch_tool

        result = await dispatch_tool("execute", {"agent_id": "localhost"})
        assert result["success"] is False
        assert "No command" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_localhost_discover_peers(self):
        from services.bash_dispatcher import dispatch_tool

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"agents": []}'

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "localhost", "command": "discover-peers"},
            )
        assert result["success"] is True
        assert result["agent_id"] == "localhost"

    @pytest.mark.asyncio
    async def test_execute_localhost_discover_peers_failure(self):
        from services.bash_dispatcher import dispatch_tool

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await dispatch_tool(
                "execute",
                {
                    "agent_id": "localhost",
                    "command": "Invoke-RestMethod discover-peers",
                },
            )
        assert result["success"] is False
        assert "500" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_localhost_shell_command(self):
        from services.bash_dispatcher import dispatch_tool

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"hello\n", b""))

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client
            with patch(
                "asyncio.create_subprocess_shell", AsyncMock(return_value=mock_proc)
            ), patch("asyncio.wait_for", AsyncMock(return_value=(b"hello\n", b""))):
                result = await dispatch_tool(
                    "execute",
                    {"agent_id": "localhost", "command": "echo hello"},
                )
        assert result["success"] is True
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_localhost_shell_failure(self):
        from services.bash_dispatcher import dispatch_tool

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"error msg"))

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client
            with patch(
                "asyncio.create_subprocess_shell", AsyncMock(return_value=mock_proc)
            ), patch("asyncio.wait_for", AsyncMock(return_value=(b"", b"error msg"))):
                result = await dispatch_tool(
                    "execute",
                    {"agent_id": "localhost", "command": "bad_command"},
                )
        assert result["success"] is False
        assert result["error"] == "error msg"

    @pytest.mark.asyncio
    async def test_execute_localhost_exception(self):
        from services.bash_dispatcher import dispatch_tool

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("conn refused"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "localhost", "command": "discover-peers"},
            )
        assert result["success"] is False
        assert "conn refused" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_remote_agent_not_found(self):
        from services.bash_dispatcher import dispatch_tool

        with patch(
            "services.bash_dispatcher.get_agent_by_id", AsyncMock(return_value=None)
        ), patch(
            "services.bash_dispatcher.get_available_agents", AsyncMock(return_value=[])
        ):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "workstation99", "command": "ls"},
            )
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_remote_agent_not_found_shows_available(self):
        from services.bash_dispatcher import dispatch_tool

        available = [FakeAgent(agent_id="ws1"), FakeAgent(agent_id="ws2")]
        with patch(
            "services.bash_dispatcher.get_agent_by_id", AsyncMock(return_value=None)
        ), patch(
            "services.bash_dispatcher.get_available_agents",
            AsyncMock(return_value=available),
        ):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "workstation99", "command": "ls"},
            )
        assert "ws1" in result["error"]
        assert "ws2" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_remote_agent_grpc_success(self):
        from services.bash_dispatcher import dispatch_tool

        agent = FakeAgent(agent_id="ws1", platform="windows")
        mock_grpc = MagicMock()
        mock_grpc.execute = AsyncMock(
            return_value=FakeTaskResult(success=True, stdout="output", stderr="")
        )

        with patch(
            "services.bash_dispatcher.get_agent_by_id", AsyncMock(return_value=agent)
        ), patch("services.bash_dispatcher.get_grpc_client", return_value=mock_grpc):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "ws1", "command": "Get-Process"},
            )
        assert result["success"] is True
        assert result["output"] == "output"
        assert result["platform"] == "windows"
        mock_grpc.execute.assert_called_once_with(
            agent_id="ws1",
            command="Get-Process",
            task_type="powershell",
            timeout_seconds=60,
        )

    @pytest.mark.asyncio
    async def test_execute_remote_agent_grpc_linux(self):
        from services.bash_dispatcher import dispatch_tool

        agent = FakeAgent(agent_id="ws1", platform="linux")
        mock_grpc = MagicMock()
        mock_grpc.execute = AsyncMock(
            return_value=FakeTaskResult(success=True, stdout="result", stderr="")
        )

        with patch(
            "services.bash_dispatcher.get_agent_by_id", AsyncMock(return_value=agent)
        ), patch("services.bash_dispatcher.get_grpc_client", return_value=mock_grpc):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "ws1", "command": "ls -la"},
            )
        mock_grpc.execute.assert_called_once_with(
            agent_id="ws1",
            command="ls -la",
            task_type="shell",
            timeout_seconds=60,
        )

    @pytest.mark.asyncio
    async def test_execute_remote_agent_grpc_failure(self):
        from services.bash_dispatcher import dispatch_tool

        agent = FakeAgent(agent_id="ws1", platform="linux")
        mock_grpc = MagicMock()
        mock_grpc.execute = AsyncMock(side_effect=Exception("gRPC down"))

        with patch(
            "services.bash_dispatcher.get_agent_by_id", AsyncMock(return_value=agent)
        ), patch("services.bash_dispatcher.get_grpc_client", return_value=mock_grpc):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "ws1", "command": "ls"},
            )
        assert result["success"] is False
        assert "gRPC down" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_remote_grpc_result_stderr_only(self):
        from services.bash_dispatcher import dispatch_tool

        agent = FakeAgent(agent_id="ws1", platform="linux")
        mock_grpc = MagicMock()
        mock_grpc.execute = AsyncMock(
            return_value=FakeTaskResult(
                success=False, stdout="", stderr="error occurred"
            )
        )

        with patch(
            "services.bash_dispatcher.get_agent_by_id", AsyncMock(return_value=agent)
        ), patch("services.bash_dispatcher.get_grpc_client", return_value=mock_grpc):
            result = await dispatch_tool(
                "execute",
                {"agent_id": "ws1", "command": "bad_cmd"},
            )
        assert result["success"] is False
        assert result["output"] == "error occurred"
        assert result["error"] == "error occurred"

    @pytest.mark.asyncio
    async def test_think_tool(self):
        from services.bash_dispatcher import dispatch_tool

        result = await dispatch_tool("think", {"thought": "considering options"})
        assert result["success"] is True
        assert "considering options" in result["output"]

    @pytest.mark.asyncio
    async def test_think_with_reasoning_key(self):
        from services.bash_dispatcher import dispatch_tool

        result = await dispatch_tool("think", {"reasoning": "my reasoning"})
        assert result["success"] is True
        assert "my reasoning" in result["output"]

    @pytest.mark.asyncio
    async def test_complete_success(self):
        from services.bash_dispatcher import dispatch_tool

        result = await dispatch_tool("complete", {"message": "all done"})
        assert result["success"] is True
        assert "all done" in result["output"]

    @pytest.mark.asyncio
    async def test_complete_with_error(self):
        from services.bash_dispatcher import dispatch_tool

        result = await dispatch_tool("complete", {"error": "something broke"})
        assert result["success"] is False
        assert "something broke" in result["error"]

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        from services.bash_dispatcher import dispatch_tool

        result = await dispatch_tool("fly_to_moon", {})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


class TestGetAvailableAgents:
    @pytest.mark.asyncio
    async def test_calls_discovery(self):
        from services.bash_dispatcher import get_available_agents

        mock_discovery = MagicMock()
        mock_discovery.discover = AsyncMock(return_value=[FakeAgent("a1")])
        with patch(
            "services.bash_dispatcher.get_discovery_service",
            return_value=mock_discovery,
        ):
            result = await get_available_agents()
        assert len(result) == 1
        mock_discovery.discover.assert_called_once_with(force=False)


class TestGetAgentById:
    @pytest.mark.asyncio
    async def test_found(self):
        from services.bash_dispatcher import get_agent_by_id

        agents = [FakeAgent("ws1"), FakeAgent("ws2")]
        with patch(
            "services.bash_dispatcher.get_available_agents",
            AsyncMock(return_value=agents),
        ):
            result = await get_agent_by_id("ws2")
        assert result.agent_id == "ws2"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from services.bash_dispatcher import get_agent_by_id

        with patch(
            "services.bash_dispatcher.get_available_agents", AsyncMock(return_value=[])
        ):
            result = await get_agent_by_id("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_case_insensitive(self):
        from services.bash_dispatcher import get_agent_by_id

        agents = [FakeAgent("WorkStation01")]
        with patch(
            "services.bash_dispatcher.get_available_agents",
            AsyncMock(return_value=agents),
        ):
            result = await get_agent_by_id("workstation01")
        assert result is not None
