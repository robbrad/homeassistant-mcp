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
                - list: Get available services (GET /api/services).
                  Use domain filter to list services for a specific domain.
                  Without domain, returns a summary of domains and service counts only.
                - call: Execute a service (POST /api/services/<domain>/<service>)
            domain: For 'list': filter to a specific domain (RECOMMENDED).
                    For 'call': service domain (required, e.g., 'light', 'switch')
            service: Service name (required for 'call' action, e.g., 'turn_on', 'turn_off')
            service_data: Optional service parameters (for 'call' action)
            return_response: If True, return service response data (for 'call' action)

        Returns:
            Dictionary containing the result.

        Examples:
            # List all domains (summary only)
            services_control(action="list")

            # List services for a specific domain
            services_control(action="list", domain="light")

            # Turn on a light
            services_control(
                action="call",
                domain="light",
                service="turn_on",
                service_data={"entity_id": "light.living_room"}
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
                else:
                    services_dict = services

                # If domain filter provided, return full details for that domain only
                if domain:
                    if domain not in services_dict:
                        return {
                            "success": True,
                            "action": "list",
                            "domain": domain,
                            "data": {},
                            "message": f"No services found for domain '{domain}'",
                        }
                    return {
                        "success": True,
                        "action": "list",
                        "domain": domain,
                        "data": {domain: services_dict[domain]},
                        "service_count": len(services_dict[domain]),
                    }

                # Without domain filter, return summary only (domain -> service names)
                summary = {}
                for d, svc in services_dict.items():
                    summary[d] = list(svc.keys()) if isinstance(svc, dict) else []

                total_services = sum(len(v) for v in summary.values())

                return {
                    "success": True,
                    "action": "list",
                    "message": (
                        "Showing domain summary. Use domain parameter to get "
                        "full service details for a specific domain."
                    ),
                    "data": summary,
                    "summary": {
                        "total_domains": len(summary),
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
