"""
Agent Discovery Service - Discovers FunnelCloud agents via multicast or proxy.

Discovery Strategy:
1. First, try UDP multicast directly (works if orchestrator is on same L2 network)
2. If that fails or finds no agents, use local agent as discovery proxy via UDP
   - Send "FUNNEL_DISCOVER_PEERS" to local agent
   - Local agent multicasts on physical LAN and returns all discovered peers

This allows discovery to work even when the orchestrator is in:
- Docker with bridge networking
- WSL with NAT
- Any other network that can't reach the physical LAN via multicast

The only requirement is UDP connectivity to ONE known agent (the local one).
"""

import asyncio
import json
import logging
import os
import socket
import struct
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("orchestrator.discovery")

# Discovery constants
DISCOVERY_PORT = int(os.getenv("FUNNEL_DISCOVERY_PORT", "41420"))
DISCOVERY_MAGIC = b"FUNNEL_DISCOVER"
DISCOVERY_PEERS_MAGIC = b"FUNNEL_DISCOVER_PEERS"
DISCOVERY_TIMEOUT = float(os.getenv("FUNNEL_DISCOVERY_TIMEOUT", "2.0"))
MULTICAST_GROUP = os.getenv("FUNNEL_MULTICAST_GROUP", "239.255.77.77")

# Local agent for discovery proxy (UDP, same port)
# This is the ONLY "known" address - the gateway to the local agent
LOCAL_AGENT_HOST = os.getenv("FUNNEL_LOCAL_AGENT_HOST", "")  # e.g., "172.25.224.1"

