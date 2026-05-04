# Home Assistant MCP Server

A Model Context Protocol (MCP) server that lets AI assistants control Home Assistant. Built with Python and [FastMCP](https://github.com/jlowin/fastmcp).

Works with Claude, GPT-4, Cursor, Kiro, and any MCP-compatible client.

## What it does

- **40 tools** covering lights, climate, covers, locks, media players, vacuums, fans, cameras, alarms, and more
- **BM25 tool search** — LLMs discover tools on demand instead of receiving all 40 schemas upfront
- **MCP Resources** for read-only entity, area, device, and service data
- **MCP Prompts** for guided workflows (automation creation, troubleshooting, energy optimization)
- **Tool annotations** — `readOnlyHint` lets clients skip confirmation prompts for safe operations
- **Smart error log parsing** — deduplicates and summarises HA error logs instead of dumping raw text
- **Context-aware responses** — compact list responses, domain-filtered queries, progress reporting
- **Async throughout** with TTL-based caching to reduce API load

## Installation

### uvx (recommended)

No install needed. Just configure your MCP client:

```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "uvx",
      "args": ["homeassistant-mcp"],
      "env": {
        "HASS_HOST": "http://homeassistant.local:8123",
        "HASS_TOKEN": "your_long_lived_access_token_here"
      }
    }
  }
}
```

### pip

```bash
pip install homeassistant-mcp
homeassistant-mcp
```

### From source

```bash
git clone https://github.com/robbrad/homeassistant-mcp.git
cd homeassistant-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
homeassistant-mcp
```

## Configuration

The server needs two environment variables:

| Variable | Description |
|----------|-------------|
| `HASS_HOST` | Home Assistant URL, e.g. `http://homeassistant.local:8123` |
| `HASS_TOKEN` | Long-lived access token ([how to create one](https://www.home-assistant.io/docs/authentication/#your-account-profile)) |

Optional:

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_TTL_STATES` | `30` | Cache TTL for bulk state queries (seconds) |
| `CACHE_TTL_ENTITY` | `10` | Cache TTL for individual entity queries (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |

These can be set via environment variables (as shown in the MCP client configs above) or in a `.env` file. See [.env.example](.env.example).

## MCP Client Setup

### Claude Desktop

Add to your config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "uvx",
      "args": ["homeassistant-mcp"],
      "env": {
        "HASS_HOST": "http://homeassistant.local:8123",
        "HASS_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Cursor / Kiro / Other MCP Clients

Same config format. Place it in your client's MCP configuration file (e.g. `.cursor/mcp.json`, `.kiro/settings/mcp.json`).

The server uses stdio transport, which is the standard for MCP.

## How Tool Discovery Works

With 40 tools, the server uses BM25 search to keep the LLM's context lean. Instead of sending all 40 tool schemas upfront, the LLM sees 8 tools:

| Tool | Purpose |
|------|---------|
| `discover_tools` | Returns the full catalog of all 40 tools by category |
| `states_control` | Entity state management (list, get, set, delete) |
| `list_devices` | Device discovery with domain/area/floor filtering |
| `call_service` | Call any HA service directly |
| `template_render` | Render Jinja2 templates in HA context |
| `error_log_get` | Parsed and deduplicated error log summary |
| `search_tools` | BM25 search to find tools by description |
| `call_tool` | Execute a discovered tool by name |

The LLM calls `discover_tools()` to see what's available, then `search_tools(query="lights brightness")` to get the full schema, then calls the tool directly.

## All Tools

### Device Control (16 tools)

| Tool | Domain | Capabilities |
|------|--------|-------------|
| `lights_control` | light | Brightness, color temp, RGB |
| `climate_control` | climate | HVAC modes, temperature, fan |
| `switch_control` | switch | On/off, bulk operations |
| `cover_control` | cover | Position, tilt, open/close |
| `lock_control` | lock | Lock/unlock with codes |
| `media_player_control` | media_player | Playback, volume, source |
| `camera_control` | camera | Snapshots, streams, motion detection |
| `vacuum_control` | vacuum | Start, dock, fan speed |
| `fan_control` | fan | Speed, oscillation, direction |
| `alarm_control` | alarm_control_panel | Arm/disarm modes |
| `weather_control` | weather | Conditions, daily/hourly forecasts |
| `water_heater_control` | water_heater | Temperature, modes |
| `humidifier_control` | humidifier | Humidity levels |
| `siren_control` | siren | Activation control |
| `valve_control` | valve | Open/close |
| `lawn_mower_control` | lawn_mower | Start, stop, dock |

### Automation & Scenes (3 tools)

| Tool | Capabilities |
|------|-------------|
| `automation_control` | List, trigger, enable, disable, reload |
| `scene_control` | List, activate |
| `script_control` | List, execute with variables, reload |

### Input Helpers (5 tools)

| Tool | Capabilities |
|------|-------------|
| `input_boolean_control` | Toggle on/off |
| `input_number_control` | Set value, increment, decrement |
| `input_select_control` | Select from options |
| `input_text_control` | Set text value |
| `input_datetime_control` | Set date/time |

### API & State (4 tools)

| Tool | Capabilities |
|------|-------------|
| `api_info` | API status, HA config, loaded components |
| `events_control` | List event types, fire custom events |
| `services_control` | List services by domain, call services |
| `states_control` | List/get/set/delete entity states with filtering |

### History (3 tools)

| Tool | Capabilities |
|------|-------------|
| `history_query` | State changes by entity + hours (not ISO timestamps) |
| `logbook_query` | Human-readable logbook entries |
| `error_log_get` | Parsed, deduplicated error summary with component counts |

### Specialized (5 tools)

| Tool | Capabilities |
|------|-------------|
| `calendar_access` | List calendars, get events by date range |
| `camera_proxy_get` | Camera images with optional resize |
| `config_check` | Validate HA configuration |
| `intent_handle` | Process natural language intents |
| `template_render` | Render Jinja2 templates |

### General (4 tools)

| Tool | Capabilities |
|------|-------------|
| `list_devices` | Filter by any domain, area, or floor |
| `call_service` | Call any HA service with custom data |
| `send_notification` | Send alerts via HA notification services |
| `discover_tools` | Full tool catalog for LLM discovery |

## MCP Resources

| URI Pattern | Description |
|-------------|-------------|
| `hass://entity/{entity_id}` | Entity state and attributes |
| `hass://area/{area_id}` | Area entities (compact summaries) |
| `hass://device/{device_id}` | Device entities (compact summaries) |
| `hass://services` | All services organized by domain |
| `hass://entity/{entity_id}/history` | Entity history with pagination |

## Development

```bash
git clone https://github.com/robbrad/homeassistant-mcp.git
cd homeassistant-mcp
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Format and lint
black src/ tests/
ruff check src/ tests/

# Type check
mypy src/
```

### Publishing

Commits to `main` auto-publish to PyPI via GitHub Actions + python-semantic-release:
- `fix:` commits → patch bump (3.1.0 → 3.1.1)
- `feat:` commits → minor bump (3.1.0 → 3.2.0)
- `BREAKING CHANGE:` → major bump (3.1.0 → 4.0.0)

## Architecture

```
AI Assistant  <-->  MCP Server (FastMCP/stdio)  <-->  Home Assistant REST API
                         |
                   +-----+-----+
                   |           |
                 Tools      Cache
                 Layer      Layer
```

- **FastMCP Server** handles MCP protocol over stdio with BM25 tool search
- **Home Assistant Client** is an async httpx client with auth and connection pooling
- **Cache Layer** provides TTL-based caching for states and entities
- **Tools Layer** — 40 tools with annotations, tags, timeouts, and context logging
- **Resources** — 5 read-only data endpoints with compact response envelopes
- **Prompts** — 13 guided workflows for automation, troubleshooting, and optimization

## License

MIT
