"""State management tool for Home Assistant entities."""

import logging
from collections.abc import Callable
from typing import Any, Literal

from fastmcp import Context

from ...exceptions import EntityNotFoundError, ServiceCallError

logger = logging.getLogger(__name__)


def register_states_control_tool(mcp: Any, get_client: Callable) -> None:
    """Register the states_control tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function to get the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"state", "read-write"},
        timeout=30,
    )
    async def states_control(
        action: Literal["list", "get", "set", "delete"],
        entity_id: str | None = None,
        state: str | None = None,
        attributes: dict[str, Any] | None = None,
        domain: str | None = None,
        area: str | None = None,
        limit: int = 100,
        offset: int = 0,
        ctx: Context = None,
    ) -> dict[str, Any]:
        """Manage entity states with filtering support.

        ⚠️ FILTERING IS CRITICAL: Large Home Assistant installations can have 1000+ entities.
        Always use domain and/or area filters to prevent context overflow in AI assistants.

        Actions:
        - list: Get entity states with optional filtering (GET /api/states)
        - get: Get specific entity state (GET /api/states/<entity_id>)
        - set: Update/create entity state (POST /api/states/<entity_id>)
        - delete: Remove entity state (DELETE /api/states/<entity_id>)

        Filtering (for list action):
        - domain: Filter by entity domain (e.g., "light", "switch", "sensor")
        - area: Filter by area name (e.g., "Living Room", "Kitchen")
        - limit: Maximum number of entities to return (default 100, max 500)
        - offset: Number of entities to skip for pagination (default 0)

        Examples:
        - List all lights: action="list", domain="light"
        - List living room devices: action="list", area="Living Room"
        - List living room lights: action="list", domain="light", area="Living Room"
        - Get specific entity: action="get", entity_id="light.living_room"
        - Set entity state: action="set", entity_id="sensor.custom", state="42", attributes={"unit": "°C"}
        - Delete entity: action="delete", entity_id="sensor.old_sensor"

        Args:
            action: Action to perform (list, get, set, delete)
            entity_id: Entity ID (required for get, set, delete actions)
            state: New state value (required for set action)
            attributes: Entity attributes (optional for set action)
            domain: Domain filter for list action (e.g., "light", "switch")
            area: Area filter for list action (e.g., "Living Room")
            limit: Maximum results for list action (default 100, max 500)
            offset: Pagination offset for list action (default 0)

        Returns:
            Dictionary containing:
            - For list: {"success": True, "entities": [...], "count": N, "total": M, "truncated": bool}
            - For get: {"success": True, "entity": {...}}
            - For set: {"success": True, "entity": {...}}
            - For delete: {"success": True, "message": "..."}
            - For errors: {"success": False, "error": "...", "error_type": "..."}
        """
        client = get_client()

        try:
            if action == "list":
                # Get states with filtering
                states = await client.get_states(domain=domain, area=area, limit=limit + offset)

                # Apply offset for pagination
                if offset > 0:
                    states = states[offset:]

                # Track if results were truncated
                total_found = len(states)
                truncated = total_found >= limit

                # Apply final limit
                if len(states) > limit:
                    states = states[:limit]

                if ctx:
                    await ctx.info(
                        f"Listed {len(states)} entities "
                        f"(domain={domain}, area={area}, limit={limit}, offset={offset})"
                    )
                logger.info(
                    f"Listed {len(states)} entities "
                    f"(domain={domain}, area={area}, limit={limit}, offset={offset})"
                )

                # For list action, return compact summaries to reduce context size
                compact_entities = [
                    {
                        "entity_id": s.get("entity_id"),
                        "state": s.get("state"),
                        "name": s.get("attributes", {}).get("friendly_name"),
                    }
                    for s in states
                ]

                return {
                    "success": True,
                    "entities": compact_entities,
                    "count": len(states),
                    "total": total_found,
                    "truncated": truncated,
                    "message": (
                        f"Showing {len(states)} entities. "
                        f"Use domain/area filters for more specific results."
                        if truncated
                        else f"Found {len(states)} entities."
                    ),
                }

            elif action == "get":
                if not entity_id:
                    return {
                        "success": False,
                        "error": "entity_id is required for get action",
                        "error_type": "validation_error",
                    }

                # Get specific entity state
                if ctx:
                    await ctx.info(f"Retrieving state for {entity_id}")
                logger.info(f"Retrieving state for {entity_id}")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                entity_state = await client.get_state(entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)

                logger.info(f"Retrieved state for {entity_id}")

                return {
                    "success": True,
                    "entity": entity_state,
                }

            elif action == "set":
                if not entity_id:
                    return {
                        "success": False,
                        "error": "entity_id is required for set action",
                        "error_type": "validation_error",
                    }

                if not state:
                    return {
                        "success": False,
                        "error": "state is required for set action",
                        "error_type": "validation_error",
                    }

                # Set entity state
                if ctx:
                    await ctx.info(f"Setting state for {entity_id} to '{state}'")
                logger.info(f"Setting state for {entity_id} to '{state}'")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await client.set_state(entity_id, state, attributes)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)

                logger.info(f"Set state for {entity_id} to '{state}'")

                return {
                    "success": True,
                    "entity": result,
                    "message": f"State set successfully for {entity_id}",
                }

            elif action == "delete":
                if not entity_id:
                    return {
                        "success": False,
                        "error": "entity_id is required for delete action",
                        "error_type": "validation_error",
                    }

                # Delete entity state
                if ctx:
                    await ctx.info(f"Deleting state for {entity_id}")
                logger.info(f"Deleting state for {entity_id}")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await client.delete_state(entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)

                logger.info(f"Deleted state for {entity_id}")

                return {
                    "success": True,
                    "message": f"State deleted successfully for {entity_id}",
                    "details": result,
                }

            else:
                return {
                    "success": False,
                    "error": f"Invalid action: {action}",
                    "error_type": "validation_error",
                }

        except EntityNotFoundError as e:
            logger.warning(f"Entity not found: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "entity_not_found",
            }

        except ServiceCallError as e:
            logger.error(f"Service call error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "service_call_error",
            }

        except Exception as e:
            logger.exception(f"Unexpected error in states_control: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error",
            }
