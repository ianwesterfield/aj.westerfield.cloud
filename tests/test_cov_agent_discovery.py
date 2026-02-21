"""Tests for AgentDiscoveryService – 100 % coverage target."""

import pytest
import sys
import os
import json
import asyncio
import socket
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.agent_discovery import (
    AgentCapabilities,
    AgentDiscoveryService,
    get_discovery_service,
    DISCOVERY_PORT,
    AGENT_HTTP_PORT,
)


# ── helpers ──────────────────────────────────────────────────────────
def _cap(agent_id="a1", ip="10.0.0.1", platform="linux", **kw):
    return AgentCapabilities(
        agent_id=agent_id,
        hostname=kw.get("hostname", agent_id),
        platform=platform,
        capabilities=kw.get("capabilities", ["shell"]),
        workspace_roots=kw.get("workspace_roots", ["/home"]),
        certificate_fingerprint=kw.get("certificate_fingerprint", "abc"),
        ip_address=ip,
        grpc_port=kw.get("grpc_port", 41235),
    )


def _cap_dict(agent_id="a1", ip="10.0.0.1", platform="linux", **kw):
    return {
        "agentId": agent_id,
        "hostname": kw.get("hostname", agent_id),
        "platform": platform,
        "capabilities": kw.get("capabilities", ["shell"]),
        "workspaceRoots": kw.get("workspace_roots", ["/home"]),
        "certificateFingerprint": kw.get("certificate_fingerprint", "abc"),
        "grpcPort": kw.get("grpc_port", 41235),
        "ipAddress": ip,
    }


# ── AgentCapabilities dataclass ──────────────────────────────────────
class TestAgentCapabilities:
    def test_to_dict(self):
        cap = _cap()
        d = cap.to_dict()
        assert d["agent_id"] == "a1"
        assert d["ip_address"] == "10.0.0.1"
        assert "last_seen" in d

    def test_from_dict_camel_case(self):
        data = _cap_dict("b1", "10.0.0.2", "windows")
        cap = AgentCapabilities.from_dict(data)
        assert cap.agent_id == "b1"
        assert cap.ip_address == "10.0.0.2"
        assert cap.platform == "windows"

    def test_from_dict_snake_case(self):
        data = {
            "agent_id": "c1",
            "hostname": "c1",
            "platform": "macos",
            "capabilities": [],
            "workspace_roots": ["/Users"],
            "certificate_fingerprint": "xyz",
            "discovery_port": 9999,
            "grpc_port": 50000,
            "ip_address": "10.0.0.3",
        }
        cap = AgentCapabilities.from_dict(data)
        assert cap.agent_id == "c1"
        assert cap.discovery_port == 9999
        assert cap.grpc_port == 50000

    def test_from_dict_ip_override(self):
        data = _cap_dict("d1", "1.2.3.4")
        cap = AgentCapabilities.from_dict(data, ip_address="5.6.7.8")
        assert cap.ip_address == "5.6.7.8"

    def test_from_dict_defaults(self):
        cap = AgentCapabilities.from_dict({})
        assert cap.agent_id == "unknown"
        assert cap.hostname == "unknown"
        assert cap.platform == "unknown"
        assert cap.capabilities == []
        assert cap.workspace_roots == []


