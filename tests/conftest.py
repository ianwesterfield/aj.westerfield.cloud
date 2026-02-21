"""Shared pytest configuration and fixtures."""

import os
import socket
import pytest

# Orchestrator URL — override with ORCHESTRATOR_URL env var for WSL, remote, etc.
ORCHESTRATOR_HOST = os.environ.get("ORCHESTRATOR_HOST", "localhost")
ORCHESTRATOR_PORT = int(os.environ.get("ORCHESTRATOR_PORT", "8004"))
ORCHESTRATOR_URL = os.environ.get(
    "ORCHESTRATOR_URL", f"http://{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}"
)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests requiring a running orchestrator",
    )


def _orchestrator_reachable(
    host: str = ORCHESTRATOR_HOST,
    port: int = ORCHESTRATOR_PORT,
    timeout: float = 1.0,
) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def pytest_collection_modifyitems(config, items):
    if _orchestrator_reachable():
        return  # orchestrator is up — run everything

    skip_integration = pytest.mark.skip(
        reason=f"Orchestrator not reachable at {ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}",
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
