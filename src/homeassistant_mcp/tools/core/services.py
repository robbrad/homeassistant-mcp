"""Services control tool for Home Assistant MCP server.

This tool provides service management capabilities including listing available
services and calling services with optional response data.
"""

import logging
from collections.abc import Callable
from typing import Any, Literal

from ...exceptions import ServiceCallError

logger = logging.getLogger(__name__)


def register_tool(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register the services_control tool with the MCP server.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def services_control(
        action: Literal["list", "call"],
        domain: str | None = None,
        service: str | None = None,
        service_data: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> dict[str, Any]:
        """Manage Home Assistant services.

        This tool provides service management capabilities for Home Assistant,
        allowing you to list available services and call services with parameters.

        Args:
            action: The action to perform:
                - list: Get all available services (GET /api/services)
                - call: Execute a service (POST /api/services/<domain>/<service>)
            domain: Service domain (required for 'call' action, e.g., 'light', 'switch')
            service: Service name (required for 'call' action, e.g., 'turn_on', 'turn_off')
            service_data: Optional service parameters (for 'call' action)
            return_response: If True, return service response data (for 'call' action)

        Returns:
            Dictionary containing the result:
            - list: {"success": True, "action": "list", "data": {...}}
            - call: {"success": True, "action": "call", "domain": "...", "service": "...", ...}

        Examples:
            # List all available services
            services_control(action="list")

            # Turn on a light
            services_control(
                action="call",
                domain="light",
                service="turn_on",
                service_data={"entity_id": "light.living_room"}
            )

            # Call a service with return_response
            services_control(
                action="call",
                domain="weather",
                service="get_forecasts",
                service_data={"type": "daily"},
                return_response=True
            )

            # Set climate temperature
            services_control(
                action="call",
                domain="climate",
                service="set_temperature",
                service_data={
                    "entity_id": "climate.living_room",
                    "temperature": 22
                }
            )

        Raises:
            ServiceCallError: If the API call fails or parameters are invalid
        """
        client = get_client()

        try:
            if action == "list":
                logger.info("Listing available services")
                services = await client.get_services()

                # Handle both list and dict formats from the API
                if isinstance(services, list):
                    # Convert list format to dict format for consistency
                    services_dict = {}
                    for service_domain in services:
                        domain_name = service_domain.get("domain", "unknown")
                        services_dict[domain_name] = service_domain.get("services", {})

                    total_services = sum(
                        len(domain_services) for domain_services in services_dict.values()
                    )

                    return {
                        "success": True,
                        "action": "list",
                        "data": services_dict,
                        "summary": {
                            "total_domains": len(services_dict),
                            "total_services": total_services,
                        },
                    }
                else:
                    # Original dict format
                    total_services = sum(
                        len(domain_services) for domain_services in services.values()
                    )

                    return {
                        "success": True,
                        "action": "list",
                        "data": services,
                        "summary": {
                            "total_domains": len(services),
                            "total_services": total_services,
                        },
                    }

            elif action == "call":
                # Validate required parameters
                if not domain:
                    raise ServiceCallError("domain is required for 'call' action")

                if not service:
                    raise ServiceCallError("service is required for 'call' action")

                # Validate domain and service are non-empty strings
                if not isinstance(domain, str) or len(domain.strip()) == 0:
                    raise ServiceCallError(
                        f"Invalid domain: must be a non-empty string, got {type(domain).__name__}"
                    )

                if not isinstance(service, str) or len(service.strip()) == 0:
                    raise ServiceCallError(
                        f"Invalid service: must be a non-empty string, got {type(service).__name__}"
                    )

                # Validate service_data is a dict if provided
                if service_data is not None and not isinstance(service_data, dict):
                    raise ServiceCallError(
                        f"Invalid service_data: must be a dictionary, got {type(service_data).__name__}"
                    )

                logger.info(f"Calling service: {domain}.{service}")
                result = await client.call_service(
                    domain=domain,
                    service=service,
                    data=service_data,
                    return_response=return_response,
                )

                return {
                    "success": True,
                    "action": "call",
                    "domain": domain,
                    "service": service,
                    "return_response": return_response,
                    "message": f"Service '{domain}.{service}' called successfully",
                    "data": result,
                }

            else:
                # This should never happen due to Literal type, but handle it anyway
                raise ServiceCallError(f"Invalid action: {action}")

        except Exception as e:
            logger.error(f"Failed to execute services_control ({action}): {str(e)}")
            return {
                "success": False,
                "action": action,
                "domain": domain if domain else None,
                "service": service if service else None,
                "error": str(e),
                "error_type": type(e).__name__,
            }