# ── AgentDiscoveryService – cache helpers ────────────────────────────
class TestCacheHelpers:
    def test_is_cache_valid_no_discovery(self):
        svc = AgentDiscoveryService()
        assert svc._is_cache_valid() is False

    def test_is_cache_valid_fresh(self):
        svc = AgentDiscoveryService(cache_ttl_seconds=300)
        svc._last_discovery = datetime.utcnow()
        assert svc._is_cache_valid() is True

    def test_is_cache_valid_expired(self):
        svc = AgentDiscoveryService(cache_ttl_seconds=1)
        svc._last_discovery = datetime.utcnow() - timedelta(seconds=10)
        assert svc._is_cache_valid() is False

    def test_get_agent(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1")
        assert svc.get_agent("a1").agent_id == "a1"
        assert svc.get_agent("nope") is None

    def test_get_agents_with_capability(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1", capabilities=["docker", "git"])
        svc._cache["a2"] = _cap("a2", capabilities=["shell"])
        result = svc.get_agents_with_capability("docker")
        assert len(result) == 1
        assert result[0].agent_id == "a1"

    def test_get_agents_for_workspace(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1", workspace_roots=["/home/user/code"])
        svc._cache["a2"] = _cap("a2", workspace_roots=["C:\\Users\\dev"])
        result = svc.get_agents_for_workspace("/home/user/code/project")
        assert len(result) == 1
        assert result[0].agent_id == "a1"

    def test_get_agents_for_workspace_windows_backslash(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1", workspace_roots=["C:\\Users\\dev"])
        result = svc.get_agents_for_workspace("C:\\Users\\dev\\project")
        assert len(result) == 1

    def test_mark_agent_stale(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1")
        svc.mark_agent_stale("a1")
        assert "a1" not in svc._cache

    def test_mark_agent_stale_missing(self):
        svc = AgentDiscoveryService()
        svc.mark_agent_stale("nope")  # no error

    def test_invalidate_cache(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1")
        svc._last_discovery = datetime.utcnow()
        svc.invalidate_cache()
        assert svc._cache == {}
        assert svc._last_discovery is None

    def test_list_agents(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1")
        result = svc.list_agents()
        assert len(result) == 1
        assert result[0]["agent_id"] == "a1"


# ── discover() orchestration ─────────────────────────────────────────
class TestDiscover:
    @pytest.mark.asyncio
    async def test_discover_returns_cached(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1")
        svc._last_discovery = datetime.utcnow()
        result = await svc.discover()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_discover_force_bypasses_cache(self):
        svc = AgentDiscoveryService()
        svc._cache["a1"] = _cap("a1")
        svc._last_discovery = datetime.utcnow()
        svc._discover_multicast = AsyncMock(return_value=[])
        result = await svc.discover(force=True)
        assert len(result) == 0  # cache was bypassed, multicast found nothing
        svc._discover_multicast.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_multicast_only(self):
        svc = AgentDiscoveryService()
        agent = _cap("m1")
        svc._discover_multicast = AsyncMock(return_value=[agent])
        result = await svc.discover(force=True)
        assert len(result) == 1
        assert result[0].agent_id == "m1"

    @pytest.mark.asyncio
    async def test_discover_deduplicates(self):
        svc = AgentDiscoveryService()
        agent = _cap("m1")
        svc._discover_multicast = AsyncMock(return_value=[agent, agent])
        result = await svc.discover(force=True)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_discover_uses_proxy_when_multicast_empty(self):
        svc = AgentDiscoveryService()
        svc._discover_multicast = AsyncMock(return_value=[])
        proxy_agent = _cap("p1")
        svc._discover_via_proxy = AsyncMock(return_value=[proxy_agent])
        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"):
            result = await svc.discover(force=True)
        assert len(result) == 1
        assert result[0].agent_id == "p1"

    @pytest.mark.asyncio
    async def test_discover_proxy_skipped_when_no_host(self):
        svc = AgentDiscoveryService()
        svc._discover_multicast = AsyncMock(return_value=[])
        svc._discover_via_proxy = AsyncMock(return_value=[])
        with patch("services.agent_discovery.LOCAL_AGENT_HOST", ""):
            result = await svc.discover(force=True)
        assert len(result) == 0
        svc._discover_via_proxy.assert_not_called()

    @pytest.mark.asyncio
    async def test_discover_gossip_expands(self):
        svc = AgentDiscoveryService()
        m1 = _cap("m1", "10.0.0.1")
        g1 = _cap("g1", "10.0.0.2")
        svc._discover_multicast = AsyncMock(return_value=[m1])
        svc._discover_via_gossip = AsyncMock(return_value=[g1])

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", ""), patch(
            "services.agent_discovery.GOSSIP_SEED_HOST", ""
        ):
            result = await svc.discover(force=True)

        assert len(result) == 2
        ids = {a.agent_id for a in result}
        assert ids == {"m1", "g1"}

    @pytest.mark.asyncio
    async def test_discover_cross_subnet_bootstrap(self):
        svc = AgentDiscoveryService()
        m1 = _cap("m1", "10.0.0.1")
        svc._discover_multicast = AsyncMock(return_value=[m1])
        svc._discover_via_gossip = AsyncMock(return_value=[])
        svc._bootstrap_cross_subnet = AsyncMock()

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.1"), patch(
            "services.agent_discovery.GOSSIP_SEED_HOST", "192.168.1.1"
        ):
            await svc.discover(force=True)

        svc._bootstrap_cross_subnet.assert_called_once_with("10.0.0.1", "192.168.1.1")


# ── _discover_multicast ──────────────────────────────────────────────
class TestDiscoverMulticast:
    @pytest.mark.asyncio
    async def test_multicast_success(self):
        svc = AgentDiscoveryService()
        agent_json = json.dumps(_cap_dict("mc1", "10.0.0.5")).encode("utf-8")
        responses = [agent_json]
        call_count = 0

        def fake_recvfrom(bufsize):
            nonlocal call_count
            if call_count < len(responses):
                call_count += 1
                return responses[call_count - 1], ("10.0.0.5", 41420)
            raise socket.timeout("done")

        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("", 12345)

        with patch("services.agent_discovery.socket.socket", return_value=mock_sock):
            # Make run_in_executor call the function directly
            loop = asyncio.get_event_loop()
            original_wait_for = asyncio.wait_for

            async def patched_wait_for(coro, timeout):
                try:
                    return await coro
                except socket.timeout:
                    raise asyncio.TimeoutError()

            with patch("asyncio.wait_for", side_effect=patched_wait_for):
                mock_sock.recvfrom = fake_recvfrom

                async def fake_run_in_executor(executor, func):
                    return func()

                with patch.object(
                    loop, "run_in_executor", side_effect=fake_run_in_executor
                ):
                    result = await svc._discover_multicast()

        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_multicast_socket_error(self):
        svc = AgentDiscoveryService()
        with patch(
            "services.agent_discovery.socket.socket",
            side_effect=OSError("no multicast"),
        ):
            result = await svc._discover_multicast()
        assert result == []

    @pytest.mark.asyncio
    async def test_multicast_invalid_json(self):
        svc = AgentDiscoveryService()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("", 12345)

        call_count = 0

        def fake_recvfrom(bufsize):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return b"not-json", ("10.0.0.5", 41420)
            raise socket.timeout("done")

        mock_sock.recvfrom = fake_recvfrom

        with patch("services.agent_discovery.socket.socket", return_value=mock_sock):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            async def patched_wait_for(coro, timeout):
                try:
                    return await coro
                except socket.timeout:
                    raise asyncio.TimeoutError()

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ), patch("asyncio.wait_for", side_effect=patched_wait_for):
                result = await svc._discover_multicast()

        assert result == []

    @pytest.mark.asyncio
    async def test_multicast_timeout_continues(self):
        """Timeout on recvfrom should continue the loop, not crash."""
        svc = AgentDiscoveryService()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("", 12345)

        def always_timeout(bufsize):
            raise socket.timeout("timeout")

        mock_sock.recvfrom = always_timeout

        with patch("services.agent_discovery.socket.socket", return_value=mock_sock):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            async def patched_wait_for(coro, timeout):
                try:
                    return await coro
                except socket.timeout:
                    raise asyncio.TimeoutError()

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ), patch("asyncio.wait_for", side_effect=patched_wait_for), patch(
                "services.agent_discovery.DISCOVERY_TIMEOUT", 0.01
            ):
                result = await svc._discover_multicast()

        assert result == []

    @pytest.mark.asyncio
    async def test_multicast_recv_generic_error(self):
        """recvfrom raises a non-timeout exception -> logged & continue."""
        svc = AgentDiscoveryService()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("", 12345)

        def bad_recv(bufsize):
            raise RuntimeError("recv broken")

        mock_sock.recvfrom = bad_recv

        with patch("services.agent_discovery.socket.socket", return_value=mock_sock):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            # The try/except in multicast catches the generic Exception
            # then continues the loop
            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ), patch("services.agent_discovery.DISCOVERY_TIMEOUT", 0.01):
                result = await svc._discover_multicast()

        assert result == []

    @pytest.mark.asyncio
    async def test_multicast_remaining_le_zero(self):
        """Cover the `if remaining <= 0: break` branch (line 569).

        We mock loop.time() so that:
          call 1 → 0   (end_time = 0 + DISCOVERY_TIMEOUT)
          call 2 → 0.5 (while condition passes)
          call 3 → 999 (remaining < 0 → break)
        No real asyncio scheduling happens before the break, so this is safe.
        """
        svc = AgentDiscoveryService()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("", 12345)

        with patch("services.agent_discovery.socket.socket", return_value=mock_sock):
            loop = asyncio.get_event_loop()
            time_values = iter([0, 0.5, 999])
            with patch.object(
                loop, "time", side_effect=lambda: next(time_values)
            ), patch("services.agent_discovery.DISCOVERY_TIMEOUT", 2.0):
                result = await svc._discover_multicast()

        assert result == []
        mock_sock.close.assert_called_once()


# ── _discover_via_proxy ──────────────────────────────────────────────
class TestDiscoverViaProxy:
    @pytest.mark.asyncio
    async def test_proxy_no_host(self):
        svc = AgentDiscoveryService()
        with patch("services.agent_discovery.LOCAL_AGENT_HOST", ""):
            result = await svc._discover_via_proxy()
        assert result == []

    @pytest.mark.asyncio
    async def test_proxy_success(self):
        svc = AgentDiscoveryService()
        response_data = {
            "discoveredBy": "local1",
            "agents": [_cap_dict("p1", "10.0.0.10")],
        }
        response_bytes = json.dumps(response_data).encode("utf-8")

        mock_sock = MagicMock()

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"), patch(
            "services.agent_discovery.socket.socket", return_value=mock_sock
        ):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            mock_sock.recvfrom = MagicMock(
                return_value=(response_bytes, ("10.0.0.99", 41420))
            )

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ):
                result = await svc._discover_via_proxy()

        assert len(result) == 1
        assert result[0].agent_id == "p1"

    @pytest.mark.asyncio
    async def test_proxy_agent_missing_ip_uses_host(self):
        """Agent discovered via proxy with no IP gets the proxy host IP."""
        svc = AgentDiscoveryService()
        agent_data = _cap_dict("local1", "")
        response_data = {"discoveredBy": "local1", "agents": [agent_data]}
        response_bytes = json.dumps(response_data).encode("utf-8")

        mock_sock = MagicMock()

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"), patch(
            "services.agent_discovery.socket.socket", return_value=mock_sock
        ):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            mock_sock.recvfrom = MagicMock(
                return_value=(response_bytes, ("10.0.0.99", 41420))
            )

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ):
                result = await svc._discover_via_proxy()

        assert len(result) == 1
        assert result[0].ip_address == "10.0.0.99"

    @pytest.mark.asyncio
    async def test_proxy_timeout(self):
        svc = AgentDiscoveryService()
        mock_sock = MagicMock()

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"), patch(
            "services.agent_discovery.socket.socket", return_value=mock_sock
        ):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                await asyncio.sleep(0)
                raise asyncio.TimeoutError()

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ), patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                result = await svc._discover_via_proxy()

        assert result == []
        mock_sock.close.assert_called()

    @pytest.mark.asyncio
    async def test_proxy_invalid_json(self):
        svc = AgentDiscoveryService()
        mock_sock = MagicMock()

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"), patch(
            "services.agent_discovery.socket.socket", return_value=mock_sock
        ):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            mock_sock.recvfrom = MagicMock(
                return_value=(b"not-json!", ("10.0.0.99", 41420))
            )

            # wait_for wraps the executor call
            async def real_wait_for(coro, timeout):
                return await coro

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ), patch("asyncio.wait_for", side_effect=real_wait_for):
                result = await svc._discover_via_proxy()

        assert result == []

    @pytest.mark.asyncio
    async def test_proxy_socket_error(self):
        svc = AgentDiscoveryService()
        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"), patch(
            "services.agent_discovery.socket.socket",
            side_effect=OSError("socket fail"),
        ):
            result = await svc._discover_via_proxy()
        assert result == []

    @pytest.mark.asyncio
    async def test_proxy_bad_agent_data(self):
        """Invalid agent data in the response is skipped, not crash."""
        svc = AgentDiscoveryService()
        response_data = {
            "discoveredBy": "local1",
            "agents": [{"INVALID": True}],  # parseable but weird
        }
        response_bytes = json.dumps(response_data).encode("utf-8")

        mock_sock = MagicMock()

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"), patch(
            "services.agent_discovery.socket.socket", return_value=mock_sock
        ):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            mock_sock.recvfrom = MagicMock(
                return_value=(response_bytes, ("10.0.0.99", 41420))
            )

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ):
                result = await svc._discover_via_proxy()

        # from_dict with weird data returns defaults, doesn't crash
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_proxy_agent_data_raises(self):
        """Lines 307-308: from_dict raises an exception for truly bad data."""
        svc = AgentDiscoveryService()
        response_data = {
            "discoveredBy": "local1",
            "agents": [{"agentId": "ok"}],
        }
        response_bytes = json.dumps(response_data).encode("utf-8")

        mock_sock = MagicMock()

        with patch("services.agent_discovery.LOCAL_AGENT_HOST", "10.0.0.99"), patch(
            "services.agent_discovery.socket.socket", return_value=mock_sock
        ):
            loop = asyncio.get_event_loop()

            async def fake_run_in_executor(executor, func):
                return func()

            mock_sock.recvfrom = MagicMock(
                return_value=(response_bytes, ("10.0.0.99", 41420))
            )

            with patch.object(
                loop, "run_in_executor", side_effect=fake_run_in_executor
            ), patch.object(
                AgentCapabilities, "from_dict", side_effect=TypeError("bad data")
            ):
                result = await svc._discover_via_proxy()

        assert result == []  # Agent data was rejected


