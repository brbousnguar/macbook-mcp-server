from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    server_name: str = "MacBook Status"
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8765
    bind_public: bool = False
    shared_token: str | None = None
    external_base_url: str | None = None

    @property
    def effective_host(self) -> str:
        if self.bind_public:
            return "0.0.0.0"
        return self.host

    @property
    def effective_base_url(self) -> str:
        if self.external_base_url:
            return self.external_base_url.rstrip("/")
        return f"http://{self.host}:{self.port}"


def load_settings() -> Settings:
    return Settings(
        server_name=os.getenv("MCP_SERVER_NAME", "MacBook Status"),
        transport=os.getenv("MCP_TRANSPORT", "stdio"),
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8765")),
        bind_public=_as_bool(os.getenv("MCP_BIND_PUBLIC"), default=False),
        shared_token=os.getenv("MCP_SHARED_TOKEN"),
        external_base_url=os.getenv("MCP_EXTERNAL_BASE_URL"),
    )
