"""Tests for AgentGrpcClient - 100% coverage target."""

import pytest
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from dataclasses import dataclass

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)


# We must mock grpc and protobuf modules BEFORE importing
@dataclass
class FakeAgentCap:
    agent_id: str
    hostname: str = "host1"
    ip_address: str = "10.0.0.1"
    grpc_port: int = 50051
    platform: str = "linux"
    capabilities: list = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@pytest.fixture(autouse=True)
def reset_grpc_singleton():
    """Reset the singleton between tests."""
    import services.grpc_client as mod

    mod._grpc_client = None
    yield
    mod._grpc_client = None


class TestGetGrpcClient:
    def test_creates_singleton(self):
        from services.grpc_client import get_grpc_client, AgentGrpcClient

        with patch.object(AgentGrpcClient, "__init__", return_value=None):
            client = get_grpc_client()
            client2 = get_grpc_client()
            assert client is client2


class TestEnsureProtoImports:
    def test_imports_succeed(self):
        from services.grpc_client import AgentGrpcClient, get_discovery_service

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2_grpc = MagicMock()
        with patch.dict(
            "sys.modules",
            {
                "protos": MagicMock(),
                "protos.task_service_pb2": mock_pb2,
                "protos.task_service_pb2_grpc": mock_pb2_grpc,
            },
        ):
            client._ensure_proto_imports()
            assert client._task_service_pb2 is not None

    def test_imports_fail(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        with patch.dict("sys.modules", {"protos": None}):
            with pytest.raises(ImportError):
                # Force reimport by clearing cached module
                client._task_service_pb2 = None
                client._ensure_proto_imports()

    def test_already_imported(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()
        client._task_service_pb2 = MagicMock()
        client._task_service_pb2_grpc = MagicMock()
        # Should not raise, just return immediately
        client._ensure_proto_imports()


class TestLoadCredentials:
    def test_no_cert_files(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        with patch("os.path.exists", return_value=False):
            result = client._load_credentials()
        assert result is None

    def test_cert_files_loaded(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        mock_cred = MagicMock()
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", MagicMock()
        ), patch("grpc.ssl_channel_credentials", return_value=mock_cred):
            result = client._load_credentials()
        assert result is mock_cred
        # Second call returns cached
        result2 = client._load_credentials()
        assert result2 is mock_cred

    def test_cert_read_error(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", side_effect=IOError("bad")
        ):
            result = client._load_credentials()
        assert result is None


class TestGetChannel:
    @pytest.mark.asyncio
    async def test_insecure_channel(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        agent = FakeAgentCap("ws1")
        mock_channel = MagicMock()

        with patch("services.grpc_client.FUNNEL_INSECURE", True), patch(
            "grpc.aio.insecure_channel", return_value=mock_channel
        ):
            channel = await client._get_channel(agent)
        assert channel is mock_channel

    @pytest.mark.asyncio
    async def test_secure_channel(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        agent = FakeAgentCap("ws1")
        mock_channel = MagicMock()
        mock_cred = MagicMock()

        with patch("services.grpc_client.FUNNEL_INSECURE", False), patch.object(
            client, "_load_credentials", return_value=mock_cred
        ), patch("grpc.aio.secure_channel", return_value=mock_channel):
            channel = await client._get_channel(agent)
        assert channel is mock_channel

    @pytest.mark.asyncio
    async def test_cached_channel_reused(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        agent = FakeAgentCap("ws1")
        mock_channel = MagicMock()
        import grpc as grpc_mod

        mock_channel.get_state.return_value = grpc_mod.ChannelConnectivity.READY

        key = f"{agent.agent_id}:{agent.ip_address}:{agent.grpc_port}"
        client._channels[key] = mock_channel

        channel = await client._get_channel(agent)
        assert channel is mock_channel

    @pytest.mark.asyncio
    async def test_shutdown_channel_replaced(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        agent = FakeAgentCap("ws1")
        import grpc as grpc_mod

        old_channel = MagicMock()
        old_channel.get_state.return_value = grpc_mod.ChannelConnectivity.SHUTDOWN
        key = f"{agent.agent_id}:{agent.ip_address}:{agent.grpc_port}"
        client._channels[key] = old_channel
        client._stubs[key] = MagicMock()  # Also has a stub to clean up (line 153)

        new_channel = MagicMock()
        with patch("services.grpc_client.FUNNEL_INSECURE", True), patch(
            "grpc.aio.insecure_channel", return_value=new_channel
        ):
            result = await client._get_channel(agent)
        assert result is new_channel
        assert key not in client._stubs  # stub was cleaned up

    @pytest.mark.asyncio
    async def test_bad_channel_state_check(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        agent = FakeAgentCap("ws1")
        old_channel = MagicMock()
        old_channel.get_state.side_effect = Exception("dead")
        key = f"{agent.agent_id}:{agent.ip_address}:{agent.grpc_port}"
        client._channels[key] = old_channel

        new_channel = MagicMock()
        with patch("services.grpc_client.FUNNEL_INSECURE", True), patch(
            "grpc.aio.insecure_channel", return_value=new_channel
        ):
            result = await client._get_channel(agent)
        assert result is new_channel

    @pytest.mark.asyncio
    async def test_no_credentials_falls_to_insecure(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        agent = FakeAgentCap("ws1")
        mock_channel = MagicMock()

        with patch("services.grpc_client.FUNNEL_INSECURE", False), patch.object(
            client, "_load_credentials", return_value=None
        ), patch("grpc.aio.insecure_channel", return_value=mock_channel):
            channel = await client._get_channel(agent)
        assert channel is mock_channel


class TestResolveAgent:
    @pytest.mark.asyncio
    async def test_agent_found(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent
        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()
        result = await client._resolve_agent("ws1")
        assert result is agent

    @pytest.mark.asyncio
    async def test_agent_not_found_rediscovery(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.side_effect = [None, agent]
        mock_discovery.discover = AsyncMock(return_value=[agent])
        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()
        result = await client._resolve_agent("ws1")
        assert result is agent

    @pytest.mark.asyncio
    async def test_agent_not_found_after_rediscovery(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        mock_discovery.get_agent.return_value = None
        mock_discovery.discover = AsyncMock(return_value=[])
        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()
        with pytest.raises(ValueError, match="not found"):
            await client._resolve_agent("ws99")


class TestExecute:
    @pytest.mark.asyncio
    async def test_execute_success(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        # Mock proto modules
        mock_pb2 = MagicMock()
        mock_pb2.POWERSHELL = 1
        mock_pb2.SHELL = 0
        mock_pb2.READ_FILE = 2
        mock_pb2.WRITE_FILE = 3
        mock_pb2.LIST_DIRECTORY = 4
        mock_pb2.DOTNET_CODE = 5
        mock_pb2.ERROR_NONE = 0
        mock_pb2.ERROR_TIMEOUT = 1
        mock_pb2.ERROR_ELEVATION_REQUIRED = 2
        mock_pb2.ERROR_NOT_FOUND = 3
        mock_pb2.ERROR_PERMISSION_DENIED = 4
        mock_pb2.ERROR_INTERNAL = 5
        mock_pb2.ERROR_CANCELLED = 6
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.stdout = "output"
        mock_response.stderr = ""
        mock_response.exit_code = 0
        mock_response.error_code = 0  # ERROR_NONE
        mock_response.duration_ms = 150
        mock_response.task_id = "t1"

        mock_stub = MagicMock()
        mock_stub.Execute = AsyncMock(return_value=mock_response)

        mock_channel = MagicMock()
        import grpc as grpc_mod

        mock_channel.get_state.return_value = grpc_mod.ChannelConnectivity.READY

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=mock_channel)
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.execute("ws1", "hostname", task_type="powershell")

        assert result.success is True
        assert result.stdout == "output"

    @pytest.mark.asyncio
    async def test_execute_grpc_error(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2.POWERSHELL = 1
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        import grpc as grpc_mod

        mock_rpc_error = grpc_mod.aio.AioRpcError(
            code=grpc_mod.StatusCode.UNAVAILABLE,
            initial_metadata=grpc_mod.aio.Metadata(),
            trailing_metadata=grpc_mod.aio.Metadata(),
            details="connection refused",
        )

        mock_stub = MagicMock()
        mock_stub.Execute = AsyncMock(side_effect=mock_rpc_error)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.execute("ws1", "hostname")

        assert result.success is False
        assert "gRPC error" in result.stderr

    @pytest.mark.asyncio
    async def test_execute_shell_type(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2.SHELL = 0
        mock_pb2.POWERSHELL = 1
        mock_pb2.ERROR_NONE = 0
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.stdout = "ok"
        mock_response.stderr = ""
        mock_response.exit_code = 0
        mock_response.error_code = 0
        mock_response.duration_ms = 10
        mock_response.task_id = "t2"

        mock_stub = MagicMock()
        mock_stub.Execute = AsyncMock(return_value=mock_response)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.execute("ws1", "ls", task_type="shell")

        assert result.success is True


class TestPing:
    @pytest.mark.asyncio
    async def test_ping_success(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        mock_response = MagicMock()
        mock_response.agent_id = "ws1"
        mock_response.hostname = "host1"
        mock_response.response_timestamp_ms = 1000

        mock_stub = MagicMock()
        mock_stub.Ping = AsyncMock(return_value=mock_response)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.ping("ws1")

        assert result["success"] is True
        assert result["agent_id"] == "ws1"

    @pytest.mark.asyncio
    async def test_ping_failure(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        import grpc as grpc_mod

        mock_rpc_error = grpc_mod.aio.AioRpcError(
            code=grpc_mod.StatusCode.UNAVAILABLE,
            initial_metadata=grpc_mod.aio.Metadata(),
            trailing_metadata=grpc_mod.aio.Metadata(),
            details="unreachable",
        )

        mock_stub = MagicMock()
        mock_stub.Ping = AsyncMock(side_effect=mock_rpc_error)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.ping("ws1")

        assert result["success"] is False


class TestGetStatus:
    @pytest.mark.asyncio
    async def test_get_status_success(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2.TASK_PENDING = 0
        mock_pb2.TASK_RUNNING = 1
        mock_pb2.TASK_COMPLETED = 2
        mock_pb2.TASK_FAILED = 3
        mock_pb2.TASK_CANCELLED = 4
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        mock_response = MagicMock()
        mock_response.task_id = "t1"
        mock_response.state = 2  # TASK_COMPLETED
        mock_response.progress_percent = 100
        mock_response.status_message = "done"

        mock_stub = MagicMock()
        mock_stub.GetStatus = AsyncMock(return_value=mock_response)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.get_status("ws1", "t1")

        assert result["task_id"] == "t1"

    @pytest.mark.asyncio
    async def test_get_status_error(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        import grpc as grpc_mod

        mock_rpc_error = grpc_mod.aio.AioRpcError(
            code=grpc_mod.StatusCode.NOT_FOUND,
            initial_metadata=grpc_mod.aio.Metadata(),
            trailing_metadata=grpc_mod.aio.Metadata(),
            details="task not found",
        )

        mock_stub = MagicMock()
        mock_stub.GetStatus = AsyncMock(side_effect=mock_rpc_error)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.get_status("ws1", "t1")

        assert result["state"] == "error"


class TestCancel:
    @pytest.mark.asyncio
    async def test_cancel_success(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        mock_response = MagicMock()
        mock_response.cancelled = True
        mock_response.message = "cancelled"

        mock_stub = MagicMock()
        mock_stub.Cancel = AsyncMock(return_value=mock_response)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.cancel("ws1", "t1", force=True)

        assert result["cancelled"] is True

    @pytest.mark.asyncio
    async def test_cancel_error(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        import grpc as grpc_mod

        mock_rpc_error = grpc_mod.aio.AioRpcError(
            code=grpc_mod.StatusCode.INTERNAL,
            initial_metadata=grpc_mod.aio.Metadata(),
            trailing_metadata=grpc_mod.aio.Metadata(),
            details="internal error",
        )

        mock_stub = MagicMock()
        mock_stub.Cancel = AsyncMock(side_effect=mock_rpc_error)

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            result = await client.cancel("ws1", "t1")

        assert result["cancelled"] is False


class TestExecuteStreaming:
    @pytest.mark.asyncio
    async def test_streaming_success(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2.POWERSHELL = 1
        mock_pb2.SHELL = 0
        mock_pb2.READ_FILE = 2
        mock_pb2.WRITE_FILE = 3
        mock_pb2.LIST_DIRECTORY = 4
        mock_pb2.DOTNET_CODE = 5
        mock_pb2.STDOUT = 0
        mock_pb2.STDERR = 1
        mock_pb2.STATUS = 2
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        output1 = MagicMock(task_id="t1", type=0, content="line1", timestamp_ms=100)
        output2 = MagicMock(task_id="t1", type=1, content="warn", timestamp_ms=200)

        mock_stub = MagicMock()

        async def fake_streaming(*args, **kwargs):
            for o in [output1, output2]:
                yield o

        mock_stub.ExecuteStreaming = fake_streaming

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            outputs = []
            async for out in client.execute_streaming("ws1", "hostname"):
                outputs.append(out)

        assert len(outputs) == 2
        assert outputs[0].output_type == "stdout"
        assert outputs[1].output_type == "stderr"

    @pytest.mark.asyncio
    async def test_streaming_grpc_error(self):
        from services.grpc_client import AgentGrpcClient

        mock_discovery = MagicMock()
        agent = FakeAgentCap("ws1")
        mock_discovery.get_agent.return_value = agent

        with patch(
            "services.grpc_client.get_discovery_service", return_value=mock_discovery
        ):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2.POWERSHELL = 1
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = MagicMock()

        import grpc as grpc_mod

        mock_rpc_error = grpc_mod.aio.AioRpcError(
            code=grpc_mod.StatusCode.UNAVAILABLE,
            initial_metadata=grpc_mod.aio.Metadata(),
            trailing_metadata=grpc_mod.aio.Metadata(),
            details="disconnected",
        )

        mock_stub = MagicMock()

        async def error_streaming(*args, **kwargs):
            raise mock_rpc_error
            yield  # make it a generator

        mock_stub.ExecuteStreaming = error_streaming

        with patch.object(
            client, "_get_channel", AsyncMock(return_value=MagicMock())
        ), patch.object(client, "_get_stub", return_value=mock_stub):
            outputs = []
            async for out in client.execute_streaming("ws1", "hostname"):
                outputs.append(out)

        assert len(outputs) == 1
        assert outputs[0].output_type == "error"


class TestClose:
    @pytest.mark.asyncio
    async def test_close_channels(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        chan1 = AsyncMock()
        chan2 = AsyncMock()
        chan2.close = AsyncMock(side_effect=Exception("already closed"))

        client._channels = {"a": chan1, "b": chan2}
        client._stubs = {"a": MagicMock(), "b": MagicMock()}

        await client.close()
        assert len(client._channels) == 0
        assert len(client._stubs) == 0


class TestGetStub:
    def test_creates_stub(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2_grpc = MagicMock()
        mock_stub_instance = MagicMock()
        mock_pb2_grpc.TaskServiceStub.return_value = mock_stub_instance

        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = mock_pb2_grpc

        agent = FakeAgentCap("ws1")
        channel = MagicMock()

        stub = client._get_stub(agent, channel)
        assert stub is mock_stub_instance

    def test_cached_stub(self):
        from services.grpc_client import AgentGrpcClient

        with patch("services.grpc_client.get_discovery_service"):
            client = AgentGrpcClient()

        mock_pb2 = MagicMock()
        mock_pb2_grpc = MagicMock()
        client._task_service_pb2 = mock_pb2
        client._task_service_pb2_grpc = mock_pb2_grpc

        agent = FakeAgentCap("ws1")
        cached_stub = MagicMock()
        key = f"{agent.agent_id}:{agent.ip_address}:{agent.grpc_port}"
        client._stubs[key] = cached_stub

        stub = client._get_stub(agent, MagicMock())
        assert stub is cached_stub