# ── _bootstrap_cross_subnet ──────────────────────────────────────────
class TestBootstrapCrossSubnet:
    @pytest.mark.asyncio
    async def test_bootstrap_success(self):
        svc = AgentDiscoveryService()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "success": True,
                "agentId": "seed1",
                "ipAddress": "192.168.1.1",
            }
        )

        mock_session = AsyncMock()
        mock_session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_resp),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        with patch(
            "aiohttp.ClientSession",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            ),
        ):
            await svc._bootstrap_cross_subnet("10.0.0.1", "192.168.1.1")

    @pytest.mark.asyncio
    async def test_bootstrap_failure_response(self):
        svc = AgentDiscoveryService()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"success": False, "error": "already known"}
        )

        mock_session = AsyncMock()
        mock_session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_resp),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        with patch(
            "aiohttp.ClientSession",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            ),
        ):
            await svc._bootstrap_cross_subnet("10.0.0.1", "192.168.1.1")

    @pytest.mark.asyncio
    async def test_bootstrap_non_200(self):
        svc = AgentDiscoveryService()
        mock_resp = AsyncMock()
        mock_resp.status = 500

        mock_session = AsyncMock()
        mock_session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_resp),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        with patch(
            "aiohttp.ClientSession",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            ),
        ):
            await svc._bootstrap_cross_subnet("10.0.0.1", "192.168.1.1")

    @pytest.mark.asyncio
    async def test_bootstrap_exception(self):
        svc = AgentDiscoveryService()
        with patch("aiohttp.ClientSession", side_effect=Exception("net error")):
            await svc._bootstrap_cross_subnet("10.0.0.1", "192.168.1.1")


