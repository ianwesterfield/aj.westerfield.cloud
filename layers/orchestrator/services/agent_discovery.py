"""
Agent Discovery Service - UDP broadcast to find FunnelCloud agents.

Broadcasts "FUNNEL_DISCOVER" to the local network and collects
responses from available FunnelCloud agents.

Discovery happens once per conversation, results are cached.

When running in Docker, also tries direct connection to host.docker.internal.
"""

import asyncio
import json
import logging
import os
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("orchestrator.discovery")

# Discovery constants
DISCOVERY_PORT = int(os.getenv("FUNNEL_DISCOVERY_PORT", "41234"))
DISCOVERY_MAGIC = b"FUNNEL_DISCOVER"
DISCOVERY_TIMEOUT = float(os.getenv("FUNNEL_DISCOVERY_TIMEOUT", "2.0"))
BROADCAST_ADDRESS = "255.255.255.255"

# Docker host address (set when running in container)
DOCKER_HOST_ADDRESS = os.getenv("FUNNEL_HOST_ADDRESS", "")


@dataclass
class AgentCapabilities:
    """Capabilities advertised by a FunnelCloud agent."""
    agent_id: str
    hostname: str
    platform: str  # "windows", "linux", "macos"
    capabilities: List[str]  # ["powershell", "dotnet", "git", "docker"]
    workspace_roots: List[str]
    certificate_fingerprint: str
    discovery_port: int = DISCOVERY_PORT
    grpc_port: int = 41235
    ip_address: str = ""  # Filled in from response source
    last_seen: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "platform": self.platform,
            "capabilities": self.capabilities,
            "workspace_roots": self.workspace_roots,
            "certificate_fingerprint": self.certificate_fingerprint,
            "discovery_port": self.discovery_port,
            "grpc_port": self.grpc_port,
            "ip_address": self.ip_address,
            "last_seen": self.last_seen.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict, ip_address: str = "") -> "AgentCapabilities":
        return cls(
            agent_id=data.get("agentId", data.get("agent_id", "unknown")),
            hostname=data.get("hostname", "unknown"),
            platform=data.get("platform", "unknown"),
            capabilities=data.get("capabilities", []),
            workspace_roots=data.get("workspaceRoots", data.get("workspace_roots", [])),
            certificate_fingerprint=data.get("certificateFingerprint", data.get("certificate_fingerprint", "")),
            discovery_port=data.get("discoveryPort", data.get("discovery_port", DISCOVERY_PORT)),
            grpc_port=data.get("grpcPort", data.get("grpc_port", 41235)),
            ip_address=ip_address,
        )


