"""Input helper control tools for Home Assistant MCP server."""

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


def register_input_boolean_tool(mcp: Any, get_client: Any) -> None:
    """Register the input_boolean control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "input"},
        timeout=30,
    )
    async def input_boolean_control(
        action: Annotated[
            Literal["list", "get", "turn_on", "turn_off", "toggle"],
            Field(
                description="Action to perform: list all input booleans, get specific input boolean, turn on, turn off, or toggle"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Input boolean entity ID (required for get, turn_on, turn_off, toggle). Example: 'input_boolean.guest_mode'"
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control input boolean helpers in Home Assistant.

        This tool allows you to manage input boolean helpers, which are simple on/off toggles
        used in automations and scripts to maintain state.

        Actions:
        - list: Get all input boolean entities with their current states
        - get: Get detailed information about a specific input boolean
        - turn_on: Turn on an input boolean
        - turn_off: Turn off an input boolean
        - toggle: Toggle an input boolean state

        Examples:
        - List all: input_boolean_control(action="list")
        - Get details: input_boolean_control(action="get", entity_id="input_boolean.guest_mode")
        - Turn on: input_boolean_control(action="turn_on", entity_id="input_boolean.guest_mode")
        - Turn off: input_boolean_control(action="turn_off", entity_id="input_boolean.guest_mode")
        - Toggle: input_boolean_control(action="toggle", entity_id="input_boolean.guest_mode")

        Args:
            action: The action to perform
            entity_id: The input boolean entity ID (required for get, turn_on, turn_off, toggle)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing input_boolean_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_input_booleans(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_input_boolean(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_on":
                if not entity_id:
                    return {"error": "entity_id is required for 'turn_on' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_on_input_boolean(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_off":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'turn_off' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_off_input_boolean(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "toggle":
                if not entity_id:
                    return {"error": "entity_id is required for 'toggle' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _toggle_input_boolean(client, entity_id)
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
            logger.error(f"Unexpected error in input_boolean_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


def register_input_number_tool(mcp: Any, get_client: Any) -> None:
    """Register the input_number control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "input"},
        timeout=30,
    )
    async def input_number_control(
        action: Annotated[
            Literal["list", "get", "set_value", "increment", "decrement"],
            Field(
                description="Action to perform: list all input numbers, get specific input number, set value, increment, or decrement"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Input number entity ID (required for get, set_value, increment, decrement). Example: 'input_number.temperature_threshold'"
            ),
        ] = None,
        value: Annotated[
            float | None,
            Field(description="Value to set (required for set_value action)"),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control input number helpers in Home Assistant.

        This tool allows you to manage input number helpers, which store numeric values
        with configurable min/max ranges and step sizes.

        Actions:
        - list: Get all input number entities with their current values
        - get: Get detailed information about a specific input number
        - set_value: Set the input number to a specific value
        - increment: Increase the value by the configured step
        - decrement: Decrease the value by the configured step

        Examples:
        - List all: input_number_control(action="list")
        - Get details: input_number_control(action="get", entity_id="input_number.temperature_threshold")
        - Set value: input_number_control(action="set_value", entity_id="input_number.temperature_threshold", value=22.5)
        - Increment: input_number_control(action="increment", entity_id="input_number.counter")
        - Decrement: input_number_control(action="decrement", entity_id="input_number.counter")

        Args:
            action: The action to perform
            entity_id: The input number entity ID (required for get, set_value, increment, decrement)
            value: The value to set (required for set_value)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing input_number_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_input_numbers(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_input_number(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_value":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_value' action",
                        "success": False,
                    }
                if value is None:
                    return {"error": "value is required for 'set_value' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_input_number_value(client, entity_id, value)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "increment":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'increment' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _increment_input_number(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "decrement":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'decrement' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _decrement_input_number(client, entity_id)
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
            logger.error(f"Unexpected error in input_number_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


def register_input_select_tool(mcp: Any, get_client: Any) -> None:
    """Register the input_select control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "input"},
        timeout=30,
    )
    async def input_select_control(
        action: Annotated[
            Literal["list", "get", "select_option"],
            Field(
                description="Action to perform: list all input selects, get specific input select, or select an option"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Input select entity ID (required for get, select_option). Example: 'input_select.home_mode'"
            ),
        ] = None,
        option: Annotated[
            str | None,
            Field(description="Option to select (required for select_option action)"),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control input select helpers in Home Assistant.

        This tool allows you to manage input select helpers, which provide a dropdown list
        of predefined options.

        Actions:
        - list: Get all input select entities with their current selections
        - get: Get detailed information about a specific input select including available options
        - select_option: Select a specific option from the available list

        Examples:
        - List all: input_select_control(action="list")
        - Get details: input_select_control(action="get", entity_id="input_select.home_mode")
        - Select option: input_select_control(action="select_option", entity_id="input_select.home_mode", option="Away")

        Args:
            action: The action to perform
            entity_id: The input select entity ID (required for get, select_option)
            option: The option to select (required for select_option)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing input_select_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_input_selects(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_input_select(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "select_option":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'select_option' action",
                        "success": False,
                    }
                if not option:
                    return {
                        "error": "option is required for 'select_option' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _select_input_select_option(client, entity_id, option)
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
            logger.error(f"Unexpected error in input_select_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


def register_input_text_tool(mcp: Any, get_client: Any) -> None:
    """Register the input_text control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "input"},
        timeout=30,
    )
    async def input_text_control(
        action: Annotated[
            Literal["list", "get", "set_value"],
            Field(
                description="Action to perform: list all input texts, get specific input text, or set value"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Input text entity ID (required for get, set_value). Example: 'input_text.notification_message'"
            ),
        ] = None,
        value: Annotated[
            str | None,
            Field(description="Text value to set (required for set_value action)"),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control input text helpers in Home Assistant.

        This tool allows you to manage input text helpers, which store text strings
        that can be used in automations and scripts.

        Actions:
        - list: Get all input text entities with their current values
        - get: Get detailed information about a specific input text
        - set_value: Set the input text to a specific value

        Examples:
        - List all: input_text_control(action="list")
        - Get details: input_text_control(action="get", entity_id="input_text.notification_message")
        - Set value: input_text_control(action="set_value", entity_id="input_text.notification_message", value="Hello World")

        Args:
            action: The action to perform
            entity_id: The input text entity ID (required for get, set_value)
            value: The text value to set (required for set_value)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing input_text_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_input_texts(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_input_text(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_value":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_value' action",
                        "success": False,
                    }
                if value is None:
                    return {"error": "value is required for 'set_value' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_input_text_value(client, entity_id, value)
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
            logger.error(f"Unexpected error in input_text_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


def register_input_datetime_tool(mcp: Any, get_client: Any) -> None:
    """Register the input_datetime control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "input"},
        timeout=30,
    )
    async def input_datetime_control(
        action: Annotated[
            Literal["list", "get", "set_datetime"],
            Field(
                description="Action to perform: list all input datetimes, get specific input datetime, or set datetime"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Input datetime entity ID (required for get, set_datetime). Example: 'input_datetime.alarm_time'"
            ),
        ] = None,
        datetime: Annotated[
            str | None,
            Field(
                description="Datetime value to set in ISO 8601 format (required for set_datetime action). Example: '2024-01-15T08:30:00'"
            ),
        ] = None,
        date: Annotated[
            str | None,
            Field(
                description="Date value to set in YYYY-MM-DD format (optional for set_datetime). Example: '2024-01-15'"
            ),
        ] = None,
        time: Annotated[
            str | None,
            Field(
                description="Time value to set in HH:MM:SS format (optional for set_datetime). Example: '08:30:00'"
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control input datetime helpers in Home Assistant.

        This tool allows you to manage input datetime helpers, which store date and/or time values
        that can be used in automations and scripts.

        Actions:
        - list: Get all input datetime entities with their current values
        - get: Get detailed information about a specific input datetime
        - set_datetime: Set the input datetime to a specific value

        Examples:
        - List all: input_datetime_control(action="list")
        - Get details: input_datetime_control(action="get", entity_id="input_datetime.alarm_time")
        - Set datetime: input_datetime_control(action="set_datetime", entity_id="input_datetime.alarm_time", datetime="2024-01-15T08:30:00")
        - Set date only: input_datetime_control(action="set_datetime", entity_id="input_datetime.vacation_start", date="2024-07-01")
        - Set time only: input_datetime_control(action="set_datetime", entity_id="input_datetime.wake_time", time="07:00:00")

        Args:
            action: The action to perform
            entity_id: The input datetime entity ID (required for get, set_datetime)
            datetime: The datetime value in ISO 8601 format (for set_datetime)
            date: The date value in YYYY-MM-DD format (for set_datetime)
            time: The time value in HH:MM:SS format (for set_datetime)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing input_datetime_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_input_datetimes(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_input_datetime(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_datetime":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_datetime' action",
                        "success": False,
                    }
                if not datetime and not date and not time:
                    return {
                        "error": "At least one of datetime, date, or time is required for 'set_datetime' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_input_datetime_value(client, entity_id, datetime, date, time)
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
            logger.error(f"Unexpected error in input_datetime_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


# Helper functions for input_boolean


async def _list_input_booleans(client: HomeAssistantClient) -> dict:
    """List all input boolean entities."""
    logger.info("Listing all input boolean entities")
    all_states = await client.get_states()
    entities = [
        state for state in all_states if state.get("entity_id", "").startswith("input_boolean.")
    ]

    entity_list = []
    for entity in entities:
        entity_info = {
            "entity_id": entity.get("entity_id"),
            "name": entity.get("attributes", {}).get("friendly_name", entity.get("entity_id")),
            "state": entity.get("state"),
        }
        entity_list.append(entity_info)

    logger.info(f"Found {len(entity_list)} input boolean entities")
    return {"success": True, "count": len(entity_list), "input_booleans": entity_list}


async def _get_input_boolean(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific input boolean."""
    logger.info(f"Getting details for input boolean: {entity_id}")

    if not entity_id.startswith("input_boolean."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input boolean entity. Input boolean entities must start with 'input_boolean.'"
        )

    state = await client.get_state(entity_id)
    entity_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "input_boolean": entity_info}


async def _turn_on_input_boolean(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn on an input boolean."""
    logger.info(f"Turning on input boolean: {entity_id}")

    if not entity_id.startswith("input_boolean."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input boolean entity. Input boolean entities must start with 'input_boolean.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("input_boolean", "turn_on", service_data)

    logger.info(f"Successfully turned on input boolean: {entity_id}")
    return {
        "success": True,
        "message": f"Input boolean '{entity_id}' turned on",
        "entity_id": entity_id,
    }


async def _turn_off_input_boolean(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn off an input boolean."""
    logger.info(f"Turning off input boolean: {entity_id}")

    if not entity_id.startswith("input_boolean."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input boolean entity. Input boolean entities must start with 'input_boolean.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("input_boolean", "turn_off", service_data)

    logger.info(f"Successfully turned off input boolean: {entity_id}")
    return {
        "success": True,
        "message": f"Input boolean '{entity_id}' turned off",
        "entity_id": entity_id,
    }


async def _toggle_input_boolean(client: HomeAssistantClient, entity_id: str) -> dict:
    """Toggle an input boolean."""
    logger.info(f"Toggling input boolean: {entity_id}")

    if not entity_id.startswith("input_boolean."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input boolean entity. Input boolean entities must start with 'input_boolean.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("input_boolean", "toggle", service_data)

    logger.info(f"Successfully toggled input boolean: {entity_id}")
    return {
        "success": True,
        "message": f"Input boolean '{entity_id}' toggled",
        "entity_id": entity_id,
    }


# Helper functions for input_number


async def _list_input_numbers(client: HomeAssistantClient) -> dict:
    """List all input number entities."""
    logger.info("Listing all input number entities")
    all_states = await client.get_states()
    entities = [
        state for state in all_states if state.get("entity_id", "").startswith("input_number.")
    ]

    entity_list = []
    for entity in entities:
        attrs = entity.get("attributes", {})
        entity_info = {
            "entity_id": entity.get("entity_id"),
            "name": attrs.get("friendly_name", entity.get("entity_id")),
            "state": entity.get("state"),
            "min": attrs.get("min"),
            "max": attrs.get("max"),
            "step": attrs.get("step"),
            "unit_of_measurement": attrs.get("unit_of_measurement"),
        }
        entity_list.append(entity_info)

    logger.info(f"Found {len(entity_list)} input number entities")
    return {"success": True, "count": len(entity_list), "input_numbers": entity_list}


async def _get_input_number(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific input number."""
    logger.info(f"Getting details for input number: {entity_id}")

    if not entity_id.startswith("input_number."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input number entity. Input number entities must start with 'input_number.'"
        )

    state = await client.get_state(entity_id)
    attrs = state.get("attributes", {})
    entity_info = {
        "entity_id": state.get("entity_id"),
        "name": attrs.get("friendly_name", entity_id),
        "state": state.get("state"),
        "min": attrs.get("min"),
        "max": attrs.get("max"),
        "step": attrs.get("step"),
        "mode": attrs.get("mode"),
        "unit_of_measurement": attrs.get("unit_of_measurement"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": attrs,
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "input_number": entity_info}


async def _set_input_number_value(
    client: HomeAssistantClient, entity_id: str, value: float
) -> dict:
    """Set the value of an input number."""
    logger.info(f"Setting input number {entity_id} to value: {value}")

    if not entity_id.startswith("input_number."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input number entity. Input number entities must start with 'input_number.'"
        )

    # Get current state to validate min/max
    state = await client.get_state(entity_id)
    attrs = state.get("attributes", {})
    min_value = attrs.get("min")
    max_value = attrs.get("max")

    if min_value is not None and value < min_value:
        raise ServiceCallError(
            f"Value {value} is below minimum allowed value {min_value} for {entity_id}"
        )
    if max_value is not None and value > max_value:
        raise ServiceCallError(
            f"Value {value} is above maximum allowed value {max_value} for {entity_id}"
        )

    service_data = {"entity_id": entity_id, "value": value}
    await client.call_service("input_number", "set_value", service_data)

    logger.info(f"Successfully set input number {entity_id} to {value}")
    return {
        "success": True,
        "message": f"Input number '{entity_id}' set to {value}",
        "entity_id": entity_id,
        "value": value,
    }


async def _increment_input_number(client: HomeAssistantClient, entity_id: str) -> dict:
    """Increment an input number."""
    logger.info(f"Incrementing input number: {entity_id}")

    if not entity_id.startswith("input_number."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input number entity. Input number entities must start with 'input_number.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("input_number", "increment", service_data)

    logger.info(f"Successfully incremented input number: {entity_id}")
    return {
        "success": True,
        "message": f"Input number '{entity_id}' incremented",
        "entity_id": entity_id,
    }


async def _decrement_input_number(client: HomeAssistantClient, entity_id: str) -> dict:
    """Decrement an input number."""
    logger.info(f"Decrementing input number: {entity_id}")

    if not entity_id.startswith("input_number."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input number entity. Input number entities must start with 'input_number.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("input_number", "decrement", service_data)

    logger.info(f"Successfully decremented input number: {entity_id}")
    return {
        "success": True,
        "message": f"Input number '{entity_id}' decremented",
        "entity_id": entity_id,
    }


# Helper functions for input_select


async def _list_input_selects(client: HomeAssistantClient) -> dict:
    """List all input select entities."""
    logger.info("Listing all input select entities")
    all_states = await client.get_states()
    entities = [
        state for state in all_states if state.get("entity_id", "").startswith("input_select.")
    ]

    entity_list = []
    for entity in entities:
        attrs = entity.get("attributes", {})
        entity_info = {
            "entity_id": entity.get("entity_id"),
            "name": attrs.get("friendly_name", entity.get("entity_id")),
            "state": entity.get("state"),
            "options": attrs.get("options", []),
        }
        entity_list.append(entity_info)

    logger.info(f"Found {len(entity_list)} input select entities")
    return {"success": True, "count": len(entity_list), "input_selects": entity_list}


async def _get_input_select(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific input select."""
    logger.info(f"Getting details for input select: {entity_id}")

    if not entity_id.startswith("input_select."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input select entity. Input select entities must start with 'input_select.'"
        )

    state = await client.get_state(entity_id)
    attrs = state.get("attributes", {})
    entity_info = {
        "entity_id": state.get("entity_id"),
        "name": attrs.get("friendly_name", entity_id),
        "state": state.get("state"),
        "options": attrs.get("options", []),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": attrs,
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "input_select": entity_info}


async def _select_input_select_option(
    client: HomeAssistantClient, entity_id: str, option: str
) -> dict:
    """Select an option for an input select."""
    logger.info(f"Selecting option '{option}' for input select: {entity_id}")

    if not entity_id.startswith("input_select."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input select entity. Input select entities must start with 'input_select.'"
        )

    # Get current state to validate option
    state = await client.get_state(entity_id)
    attrs = state.get("attributes", {})
    available_options = attrs.get("options", [])

    if option not in available_options:
        raise ServiceCallError(
            f"Option '{option}' is not valid for {entity_id}. Available options: {', '.join(available_options)}"
        )

    service_data = {"entity_id": entity_id, "option": option}
    await client.call_service("input_select", "select_option", service_data)

    logger.info(f"Successfully selected option '{option}' for input select: {entity_id}")
    return {
        "success": True,
        "message": f"Input select '{entity_id}' set to '{option}'",
        "entity_id": entity_id,
        "option": option,
    }


# Helper functions for input_text


async def _list_input_texts(client: HomeAssistantClient) -> dict:
    """List all input text entities."""
    logger.info("Listing all input text entities")
    all_states = await client.get_states()
    entities = [
        state for state in all_states if state.get("entity_id", "").startswith("input_text.")
    ]

    entity_list = []
    for entity in entities:
        attrs = entity.get("attributes", {})
        entity_info = {
            "entity_id": entity.get("entity_id"),
            "name": attrs.get("friendly_name", entity.get("entity_id")),
            "state": entity.get("state"),
            "mode": attrs.get("mode"),
        }
        entity_list.append(entity_info)

    logger.info(f"Found {len(entity_list)} input text entities")
    return {"success": True, "count": len(entity_list), "input_texts": entity_list}


async def _get_input_text(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific input text."""
    logger.info(f"Getting details for input text: {entity_id}")

    if not entity_id.startswith("input_text."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input text entity. Input text entities must start with 'input_text.'"
        )

    state = await client.get_state(entity_id)
    attrs = state.get("attributes", {})
    entity_info = {
        "entity_id": state.get("entity_id"),
        "name": attrs.get("friendly_name", entity_id),
        "state": state.get("state"),
        "mode": attrs.get("mode"),
        "min": attrs.get("min"),
        "max": attrs.get("max"),
        "pattern": attrs.get("pattern"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": attrs,
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "input_text": entity_info}


async def _set_input_text_value(client: HomeAssistantClient, entity_id: str, value: str) -> dict:
    """Set the value of an input text."""
    logger.info(f"Setting input text {entity_id} to value: {value}")

    if not entity_id.startswith("input_text."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input text entity. Input text entities must start with 'input_text.'"
        )

    service_data = {"entity_id": entity_id, "value": value}
    await client.call_service("input_text", "set_value", service_data)

    logger.info(f"Successfully set input text {entity_id} to '{value}'")
    return {
        "success": True,
        "message": f"Input text '{entity_id}' set to '{value}'",
        "entity_id": entity_id,
        "value": value,
    }


# Helper functions for input_datetime


async def _list_input_datetimes(client: HomeAssistantClient) -> dict:
    """List all input datetime entities."""
    logger.info("Listing all input datetime entities")
    all_states = await client.get_states()
    entities = [
        state for state in all_states if state.get("entity_id", "").startswith("input_datetime.")
    ]

    entity_list = []
    for entity in entities:
        attrs = entity.get("attributes", {})
        entity_info = {
            "entity_id": entity.get("entity_id"),
            "name": attrs.get("friendly_name", entity.get("entity_id")),
            "state": entity.get("state"),
            "has_date": attrs.get("has_date", False),
            "has_time": attrs.get("has_time", False),
        }
        entity_list.append(entity_info)

    logger.info(f"Found {len(entity_list)} input datetime entities")
    return {"success": True, "count": len(entity_list), "input_datetimes": entity_list}


async def _get_input_datetime(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific input datetime."""
    logger.info(f"Getting details for input datetime: {entity_id}")

    if not entity_id.startswith("input_datetime."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input datetime entity. Input datetime entities must start with 'input_datetime.'"
        )

    state = await client.get_state(entity_id)
    attrs = state.get("attributes", {})
    entity_info = {
        "entity_id": state.get("entity_id"),
        "name": attrs.get("friendly_name", entity_id),
        "state": state.get("state"),
        "has_date": attrs.get("has_date", False),
        "has_time": attrs.get("has_time", False),
        "year": attrs.get("year"),
        "month": attrs.get("month"),
        "day": attrs.get("day"),
        "hour": attrs.get("hour"),
        "minute": attrs.get("minute"),
        "second": attrs.get("second"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": attrs,
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "input_datetime": entity_info}


async def _set_input_datetime_value(
    client: HomeAssistantClient,
    entity_id: str,
    datetime: str | None = None,
    date: str | None = None,
    time: str | None = None,
) -> dict:
    """Set the value of an input datetime."""
    logger.info(f"Setting input datetime {entity_id}")

    if not entity_id.startswith("input_datetime."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an input datetime entity. Input datetime entities must start with 'input_datetime.'"
        )

    service_data = {"entity_id": entity_id}

    if datetime:
        service_data["datetime"] = datetime
    if date:
        service_data["date"] = date
    if time:
        service_data["time"] = time

    await client.call_service("input_datetime", "set_datetime", service_data)

    logger.info(f"Successfully set input datetime {entity_id}")
    return {
        "success": True,
        "message": f"Input datetime '{entity_id}' updated",
        "entity_id": entity_id,
    }