# ── _discover_via_gossip ─────────────────────────────────────────────
class TestDiscoverViaGossip:
    @pytest.mark.asyncio
    async def test_gossip_finds_new_agents(self):
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "10.0.0.1")]
        peer = _cap("g1", "10.0.0.2")

        svc._query_agent_peers = AsyncMock(return_value=[peer])
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", ""):
            result = await svc._discover_via_gossip(initial, {"a1"})
        assert len(result) == 1
        assert result[0].agent_id == "g1"

    @pytest.mark.asyncio
    async def test_gossip_deduplicates(self):
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "10.0.0.1")]
        svc._query_agent_peers = AsyncMock(
            return_value=[_cap("a1", "10.0.0.1")]  # same as known
        )
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", ""):
            result = await svc._discover_via_gossip(initial, {"a1"})
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_gossip_exception_handled(self):
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "10.0.0.1")]
        svc._query_agent_peers = AsyncMock(side_effect=Exception("gossip fail"))
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", ""):
            result = await svc._discover_via_gossip(initial, {"a1"})
        assert result == []

    @pytest.mark.asyncio
    async def test_gossip_no_ip_skipped(self):
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "")]  # no IP
        svc._query_agent_peers = AsyncMock(return_value=[])
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", ""):
            result = await svc._discover_via_gossip(initial, set())
        assert result == []
        svc._query_agent_peers.assert_not_called()

    @pytest.mark.asyncio
    async def test_gossip_seed_host_added(self):
        """When GOSSIP_SEED_HOST is set and not already known, it's added."""
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "10.0.0.1")]
        seed_peer = _cap("seed1", "192.168.1.1")
        a1_peers = []

        call_count = 0

        async def mock_query(agent):
            nonlocal call_count
            call_count += 1
            if agent.ip_address == "192.168.1.1":
                return [seed_peer]
            return a1_peers

        svc._query_agent_peers = mock_query
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", "192.168.1.1"):
            result = await svc._discover_via_gossip(initial, {"a1"})

        assert any(a.agent_id == "seed1" for a in result)

    @pytest.mark.asyncio
    async def test_gossip_seed_already_known(self):
        """When GOSSIP_SEED_HOST matches an existing agent IP, it's not duplicated."""
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "192.168.1.1")]  # seed IP is same as initial
        svc._query_agent_peers = AsyncMock(return_value=[])

        with patch("services.agent_discovery.GOSSIP_SEED_HOST", "192.168.1.1"):
            result = await svc._discover_via_gossip(initial, {"a1"})

        assert result == []

    @pytest.mark.asyncio
    async def test_gossip_multi_round(self):
        """Gossip expands across multiple rounds."""
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "10.0.0.1")]

        round1_peer = _cap("g1", "10.0.0.2")
        round2_peer = _cap("g2", "10.0.0.3")

        async def mock_query(agent):
            if agent.ip_address == "10.0.0.1":
                return [round1_peer]
            elif agent.ip_address == "10.0.0.2":
                return [round2_peer]
            return []

        svc._query_agent_peers = mock_query
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", ""), patch(
            "services.agent_discovery.GOSSIP_MAX_ROUNDS", 3
        ):
            result = await svc._discover_via_gossip(initial, {"a1"})

        ids = {a.agent_id for a in result}
        assert "g1" in ids
        assert "g2" in ids

    @pytest.mark.asyncio
    async def test_gossip_stops_when_no_new(self):
        """Gossip stops early if a round finds nothing new."""
        svc = AgentDiscoveryService()
        initial = [_cap("a1", "10.0.0.1")]

        svc._query_agent_peers = AsyncMock(return_value=[])
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", ""), patch(
            "services.agent_discovery.GOSSIP_MAX_ROUNDS", 5
        ):
            result = await svc._discover_via_gossip(initial, {"a1"})

        assert result == []
        # Should have been called just once (round 1), then stopped
        svc._query_agent_peers.assert_called_once()

    @pytest.mark.asyncio
    async def test_gossip_empty_initial_no_seed(self):
        """Empty initial_agents + no gossip seed → agents_to_query is empty → immediate break (line 378)."""
        svc = AgentDiscoveryService()
        svc._query_agent_peers = AsyncMock(return_value=[])
        with patch("services.agent_discovery.GOSSIP_SEED_HOST", ""):
            result = await svc._discover_via_gossip([], set())
        assert result == []
        svc._query_agent_peers.assert_not_called()


