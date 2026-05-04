"""Error log retrieval tool for Home Assistant MCP server."""

import logging
import re
from collections import Counter
from typing import Any

from fastmcp import Context

from ...exceptions import (
    AuthenticationError,
    ConnectionError,
    HomeAssistantError,
    ServiceCallError,
)
from ...hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)

# Matches HA log lines like:
# 2024-01-15 10:30:45.123 ERROR (MainThread) [homeassistant.components.mqtt] Message
# 2024-01-15 10:30:45 WARNING (MainThread) [custom_components.hacs] Message
_LOG_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})(?:\.\d+)?\s+"
    r"(ERROR|WARNING|CRITICAL|FATAL)\s+"
    r"\([^)]*\)\s+"
    r"\[([^\]]+)\]\s+"
    r"(.+)$"
)


def _parse_log_entries(raw_log: str) -> list[dict[str, str]]:
    """Parse raw HA log text into structured entries.

    Each entry is a log line that starts with a timestamp + level.
    Continuation lines (tracebacks) are attached to the preceding entry.
    """
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for line in raw_log.splitlines():
        match = _LOG_LINE_RE.match(line)
        if match:
            # Save previous entry
            if current is not None:
                entries.append(current)
            current = {
                "timestamp": match.group(1),
                "level": match.group(2),
                "component": match.group(3),
                "message": match.group(4),
                "traceback": "",
            }
        elif current is not None:
            # Continuation / traceback line
            if current["traceback"]:
                current["traceback"] += "\n" + line
            else:
                current["traceback"] = line

    if current is not None:
        entries.append(current)

    return entries


def _summarise_entries(
    entries: list[dict[str, str]], max_unique: int = 30
) -> dict[str, Any]:
    """Build a compact summary from parsed log entries.

    Groups by component, deduplicates repeated messages, and keeps
    only the most recent occurrence of each unique error.
    """
    # Count by level
    level_counts = Counter(e["level"] for e in entries)

    # Group by component
    by_component: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        by_component.setdefault(entry["component"], []).append(entry)

    component_counts = {comp: len(items) for comp, items in by_component.items()}

    # Deduplicate: keep last occurrence of each (component, message_prefix)
    seen: dict[tuple[str, str], dict[str, str]] = {}
    for entry in entries:
        # Use first 120 chars of message as dedup key
        key = (entry["component"], entry["message"][:120])
        seen[key] = entry  # last occurrence wins

    unique_entries = list(seen.values())

    # Sort by timestamp descending (most recent first)
    unique_entries.sort(key=lambda e: e["timestamp"], reverse=True)

    # Trim to max_unique
    truncated = len(unique_entries) > max_unique
    unique_entries = unique_entries[:max_unique]

    # Format each entry compactly
    formatted = []
    for entry in unique_entries:
        item: dict[str, str] = {
            "time": entry["timestamp"],
            "level": entry["level"],
            "component": entry["component"],
            "message": entry["message"][:200],
        }
        # Include first 3 lines of traceback if present
        if entry["traceback"]:
            tb_lines = entry["traceback"].strip().splitlines()
            # Get the last line (usually the actual exception) and a couple of context lines
            if len(tb_lines) > 3:
                item["traceback_tail"] = "\n".join(tb_lines[-3:])
            else:
                item["traceback_tail"] = "\n".join(tb_lines)
        formatted.append(item)

    return {
        "total_entries": len(entries),
        "unique_errors": len(seen),
        "level_counts": dict(level_counts),
        "top_components": dict(
            Counter(component_counts).most_common(10)
        ),
        "truncated": truncated,
        "recent_errors": formatted,
    }


def register_error_log_tool(mcp: Any, get_client: Any) -> None:
    """Register the error log retrieval tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True},
        tags={"history", "read"},
        timeout=30,
    )
    async def error_log_get(
        max_entries: int = 30,
        ctx: Context = None,
    ) -> dict:
        """Retrieve and summarise Home Assistant error logs.

        Parses the raw error log into structured entries, deduplicates repeated
        messages, and returns a compact summary with the most recent unique
        errors. Much smaller than the raw log — safe for AI assistant context.

        Use this tool to:
        - Diagnose problems with Home Assistant
        - Monitor system health and spot recurring errors
        - Troubleshoot integration issues
        - Debug automation failures

        Args:
            max_entries: Maximum unique error entries to return (default 30, max 100).

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - log_size: Total raw log size in bytes
                - summary: Parsed summary with:
                    - total_entries: Total log entries found
                    - unique_errors: Count of deduplicated errors
                    - level_counts: {"ERROR": N, "WARNING": M, ...}
                    - top_components: Top 10 components by error count
                    - recent_errors: List of most recent unique errors, each with
                      time, level, component, message, and traceback_tail
        """
        client: HomeAssistantClient = get_client()

        max_entries = max(5, min(max_entries, 100))

        try:
            if ctx:
                await ctx.info("Retrieving Home Assistant error log")
            logger.info("Retrieving Home Assistant error log")

            if ctx:
                await ctx.report_progress(progress=50, total=100)
            raw_log = await client.get_error_log()
            if ctx:
                await ctx.report_progress(progress=100, total=100)
            log_size = len(raw_log) if raw_log else 0

            if not raw_log or not raw_log.strip():
                return {
                    "success": True,
                    "log_size": 0,
                    "summary": {
                        "total_entries": 0,
                        "unique_errors": 0,
                        "level_counts": {},
                        "top_components": {},
                        "truncated": False,
                        "recent_errors": [],
                    },
                }

            entries = _parse_log_entries(raw_log)
            summary = _summarise_entries(entries, max_unique=max_entries)

            logger.info(
                f"Parsed error log: {log_size} bytes, "
                f"{summary['total_entries']} entries, "
                f"{summary['unique_errors']} unique"
            )

            return {
                "success": True,
                "log_size": log_size,
                "summary": summary,
            }

        except AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "authentication_error"}
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "connection_error"}
        except ServiceCallError as e:
            logger.error(f"Service call error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "service_call_error"}
        except HomeAssistantError as e:
            logger.error(f"Home Assistant error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "home_assistant_error"}
        except Exception as e:
            logger.error(f"Unexpected error in error_log_get: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }
