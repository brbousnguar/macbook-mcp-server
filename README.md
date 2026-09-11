# MacBook Status MCP

Small MCP server for a MacBook Pro that exposes machine status over MCP tools and a readable resource.

It is designed for:

- CPU, memory, disk, battery, network status
- top processes by CPU or memory
- GPU hardware visibility on macOS
- remote access from another machine through a private network such as Tailscale

## Why this design

This uses the native Python MCP SDK because local machine monitoring is a code problem more than an automation problem. `n8n` can still be added later if you want alerting or workflows.

## What it exposes

Tools:

- `get_system_overview`
- `get_disk_usage`
- `get_battery`
- `get_network`
- `get_gpu`
- `get_top_resource_processes`

Resource:

- `status://system/overview`

## Local setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python3 -m pip install -e .
```

3. Optional: set environment variables. The server reads plain env vars (defaults in `.env.example`):

```bash
cp .env.example .env
set -a; source .env; set +a
```

4. Start the server locally for Claude Desktop:

```bash
PYTHONPATH=src MCP_TRANSPORT=stdio python3 -m macbook_status_mcp.server
```

5. Optional: start the HTTP version instead:

```bash
PYTHONPATH=src MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 -m macbook_status_mcp.server
```

HTTP endpoint:

- `http://127.0.0.1:8765/mcp`

If `MCP_SHARED_TOKEN` is set, send:

- `Authorization: Bearer <your-token>`

## Claude Desktop local setup

For same-machine usage, prefer `stdio`.

Sample config:

- `claude-desktop/claude_desktop_config.sample.json`

The sample runs:

- `/path/to/macbook-mcp-server/.venv/bin/python -m macbook_status_mcp.server`

with:

- `PYTHONPATH` pointing to this project's `src` directory
- `MCP_TRANSPORT=stdio`

If your Claude Desktop still supports developer-defined local MCP config, the usual macOS path is:

- `~/Library/Application Support/Claude/claude_desktop_config.json`

Copy the sample entry into that file and restart Claude Desktop.

If your Claude Desktop only shows the newer Extensions flow, the durable option is to package this project as an `.mcpb` desktop extension.

## Remote access recommendation

Do not expose this directly on the public internet.

Recommended setup:

1. Install Tailscale on the MacBook and on the remote machine.
2. Keep the MCP server private.
3. If your MCP client requires a reachable TCP endpoint, either:
   - bind the server to the Tailscale IP only, or
   - front it with a small authenticated reverse proxy.

If the URL seen by the remote client is not the same as `MCP_HOST` and `MCP_PORT`, set `MCP_EXTERNAL_BASE_URL` to the client-facing URL.

The MCP transport spec warns about DNS rebinding and requires origin validation plus authentication for remote HTTP deployments.

## `launchd` setup

Template file (replace `/path/to/macbook-mcp-server` with your clone path first):

- `launchd/com.brbousnguar.macbook-status-mcp.plist`

To install it for your user:

```bash
mkdir -p ~/Library/LaunchAgents
cp launchd/com.brbousnguar.macbook-status-mcp.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.brbousnguar.macbook-status-mcp.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.brbousnguar.macbook-status-mcp.plist
launchctl start com.brbousnguar.macbook-status-mcp
```

Logs:

- `/tmp/macbook-status-mcp.log`
- `/tmp/macbook-status-mcp.err.log`

## Notes about GPU metrics on macOS

Static GPU information is easy to expose through `system_profiler`.

Real GPU utilization on macOS is much less straightforward:

- it is not consistently available through a simple user-space API
- `powermetrics` can expose more detail, but often needs elevated privileges
- because of that, this project currently returns GPU hardware info and a note about the limitation

## Roadmap

- Tailscale-only bind mode
- Optional privileged collector for deeper GPU and thermal data

## License

Apache-2.0. See [LICENSE](LICENSE).
# MacBook Status MCP

Small MCP server for a MacBook Pro that exposes machine status over MCP tools and a readable resource.

It is designed for:

- CPU, memory, disk, battery, network status
- top processes by CPU or memory
- GPU hardware visibility on macOS
- remote access from another machine through a private network such as Tailscale

## Why this design

This uses the native Python MCP SDK because local machine monitoring is a code problem more than an automation problem. `n8n` can still be added later if you want alerting or workflows.

## What it exposes

Tools:

- `get_system_overview`
- `get_disk_usage`
- `get_battery`
- `get_network`
- `get_gpu`
- `get_top_resource_processes`

Resource:

- `status://system/overview`

## Local setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python3 -m pip install -e .
```

3. Copy environment values:

```bash
cp .env.example .env
```

4. Start the server locally for Claude Desktop:

```bash
PYTHONPATH=src MCP_TRANSPORT=stdio python3 -m macbook_status_mcp.server
```

5. Optional: start the HTTP version instead:

```bash
PYTHONPATH=src MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 -m macbook_status_mcp.server
```

HTTP endpoint:

- `http://127.0.0.1:8765/mcp`

If `MCP_SHARED_TOKEN` is set, send:

- `Authorization: Bearer <your-token>`

## Claude Desktop local setup

For same-machine usage, prefer `stdio`.

Sample config:

- `claude-desktop/claude_desktop_config.sample.json`

The sample runs:

- `/Users/brbousnguar/Documents/Projects/Perso/mcp-macbook-settings/.venv/bin/python -m macbook_status_mcp.server`

with:

- `PYTHONPATH` pointing to this project's `src` directory
- `MCP_TRANSPORT=stdio`

If your Claude Desktop still supports developer-defined local MCP config, the usual macOS path is:

- `~/Library/Application Support/Claude/claude_desktop_config.json`

Copy the sample entry into that file and restart Claude Desktop.

If your Claude Desktop only shows the newer Extensions flow, the durable option is to package this project as an `.mcpb` desktop extension.

## Remote access recommendation

Do not expose this directly on the public internet.

Recommended setup:

1. Install Tailscale on the MacBook and on the remote machine.
2. Keep the MCP server private.
3. If your MCP client requires a reachable TCP endpoint, either:
   - bind the server to the Tailscale IP only, or
   - front it with a small authenticated reverse proxy.

If the URL seen by the remote client is not the same as `MCP_HOST` and `MCP_PORT`, set `MCP_EXTERNAL_BASE_URL` to the client-facing URL.

The MCP transport spec warns about DNS rebinding and requires origin validation plus authentication for remote HTTP deployments.

## `launchd` setup

Template file:

- `launchd/com.brbousnguar.macbook-status-mcp.plist`

To install it for your user:

```bash
mkdir -p ~/Library/LaunchAgents
cp launchd/com.brbousnguar.macbook-status-mcp.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.brbousnguar.macbook-status-mcp.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.brbousnguar.macbook-status-mcp.plist
launchctl start com.brbousnguar.macbook-status-mcp
```

Logs:

- `/tmp/macbook-status-mcp.log`
- `/tmp/macbook-status-mcp.err.log`

## Notes about GPU metrics on macOS

Static GPU information is easy to expose through `system_profiler`.

Real GPU utilization on macOS is much less straightforward:

- it is not consistently available through a simple user-space API
- `powermetrics` can expose more detail, but often needs elevated privileges
- because of that, this project currently returns GPU hardware info and a note about the limitation

If you want, the next step can be:

1. bind only to your Tailscale interface or front it with a small reverse proxy
2. add a Tailscale-only bind mode
3. add an optional privileged collector for deeper GPU and thermal data
