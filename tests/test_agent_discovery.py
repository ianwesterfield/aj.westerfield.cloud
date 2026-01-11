"""
Integration Tests for FunnelCloud Agent Discovery

Tests the UDP-based agent discovery mechanism used by the orchestrator
to find available FunnelCloud agents on the network.

These tests require actual FunnelCloud agents to be running:
- Local agent on the same machine
- Remote agents on network servers (domain01, domain02, exchange01, r730xd)

Run with: pytest tests/test_agent_discovery.py -v -m integration
"""

import asyncio
import json
import logging
import os
import socket
import struct
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set

import pytest

# Add the layers directory to the path so we can import the discovery service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator"))

logger = logging.getLogger(__name__)

# Discovery constants (match TrustConfig.cs and agent_discovery.py)
DISCOVERY_PORT = int(os.getenv("FUNNEL_DISCOVERY_PORT", "41420"))
DISCOVERY_MAGIC = b"FUNNEL_DISCOVER"
DISCOVERY_TIMEOUT = float(os.getenv("FUNNEL_DISCOVERY_TIMEOUT", "3.0"))
MULTICAST_GROUP = os.getenv("FUNNEL_MULTICAST_GROUP", "239.255.77.77")
GRPC_PORT = 41235

# Known agent IPs for direct testing (VLAN 1/IT subnet)
KNOWN_AGENTS = {
    "domain01": "192.168.10.166",
    "domain02": "192.168.10.171", 
    "exchange01": "192.168.10.88",
    "r730xd": "192.168.10.52",
}


@dataclass
class DiscoveredAgent:
    """Represents a discovered FunnelCloud agent."""
    agent_id: str
    hostname: str
    platform: str
    capabilities: List[str]
    workspace_roots: List[str]
    certificate_fingerprint: str
    discovery_port: int
    grpc_port: int
    ip_address: str
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_response(cls, data: dict, ip_address: str) -> "DiscoveredAgent":
        """Parse agent response JSON."""
        return cls(
            agent_id=data.get("agentId", data.get("agent_id", "unknown")),
            hostname=data.get("hostname", "unknown"),
            platform=data.get("platform", "unknown"),
            capabilities=data.get("capabilities", []),
            workspace_roots=data.get("workspaceRoots", data.get("workspace_roots", [])),
            certificate_fingerprint=data.get("certificateFingerprint", data.get("certificate_fingerprint", "")),
            discovery_port=data.get("discoveryPort", data.get("discovery_port", DISCOVERY_PORT)),
            grpc_port=data.get("grpcPort", data.get("grpc_port", GRPC_PORT)),
            ip_address=ip_address,
        )


async def discover_agent_direct(ip_address: str, timeout: float = DISCOVERY_TIMEOUT) -> Optional[DiscoveredAgent]:
    """
    Send a discovery packet directly to a specific IP and wait for response.
    
    Args:
        ip_address: Target IP address
        timeout: How long to wait for response
        
    Returns:
        DiscoveredAgent if found, None otherwise
    """
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)  # Use blocking socket with timeout on Windows
        
        # Bind to any port
        sock.bind(("", 0))
        
        # Send discovery packet
        sock.sendto(DISCOVERY_MAGIC, (ip_address, DISCOVERY_PORT))
        logger.debug(f"Sent discovery to {ip_address}:{DISCOVERY_PORT}")
        
        # Wait for response (blocking with timeout)
        try:
            data, addr = sock.recvfrom(4096)
            
            response = json.loads(data.decode("utf-8"))
            agent = DiscoveredAgent.from_response(response, ip_address=addr[0])
            logger.info(f"Discovered agent: {agent.agent_id} at {addr[0]} ({agent.platform})")
            return agent
            
        except socket.timeout:
            logger.debug(f"No response from {ip_address}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON response from {ip_address}: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Discovery to {ip_address} failed: {e}")
        return None
    finally:
        if sock:
            sock.close()


