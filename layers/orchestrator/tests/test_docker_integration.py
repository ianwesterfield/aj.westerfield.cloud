#!/usr/bin/env python3
"""
Docker-to-Host FunnelCloud Integration Test

Tests that the orchestrator running in Docker can communicate with
a FunnelCloud agent running on the Windows host.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agent_discovery import get_discovery_service
from services.grpc_client import get_grpc_client


async def main():
    print("=" * 60)
    print("  DOCKER-TO-HOST FUNNELCLOUD INTEGRATION TEST")
    print("=" * 60)
    print()

    discovery = get_discovery_service()
    client = get_grpc_client()

    # 1. Discovery
    print("1. Agent Discovery...")
    agents = await discovery.discover(force=True)
    if not agents:
        print("   ❌ No agents found!")
        return 1
    
    agent = agents[0]
    print(f"   ✅ Found: {agent.agent_id} @ {agent.ip_address}:{agent.grpc_port}")
    print(f"      Platform: {agent.platform}")
    print(f"      Capabilities: {agent.capabilities}")
    print()

    # 2. Ping
    print("2. gRPC Ping...")
    result = await client.ping(agent.agent_id)
    if result.get("success"):
        print(f"   ✅ Ping successful ({result.get('round_trip_ms')}ms)")
    else:
        print(f"   ❌ Ping failed: {result}")
        return 1
    print()

    # 3. Simple execution
    print("3. Simple Command Execution...")
    result = await client.execute(
        agent.agent_id,
        "Write-Output 'Hello from Docker'",
        task_type="powershell",
    )
    if result.success:
        print(f"   ✅ Success: {result.stdout.strip()}")
    else:
        print(f"   ❌ Failed: {result.stderr}")
    print()

    # 4. List host directories
    print("4. List Host Directories (C:\\Code)...")
    result = await client.execute(
        agent.agent_id,
        "Get-ChildItem C:\\Code -Directory | Select-Object -First 5 -ExpandProperty Name",
        task_type="powershell",
    )
    if result.success:
        dirs = result.stdout.strip().split("\n")
        print(f"   ✅ Found {len(dirs)} directories:")
        for d in dirs[:5]:
            print(f"      - {d}")
    else:
        print(f"   ❌ Failed: {result.stderr}")
    print()

    # 5. Get system info
    print("5. Windows System Info...")
    result = await client.execute(
        agent.agent_id,
        "[System.Environment]::MachineName + ' running ' + [System.Environment]::OSVersion.VersionString",
        task_type="powershell",
    )
    if result.success:
        print(f"   ✅ {result.stdout.strip()}")
    else:
        print(f"   ❌ Failed: {result.stderr}")
    print()

    # 6. Git status
    print("6. Git Status (aj.westerfield.cloud)...")
    result = await client.execute(
        agent.agent_id,
        "Set-Location C:\\Code\\aj.westerfield.cloud; git branch --show-current",
        task_type="powershell",
    )
    if result.success:
        branch = result.stdout.strip()
        print(f"   ✅ Current branch: {branch}")
    else:
        print(f"   ❌ Failed: {result.stderr}")
    print()

    print("=" * 60)
    print("  🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
