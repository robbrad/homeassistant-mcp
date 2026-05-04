"""Weather information tool for Home Assistant MCP server."""

import logging
from typing import Annotated, Any, Literal

from fastmcp import Context
from pydantic import Field

from ...exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    ServiceCallError,
)
from ...hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_weather_tool(mcp: Any, get_client: Any) -> None:
    """Register the weather information tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True},
        tags={"device", "read"},
        timeout=30,
    )
    async def weather_control(
        action: Annotated[
            Literal["list", "get", "get_forecast"],
            Field(
                description="Action to perform: list all weather entities, get current conditions, or get forecast"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Weather entity ID (required for get, get_forecast). Example: 'weather.home'"
            ),
        ] = None,
        forecast_type: Annotated[
            Literal["daily", "hourly"] | None,
            Field(
                description="Forecast type: daily or hourly. Only used with get_forecast action."
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Get weather information from Home Assistant.

        This tool allows you to list all weather entities, get current weather conditions,
        and retrieve weather forecasts.

        Actions:
        - list: Get all weather entities
        - get: Get current weather conditions (temperature, humidity, pressure, condition)
        - get_forecast: Get weather forecast with specified type (daily/hourly)

        Examples:
        - List all weather entities: weather_control(action="list")
        - Get current conditions: weather_control(action="get", entity_id="weather.home")
        - Get daily forecast: weather_control(action="get_forecast", entity_id="weather.home", forecast_type="daily")
        - Get hourly forecast: weather_control(action="get_forecast", entity_id="weather.home", forecast_type="hourly")

        Args:
            action: The action to perform
            entity_id: The weather entity ID (required for get, get_forecast)
            forecast_type: Forecast type - daily or hourly (required for get_forecast)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing weather_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_weather_entities(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_weather(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get_forecast":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'get_forecast' action",
                        "success": False,
                    }
                if not forecast_type:
                    return {
                        "error": "forecast_type is required for 'get_forecast' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_forecast(client, entity_id, forecast_type)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

        except EntityNotFoundError as e:
            logger.warning(f"Entity not found: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "entity_not_found"}
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
            logger.error(f"Unexpected error in weather_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_weather_entities(client: HomeAssistantClient) -> dict:
    """List all weather entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of weather entities with their states
    """
    logger.info("Listing all weather entities")

    # Get all weather entity states
    weather_entities = await client.get_states(domain="weather")

    # Format the response
    entity_list = []
    for entity in weather_entities:
        entity_info = {
            "entity_id": entity.get("entity_id"),
            "name": entity.get("attributes", {}).get("friendly_name", entity.get("entity_id")),
            "state": entity.get("state"),
        }

        # Add basic weather information if available
        attrs = entity.get("attributes", {})
        if "temperature" in attrs:
            entity_info["temperature"] = attrs["temperature"]

        if "humidity" in attrs:
            entity_info["humidity"] = attrs["humidity"]

        if "pressure" in attrs:
            entity_info["pressure"] = attrs["pressure"]

        entity_list.append(entity_info)

    logger.info(f"Found {len(entity_list)} weather entities")

    return {"success": True, "count": len(entity_list), "weather_entities": entity_list}


async def _get_weather(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get current weather conditions for a specific entity.

    Args:
        client: The Home Assistant client
        entity_id: The weather entity ID

    Returns:
        Dictionary containing current weather conditions

    Raises:
        EntityNotFoundError: If the weather entity is not found
    """
    logger.info(f"Getting current weather for: {entity_id}")

    # Validate that this is a weather entity
    if not entity_id.startswith("weather."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a weather entity. Weather entities must start with 'weather.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Extract weather information
    attrs = state.get("attributes", {})
    weather_info = {
        "entity_id": state.get("entity_id"),
        "name": attrs.get("friendly_name", entity_id),
        "condition": state.get("state"),
        "temperature": attrs.get("temperature"),
        "temperature_unit": attrs.get("temperature_unit"),
        "humidity": attrs.get("humidity"),
        "pressure": attrs.get("pressure"),
        "pressure_unit": attrs.get("pressure_unit"),
        "wind_speed": attrs.get("wind_speed"),
        "wind_speed_unit": attrs.get("wind_speed_unit"),
        "wind_bearing": attrs.get("wind_bearing"),
        "visibility": attrs.get("visibility"),
        "visibility_unit": attrs.get("visibility_unit"),
        "last_updated": state.get("last_updated"),
    }

    # Remove None values
    weather_info = {k: v for k, v in weather_info.items() if v is not None}

    logger.info(
        f"Retrieved weather for {entity_id}: condition={state.get('state')}, temp={attrs.get('temperature')}"
    )

    return {"success": True, "weather": weather_info}


async def _get_forecast(client: HomeAssistantClient, entity_id: str, forecast_type: str) -> dict:
    """Get weather forecast for a specific entity.

    Args:
        client: The Home Assistant client
        entity_id: The weather entity ID
        forecast_type: Type of forecast (daily or hourly)

    Returns:
        Dictionary containing weather forecast data

    Raises:
        EntityNotFoundError: If the weather entity is not found
        ServiceCallError: If the forecast service call fails
    """
    logger.info(f"Getting {forecast_type} forecast for: {entity_id}")

    # Validate that this is a weather entity
    if not entity_id.startswith("weather."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a weather entity. Weather entities must start with 'weather.'"
        )

    # Call the weather.get_forecasts service
    service_data = {"entity_id": entity_id, "type": forecast_type}

    try:
        # Call the service to get forecast
        forecast_response = await client.call_service("weather", "get_forecasts", service_data)

        # Extract forecast data from response
        # The response format is: {entity_id: {"forecast": [...]}}
        forecast_data = forecast_response.get(entity_id, {}).get("forecast", [])

        # Format forecast entries
        formatted_forecast = []
        for entry in forecast_data:
            forecast_entry = {
                "datetime": entry.get("datetime"),
                "condition": entry.get("condition"),
                "temperature": entry.get("temperature"),
                "templow": entry.get("templow"),
                "precipitation": entry.get("precipitation"),
                "precipitation_probability": entry.get("precipitation_probability"),
                "wind_speed": entry.get("wind_speed"),
                "wind_bearing": entry.get("wind_bearing"),
                "humidity": entry.get("humidity"),
                "pressure": entry.get("pressure"),
            }

            # Remove None values
            forecast_entry = {k: v for k, v in forecast_entry.items() if v is not None}
            formatted_forecast.append(forecast_entry)

        logger.info(
            f"Retrieved {len(formatted_forecast)} {forecast_type} forecast entries for {entity_id}"
        )

        return {
            "success": True,
            "entity_id": entity_id,
            "forecast_type": forecast_type,
            "forecast": formatted_forecast,
        }

    except Exception as e:
        logger.error(f"Error getting forecast: {str(e)}")
        raise ServiceCallError(f"Failed to get forecast: {str(e)}") from e
