"""Home Assistant API client for interacting with the REST API."""

import asyncio
import logging
import time
from typing import Any

import httpx

from ..exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    ServiceCallError,
)
from .cache import StateCache
from .performance import get_performance_monitor

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """Client for interacting with Home Assistant REST API.

    This client provides async methods for fetching entity states and calling
    services in Home Assistant. It handles authentication, error handling, and
    provides a clean interface for the rest of the application.

    Attributes:
        base_url: The base URL of the Home Assistant instance
        token: The authentication token
        client: The httpx AsyncClient instance
        cache: The state cache instance
        cache_ttl_states: TTL for bulk state queries in seconds
        cache_ttl_entity: TTL for individual entity queries in seconds
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        cache_ttl_states: int = 30,
        cache_ttl_entity: int = 10,
        max_concurrent_requests: int = 10,
    ):
        """Initialize the Home Assistant client.

        Args:
            base_url: Home Assistant base URL (e.g., http://homeassistant.local:8123)
            token: Long-lived access token for authentication
            cache_ttl_states: Cache TTL for bulk state queries in seconds (default: 30)
            cache_ttl_entity: Cache TTL for individual entity queries in seconds (default: 10)
            max_concurrent_requests: Maximum concurrent API requests (default: 10)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.cache_ttl_states = cache_ttl_states
        self.cache_ttl_entity = cache_ttl_entity
        self.max_concurrent_requests = max_concurrent_requests

        # Create async HTTP client with authentication headers
        self.client = httpx.AsyncClient(
            base_url=f"{self.base_url}/api",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        # Initialize cache
        self.cache = StateCache()

        # Initialize performance monitor
        self.performance_monitor = get_performance_monitor()

        # Semaphore for limiting concurrent requests
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)

        logger.info(
            f"Initialized Home Assistant client for {self.base_url} "
            f"(cache TTL: states={cache_ttl_states}s, entity={cache_ttl_entity}s, "
            f"max concurrent: {max_concurrent_requests})"
        )

    async def get_api_status(self) -> dict[str, Any]:
        """Get Home Assistant API status.

        Returns:
            Dictionary containing API status message

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Fetching API status")
            async with self._semaphore:
                response = await self.client.get("/")
                response.raise_for_status()

            status = response.json()
            logger.debug(f"API status: {status}")

            success = True
            return status  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch API status: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_api_status", duration, success)

    async def get_config(self) -> dict[str, Any]:
        """Get Home Assistant configuration.

        Returns:
            Dictionary containing Home Assistant configuration including
            location, units, version, etc.

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Fetching Home Assistant configuration")
            async with self._semaphore:
                response = await self.client.get("/config")
                response.raise_for_status()

            config = response.json()
            logger.debug("Retrieved Home Assistant configuration")

            success = True
            return config  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch configuration: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_config", duration, success)

    async def get_components(self) -> list[str]:
        """Get list of loaded Home Assistant components.

        Returns:
            List of component names

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Fetching loaded components")
            async with self._semaphore:
                response = await self.client.get("/components")
                response.raise_for_status()

            components = response.json()
            logger.debug(f"Retrieved {len(components)} components")

            success = True
            return components  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch components: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_components", duration, success)

    async def get_events(self) -> dict[str, Any]:
        """Get all event types with listener counts.

        Returns:
            Dictionary mapping event types to listener counts

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Fetching event types")
            async with self._semaphore:
                response = await self.client.get("/events")
                response.raise_for_status()

            events = response.json()
            logger.debug(f"Retrieved {len(events)} event types")

            success = True
            return events  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch events: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_events", duration, success)

    async def get_services(self) -> dict[str, Any]:
        """Get all available services organized by domain.

        Returns:
            Dictionary mapping domains to their services with descriptions

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Fetching available services")
            async with self._semaphore:
                response = await self.client.get("/services")
                response.raise_for_status()

            services = response.json()
            logger.debug(f"Retrieved services for {len(services)} domains")

            success = True
            return services  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch services: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_services", duration, success)

    async def fire_event(
        self, event_type: str, event_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fire a custom event in Home Assistant.

        Args:
            event_type: The type of event to fire
            event_data: Optional event data dictionary

        Returns:
            Dictionary containing success confirmation

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the event firing fails
        """
        start_time = time.time()
        success = False

        try:
            endpoint = f"/events/{event_type}"
            payload = event_data or {}

            logger.info(f"Firing event: {event_type}")
            logger.debug(f"Event data: {payload}")

            async with self._semaphore:
                response = await self.client.post(endpoint, json=payload)
                response.raise_for_status()

            result = response.json() if response.text else {"message": "Event fired"}
            logger.info(f"Event fired successfully: {event_type}")

            success = True
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fire event {event_type}: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call(f"fire_event:{event_type}", duration, success)

    async def get_states(
        self,
        domain: str | None = None,
        area: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get all entity states from Home Assistant with filtering and caching.

        Results are cached for cache_ttl_states seconds to reduce API calls.
        Filtering is applied client-side after fetching all states.

        Args:
            domain: Optional domain filter (e.g., "light", "switch")
            area: Optional area filter (e.g., "Living Room")
            limit: Maximum number of entities to return. Defaults to None (no limit)
                   when domain or area filter is provided, or 500 when unfiltered.

        Returns:
            List of entity state dictionaries, each containing:
                - entity_id: The entity identifier
                - state: The current state value
                - attributes: Dictionary of entity attributes
                - last_changed: ISO timestamp of last state change
                - last_updated: ISO timestamp of last update

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        cache_key = "states:all"

        # Check cache first
        cached_states = self.cache.get(cache_key)
        if cached_states is not None:
            logger.debug(f"Returning {len(cached_states)} cached entity states")
            all_states = cached_states
        else:
            start_time = time.time()
            success = False

            try:
                logger.debug("Fetching all entity states from API")
                async with self._semaphore:
                    response = await self.client.get("/states")
                    response.raise_for_status()

                all_states = response.json()
                logger.debug(f"Retrieved {len(all_states)} entity states from API")

                # Cache the results
                self.cache.set(cache_key, all_states, self.cache_ttl_states)

                success = True

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.error("Authentication failed - invalid token")
                    raise AuthenticationError(
                        "Invalid Home Assistant token. Please check your HASS_TOKEN."
                    ) from e
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                    raise ServiceCallError(
                        f"Failed to fetch states: HTTP {e.response.status_code}"
                    ) from e

            except httpx.RequestError as e:
                logger.error(f"Connection error: {str(e)}")
                raise ConnectionError(
                    f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
                ) from e

            finally:
                duration = time.time() - start_time
                self.performance_monitor.record_call("get_states", duration, success)

        # Apply filtering
        filtered_states = all_states

        if domain:
            filtered_states = [
                state
                for state in filtered_states
                if state.get("entity_id", "").startswith(f"{domain}.")
            ]
            logger.debug(f"Filtered to {len(filtered_states)} entities in domain '{domain}'")

        if area:
            filtered_states = [
                state
                for state in filtered_states
                if state.get("attributes", {}).get("area_id") == area
                or state.get("attributes", {}).get("friendly_name", "").lower().find(area.lower())
                != -1
            ]
            logger.debug(f"Filtered to {len(filtered_states)} entities in area '{area}'")

        # Apply limit — default to no limit when filtered, 500 when unfiltered
        has_filter = domain is not None or area is not None
        if limit is None:
            effective_limit = None if has_filter else 500
        else:
            effective_limit = min(limit, 500)

        if effective_limit and len(filtered_states) > effective_limit:
            logger.warning(
                f"Response truncated: {len(filtered_states)} entities found, "
                f"returning first {effective_limit}. Use more specific filters to see all results."
            )
            filtered_states = filtered_states[:effective_limit]

        # Track response size
        import sys

        response_size = sys.getsizeof(str(filtered_states))
        if response_size > 100_000:  # 100KB
            logger.warning(
                f"Large response size: {response_size / 1024:.1f}KB. "
                f"Consider using more specific filters to reduce context usage."
            )

        return filtered_states  # type: ignore[no-any-return]

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        """Get the state of a specific entity with caching.

        Results are cached for cache_ttl_entity seconds to reduce API calls.

        Args:
            entity_id: The entity identifier (e.g., 'light.living_room')

        Returns:
            Entity state dictionary containing:
                - entity_id: The entity identifier
                - state: The current state value
                - attributes: Dictionary of entity attributes
                - last_changed: ISO timestamp of last state change
                - last_updated: ISO timestamp of last update

        Raises:
            EntityNotFoundError: If the entity does not exist (404)
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        cache_key = f"state:{entity_id}"

        # Check cache first
        cached_state = self.cache.get(cache_key)
        if cached_state is not None:
            logger.debug(f"Returning cached state for {entity_id}")
            return cached_state  # type: ignore[no-any-return]

        start_time = time.time()
        success = False

        try:
            logger.debug(f"Fetching state for entity from API: {entity_id}")
            async with self._semaphore:
                response = await self.client.get(f"/states/{entity_id}")
                response.raise_for_status()

            state = response.json()
            logger.debug(f"Retrieved state for {entity_id}: {state.get('state')}")

            # Cache the result
            self.cache.set(cache_key, state, self.cache_ttl_entity)

            success = True
            return state  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Entity not found: {entity_id}")
                raise EntityNotFoundError(
                    f"Entity '{entity_id}' not found in Home Assistant"
                ) from e
            elif e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch state for {entity_id}: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_state", duration, success)

    async def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Set or update the state of an entity.

        Args:
            entity_id: The entity identifier (e.g., 'sensor.custom_sensor')
            state: The new state value
            attributes: Optional dictionary of entity attributes

        Returns:
            Entity state dictionary after update

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            payload = {
                "state": state,
                "attributes": attributes or {},
            }

            logger.info(f"Setting state for {entity_id} to '{state}'")
            async with self._semaphore:
                response = await self.client.post(f"/states/{entity_id}", json=payload)
                response.raise_for_status()

            result = response.json()
            logger.info(f"State set successfully for {entity_id}")

            # Invalidate cache
            self.cache.invalidate(f"state:{entity_id}")
            self.cache.invalidate("states:all")

            success = True
            return result  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to set state for {entity_id}: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("set_state", duration, success)

    async def delete_state(self, entity_id: str) -> dict[str, Any]:
        """Delete an entity state from the state machine.

        Args:
            entity_id: The entity identifier to delete

        Returns:
            Dictionary containing success confirmation

        Raises:
            EntityNotFoundError: If the entity does not exist (404)
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.info(f"Deleting state for {entity_id}")
            async with self._semaphore:
                response = await self.client.delete(f"/states/{entity_id}")
                response.raise_for_status()

            result = response.json() if response.text else {"message": "State deleted"}
            logger.info(f"State deleted successfully for {entity_id}")

            # Invalidate cache
            self.cache.invalidate(f"state:{entity_id}")
            self.cache.invalidate("states:all")

            success = True
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Entity not found: {entity_id}")
                raise EntityNotFoundError(
                    f"Entity '{entity_id}' not found in Home Assistant"
                ) from e
            elif e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to delete state for {entity_id}: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("delete_state", duration, success)

    async def get_states_concurrent(
        self,
        entity_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Get states for multiple entities concurrently.

        This method is more efficient than calling get_state() sequentially
        when you need detailed information about specific entities.

        Args:
            entity_ids: List of entity identifiers

        Returns:
            Dictionary mapping entity_id to state data

        Raises:
            EntityNotFoundError: If any entity does not exist
            AuthenticationError: If authentication fails
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        logger.debug(f"Fetching {len(entity_ids)} entity states concurrently")

        # Create tasks for all entity state fetches
        tasks = [self.get_state(entity_id) for entity_id in entity_ids]

        # Execute all tasks concurrently (semaphore limits actual concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dictionary and handle exceptions
        state_dict: dict[str, dict[str, Any]] = {}
        for entity_id, result in zip(entity_ids, results, strict=False):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch state for {entity_id}: {result}")
                raise result
            # Type narrowing: result is dict[str, Any] here since we checked for Exception
            state_dict[entity_id] = result  # type: ignore[assignment]

        logger.info(f"Fetched {len(state_dict)} entity states concurrently")
        return state_dict

    async def get_history(
        self,
        timestamp: str,
        end_time: str | None = None,
        filter_entity_id: list[str] | None = None,
        minimal_response: bool = False,
        limit: int = 100,
    ) -> list[list[dict[str, Any]]]:
        """Get historical state data with filtering support.

        Args:
            timestamp: ISO 8601 timestamp for the start of the history period
            end_time: Optional ISO 8601 timestamp for the end (defaults to now)
            filter_entity_id: Optional list of entity IDs to filter
            minimal_response: If True, return minimal data without attributes
            limit: Maximum number of history entries per entity (default 100)

        Returns:
            List of lists containing historical state data. The outer list contains
            one inner list per entity, and each inner list contains state dictionaries
            with timestamps.

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_perf = time.time()
        success = False

        try:
            # Build query parameters
            params: dict[str, Any] = {}

            # Add entity filter if provided
            if filter_entity_id:
                params["filter_entity_id"] = ",".join(filter_entity_id)

            # Add end_time if provided
            if end_time:
                params["end_time"] = end_time

            # Add minimal_response if requested
            if minimal_response:
                params["minimal_response"] = "true"

            endpoint = f"/history/period/{timestamp}"

            logger.debug(f"Fetching history from {timestamp} with filters: {params}")
            async with self._semaphore:
                response = await self.client.get(endpoint, params=params)
                response.raise_for_status()

            history = response.json()

            # Apply limit per entity
            if limit and limit < 500:
                limited_history = []
                for entity_history in history:
                    if len(entity_history) > limit:
                        logger.debug(
                            f"Limiting history for entity to {limit} entries "
                            f"(had {len(entity_history)})"
                        )
                        limited_history.append(entity_history[:limit])
                    else:
                        limited_history.append(entity_history)
                history = limited_history

            logger.debug(f"Retrieved history data for {len(history)} entities")

            # Track response size
            import sys

            response_size = sys.getsizeof(str(history))
            if response_size > 100_000:  # 100KB
                logger.warning(
                    f"Large history response: {response_size / 1024:.1f}KB. "
                    f"Consider using filter_entity_id and limit to reduce context usage."
                )

            success = True
            return history  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch history: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_perf
            self.performance_monitor.record_call("get_history", duration, success)

    async def get_logbook(
        self,
        timestamp: str,
        end_time: str | None = None,
        entity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get logbook entries with filtering support.

        Args:
            timestamp: ISO 8601 timestamp for the start of the logbook period
            end_time: Optional ISO 8601 timestamp for the end (defaults to now)
            entity: Optional entity ID filter
            limit: Maximum number of logbook entries to return (default 100)

        Returns:
            List of logbook entry dictionaries

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            # Build query parameters
            params: dict[str, Any] = {}

            if end_time:
                params["end_time"] = end_time

            if entity:
                params["entity"] = entity

            endpoint = f"/logbook/{timestamp}"

            logger.debug(f"Fetching logbook from {timestamp} with filters: {params}")
            async with self._semaphore:
                response = await self.client.get(endpoint, params=params)
                response.raise_for_status()

            logbook = response.json()

            # Apply limit
            if len(logbook) > limit:
                logger.warning(
                    f"Logbook truncated: {len(logbook)} entries found, "
                    f"returning first {limit}. Use entity filter for more specific results."
                )
                logbook = logbook[:limit]

            logger.debug(f"Retrieved {len(logbook)} logbook entries")

            # Track response size
            import sys

            response_size = sys.getsizeof(str(logbook))
            if response_size > 100_000:  # 100KB
                logger.warning(
                    f"Large logbook response: {response_size / 1024:.1f}KB. "
                    f"Consider using entity filter and limit to reduce context usage."
                )

            success = True
            return logbook  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch logbook: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_logbook", duration, success)

    async def get_error_log(self) -> str:
        """Get Home Assistant error log.

        Returns:
            Error log content as plain text

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Fetching error log")
            async with self._semaphore:
                response = await self.client.get("/error_log")
                response.raise_for_status()

            error_log = response.text
            logger.debug(f"Retrieved error log ({len(error_log)} bytes)")

            success = True
            return error_log

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch error log: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_error_log", duration, success)

    async def get_camera_proxy(
        self,
        entity_id: str,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes:
        """Get camera image through proxy.

        Args:
            entity_id: Camera entity ID
            width: Optional image width for resizing
            height: Optional image height for resizing

        Returns:
            Image data as bytes

        Raises:
            EntityNotFoundError: If camera entity does not exist (404)
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            # Build query parameters
            params: dict[str, Any] = {}
            if width:
                params["width"] = width
            if height:
                params["height"] = height

            logger.debug(f"Fetching camera image for {entity_id}")
            async with self._semaphore:
                response = await self.client.get(f"/camera_proxy/{entity_id}", params=params)
                response.raise_for_status()

            image_data = response.content
            logger.debug(f"Retrieved camera image ({len(image_data)} bytes)")

            success = True
            return image_data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Camera not found: {entity_id}")
                raise EntityNotFoundError(
                    f"Camera entity '{entity_id}' not found in Home Assistant"
                ) from e
            elif e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch camera image for {entity_id}: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_camera_proxy", duration, success)

    async def get_calendars(self) -> list[dict[str, Any]]:
        """Get all calendar entities.

        Returns:
            List of calendar entity dictionaries

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Fetching calendar entities")
            async with self._semaphore:
                response = await self.client.get("/calendars")
                response.raise_for_status()

            calendars = response.json()
            logger.debug(f"Retrieved {len(calendars)} calendar entities")

            success = True
            return calendars  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch calendars: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_calendars", duration, success)

    async def get_calendar_events(
        self,
        calendar_entity_id: str,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get calendar events for a specific calendar.

        Args:
            calendar_entity_id: Calendar entity ID
            start: Optional start date/time (ISO 8601)
            end: Optional end date/time (ISO 8601)

        Returns:
            List of calendar event dictionaries

        Raises:
            EntityNotFoundError: If calendar entity does not exist (404)
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            # Build query parameters
            params: dict[str, Any] = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end

            logger.debug(f"Fetching calendar events for {calendar_entity_id}")
            async with self._semaphore:
                response = await self.client.get(f"/calendars/{calendar_entity_id}", params=params)
                response.raise_for_status()

            events = response.json()
            logger.debug(f"Retrieved {len(events)} calendar events")

            success = True
            return events  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Calendar not found: {calendar_entity_id}")
                raise EntityNotFoundError(
                    f"Calendar entity '{calendar_entity_id}' not found in Home Assistant"
                ) from e
            elif e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to fetch calendar events: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("get_calendar_events", duration, success)

    async def render_template(self, template: str) -> str:
        """Render a Home Assistant template.

        Args:
            template: Template string to render

        Returns:
            Rendered template output

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If template rendering fails or has syntax errors
        """
        start_time = time.time()
        success = False

        try:
            payload = {"template": template}

            logger.debug("Rendering template")
            async with self._semaphore:
                response = await self.client.post("/template", json=payload)
                response.raise_for_status()

            result = response.text
            logger.debug("Template rendered successfully")

            success = True
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(f"Failed to render template: {e.response.text}") from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("render_template", duration, success)

    async def check_config(self) -> dict[str, Any]:
        """Validate Home Assistant configuration.

        Returns:
            Dictionary containing validation results with errors and warnings

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the API returns an error
        """
        start_time = time.time()
        success = False

        try:
            logger.debug("Checking Home Assistant configuration")
            async with self._semaphore:
                response = await self.client.post("/config/core/check_config")
                response.raise_for_status()

            result = response.json()
            logger.debug("Configuration check completed")

            success = True
            return result  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to check configuration: HTTP {e.response.status_code}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call("check_config", duration, success)

    async def handle_intent(
        self,
        intent_type: str,
        intent_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle a Home Assistant intent.

        Args:
            intent_type: Type of intent (e.g., "HassTurnOn", "HassTurnOff")
            intent_data: Optional intent data (entities, etc.)

        Returns:
            Dictionary containing intent response with speech and card data

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If intent handling fails
        """
        start_time = time.time()
        success = False

        try:
            payload = {
                "name": intent_type,
                "data": intent_data or {},
            }

            logger.info(f"Handling intent: {intent_type}")
            async with self._semaphore:
                response = await self.client.post("/intent/handle", json=payload)
                response.raise_for_status()

            result = response.json()
            logger.info(f"Intent handled successfully: {intent_type}")

            success = True
            return result  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(
                    f"Failed to handle intent {intent_type}: {e.response.text}"
                ) from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call(f"handle_intent:{intent_type}", duration, success)

    async def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> dict[str, Any]:
        """Call a Home Assistant service and invalidate relevant cache entries.

        After a successful service call, the cache is invalidated for entities
        that may have been affected by the service call.

        Args:
            domain: The service domain (e.g., 'light', 'climate', 'automation')
            service: The service name (e.g., 'turn_on', 'turn_off', 'set_temperature')
            data: Optional dictionary of service data/parameters
            return_response: If True, return service response data

        Returns:
            Response dictionary from the service call, typically containing:
                - context: Execution context information
                - Or service response data if return_response is True
                - Or an empty dict for successful calls with no return value

        Raises:
            AuthenticationError: If authentication fails (401)
            ConnectionError: If connection to Home Assistant fails
            ServiceCallError: If the service call fails
        """
        start_time = time.time()
        success = False

        try:
            endpoint = f"/services/{domain}/{service}"
            payload = data or {}

            # Add return_response to payload if requested
            if return_response:
                payload["return_response"] = True

            logger.info(f"Calling service: {domain}.{service}")
            logger.debug(f"Service data: {payload}")

            async with self._semaphore:
                response = await self.client.post(endpoint, json=payload)
                response.raise_for_status()

            result = response.json() if response.text else {}
            logger.info(f"Service call successful: {domain}.{service}")

            # Invalidate cache after successful service call
            self._invalidate_cache_after_service_call(domain, data)

            success = True
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed - invalid token")
                raise AuthenticationError(
                    "Invalid Home Assistant token. Please check your HASS_TOKEN."
                ) from e
            elif e.response.status_code == 400:
                logger.error(f"Invalid service call: {e.response.text}")
                raise ServiceCallError(
                    f"Invalid service call to {domain}.{service}: {e.response.text}"
                ) from e
            elif e.response.status_code == 404:
                logger.error(f"Service not found: {domain}.{service}")
                raise ServiceCallError(
                    f"Service '{domain}.{service}' not found in Home Assistant"
                ) from e
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise ServiceCallError(f"Service call failed: HTTP {e.response.status_code}") from e

        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Home Assistant at {self.base_url}: {str(e)}"
            ) from e

        finally:
            duration = time.time() - start_time
            self.performance_monitor.record_call(
                f"call_service:{domain}.{service}", duration, success
            )

    def _invalidate_cache_after_service_call(
        self,
        domain: str,
        data: dict[str, Any] | None,
    ) -> None:
        """Invalidate cache entries after a service call.

        This method invalidates cache entries that may have been affected by
        the service call. It invalidates:
        - The bulk states cache (states:all)
        - Individual entity caches for affected entities

        Args:
            domain: The service domain
            data: The service call data
        """
        # Always invalidate bulk states cache
        self.cache.invalidate("states:all")

        # If entity_id is specified, invalidate that specific entity
        if data and "entity_id" in data:
            entity_id = data["entity_id"]

            # Handle both single entity_id and lists
            if isinstance(entity_id, str):
                # Escape special regex characters in entity_id
                import re

                escaped_entity_id = re.escape(entity_id)
                self.cache.invalidate(f"state:{escaped_entity_id}")
            elif isinstance(entity_id, list):
                for eid in entity_id:
                    # Escape special regex characters in entity_id
                    import re

                    escaped_eid = re.escape(eid)
                    self.cache.invalidate(f"state:{escaped_eid}")
        else:
            # If no specific entity_id, invalidate all entities in the domain
            self.cache.invalidate(f"state:{domain}.*")

        logger.debug(f"Invalidated cache after {domain} service call")

    async def close(self) -> None:
        """Close the HTTP client and clean up resources.

        This should be called when the client is no longer needed to ensure
        proper cleanup of connections and resources.
        """
        logger.info("Closing Home Assistant client")
        await self.client.aclose()

    async def __aenter__(self) -> "HomeAssistantClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
