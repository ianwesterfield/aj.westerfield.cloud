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
from typing import Dict, List, Optional, Set

import aiohttp

logger = logging.getLogger("orchestrator.discovery")


def _get_secret_or_env(env_name: str, default: str = "") -> str:
    """Read from secret file if _FILE env var exists, otherwise use env var."""
    file_path = os.getenv(f"{env_name}_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read().strip()
    return os.getenv(env_name, default)


# Discovery constants
DISCOVERY_PORT = int(os.getenv("FUNNEL_DISCOVERY_PORT", "41420"))
DISCOVERY_MAGIC = b"FUNNEL_DISCOVER"
DISCOVERY_PEERS_MAGIC = b"FUNNEL_DISCOVER_PEERS"
DISCOVERY_TIMEOUT = float(os.getenv("FUNNEL_DISCOVERY_TIMEOUT", "2.0"))
MULTICAST_GROUP = os.getenv("FUNNEL_MULTICAST_GROUP", "239.255.77.77")

# HTTP port for agent REST API (used for gossip peer discovery)
AGENT_HTTP_PORT = int(os.getenv("FUNNEL_AGENT_HTTP_PORT", "41421"))

# Gossip configuration - how many rounds to expand peer discovery
GOSSIP_MAX_ROUNDS = int(os.getenv("FUNNEL_GOSSIP_MAX_ROUNDS", "3"))
GOSSIP_TIMEOUT = float(os.getenv("FUNNEL_GOSSIP_TIMEOUT", "2.0"))

# Local agent for discovery proxy (UDP, same port)
# This is the ONLY "known" address - the gateway to the local agent
# All other agents are discovered dynamically via gossip
LOCAL_AGENT_HOST = _get_secret_or_env("FUNNEL_LOCAL_AGENT_HOST")

# Gossip seed agent - an IP of any reachable agent to bootstrap cross-subnet discovery
# This is used when the local agent can't see other subnets via multicast
# Only ONE seed is needed - gossip will find all other agents from there
GOSSIP_SEED_HOST = _get_secret_or_env("FUNNEL_GOSSIP_SEED_HOST")


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
            certificate_fingerprint=data.get(
                "certificateFingerprint", data.get("certificate_fingerprint", "")
            ),
            discovery_port=data.get(
                "discoveryPort", data.get("discovery_port", DISCOVERY_PORT)
            ),
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
        Discover FunnelCloud agents on the network using gossip-based discovery.

        Discovery order:
        1. Try UDP multicast directly (fastest if it works)
        2. If no agents found, try local agent's UDP discovery proxy
        3. Use gossip to expand: ask each discovered agent for its known peers
           - This allows cross-subnet discovery without hardcoded IPs
           - Each agent can multicast on its local LAN and share what it finds

        Args:
            force: If True, bypass cache and re-discover

        Returns:
            List of discovered agent capabilities
        """
        # Check if cache is still valid
        if not force and self._is_cache_valid():
            logger.debug("Using cached agent list (%d agents)", len(self._cache))
            return list(self._cache.values())

        logger.info("Starting agent discovery (gossip-based)...")

        agents: List[AgentCapabilities] = []
        discovered_ids: Set[str] = set()

        # Step 1: Try direct UDP multicast
        multicast_agents = await self._discover_multicast()
        for agent in multicast_agents:
            if agent.agent_id not in discovered_ids:
                agents.append(agent)
                discovered_ids.add(agent.agent_id)

        # Step 2: If multicast didn't find anything, try the local agent proxy
        if not agents and LOCAL_AGENT_HOST:
            logger.info(
                "Multicast found no agents, trying local agent discovery proxy at %s:%d",
                LOCAL_AGENT_HOST,
                DISCOVERY_PORT,
            )
            proxy_agents = await self._discover_via_proxy()
            for agent in proxy_agents:
                if agent.agent_id not in discovered_ids:
                    agents.append(agent)
                    discovered_ids.add(agent.agent_id)

        # Step 2.5: Bootstrap cross-subnet by adding seed agent to local agent's registry
        # This ensures the local agent can gossip with cross-subnet peers
        if agents and GOSSIP_SEED_HOST and LOCAL_AGENT_HOST:
            await self._bootstrap_cross_subnet(LOCAL_AGENT_HOST, GOSSIP_SEED_HOST)

        # Step 3: Use gossip to expand discovery - ask known agents for their peers
        # This replaces hardcoded seed agents with dynamic discovery
        if agents:
            gossip_agents = await self._discover_via_gossip(agents, discovered_ids)
            agents.extend(gossip_agents)
            for agent in gossip_agents:
                discovered_ids.add(agent.agent_id)

        # Update cache
        self._cache = {agent.agent_id: agent for agent in agents}
        self._last_discovery = datetime.utcnow()

        logger.info("Discovery complete: found %d agent(s)", len(agents))
        return agents

    async def _bootstrap_cross_subnet(self, local_agent_ip: str, seed_ip: str) -> None:
        """
        Bootstrap cross-subnet discovery by adding a seed agent to the local agent's registry.

        This uses the /add-peer endpoint on the local agent to establish initial
        connectivity with an agent on another subnet. Once added, the local agent's
        gossip service will propagate peer information across subnets automatically.
        """
        url = f"http://{local_agent_ip}:{AGENT_HTTP_PORT}/add-peer?ip={seed_ip}"
        logger.info(
            "Bootstrapping cross-subnet: adding %s to local agent %s",
            seed_ip,
            local_agent_ip,
        )

        try:
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            logger.info(
                                "Successfully added cross-subnet peer: %s (%s)",
                                data.get("agentId"),
                                data.get("ipAddress"),
                            )
                        else:
                            logger.warning(
                                "Failed to add cross-subnet peer: %s", data.get("error")
                            )
                    else:
                        logger.warning("Add-peer returned status %d", response.status)
        except Exception as e:
            logger.debug(
                "Cross-subnet bootstrap failed: %s (agent may not support /add-peer)", e
            )

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

        logger.info(
            "Sending peer discovery request to local agent at %s:%d",
            LOCAL_AGENT_HOST,
            DISCOVERY_PORT,
        )

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Use blocking socket with timeout for run_in_executor
            proxy_timeout = DISCOVERY_TIMEOUT + 3.0
            sock.settimeout(proxy_timeout)

            # Send peer discovery request
            sock.sendto(DISCOVERY_PEERS_MAGIC, (LOCAL_AGENT_HOST, DISCOVERY_PORT))
            logger.debug(
                "Sent FUNNEL_DISCOVER_PEERS to %s:%d", LOCAL_AGENT_HOST, DISCOVERY_PORT
            )

            # Wait for response (blocking with timeout)
            loop = asyncio.get_event_loop()

            try:
                data, addr = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, lambda: sock.recvfrom(65535)
                    ),  # Large buffer for multi-agent response
                    timeout=proxy_timeout + 1.0,  # Slightly longer than socket timeout
                )

                response = json.loads(data.decode("utf-8"))
                discovered_by = response.get("discoveredBy", "unknown")
                agent_list = response.get("agents", [])

                logger.info(
                    "Discovery proxy (%s) returned %d agent(s)",
                    discovered_by,
                    len(agent_list),
                )

                for agent_data in agent_list:
                    try:
                        agent = AgentCapabilities.from_dict(agent_data)

                        # If the discovering agent doesn't have an IP set, use the proxy host
                        if not agent.ip_address and agent.agent_id == discovered_by:
                            agent.ip_address = LOCAL_AGENT_HOST

                        agents.append(agent)
                        logger.info(
                            "Discovered via proxy: %s at %s (%s)",
                            agent.agent_id,
                            agent.ip_address or "unknown",
                            agent.platform,
                        )
                    except Exception as e:
                        logger.warning("Failed to parse agent data: %s", e)

            except asyncio.TimeoutError:
                logger.warning(
                    "Peer discovery proxy request timed out after %.1fs", proxy_timeout
                )
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON from discovery proxy: %s", e)
            finally:
                sock.close()

        except Exception as e:
            logger.error("Peer discovery proxy request failed: %s", e)

        return agents

    async def _discover_via_gossip(
        self, initial_agents: List[AgentCapabilities], already_discovered: Set[str]
    ) -> List[AgentCapabilities]:
        """
        Expand discovery by asking known agents for their peers (gossip protocol).

        Each FunnelCloud agent can discover peers on its local LAN via multicast.
        By querying the /discover-peers HTTP endpoint on each agent, we can
        discover agents across multiple subnets without hardcoding any IPs.

        If GOSSIP_SEED_HOST is configured, we also query that agent first to
        bootstrap cross-subnet discovery (useful when local agent can only see
        its own subnet via multicast).

        This runs for multiple rounds until no new agents are found or we hit
        the max rounds limit.

        Args:
            initial_agents: Agents already discovered (to query for their peers)
            already_discovered: Set of agent IDs already known

        Returns:
            List of newly discovered agents
        """
        new_agents: List[AgentCapabilities] = []
        known_ids = set(already_discovered)
        agents_to_query = list(initial_agents)
        queried_ips: Set[str] = set()

        # If we have a gossip seed configured, add it as a synthetic agent to query
        # This bootstraps cross-subnet discovery when local agent can't multicast to other LANs
        if GOSSIP_SEED_HOST and GOSSIP_SEED_HOST not in queried_ips:
            # Check if seed is already in our initial agents
            seed_already_known = any(
                agent.ip_address == GOSSIP_SEED_HOST for agent in initial_agents
            )
            if not seed_already_known:
                logger.info(
                    "Adding gossip seed agent at %s for cross-subnet bootstrap",
                    GOSSIP_SEED_HOST,
                )
                seed_agent = AgentCapabilities(
                    agent_id="gossip-seed",
                    hostname="gossip-seed",
                    platform="unknown",
                    capabilities=[],
                    workspace_roots=[],
                    certificate_fingerprint="",
                    ip_address=GOSSIP_SEED_HOST,
                )
                agents_to_query.append(seed_agent)

        for round_num in range(GOSSIP_MAX_ROUNDS):
            if not agents_to_query:
                break

            logger.info(
                "Gossip round %d: querying %d agent(s) for peers...",
                round_num + 1,
                len(agents_to_query),
            )

            # Query all agents in this round in parallel
            tasks = []
            for agent in agents_to_query:
                if agent.ip_address and agent.ip_address not in queried_ips:
                    tasks.append(self._query_agent_peers(agent))
                    queried_ips.add(agent.ip_address)

            if not tasks:
                break

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect new agents for next round
            round_new_agents: List[AgentCapabilities] = []

            for result in results:
                if isinstance(result, list):
                    for agent in result:
                        if agent.agent_id not in known_ids:
                            new_agents.append(agent)
                            round_new_agents.append(agent)
                            known_ids.add(agent.agent_id)
                            logger.info(
                                "Gossip discovered: %s at %s (%s)",
                                agent.agent_id,
                                agent.ip_address,
                                agent.platform,
                            )
                elif isinstance(result, Exception):
                    logger.debug("Gossip query exception: %s", result)

            # Next round will query the newly discovered agents
            agents_to_query = round_new_agents

            if not round_new_agents:
                logger.debug(
                    "Gossip round %d found no new agents, stopping", round_num + 1
                )
                break

        logger.info(
            "Gossip discovery found %d new agent(s) across %d round(s)",
            len(new_agents),
            round_num + 1,
        )
        return new_agents

    async def _query_agent_peers(
        self, agent: AgentCapabilities
    ) -> List[AgentCapabilities]:
        """
        Query a single agent for its known peers via HTTP.

        Uses the /peers endpoint first (fast, cached) and falls back to
        /discover-peers (triggers multicast) if /peers fails.

        Args:
            agent: The agent to query

        Returns:
            List of agents known to this agent
        """
        peers: List[AgentCapabilities] = []

        if not agent.ip_address:
            logger.debug("Skipping gossip query for %s - no IP address", agent.agent_id)
            return peers

        # Try /peers first (fast, no multicast)
        peers_url = f"http://{agent.ip_address}:{AGENT_HTTP_PORT}/peers"
        discover_url = f"http://{agent.ip_address}:{AGENT_HTTP_PORT}/discover-peers"

        logger.debug("Querying %s at %s for peers", agent.agent_id, peers_url)

        try:
            timeout = aiohttp.ClientTimeout(total=max(GOSSIP_TIMEOUT, 5.0))
            async with aiohttp.ClientSession() as session:
                # Try /peers first (cached, fast)
                try:
                    async with session.get(peers_url, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            agent_list = data.get("agents", data.get("peers", []))
                            if agent_list:
                                logger.debug(
                                    "Agent %s returned %d cached peers",
                                    agent.agent_id,
                                    len(agent_list),
                                )
                                return self._parse_peers(agent_list, agent.agent_id)
                except Exception as e:
                    logger.debug(
                        "Cached peers query failed for %s: %s, trying discover-peers",
                        agent.agent_id,
                        e,
                    )

                # Fall back to /discover-peers (triggers multicast)
                async with session.get(discover_url, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        agent_list = data.get("agents", data.get("peers", []))
                        logger.debug(
                            "Agent %s returned %d peers via discovery",
                            agent.agent_id,
                            len(agent_list),
                        )
                        return self._parse_peers(agent_list, agent.agent_id)
                    else:
                        logger.warning(
                            "Agent %s returned status %d for peer discovery",
                            agent.agent_id,
                            response.status,
                        )
        except asyncio.TimeoutError:
            logger.warning(
                "Peer query to %s timed out after %.1fs", agent.agent_id, GOSSIP_TIMEOUT
            )
        except aiohttp.ClientError as e:
            logger.warning("HTTP error querying %s for peers: %s", agent.agent_id, e)
        except Exception as e:
            logger.debug("Failed to query %s for peers: %s", agent.agent_id, e)

        return peers

    def _parse_peers(
        self, agent_list: List[dict], source_agent_id: str
    ) -> List[AgentCapabilities]:
        """Parse a list of peer data dicts into AgentCapabilities objects."""
        peers: List[AgentCapabilities] = []
        for peer_data in agent_list:
            try:
                peer_ip = peer_data.get("ipAddress", peer_data.get("ip_address", ""))
                peer = AgentCapabilities.from_dict(peer_data, ip_address=peer_ip)
                peers.append(peer)
                logger.debug(
                    "Parsed peer from %s: %s at %s",
                    source_agent_id,
                    peer.agent_id,
                    peer.ip_address or "no-ip",
                )
            except Exception as e:
                logger.warning(
                    "Failed to parse peer data from %s: %s", source_agent_id, e
                )
        return peers

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
            ttl = struct.pack("b", 32)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

            # Bind to any available port for receiving responses
            sock.bind(("", 0))
            local_port = sock.getsockname()[1]
            logger.debug("Discovery socket bound to port %d", local_port)

            # Send to multicast group
            sock.sendto(DISCOVERY_MAGIC, (MULTICAST_GROUP, DISCOVERY_PORT))
            logger.debug(
                "Sent discovery to multicast group %s:%d",
                MULTICAST_GROUP,
                DISCOVERY_PORT,
            )

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
                        timeout=min(0.5, remaining),
                    )

                    # Parse response
                    try:
                        response = json.loads(data.decode("utf-8"))
                        agent = AgentCapabilities.from_dict(
                            response, ip_address=addr[0]
                        )
                        agents.append(agent)
                        logger.info(
                            "Discovered agent via multicast: %s at %s (%s)",
                            agent.agent_id,
                            addr[0],
                            agent.platform,
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
            agent for agent in self._cache.values() if capability in agent.capabilities
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