# Seed agents - comma-separated list of IPs for direct UDP discovery
# Use this for agents on other subnets that multicast can't reach
# Example: "192.168.10.166,192.168.10.167,192.168.10.168"
SEED_AGENT_IPS = [ip.strip() for ip in os.getenv("FUNNEL_SEED_AGENTS", "").split(",") if ip.strip()]


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
        # Use provided ip_address, or fall back to what's in the data
        final_ip = ip_address or data.get("ip_address", data.get("ipAddress", ""))
        return cls(
            agent_id=data.get("agentId", data.get("agent_id", "unknown")),
            hostname=data.get("hostname", "unknown"),
            platform=data.get("platform", "unknown"),
            capabilities=data.get("capabilities", []),
            workspace_roots=data.get("workspaceRoots", data.get("workspace_roots", [])),
            certificate_fingerprint=data.get("certificateFingerprint", data.get("certificate_fingerprint", "")),
            discovery_port=data.get("discoveryPort", data.get("discovery_port", DISCOVERY_PORT)),
            grpc_port=data.get("grpcPort", data.get("grpc_port", 41235)),
            ip_address=final_ip,
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

        Discovery order:
        1. Try UDP multicast directly (fastest if it works)
        2. If no agents found, try local agent's HTTP discovery proxy

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

        # Step 1: Try direct UDP multicast
        multicast_agents = await self._discover_multicast()
        agents.extend(multicast_agents)

        # Step 2: If multicast didn't find anything, try the local agent proxy
        if not agents and LOCAL_AGENT_HOST:
            logger.info("Multicast found no agents, trying local agent discovery proxy at %s:%d",
                        LOCAL_AGENT_HOST, DISCOVERY_PORT)
            proxy_agents = await self._discover_via_proxy()
            agents.extend(proxy_agents)

        # Step 3: Query seed agents directly (for cross-subnet discovery)
        if SEED_AGENT_IPS:
            logger.info("Querying %d seed agent(s) directly...", len(SEED_AGENT_IPS))
            seed_agents = await self._discover_seed_agents()
            # Only add agents we haven't already found
            existing_ids = {a.agent_id for a in agents}
            for agent in seed_agents:
                if agent.agent_id not in existing_ids:
                    agents.append(agent)
                    existing_ids.add(agent.agent_id)

        # Update cache
        self._cache = {agent.agent_id: agent for agent in agents}
        self._last_discovery = datetime.utcnow()

        logger.info("Discovery complete: found %d agent(s)", len(agents))
        return agents

    async def _discover_via_proxy(self) -> List[AgentCapabilities]:
        """
        Discover agents by sending FUNNEL_DISCOVER_PEERS to the local agent.
        
        The local agent will do the actual multicast on the physical network
        and return all discovered agents (including itself) via UDP.
        """
        agents: List[AgentCapabilities] = []

        if not LOCAL_AGENT_HOST:
            logger.debug("No local agent host configured, skipping proxy discovery")
            return agents

        logger.info("Sending peer discovery request to local agent at %s:%d",
                    LOCAL_AGENT_HOST, DISCOVERY_PORT)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Use blocking socket with timeout for run_in_executor
            proxy_timeout = DISCOVERY_TIMEOUT + 3.0
            sock.settimeout(proxy_timeout)
            
            # Send peer discovery request
            sock.sendto(DISCOVERY_PEERS_MAGIC, (LOCAL_AGENT_HOST, DISCOVERY_PORT))
            logger.debug("Sent FUNNEL_DISCOVER_PEERS to %s:%d", LOCAL_AGENT_HOST, DISCOVERY_PORT)
            
            # Wait for response (blocking with timeout)
            loop = asyncio.get_event_loop()
            
            try:
                data, addr = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: sock.recvfrom(65535)),  # Large buffer for multi-agent response
                    timeout=proxy_timeout + 1.0  # Slightly longer than socket timeout
                )
                
                response = json.loads(data.decode("utf-8"))
                discovered_by = response.get("discoveredBy", "unknown")
                agent_list = response.get("agents", [])
                
                logger.info("Discovery proxy (%s) returned %d agent(s)", discovered_by, len(agent_list))
                
                for agent_data in agent_list:
                    try:
                        agent = AgentCapabilities.from_dict(agent_data)
                        
                        # If the discovering agent doesn't have an IP set, use the proxy host
                        if not agent.ip_address and agent.agent_id == discovered_by:
                            agent.ip_address = LOCAL_AGENT_HOST
                        
                        agents.append(agent)
                        logger.info("Discovered via proxy: %s at %s (%s)",
                                    agent.agent_id, agent.ip_address or "unknown", agent.platform)
                    except Exception as e:
                        logger.warning("Failed to parse agent data: %s", e)
                        
            except asyncio.TimeoutError:
                logger.warning("Peer discovery proxy request timed out after %.1fs", proxy_timeout)
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON from discovery proxy: %s", e)
            finally:
                sock.close()
                
        except Exception as e:
            logger.error("Peer discovery proxy request failed: %s", e)

        return agents

    async def _discover_seed_agents(self) -> List[AgentCapabilities]:
        """
        Discover agents by sending FUNNEL_DISCOVER directly to seed IPs.
        
        This bypasses multicast for agents on other subnets that can't be
        reached via multicast or through the local agent proxy.
        """
        agents: List[AgentCapabilities] = []

        if not SEED_AGENT_IPS:
            return agents

        async def query_agent(ip: str) -> Optional[AgentCapabilities]:
            """Query a single agent by IP."""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(DISCOVERY_TIMEOUT)
                
                sock.sendto(DISCOVERY_MAGIC, (ip, DISCOVERY_PORT))
                logger.debug("Sent FUNNEL_DISCOVER to seed agent %s:%d", ip, DISCOVERY_PORT)
                
                loop = asyncio.get_event_loop()
                data, addr = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: sock.recvfrom(4096)),
                    timeout=DISCOVERY_TIMEOUT + 1.0
                )
                sock.close()
                
                response = json.loads(data.decode("utf-8"))
                agent = AgentCapabilities.from_dict(response, ip_address=ip)
                logger.info("Discovered seed agent: %s at %s (%s)",
                            agent.agent_id, ip, agent.platform)
                return agent
                
            except asyncio.TimeoutError:
                logger.debug("Seed agent %s did not respond", ip)
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON from seed agent %s: %s", ip, e)
            except Exception as e:
                logger.debug("Failed to query seed agent %s: %s", ip, e)
            finally:
                try:
                    sock.close()
                except:
                    pass
            return None

        # Query all seed agents in parallel
        tasks = [query_agent(ip) for ip in SEED_AGENT_IPS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, AgentCapabilities):
                agents.append(result)
            elif isinstance(result, Exception):
                logger.debug("Seed agent query exception: %s", result)

        logger.info("Seed discovery found %d agent(s) from %d IP(s)", 
                    len(agents), len(SEED_AGENT_IPS))
        return agents

    async def _discover_multicast(self) -> List[AgentCapabilities]:
        """Discover agents via UDP multicast."""
        agents: List[AgentCapabilities] = []

        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)

            # Set multicast TTL (time-to-live) - higher values allow crossing more routers
            # TTL 1 = same subnet, TTL 32 = reasonable for site-local
            ttl = struct.pack('b', 32)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

            # Bind to any available port for receiving responses
            sock.bind(("", 0))
            local_port = sock.getsockname()[1]
            logger.debug("Discovery socket bound to port %d", local_port)

            # Send to multicast group
            sock.sendto(DISCOVERY_MAGIC, (MULTICAST_GROUP, DISCOVERY_PORT))
            logger.debug("Sent discovery to multicast group %s:%d", MULTICAST_GROUP, DISCOVERY_PORT)

            # Collect responses with timeout
            loop = asyncio.get_event_loop()
            end_time = loop.time() + DISCOVERY_TIMEOUT

            while loop.time() < end_time:
                try:
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
                            "Discovered agent via multicast: %s at %s (%s)",
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
            logger.debug("Discovery multicast failed: %s", e)

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
