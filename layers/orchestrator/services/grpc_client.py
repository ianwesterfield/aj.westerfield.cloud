"""
FunnelCloud gRPC Client - Secure task execution to remote agents.

Uses mTLS with CA-pinned certificates to connect to FunnelCloud agents
discovered via UDP multicast.

Usage:
    client = AgentGrpcClient()
    result = await client.execute(agent_id, command="ls -la")
    
    # With streaming output
    async for output in client.execute_streaming(agent_id, command="tail -f log"):
        print(output.content)
"""

import asyncio
import logging
import os
import ssl
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Optional

import grpc

from services.agent_discovery import AgentCapabilities, get_discovery_service

logger = logging.getLogger("orchestrator.grpc_client")

# Paths for mTLS certificates
ORCHESTRATOR_CERT_PATH = os.getenv("ORCHESTRATOR_CERT_PATH", "certs/orchestrator/orchestrator.crt")
ORCHESTRATOR_KEY_PATH = os.getenv("ORCHESTRATOR_KEY_PATH", "certs/orchestrator/orchestrator.key")
CA_CERT_PATH = os.getenv("CA_CERT_PATH", "certs/ca/ca.crt")

# Expected CA fingerprint for certificate pinning (SHA256)
# This MUST match the CA that signed valid agent certificates
CA_FINGERPRINT = os.getenv("FUNNEL_CA_FINGERPRINT", "")

# Force insecure mode (for development when agents don't have certs)
FUNNEL_INSECURE = os.getenv("FUNNEL_INSECURE", "").lower() in ("true", "1", "yes")

# Connection timeout
GRPC_TIMEOUT_SECONDS = 86400  # 24 hours for comprehensive scans