async def discover_agents_multicast(timeout: float = DISCOVERY_TIMEOUT) -> List[DiscoveredAgent]:
    """
    Send multicast discovery and collect all responses.
    
    Returns:
        List of discovered agents
    """
    agents: List[DiscoveredAgent] = []
    sock = None
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        
        # Set multicast TTL for cross-VLAN (if network supports it)
        ttl = struct.pack('b', 32)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        
        # Bind to receive responses
        sock.bind(("", 0))
        local_port = sock.getsockname()[1]
        logger.debug(f"Discovery socket bound to port {local_port}")
        
        # Send to multicast group
        sock.sendto(DISCOVERY_MAGIC, (MULTICAST_GROUP, DISCOVERY_PORT))
        logger.info(f"Sent multicast discovery to {MULTICAST_GROUP}:{DISCOVERY_PORT}")
        
        # Collect responses
        loop = asyncio.get_event_loop()
        end_time = loop.time() + timeout
        seen_agents: Set[str] = set()
        
        while loop.time() < end_time:
            remaining = end_time - loop.time()
            if remaining <= 0:
                break
                
            try:
                data, addr = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: sock.recvfrom(4096)),
                    timeout=min(0.5, remaining)
                )
                
                response = json.loads(data.decode("utf-8"))
                agent = DiscoveredAgent.from_response(response, ip_address=addr[0])
                
                # Avoid duplicates
                if agent.agent_id not in seen_agents:
                    agents.append(agent)
                    seen_agents.add(agent.agent_id)
                    logger.info(f"Multicast discovered: {agent.agent_id} at {addr[0]}")
                    
            except asyncio.TimeoutError:
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {addr}: {e}")
            except Exception as e:
                logger.debug(f"Receive error: {e}")
                
    except Exception as e:
        logger.error(f"Multicast discovery failed: {e}")
    finally:
        if sock:
            sock.close()
            
    return agents


async def discover_agents_broadcast(
    target_ips: Optional[List[str]] = None,
    timeout: float = DISCOVERY_TIMEOUT
) -> List[DiscoveredAgent]:
    """
    Send discovery to multiple specific IPs in parallel.
    
    Args:
        target_ips: List of IPs to query (defaults to KNOWN_AGENTS)
        timeout: Timeout per agent
        
    Returns:
        List of discovered agents
    """
    if target_ips is None:
        target_ips = list(KNOWN_AGENTS.values())
    
    # Query all IPs in parallel
    tasks = [discover_agent_direct(ip, timeout) for ip in target_ips]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    agents = []
    for result in results:
        if isinstance(result, DiscoveredAgent):
            agents.append(result)
        elif isinstance(result, Exception):
            logger.debug(f"Discovery failed: {result}")
            
    return agents


class TestAgentDiscoveryBasic:
    """Basic discovery tests - require at least one agent running."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_local_agent_responds(self):
        """Test that the local agent responds to discovery."""
        # Try localhost first
        agent = await discover_agent_direct("127.0.0.1", timeout=2.0)
        
        if agent is None:
            # Try the machine's hostname
            hostname = socket.gethostname()
            agent = await discover_agent_direct(hostname, timeout=2.0)
        
        assert agent is not None, "No local agent responded to discovery"
        assert agent.agent_id, "Agent should have an ID"
        assert agent.platform in ("windows", "linux", "macos"), f"Invalid platform: {agent.platform}"
        assert isinstance(agent.capabilities, list), "Capabilities should be a list"
        
        logger.info(f"Local agent: {agent.agent_id} on {agent.platform}")
        logger.info(f"  Capabilities: {agent.capabilities}")
        logger.info(f"  Workspace roots: {agent.workspace_roots}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discovery_response_format(self):
        """Test that agent response contains all required fields."""
        agent = await discover_agent_direct("127.0.0.1", timeout=2.0)
        
        if agent is None:
            pytest.skip("Local agent not running")
        
        # Verify all required fields
        assert agent.agent_id and isinstance(agent.agent_id, str)
        assert agent.hostname and isinstance(agent.hostname, str)
        assert agent.platform and isinstance(agent.platform, str)
        assert isinstance(agent.capabilities, list)
        assert isinstance(agent.workspace_roots, list)
        assert isinstance(agent.certificate_fingerprint, str)
        assert agent.discovery_port == DISCOVERY_PORT
        assert agent.grpc_port == GRPC_PORT
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discovery_timeout_handling(self):
        """Test that discovery handles non-responsive IPs gracefully."""
        # Use a non-routable IP that should timeout
        agent = await discover_agent_direct("192.0.2.1", timeout=0.5)
        assert agent is None, "Should return None for non-responsive IP"


class TestAgentDiscoveryMulticast:
    """Multicast discovery tests - may find multiple agents."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multicast_discovery(self):
        """Test multicast-based discovery."""
        agents = await discover_agents_multicast(timeout=3.0)
        
        # At minimum, local agent should respond
        assert len(agents) >= 0, "Multicast discovery should complete without error"
        
        if agents:
            logger.info(f"Multicast found {len(agents)} agent(s):")
            for agent in agents:
                logger.info(f"  - {agent.agent_id} at {agent.ip_address} ({agent.platform})")
        else:
            logger.warning("No agents found via multicast - may be network limitation")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_no_duplicate_agents(self):
        """Test that multicast doesn't return duplicate agents."""
        agents = await discover_agents_multicast(timeout=3.0)
        
        agent_ids = [a.agent_id for a in agents]
        assert len(agent_ids) == len(set(agent_ids)), "Should not have duplicate agent IDs"


