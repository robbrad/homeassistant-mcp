# Home Assistant MCP Server

A Model Context Protocol (MCP) server that lets AI assistants control Home Assistant. Built with Python and [FastMCP](https://github.com/jlowin/fastmcp).

Works with Claude, GPT-4, Cursor, Kiro, and any MCP-compatible client.

## What it does

- **40+ tools** covering lights, climate, covers, locks, media players, vacuums, fans, cameras, alarms, and more
- **MCP Resources** for read-only entity, area, device, and service data
- **MCP Prompts** for guided workflows (automation creation, troubleshooting, energy optimization)
- **REST API tools** for events, services, states, history, logbook, templates, calendars, and config validation
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

## Supported Domains

| Domain | Tool | Capabilities |
|--------|------|-------------|
| Light | `lights_control` | Brightness, color temp, RGB |
| Climate | `climate_control` | HVAC modes, temperature, fan |
| Switch | `switch_control` | On/off, bulk operations |
| Cover | `cover_control` | Position, tilt, open/close |
| Lock | `lock_control` | Lock/unlock with codes |
| Media Player | `media_player_control` | Playback, volume, source |
| Camera | `camera_control` | Snapshots, streams, motion |
| Vacuum | `vacuum_control` | Start, dock, fan speed |
| Fan | `fan_control` | Speed, oscillation, direction |
| Script | `script_control` | Execute with variables |
| Scene | `scene_control` | Activate scenes |
| Automation | `automation_control` | Trigger, enable, disable |
| Alarm | `alarm_control` | Arm/disarm modes |
| Weather | `weather_control` | Conditions, forecasts |
| Input Helpers | `input_*_control` | Booleans, numbers, selects, text, datetime |
| Water Heater | `water_heater_control` | Temperature, modes |
| Humidifier | `humidifier_control` | Humidity levels |
| Siren | `siren_control` | Activation control |
| Valve | `valve_control` | Open/close |
| Lawn Mower | `lawn_mower_control` | Start, stop, dock |
| Devices | `list_devices` | Filter by domain, area, floor |
| Notifications | `send_notification` | Send alerts |
| History | `query_history` | Historical state data |
| Generic | `call_service` | Call any HA service |

### REST API Tools

| Tool | Description |
|------|-------------|
| `api_info` | API status, config, components |
| `events_control` | List and fire events |
| `services_control` | List and call services |
| `states_control` | CRUD on entity states |
| `history_query` | History with filtering |
| `logbook_query` | Logbook entries |
| `error_log_get` | Error log retrieval |
| `camera_proxy_get` | Camera images with resize |
| `calendar_access` | Calendar events |
| `template_render` | Render HA templates |
| `config_check` | Validate configuration |
| `intent_handle` | Process intents |

## Publishing to PyPI

Build and upload:

```bash
pip install build twine
python -m build
twine upload dist/*
```

After publishing, users can install with `pip install homeassistant-mcp` or run directly with `uvx homeassistant-mcp`.

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

## Architecture

```
AI Assistant  <-->  MCP Server (FastMCP/stdio)  <-->  Home Assistant REST API
                         |
                   +-----+-----+
                   |           |
                 Tools      Cache
                 Layer      Layer
```

- **FastMCP Server** handles MCP protocol over stdio
- **Home Assistant Client** is an async httpx client with auth
- **Cache Layer** provides TTL-based caching for states
- **Tools Layer** contains individual tool implementations per domain

## License

MIT
