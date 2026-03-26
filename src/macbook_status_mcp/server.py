from __future__ import annotations

import json
import sys
from typing import Any

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from macbook_status_mcp.collectors import (
    get_battery_status,
    get_disk_status,
    get_gpu_status,
    get_network_status,
    get_system_status,
    get_top_processes,
)
from macbook_status_mcp.config import load_settings

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "The 'mcp' package is required. Install dependencies with "
        "`python3 -m pip install -e .` first."
    ) from exc


settings = load_settings()


class StaticTokenVerifier:
    def __init__(self, token: str):
        self._token = token

    async def verify_token(self, token: str) -> AccessToken | None:
        if token != self._token:
            return None
        return AccessToken(
            token=token,
            client_id="shared-token-client",
            scopes=[],
            resource=settings.effective_base_url,
        )


auth_settings = None
token_verifier = None
if settings.shared_token:
    auth_settings = AuthSettings(
        issuer_url=settings.effective_base_url,
        resource_server_url=settings.effective_base_url,
        required_scopes=[],
    )
    token_verifier = StaticTokenVerifier(settings.shared_token)

mcp = FastMCP(
    settings.server_name,
    host=settings.effective_host,
    port=settings.port,
    streamable_http_path="/mcp",
    auth=auth_settings,
    token_verifier=token_verifier,
)


def _to_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


@mcp.tool()
def get_system_overview() -> str:
    """Return a full snapshot of CPU, memory, disk, battery, network, and GPU data."""
    return _to_json(get_system_status())


@mcp.tool()
def get_disk_usage() -> str:
    """Return usage for the root filesystem."""
    return _to_json(get_disk_status())


@mcp.tool()
def get_battery() -> str:
    """Return battery state and charging information."""
    return _to_json(get_battery_status())


@mcp.tool()
def get_network() -> str:
    """Return network I/O counters and active IPv4 addresses."""
    return _to_json(get_network_status())


@mcp.tool()
def get_gpu() -> str:
    """Return GPU hardware information and notes about utilization support on macOS."""
    return _to_json(get_gpu_status())


@mcp.tool()
def get_top_resource_processes(limit: int = 5, sort_by: str = "cpu") -> str:
    """Return top processes sorted by CPU or memory usage."""
    if sort_by not in {"cpu", "memory"}:
        raise ValueError("sort_by must be either 'cpu' or 'memory'")
    return _to_json(get_top_processes(limit=limit, sort_by=sort_by))


@mcp.resource("status://system/overview")
def system_overview_resource() -> str:
    """Readable system overview resource."""
    return _to_json(get_system_status())


def main() -> int:
    transport = settings.transport.strip().lower()
    if transport not in {"stdio", "streamable-http", "sse"}:
        raise ValueError("MCP_TRANSPORT must be one of: stdio, streamable-http, sse")
    mcp.run(transport=transport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