# ── _query_agent_peers ───────────────────────────────────────────────
class TestQueryAgentPeers:
    @pytest.mark.asyncio
    async def test_no_ip(self):
        svc = AgentDiscoveryService()
        agent = _cap("a1", "")
        result = await svc._query_agent_peers(agent)
        assert result == []

    @pytest.mark.asyncio
    async def test_peers_endpoint_success(self):
        svc = AgentDiscoveryService()
        agent = _cap("a1", "10.0.0.1")
        peer_data = [_cap_dict("p1", "10.0.0.2")]

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"agents": peer_data})

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_resp),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        with patch(
            "aiohttp.ClientSession",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            ),
        ):
            result = await svc._query_agent_peers(agent)

        assert len(result) == 1
        assert result[0].agent_id == "p1"

    @pytest.mark.asyncio
    async def test_peers_endpoint_fails_discover_fallback(self):
        svc = AgentDiscoveryService()
        agent = _cap("a1", "10.0.0.1")
        peer_data = [_cap_dict("p1", "10.0.0.2")]

        # First call (/peers) raises, second (/discover-peers) succeeds
        call_count = 0
        mock_fail_resp = MagicMock()
        mock_ok_resp = AsyncMock()
        mock_ok_resp.status = 200
        mock_ok_resp.json = AsyncMock(return_value={"peers": peer_data})

        mock_session = AsyncMock()

        def get_side_effect(url, **kw):
            if "/peers" in url and "/discover" not in url:
                # raise on /peers
                cm = AsyncMock()
                cm.__aenter__ = AsyncMock(side_effect=Exception("no /peers endpoint"))
                cm.__aexit__ = AsyncMock(return_value=False)
                return cm
            else:
                cm = AsyncMock()
                cm.__aenter__ = AsyncMock(return_value=mock_ok_resp)
                cm.__aexit__ = AsyncMock(return_value=False)
                return cm

        mock_session.get = MagicMock(side_effect=get_side_effect)

        with patch(
            "aiohttp.ClientSession",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            ),
        ):
            result = await svc._query_agent_peers(agent)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_discover_peers_non_200(self):
        svc = AgentDiscoveryService()
        agent = _cap("a1", "10.0.0.1")

        mock_fail_resp = AsyncMock()
        mock_fail_resp.status = 404

        # /peers returns empty (no agents key), /discover-peers returns 404
        mock_peers_resp = AsyncMock()
        mock_peers_resp.status = 200
        mock_peers_resp.json = AsyncMock(return_value={})  # no "agents" key

        mock_session = AsyncMock()

        def get_side_effect(url, **kw):
            if "/discover-peers" in url:
                cm = AsyncMock()
                cm.__aenter__ = AsyncMock(return_value=mock_fail_resp)
                cm.__aexit__ = AsyncMock(return_value=False)
                return cm
            else:
                cm = AsyncMock()
                cm.__aenter__ = AsyncMock(return_value=mock_peers_resp)
                cm.__aexit__ = AsyncMock(return_value=False)
                return cm

        mock_session.get = MagicMock(side_effect=get_side_effect)

        with patch(
            "aiohttp.ClientSession",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            ),
        ):
            result = await svc._query_agent_peers(agent)

        assert result == []

    @pytest.mark.asyncio
    async def test_timeout(self):
        svc = AgentDiscoveryService()
        agent = _cap("a1", "10.0.0.1")
        with patch(
            "aiohttp.ClientSession",
            side_effect=asyncio.TimeoutError(),
        ):
            result = await svc._query_agent_peers(agent)
        assert result == []

    @pytest.mark.asyncio
    async def test_client_error(self):
        svc = AgentDiscoveryService()
        agent = _cap("a1", "10.0.0.1")
        import aiohttp

        with patch(
            "aiohttp.ClientSession",
            side_effect=aiohttp.ClientError("conn refused"),
        ):
            result = await svc._query_agent_peers(agent)
        assert result == []

    @pytest.mark.asyncio
    async def test_generic_exception(self):
        svc = AgentDiscoveryService()
        agent = _cap("a1", "10.0.0.1")
        with patch(
            "aiohttp.ClientSession",
            side_effect=RuntimeError("unexpected"),
        ):
            result = await svc._query_agent_peers(agent)
        assert result == []