class AgentDiscoveryService:
    """
    Service for discovering FunnelCloud agents on the network.
    
    Usage:
        discovery = AgentDiscoveryService()
        agents = await discovery.discover()
        
        # Or get cached agents
        agent = discovery.get_agent("dev-workstation")
    """
    
    def __init__(self, cache_ttl_seconds: int = 300):
        self._cache: Dict[str, AgentCapabilities] = {}
        self._cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._last_discovery: Optional[datetime] = None
    
    async def discover(self, force: bool = False) -> List[AgentCapabilities]:
        """
        Discover FunnelCloud agents on the network.
        
        Args:
            force: If True, bypass cache and re-discover
            
        Returns:
            List of discovered agent capabilities
        """
        # Check if cache is still valid
        if not force and self._is_cache_valid():
            logger.debug("Using cached agent list (%d agents)", len(self._cache))
            return list(self._cache.values())
        
        logger.info("Starting agent discovery...")
        
        agents: List[AgentCapabilities] = []
        
        # Try direct connection to Docker host first (when running in container)
        if DOCKER_HOST_ADDRESS:
            logger.info("Trying direct discovery to Docker host: %s", DOCKER_HOST_ADDRESS)
            host_agent = await self._discover_direct(DOCKER_HOST_ADDRESS)
            if host_agent:
                agents.append(host_agent)
        
        # Also try UDP broadcast (works when on same network)
        broadcast_agents = await self._discover_broadcast()
        
        # Merge results (avoid duplicates by agent_id)
        seen_ids = {a.agent_id for a in agents}
        for agent in broadcast_agents:
            if agent.agent_id not in seen_ids:
                agents.append(agent)
                seen_ids.add(agent.agent_id)
        
        # Update cache
        self._cache = {agent.agent_id: agent for agent in agents}
        self._last_discovery = datetime.utcnow()
        
        logger.info("Discovery complete: found %d agent(s)", len(agents))
        return agents
    
    async def _discover_direct(self, host_address: str) -> Optional[AgentCapabilities]:
        """Try direct UDP discovery to a specific host."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)
            sock.settimeout(DISCOVERY_TIMEOUT)
            
            # Resolve hostname if needed for sending
            try:
                resolved_ip = socket.gethostbyname(host_address)
                logger.debug("Resolved %s to %s", host_address, resolved_ip)
            except socket.gaierror:
                resolved_ip = host_address
            
            # Send discovery packet directly to host
            sock.sendto(DISCOVERY_MAGIC, (resolved_ip, DISCOVERY_PORT))
            logger.debug("Sent direct discovery to %s:%d", resolved_ip, DISCOVERY_PORT)
            
            # Wait for response
            loop = asyncio.get_event_loop()
            try:
                data, addr = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: sock.recvfrom(4096)),
                    timeout=DISCOVERY_TIMEOUT
                )
                
                response = json.loads(data.decode("utf-8"))
                # IMPORTANT: Use the original host_address (e.g., host.docker.internal) 
                # for gRPC connection, NOT the resolved IP. Docker's DNS handles routing.
                agent = AgentCapabilities.from_dict(response, ip_address=host_address)
                logger.info("Direct discovery found agent: %s at %s (resolved from %s)", 
                           agent.agent_id, host_address, resolved_ip)
                return agent
                
            except asyncio.TimeoutError:
                logger.debug("No response from direct discovery to %s", host_address)
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON from direct discovery: %s", e)
            finally:
                sock.close()
                
        except Exception as e:
            logger.debug("Direct discovery failed: %s", e)
        
        return None
    
    async def _discover_broadcast(self) -> List[AgentCapabilities]:
        """Discover agents via UDP broadcast."""
        agents: List[AgentCapabilities] = []
        
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)
            
            # Bind to any available port
            sock.bind(("", 0))
            local_port = sock.getsockname()[1]
            logger.debug("Discovery socket bound to port %d", local_port)
            
            # Send broadcast
            sock.sendto(DISCOVERY_MAGIC, (BROADCAST_ADDRESS, DISCOVERY_PORT))
            logger.debug("Sent discovery broadcast to %s:%d", BROADCAST_ADDRESS, DISCOVERY_PORT)
            
            # Collect responses with timeout
            loop = asyncio.get_event_loop()
            end_time = loop.time() + DISCOVERY_TIMEOUT
            
            while loop.time() < end_time:
                try:
                    # Non-blocking receive with short timeout
                    remaining = end_time - loop.time()
                    if remaining <= 0:
                        break
                    
                    data, addr = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: sock.recvfrom(4096)),
                        timeout=min(0.5, remaining)
                    )
                    
                    # Parse response
                    try:
                        response = json.loads(data.decode("utf-8"))
                        agent = AgentCapabilities.from_dict(response, ip_address=addr[0])
                        agents.append(agent)
                        logger.info(
                            "Discovered agent: %s at %s (%s)",
                            agent.agent_id, addr[0], agent.platform
                        )
                    except json.JSONDecodeError as e:
                        logger.warning("Invalid JSON from %s: %s", addr, e)
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.debug("Receive error: %s", e)
                    continue
            
            sock.close()
            
        except Exception as e:
            logger.error("Discovery broadcast failed: %s", e)
        
        return agents
    
    def _is_cache_valid(self) -> bool:
        """Check if the agent cache is still valid."""
        if not self._last_discovery:
            return False
        return datetime.utcnow() - self._last_discovery < self._cache_ttl
    
    def get_agent(self, agent_id: str) -> Optional[AgentCapabilities]:
        """Get a cached agent by ID."""
        return self._cache.get(agent_id)
    
    def get_agents_with_capability(self, capability: str) -> List[AgentCapabilities]:
        """Get all cached agents that have a specific capability."""
        return [
            agent for agent in self._cache.values()
            if capability in agent.capabilities
        ]
    
    def get_agents_for_workspace(self, workspace_path: str) -> List[AgentCapabilities]:
        """Get agents that can access a given workspace path."""
        results = []
        for agent in self._cache.values():
            for root in agent.workspace_roots:
                # Normalize paths for comparison
                norm_path = workspace_path.lower().replace("\\", "/")
                norm_root = root.lower().replace("\\", "/")
                if norm_path.startswith(norm_root):
                    results.append(agent)
                    break
        return results
    
    def mark_agent_stale(self, agent_id: str) -> None:
        """Mark an agent as stale (will be re-discovered on next request)."""
        if agent_id in self._cache:
            del self._cache[agent_id]
            logger.info("Marked agent %s as stale", agent_id)
    
    def invalidate_cache(self) -> None:
        """Force cache invalidation."""
        self._cache.clear()
        self._last_discovery = None
        logger.info("Agent cache invalidated")
    
    def list_agents(self) -> List[dict]:
        """List all cached agents as dicts (for API responses)."""
        return [agent.to_dict() for agent in self._cache.values()]


# Singleton instance
_discovery_service: Optional[AgentDiscoveryService] = None


def get_discovery_service() -> AgentDiscoveryService:
    """Get or create the singleton discovery service."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = AgentDiscoveryService()
    return _discovery_service
