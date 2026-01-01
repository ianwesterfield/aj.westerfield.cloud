#!/usr/bin/env python3
"""
FunnelCloud Integration Test

Tests the complete flow:
1. UDP Discovery - Find agents on the network
2. gRPC Connection - Connect with mTLS
3. Task Execution - Execute a command and receive output
4. Streaming - Execute with streaming output

Usage:
    python test_funnelcloud.py
    
    # With specific agent
    python test_funnelcloud.py --agent-id DEV-WORKSTATION
    
    # Skip mTLS (insecure - dev only)
    python test_funnelcloud.py --insecure

Requirements:
    - FunnelCloud agent running on the network
    - mTLS certificates (or --insecure for dev testing)
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agent_discovery import get_discovery_service, AgentDiscoveryService
from services.grpc_client import get_grpc_client, AgentGrpcClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("funnelcloud.test")


class TestRunner:
    """Integration test runner for FunnelCloud."""
    
    def __init__(self, agent_id: str = None, insecure: bool = False):
        self.discovery = get_discovery_service()
        self.grpc_client = get_grpc_client()
        self.target_agent_id = agent_id
        self.insecure = insecure
        
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        logger.info(f"{status}: {name}")
        if details:
            for line in details.split("\n"):
                logger.info(f"       {line}")
    
    def log_skip(self, name: str, reason: str):
        """Log a skipped test."""
        self.skipped += 1
        logger.warning(f"⏭️ SKIP: {name} - {reason}")
    
    async def test_discovery(self) -> list:
        """Test 1: UDP Discovery"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: UDP Discovery")
        logger.info("=" * 60)
        
        try:
            # Force fresh discovery
            agents = await self.discovery.discover(force=True)
            
            if agents:
                details = f"Found {len(agents)} agent(s):\n"
                for agent in agents:
                    details += f"  - {agent.agent_id} @ {agent.ip_address}:{agent.grpc_port}\n"
                    details += f"    Platform: {agent.platform}, Capabilities: {agent.capabilities}\n"
                
                self.log_test("UDP Discovery", True, details)
                return agents
            else:
                self.log_test("UDP Discovery", False, "No agents discovered")
                return []
                
        except Exception as e:
            self.log_test("UDP Discovery", False, f"Error: {e}")
            return []
    
    async def test_ping(self, agent_id: str) -> bool:
        """Test 2: gRPC Ping"""
        logger.info("\n" + "=" * 60)
        logger.info(f"TEST 2: gRPC Ping ({agent_id})")
        logger.info("=" * 60)
        
        try:
            result = await self.grpc_client.ping(agent_id)
            
            if result.get("success"):
                details = (
                    f"Agent: {result.get('agent_id')} ({result.get('hostname')})\n"
                    f"Round-trip time: {result.get('round_trip_ms')}ms"
                )
                self.log_test("gRPC Ping", True, details)
                return True
            else:
                details = f"Error: {result.get('error')} - {result.get('details')}"
                self.log_test("gRPC Ping", False, details)
                return False
                
        except Exception as e:
            self.log_test("gRPC Ping", False, f"Exception: {e}")
            return False
    
    async def test_execute_simple(self, agent_id: str) -> bool:
        """Test 3: Simple command execution"""
        logger.info("\n" + "=" * 60)
        logger.info(f"TEST 3: Simple Execution ({agent_id})")
        logger.info("=" * 60)
        
        try:
            # Simple PowerShell command
            command = 'Write-Output "Hello from FunnelCloud test at $(Get-Date)"'
            
            result = await self.grpc_client.execute(
                agent_id=agent_id,
                command=command,
                task_type="powershell",
                timeout_seconds=10,
            )
            
            if result.success:
                details = (
                    f"Command: {command[:50]}...\n"
                    f"Exit code: {result.exit_code}\n"
                    f"Duration: {result.duration_ms}ms\n"
                    f"Stdout: {result.stdout.strip()[:100]}"
                )
                self.log_test("Simple Execution", True, details)
                return True
            else:
                details = (
                    f"Exit code: {result.exit_code}\n"
                    f"Error: {result.error_code}\n"
                    f"Stderr: {result.stderr[:200]}"
                )
                self.log_test("Simple Execution", False, details)
                return False
                
        except Exception as e:
            self.log_test("Simple Execution", False, f"Exception: {e}")
            return False
    
    async def test_execute_with_output(self, agent_id: str) -> bool:
        """Test 4: Command with substantial output"""
        logger.info("\n" + "=" * 60)
        logger.info(f"TEST 4: Command with Output ({agent_id})")
        logger.info("=" * 60)
        
        try:
            # Get process list
            command = 'Get-Process | Select-Object -First 5 | Format-Table Name, Id, CPU -AutoSize'
            
            result = await self.grpc_client.execute(
                agent_id=agent_id,
                command=command,
                task_type="powershell",
                timeout_seconds=15,
            )
            
            if result.success and result.stdout:
                lines = result.stdout.strip().split("\n")
                details = (
                    f"Got {len(lines)} lines of output\n"
                    f"First line: {lines[0][:60] if lines else 'N/A'}\n"
                    f"Duration: {result.duration_ms}ms"
                )
                self.log_test("Command with Output", True, details)
                return True
            else:
                details = f"No output or failed. Exit: {result.exit_code}, Stderr: {result.stderr[:100]}"
                self.log_test("Command with Output", False, details)
                return False
                
        except Exception as e:
            self.log_test("Command with Output", False, f"Exception: {e}")
            return False
    
    async def test_streaming_execution(self, agent_id: str) -> bool:
        """Test 5: Streaming execution"""
        logger.info("\n" + "=" * 60)
        logger.info(f"TEST 5: Streaming Execution ({agent_id})")
        logger.info("=" * 60)
        
        try:
            # Command that produces multiple outputs
            command = '''
            1..5 | ForEach-Object {
                Write-Output "Line $_"
                Start-Sleep -Milliseconds 200
            }
            '''
            
            outputs = []
            async for output in self.grpc_client.execute_streaming(
                agent_id=agent_id,
                command=command,
                task_type="powershell",
                timeout_seconds=15,
            ):
                outputs.append(output)
                if output.output_type == "error":
                    self.log_test("Streaming Execution", False, f"Stream error: {output.content}")
                    return False
            
            if outputs:
                stdout_outputs = [o for o in outputs if o.output_type == "stdout"]
                details = (
                    f"Received {len(outputs)} output events\n"
                    f"Stdout events: {len(stdout_outputs)}\n"
                    f"Sample: {outputs[0].content[:50] if outputs else 'N/A'}..."
                )
                self.log_test("Streaming Execution", True, details)
                return True
            else:
                self.log_test("Streaming Execution", False, "No streaming output received")
                return False
                
        except Exception as e:
            self.log_test("Streaming Execution", False, f"Exception: {e}")
            return False
    
    async def test_error_handling(self, agent_id: str) -> bool:
        """Test 6: Error handling for invalid commands"""
        logger.info("\n" + "=" * 60)
        logger.info(f"TEST 6: Error Handling ({agent_id})")
        logger.info("=" * 60)
        
        try:
            # Invalid command that should fail
            command = 'Get-NonExistentCmdlet -ThisDoesNotExist'
            
            result = await self.grpc_client.execute(
                agent_id=agent_id,
                command=command,
                task_type="powershell",
                timeout_seconds=10,
            )
            
            # Expected to fail
            if not result.success and result.exit_code != 0:
                details = (
                    f"Correctly reported failure\n"
                    f"Exit code: {result.exit_code}\n"
                    f"Error code: {result.error_code}\n"
                    f"Stderr (first 100 chars): {result.stderr[:100]}"
                )
                self.log_test("Error Handling", True, details)
                return True
            else:
                details = f"Expected failure but got success. Stdout: {result.stdout[:100]}"
                self.log_test("Error Handling", False, details)
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "=" * 70)
        print("  FUNNELCLOUD INTEGRATION TEST SUITE")
        print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 70)
        
        # Test 1: Discovery
        agents = await self.test_discovery()
        
        if not agents:
            print("\n" + "=" * 70)
            print("❌ CANNOT CONTINUE: No agents discovered")
            print("   Make sure FunnelCloud agent is running.")
            print("=" * 70)
            return self.print_summary()
        
        # Select target agent
        if self.target_agent_id:
            agent = next((a for a in agents if a.agent_id == self.target_agent_id), None)
            if not agent:
                print(f"\n❌ Agent '{self.target_agent_id}' not found in discovered agents")
                return self.print_summary()
        else:
            agent = agents[0]  # Use first discovered agent
        
        logger.info(f"\nUsing agent: {agent.agent_id} @ {agent.ip_address}")
        
        # Test 2: Ping
        ping_ok = await self.test_ping(agent.agent_id)
        
        if not ping_ok:
            print("\n" + "=" * 70)
            print("❌ CANNOT CONTINUE: Ping failed")
            print("   Check gRPC connectivity and mTLS certificates.")
            print("=" * 70)
            return self.print_summary()
        
        # Test 3-6: Execution tests
        await self.test_execute_simple(agent.agent_id)
        await self.test_execute_with_output(agent.agent_id)
        await self.test_streaming_execution(agent.agent_id)
        await self.test_error_handling(agent.agent_id)
        
        return self.print_summary()
    
    def print_summary(self) -> int:
        """Print test summary and return exit code."""
        print("\n" + "=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)
        print(f"  ✅ Passed:  {self.passed}")
        print(f"  ❌ Failed:  {self.failed}")
        print(f"  ⏭️ Skipped: {self.skipped}")
        print("-" * 70)
        
        total = self.passed + self.failed
        if total > 0:
            success_rate = (self.passed / total) * 100
            print(f"  Success rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n  🎉 ALL TESTS PASSED!")
        else:
            print(f"\n  ⚠️ {self.failed} TEST(S) FAILED")
        
        print("=" * 70)
        
        return 0 if self.failed == 0 else 1


async def main():
    parser = argparse.ArgumentParser(description="FunnelCloud Integration Tests")
    parser.add_argument("--agent-id", help="Specific agent ID to test")
    parser.add_argument("--insecure", action="store_true", help="Skip mTLS (dev only)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = TestRunner(agent_id=args.agent_id, insecure=args.insecure)
    return await runner.run_all_tests()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