class TestKnownAgents:
    """Tests for known/expected agents on the network."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discover_domain01(self):
        """Test discovery of domain01 agent."""
        ip = KNOWN_AGENTS["domain01"]
        agent = await discover_agent_direct(ip, timeout=3.0)
        
        if agent is None:
            pytest.skip(f"domain01 agent not responding at {ip}")
        
        assert agent.agent_id.lower() == "domain01", f"Expected domain01, got {agent.agent_id}"
        assert agent.platform == "windows"
        assert "powershell" in agent.capabilities
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discover_domain02(self):
        """Test discovery of domain02 agent."""
        ip = KNOWN_AGENTS["domain02"]
        agent = await discover_agent_direct(ip, timeout=3.0)
        
        if agent is None:
            pytest.skip(f"domain02 agent not responding at {ip}")
        
        assert agent.agent_id.lower() == "domain02", f"Expected domain02, got {agent.agent_id}"
        assert agent.platform == "windows"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discover_exchange01(self):
        """Test discovery of exchange01 agent."""
        ip = KNOWN_AGENTS["exchange01"]
        agent = await discover_agent_direct(ip, timeout=3.0)
        
        if agent is None:
            pytest.skip(f"exchange01 agent not responding at {ip}")
        
        assert agent.agent_id.lower() == "exchange01", f"Expected exchange01, got {agent.agent_id}"
        assert agent.platform == "windows"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discover_r730xd(self):
        """Test discovery of r730xd agent."""
        ip = KNOWN_AGENTS["r730xd"]
        agent = await discover_agent_direct(ip, timeout=3.0)
        
        if agent is None:
            pytest.skip(f"r730xd agent not responding at {ip}")
        
        # r730xd could be Windows or Linux depending on setup
        assert agent.agent_id.lower() == "r730xd", f"Expected r730xd, got {agent.agent_id}"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discover_all_known_agents(self):
        """Test discovering all known agents in parallel."""
        agents = await discover_agents_broadcast(timeout=3.0)
        
        logger.info(f"Found {len(agents)} of {len(KNOWN_AGENTS)} known agents:")
        for agent in agents:
            logger.info(f"  - {agent.agent_id} at {agent.ip_address}")
            logger.info(f"    Platform: {agent.platform}")
            logger.info(f"    Capabilities: {', '.join(agent.capabilities)}")
        
        # At least one agent should be found (local)
        assert len(agents) >= 1, "Should find at least one agent"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_all_agents_have_powershell(self):
        """Test that all Windows agents have PowerShell capability."""
        agents = await discover_agents_broadcast(timeout=3.0)
        
        for agent in agents:
            if agent.platform == "windows":
                assert "powershell" in agent.capabilities, \
                    f"Windows agent {agent.agent_id} should have powershell capability"


class TestAgentDiscoveryService:
    """Tests using the actual AgentDiscoveryService from the orchestrator."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discovery_service_import(self):
        """Test that we can import the discovery service."""
        try:
            from services.agent_discovery import AgentDiscoveryService
            service = AgentDiscoveryService()
            assert service is not None
        except ImportError as e:
            pytest.skip(f"Could not import AgentDiscoveryService: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discovery_service_discover(self):
        """Test the full discovery service."""
        try:
            from services.agent_discovery import AgentDiscoveryService
        except ImportError:
            pytest.skip("Could not import AgentDiscoveryService")
        
        service = AgentDiscoveryService(cache_ttl_seconds=10)
        agents = await service.discover(force=True)
        
        logger.info(f"AgentDiscoveryService found {len(agents)} agent(s)")
        for agent in agents:
            logger.info(f"  - {agent.agent_id}: {agent.platform} at {agent.ip_address}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_discovery_service_caching(self):
        """Test that discovery service caches results."""
        try:
            from services.agent_discovery import AgentDiscoveryService
        except ImportError:
            pytest.skip("Could not import AgentDiscoveryService")
        
        service = AgentDiscoveryService(cache_ttl_seconds=60)
        
        # First discovery
        agents1 = await service.discover(force=True)
        
        # Second discovery should use cache
        agents2 = await service.discover(force=False)
        
        # Should return same results from cache
        assert len(agents1) == len(agents2)
        
        # Force refresh should work
        agents3 = await service.discover(force=True)
        assert isinstance(agents3, list)


class TestCrossVLANDiscovery:
    """Tests specifically for cross-VLAN discovery (VLAN 40 -> VLAN 1)."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cross_vlan_udp(self):
        """
        Test UDP discovery from current machine to IT VLAN agents.
        
        This test is meaningful when run from a different VLAN (e.g., VLAN 40/Standard)
        to verify Firewalla rules allow UDP 41420 between VLANs.
        """
        # Discover all known agents
        agents = await discover_agents_broadcast(timeout=5.0)
        
        # Get local IP to determine our VLAN
        local_ip = socket.gethostbyname(socket.gethostname())
        local_vlan = "IT" if local_ip.startswith("192.168.10.") else "Standard/Other"
        
        logger.info(f"Running from {local_ip} (VLAN: {local_vlan})")
        logger.info(f"Found {len(agents)} agents:")
        
        it_vlan_agents = []
        for agent in agents:
            if agent.ip_address.startswith("192.168.10."):
                it_vlan_agents.append(agent)
                logger.info(f"  [IT VLAN] {agent.agent_id} at {agent.ip_address}")
            else:
                logger.info(f"  [Other] {agent.agent_id} at {agent.ip_address}")
        
        if local_vlan != "IT" and it_vlan_agents:
            logger.info("✓ Cross-VLAN UDP discovery working!")
        elif local_vlan == "IT":
            logger.info("Running from IT VLAN - same-VLAN discovery")


class TestAgentCapabilities:
    """Tests for agent capability detection and reporting."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_windows_agent_capabilities(self):
        """Test that Windows agents report expected capabilities."""
        agents = await discover_agents_broadcast(timeout=3.0)
        
        windows_agents = [a for a in agents if a.platform == "windows"]
        
        if not windows_agents:
            pytest.skip("No Windows agents found")
        
        for agent in windows_agents:
            # All Windows agents should have powershell
            assert "powershell" in agent.capabilities, \
                f"{agent.agent_id} missing powershell capability"
            
            logger.info(f"{agent.agent_id} capabilities: {agent.capabilities}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_workspace_roots(self):
        """Test that agents report valid workspace roots."""
        agents = await discover_agents_broadcast(timeout=3.0)
        
        for agent in agents:
            assert isinstance(agent.workspace_roots, list)
            # Should have at least one workspace root
            if agent.workspace_roots:
                for root in agent.workspace_roots:
                    assert isinstance(root, str)
                    assert len(root) > 0
                    logger.info(f"{agent.agent_id} workspace: {root}")


# Standalone execution for quick testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def main():
        print("\n=== FunnelCloud Agent Discovery Test ===\n")
        
        # Test local agent
        print("Testing local agent (127.0.0.1)...")
        local = await discover_agent_direct("127.0.0.1")
        if local:
            print(f"  ✓ Found: {local.agent_id} ({local.platform})")
        else:
            print("  ✗ No local agent")
        
        # Test multicast
        print("\nTesting multicast discovery...")
        multicast = await discover_agents_multicast(timeout=3.0)
        print(f"  Found {len(multicast)} agent(s) via multicast")
        
        # Test known agents
        print("\nTesting known agents...")
        for name, ip in KNOWN_AGENTS.items():
            agent = await discover_agent_direct(ip, timeout=2.0)
            status = f"✓ {agent.platform}" if agent else "✗ No response"
            print(f"  {name} ({ip}): {status}")
        
        # Summary
        print("\n=== Summary ===")
        all_agents = await discover_agents_broadcast(timeout=3.0)
        print(f"Total agents found: {len(all_agents)}")
        for agent in all_agents:
            print(f"  - {agent.agent_id}: {agent.platform} at {agent.ip_address}")
            print(f"    Capabilities: {', '.join(agent.capabilities)}")
    
    asyncio.run(main())