# ── _parse_peers ─────────────────────────────────────────────────────
class TestParsePeers:
    def test_parse_valid(self):
        svc = AgentDiscoveryService()
        data = [_cap_dict("p1", "10.0.0.2"), _cap_dict("p2", "10.0.0.3")]
        result = svc._parse_peers(data, "source1")
        assert len(result) == 2
        assert result[0].agent_id == "p1"
        assert result[1].agent_id == "p2"

    def test_parse_empty(self):
        svc = AgentDiscoveryService()
        assert svc._parse_peers([], "source1") == []

    def test_parse_bad_entry_skipped(self):
        """If from_dict raises, the bad entry is skipped."""
        svc = AgentDiscoveryService()
        with patch.object(
            AgentCapabilities,
            "from_dict",
            side_effect=Exception("bad data"),
        ):
            result = svc._parse_peers([{"bad": True}], "source1")
        assert result == []

    def test_parse_uses_ip_from_data(self):
        svc = AgentDiscoveryService()
        data = [{"agentId": "x1", "ipAddress": "1.2.3.4"}]
        result = svc._parse_peers(data, "source1")
        assert result[0].ip_address == "1.2.3.4"


# ── singleton get_discovery_service ──────────────────────────────────
class TestSingleton:
    def test_returns_same_instance(self):
        import services.agent_discovery as mod

        old = mod._discovery_service
        try:
            mod._discovery_service = None
            svc1 = get_discovery_service()
            svc2 = get_discovery_service()
            assert svc1 is svc2
        finally:
            mod._discovery_service = old


