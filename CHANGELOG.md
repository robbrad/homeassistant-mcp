# Changelog

All notable changes to the Home Assistant MCP Server (Python/FastMCP) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-15

### Added

#### Core Features
- Complete Python rewrite using FastMCP framework
- Async/await architecture for improved performance
- Comprehensive type hints with Pydantic validation
- Intelligent TTL-based caching system
- Structured logging with configurable levels
- Custom exception hierarchy for better error handling

#### Tools
- `lights_control` - Control lights with brightness, color temperature, and RGB support
- `climate_control` - Manage thermostats and HVAC systems
- `list_devices` - List and filter devices by domain, area, or floor
- `automation_control` - Manage automations (list, toggle, trigger)
- `scene_control` - Activate scenes
- `send_notification` - Send notifications through Home Assistant
- `query_history` - Retrieve historical state data
- `call_service` - Generic service call interface
- `get_automation_config` - Retrieve automation configurations

#### Configuration
- Environment variable-based configuration with Pydantic Settings
- Configurable cache TTL values
- Configurable logging levels
- Support for .env files

#### Testing
- Comprehensive test suite with pytest
- >95% code coverage
- Mocked Home Assistant API for reliable testing
- Async test support with pytest-asyncio

#### Documentation
- Complete README with setup instructions
- API documentation with examples
- Contributing guidelines
- Troubleshooting guide
- Development setup instructions
- MCP client configuration examples (Claude Desktop, Cursor)

#### Code Quality
- Black code formatting
- Ruff linting
- MyPy type checking
- Pre-configured pyproject.toml

### Changed
- Migrated from TypeScript/Bun to Python/FastMCP
- Simplified architecture leveraging FastMCP features
- Improved error messages with specific error types
- Enhanced caching strategy with automatic invalidation

### Removed
- TypeScript/Bun implementation (moved to separate branch)
- Custom MCP protocol implementation (now using FastMCP)
- WebSocket transport (stdio only in initial release)
- HTTP REST API (stdio only in initial release)
- Speech-to-text features (may be added in future)
- Wake word detection (may be added in future)

### Technical Details

#### Dependencies
- fastmcp >= 2.0.0
- httpx >= 0.27.0
- pydantic >= 2.0.0
- pydantic-settings >= 2.0.0
- python-dotenv >= 1.0.0

#### Python Version
- Requires Python 3.10 or higher

#### Breaking Changes
- Complete API rewrite - not compatible with TypeScript version
- Configuration format changed to environment variables
- Tool names and parameters remain compatible at MCP protocol level

## [1.x.x] - Previous Versions

Previous versions were implemented in TypeScript/Bun. See the TypeScript branch for historical changes.

---

## Upgrade Guide

### From TypeScript Version

The Python version maintains MCP protocol compatibility, so AI assistants can switch seamlessly. However, the server configuration has changed:

**Old Configuration (TypeScript):**
```json
{
  "hassHost": "http://homeassistant.local:8123",
  "hassToken": "token",
  "port": 3000
}
```

**New Configuration (Python):**
```env
HASS_HOST=http://homeassistant.local:8123
HASS_TOKEN=token
```

**MCP Client Configuration:**

Old:
```json
{
  "command": "npx",
  "args": ["@jango-blockchained/homeassistant-mcp@latest"]
}
```

New:
```json
{
  "command": "uvx",
  "args": ["homeassistant-mcp"]
}
```

### Migration Steps

1. **Install Python version:**
   ```bash
   pip install homeassistant-mcp
   ```

2. **Create .env file:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Update MCP client configuration:**
   - Update command to use `uvx` or `homeassistant-mcp`
   - Move configuration to `env` section

4. **Test the connection:**
   ```bash
   homeassistant-mcp
   ```

5. **Restart your MCP client** (Claude Desktop, Cursor, etc.)

---

## Future Roadmap

### Planned Features

#### Version 2.1.0
- [ ] WebSocket support for real-time events
- [ ] Batch operations for multiple entities
- [ ] Enhanced history queries with aggregation
- [ ] Performance metrics and monitoring

#### Version 2.2.0
- [ ] Redis-based distributed caching
- [ ] HTTP transport support
- [ ] Authentication middleware
- [ ] Rate limiting

#### Version 2.3.0
- [ ] Home Assistant add-on management
- [ ] HACS package management
- [ ] Webhook integration
- [ ] Advanced automation features

#### Version 3.0.0
- [ ] Speech-to-text integration
- [ ] Wake word detection
- [ ] Multi-instance support
- [ ] Advanced AI features

### Community Requests

We welcome feature requests! Please open an issue on GitHub to suggest new features or improvements.

---

## Support

For issues, questions, or contributions:
- **Issues**: [GitHub Issues](https://github.com/jango-blockchained/homeassistant-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jango-blockchained/homeassistant-mcp/discussions)
- **Documentation**: [README.md](README.md)