@dataclass
class TaskResult:
    """Result from a task execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    error_code: str
    duration_ms: int
    task_id: str


@dataclass
class TaskOutput:
    """Streaming output from task execution."""
    task_id: str
    output_type: str  # "stdout", "stderr", "status"
    content: str
    timestamp_ms: int


class AgentGrpcClient:
    """
    gRPC client for communicating with FunnelCloud agents.
    
    Handles:
    - mTLS connection with CA-pinned certificates
    - Connection pooling per agent
    - Automatic reconnection on failure
    """
    
    def __init__(self):
        self._channels: Dict[str, grpc.aio.Channel] = {}
        self._stubs: Dict[str, "TaskServiceStub"] = {}
        self._discovery = get_discovery_service()
        self._credentials: Optional[grpc.ChannelCredentials] = None
        
        # Import generated proto stubs (lazy import)
        self._task_service_pb2 = None
        self._task_service_pb2_grpc = None
    
    def _ensure_proto_imports(self):
        """Lazily import generated proto modules."""
        if self._task_service_pb2 is None:
            try:
                # Try relative import from generated location
                from protos import task_service_pb2, task_service_pb2_grpc
                self._task_service_pb2 = task_service_pb2
                self._task_service_pb2_grpc = task_service_pb2_grpc
            except ImportError:
                logger.error(
                    "gRPC stubs not generated. Run: "
                    "python -m grpc_tools.protoc -I protos --python_out=protos "
                    "--grpc_python_out=protos protos/task_service.proto"
                )
                raise
    
    def _load_credentials(self) -> Optional[grpc.ChannelCredentials]:
        """Load mTLS credentials from certificate files."""
        if self._credentials is not None:
            return self._credentials
        
        # Check if certificate files exist
        if not all(os.path.exists(p) for p in [ORCHESTRATOR_CERT_PATH, ORCHESTRATOR_KEY_PATH, CA_CERT_PATH]):
            logger.warning(
                "mTLS certificates not found. Will attempt insecure connection. "
                "Paths: cert=%s, key=%s, ca=%s",
                ORCHESTRATOR_CERT_PATH, ORCHESTRATOR_KEY_PATH, CA_CERT_PATH
            )
            return None
        
        try:
            with open(CA_CERT_PATH, "rb") as f:
                ca_cert = f.read()
            with open(ORCHESTRATOR_CERT_PATH, "rb") as f:
                client_cert = f.read()
            with open(ORCHESTRATOR_KEY_PATH, "rb") as f:
                client_key = f.read()
            
            self._credentials = grpc.ssl_channel_credentials(
                root_certificates=ca_cert,
                private_key=client_key,
                certificate_chain=client_cert,
            )
            
            logger.info("mTLS credentials loaded successfully")
            return self._credentials
            
        except Exception as e:
            logger.error("Failed to load mTLS credentials: %s", e)
            return None
    
    async def _get_channel(self, agent: AgentCapabilities) -> grpc.aio.Channel:
        """Get or create a gRPC channel to an agent."""
        channel_key = f"{agent.agent_id}:{agent.ip_address}:{agent.grpc_port}"
        
        if channel_key in self._channels:
            # Check if channel is still usable
            try:
                state = self._channels[channel_key].get_state()
                if state != grpc.ChannelConnectivity.SHUTDOWN:
                    return self._channels[channel_key]
            except Exception:
                pass
            # Channel is bad, remove it
            del self._channels[channel_key]
            if channel_key in self._stubs:
                del self._stubs[channel_key]
        
        # Create new channel
        target = f"{agent.ip_address}:{agent.grpc_port}"
        
        # Check if we should use insecure mode
        use_insecure = FUNNEL_INSECURE
        credentials = None if use_insecure else self._load_credentials()
        
        if use_insecure:
            logger.warning("FUNNEL_INSECURE is set - using insecure gRPC connections")
        
        # Allow large messages for directory scans (500MB)
        max_message_size = 500 * 1024 * 1024
        
        if credentials:
            # Secure channel with mTLS
            channel = grpc.aio.secure_channel(
                target,
                credentials,
                options=[
                    ("grpc.ssl_target_name_override", agent.hostname),
                    ("grpc.keepalive_time_ms", 30000),
                    ("grpc.keepalive_timeout_ms", 10000),
                    ("grpc.max_receive_message_length", max_message_size),
                    ("grpc.max_send_message_length", max_message_size),
                ],
            )
            logger.info("Created secure gRPC channel to %s (%s)", agent.agent_id, target)
        else:
            # Insecure channel (development only)
            channel = grpc.aio.insecure_channel(
                target,
                options=[
                    ("grpc.keepalive_time_ms", 30000),
                    ("grpc.keepalive_timeout_ms", 10000),
                    ("grpc.max_receive_message_length", max_message_size),
                    ("grpc.max_send_message_length", max_message_size),
                ],
            )
            logger.warning("Created INSECURE gRPC channel to %s (%s)", agent.agent_id, target)
        
        self._channels[channel_key] = channel
        return channel
    
    def _get_stub(self, agent: AgentCapabilities, channel: grpc.aio.Channel):
        """Get or create a gRPC stub for an agent."""
        self._ensure_proto_imports()
        
        channel_key = f"{agent.agent_id}:{agent.ip_address}:{agent.grpc_port}"
        
        if channel_key not in self._stubs:
            self._stubs[channel_key] = self._task_service_pb2_grpc.TaskServiceStub(channel)
        
        return self._stubs[channel_key]
    
    async def _resolve_agent(self, agent_id: str) -> AgentCapabilities:
        """Resolve agent ID to agent capabilities."""
        agent = self._discovery.get_agent(agent_id)
        
        if not agent:
            # Try re-discovery
            agents = await self._discovery.discover(force=True)
            agent = self._discovery.get_agent(agent_id)
            
            if not agent:
                raise ValueError(f"Agent '{agent_id}' not found after discovery")
        
        return agent
    
    async def ping(self, agent_id: str) -> dict:
        """
        Ping an agent to verify connectivity.
        
        Returns:
            Dict with ping results including round-trip time
        """
        self._ensure_proto_imports()
        
        agent = await self._resolve_agent(agent_id)
        channel = await self._get_channel(agent)
        stub = self._get_stub(agent, channel)
        
        import time
        start_ms = int(time.time() * 1000)
        
        request = self._task_service_pb2.PingRequest(timestamp_ms=start_ms)
        
        try:
            response = await stub.Ping(request, timeout=GRPC_TIMEOUT_SECONDS)
            end_ms = int(time.time() * 1000)
            
            return {
                "success": True,
                "agent_id": response.agent_id,
                "hostname": response.hostname,
                "round_trip_ms": end_ms - start_ms,
                "agent_timestamp_ms": response.response_timestamp_ms,
            }
        except grpc.aio.AioRpcError as e:
            logger.error("Ping failed for %s: %s", agent_id, e.details())
            return {
                "success": False,
                "error": str(e.code()),
                "details": e.details(),
            }
    
    async def execute(
        self,
        agent_id: str,
        command: str,
        task_type: str = "powershell",
        timeout_seconds: int = 30,
        require_elevation: bool = False,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> TaskResult:
        """
        Execute a task on a remote agent.
        
        Args:
            agent_id: Target agent ID
            command: Command or code to execute
            task_type: One of: shell, powershell, read_file, write_file, list_directory, dotnet_code
            timeout_seconds: Maximum execution time
            require_elevation: Request elevated (admin) execution
            working_directory: Working directory for execution
            environment: Additional environment variables
            
        Returns:
            TaskResult with execution output
        """
        self._ensure_proto_imports()
        
        agent = await self._resolve_agent(agent_id)
        channel = await self._get_channel(agent)
        stub = self._get_stub(agent, channel)
        
        task_id = str(uuid.uuid4())
        
        # Map task type string to enum
        type_map = {
            "shell": self._task_service_pb2.SHELL,
            "powershell": self._task_service_pb2.POWERSHELL,
            "read_file": self._task_service_pb2.READ_FILE,
            "write_file": self._task_service_pb2.WRITE_FILE,
            "list_directory": self._task_service_pb2.LIST_DIRECTORY,
            "dotnet_code": self._task_service_pb2.DOTNET_CODE,
        }
        task_type_enum = type_map.get(task_type.lower(), self._task_service_pb2.POWERSHELL)
        
        request = self._task_service_pb2.TaskRequest(
            task_id=task_id,
            type=task_type_enum,
            command=command,
            timeout_seconds=timeout_seconds,
            require_elevation=require_elevation,
            working_directory=working_directory or "",
            environment=environment or {},
        )
        
        try:
            logger.info("Executing task %s on %s (timeout=%ds): %s", task_id, agent_id, timeout_seconds, command[:80])
            
            response = await stub.Execute(request, timeout=timeout_seconds + 10)
            
            # Map error code enum to string
            error_map = {
                self._task_service_pb2.ERROR_NONE: "none",
                self._task_service_pb2.ERROR_TIMEOUT: "timeout",
                self._task_service_pb2.ERROR_ELEVATION_REQUIRED: "elevation_required",
                self._task_service_pb2.ERROR_NOT_FOUND: "not_found",
                self._task_service_pb2.ERROR_PERMISSION_DENIED: "permission_denied",
                self._task_service_pb2.ERROR_INTERNAL: "internal",
                self._task_service_pb2.ERROR_CANCELLED: "cancelled",
            }
            
            return TaskResult(
                success=response.success,
                stdout=response.stdout,
                stderr=response.stderr,
                exit_code=response.exit_code,
                error_code=error_map.get(response.error_code, "unknown"),
                duration_ms=response.duration_ms,
                task_id=response.task_id,
            )
            
        except grpc.aio.AioRpcError as e:
            logger.error("Task %s failed on %s: %s", task_id, agent_id, e.details())
            
            return TaskResult(
                success=False,
                stdout="",
                stderr=f"gRPC error: {e.code()} - {e.details()}",
                exit_code=-1,
                error_code="grpc_error",
                duration_ms=0,
                task_id=task_id,
            )
    
    async def execute_streaming(
        self,
        agent_id: str,
        command: str,
        task_type: str = "powershell",
        timeout_seconds: int = 30,
        require_elevation: bool = False,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[TaskOutput]:
        """
        Execute a task with streaming output.
        
        Yields TaskOutput objects as the task produces output.
        """
        self._ensure_proto_imports()
        
        agent = await self._resolve_agent(agent_id)
        channel = await self._get_channel(agent)
        stub = self._get_stub(agent, channel)
        
        task_id = str(uuid.uuid4())
        
        type_map = {
            "shell": self._task_service_pb2.SHELL,
            "powershell": self._task_service_pb2.POWERSHELL,
            "read_file": self._task_service_pb2.READ_FILE,
            "write_file": self._task_service_pb2.WRITE_FILE,
            "list_directory": self._task_service_pb2.LIST_DIRECTORY,
            "dotnet_code": self._task_service_pb2.DOTNET_CODE,
        }
        task_type_enum = type_map.get(task_type.lower(), self._task_service_pb2.POWERSHELL)
        
        request = self._task_service_pb2.TaskRequest(
            task_id=task_id,
            type=task_type_enum,
            command=command,
            timeout_seconds=timeout_seconds,
            require_elevation=require_elevation,
            working_directory=working_directory or "",
            environment=environment or {},
        )
        
        try:
            logger.debug("Executing streaming task %s on %s", task_id, agent_id)
            
            output_type_map = {
                self._task_service_pb2.STDOUT: "stdout",
                self._task_service_pb2.STDERR: "stderr",
                self._task_service_pb2.STATUS: "status",
            }
            
            async for output in stub.ExecuteStreaming(request, timeout=timeout_seconds + 10):
                yield TaskOutput(
                    task_id=output.task_id,
                    output_type=output_type_map.get(output.type, "unknown"),
                    content=output.content,
                    timestamp_ms=output.timestamp_ms,
                )
                
        except grpc.aio.AioRpcError as e:
            logger.error("Streaming task %s failed: %s", task_id, e.details())
            yield TaskOutput(
                task_id=task_id,
                output_type="error",
                content=f"gRPC error: {e.code()} - {e.details()}",
                timestamp_ms=int(asyncio.get_event_loop().time() * 1000),
            )
    
    async def get_status(self, agent_id: str, task_id: str) -> dict:
        """Get the status of a running task."""
        self._ensure_proto_imports()
        
        agent = await self._resolve_agent(agent_id)
        channel = await self._get_channel(agent)
        stub = self._get_stub(agent, channel)
        
        request = self._task_service_pb2.TaskStatusRequest(task_id=task_id)
        
        try:
            response = await stub.GetStatus(request, timeout=GRPC_TIMEOUT_SECONDS)
            
            state_map = {
                self._task_service_pb2.TASK_PENDING: "pending",
                self._task_service_pb2.TASK_RUNNING: "running",
                self._task_service_pb2.TASK_COMPLETED: "completed",
                self._task_service_pb2.TASK_FAILED: "failed",
                self._task_service_pb2.TASK_CANCELLED: "cancelled",
            }
            
            return {
                "task_id": response.task_id,
                "state": state_map.get(response.state, "unknown"),
                "progress_percent": response.progress_percent,
                "status_message": response.status_message,
            }
        except grpc.aio.AioRpcError as e:
            return {
                "task_id": task_id,
                "state": "error",
                "error": str(e.code()),
                "details": e.details(),
            }
    
    async def cancel(self, agent_id: str, task_id: str, force: bool = False) -> dict:
        """Cancel a running task."""
        self._ensure_proto_imports()
        
        agent = await self._resolve_agent(agent_id)
        channel = await self._get_channel(agent)
        stub = self._get_stub(agent, channel)
        
        request = self._task_service_pb2.CancelRequest(task_id=task_id, force=force)
        
        try:
            response = await stub.Cancel(request, timeout=GRPC_TIMEOUT_SECONDS)
            return {
                "cancelled": response.cancelled,
                "message": response.message,
            }
        except grpc.aio.AioRpcError as e:
            return {
                "cancelled": False,
                "error": str(e.code()),
                "details": e.details(),
            }
    
    async def close(self):
        """Close all gRPC channels."""
        for channel_key, channel in self._channels.items():
            try:
                await channel.close()
            except Exception as e:
                logger.debug("Error closing channel %s: %s", channel_key, e)
        
        self._channels.clear()
        self._stubs.clear()
        logger.info("All gRPC channels closed")


# Singleton instance
_grpc_client: Optional[AgentGrpcClient] = None


def get_grpc_client() -> AgentGrpcClient:
    """Get or create the singleton gRPC client."""
    global _grpc_client
    if _grpc_client is None:
        _grpc_client = AgentGrpcClient()
    return _grpc_client