# ── _get_secret_or_env ───────────────────────────────────────────────
class TestGetSecretOrEnv:
    def test_env_var(self):
        from services.agent_discovery import _get_secret_or_env

        with patch.dict(os.environ, {"TEST_VAR": "hello"}, clear=False):
            assert _get_secret_or_env("TEST_VAR") == "hello"

    def test_env_var_default(self):
        from services.agent_discovery import _get_secret_or_env

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NONEXISTENT_VAR", None)
            os.environ.pop("NONEXISTENT_VAR_FILE", None)
            assert _get_secret_or_env("NONEXISTENT_VAR", "fallback") == "fallback"

    def test_file_secret(self, tmp_path):
        from services.agent_discovery import _get_secret_or_env

        secret_file = tmp_path / "secret.txt"
        secret_file.write_text("file_secret")
        with patch.dict(os.environ, {"MY_SECRET_FILE": str(secret_file)}, clear=False):
            assert _get_secret_or_env("MY_SECRET") == "file_secret"

    def test_file_secret_missing(self):
        from services.agent_discovery import _get_secret_or_env

        with patch.dict(
            os.environ,
            {"MISS_SECRET_FILE": "/nonexistent/path.txt"},
            clear=False,
        ):
            os.environ.pop("MISS_SECRET", None)
            assert _get_secret_or_env("MISS_SECRET", "def") == "def"
