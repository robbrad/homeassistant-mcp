"""Performance optimization utilities for Home Assistant MCP server."""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def gather_with_concurrency(n: int, *tasks: Coroutine[Any, Any, T]) -> list[T]:
    """Execute coroutines with a maximum concurrency limit.

    This function limits the number of concurrent tasks to prevent
    overwhelming the Home Assistant API with too many simultaneous requests.

    Args:
        n: Maximum number of concurrent tasks
        *tasks: Coroutines to execute

    Returns:
        List of results from all tasks in the same order as input

    Example:
        results = await gather_with_concurrency(
            5,
            client.get_state("light.1"),
            client.get_state("light.2"),
            client.get_state("light.3"),
        )
    """
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def batch_service_calls(
    client: Any,
    domain: str,
    service: str,
    entity_ids: list[str],
    batch_size: int = 10,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Execute service calls in batches to avoid overwhelming the API.

    Args:
        client: The Home Assistant client
        domain: Service domain
        service: Service name
        entity_ids: List of entity IDs to call service on
        batch_size: Number of entities per batch (default: 10)
        **kwargs: Additional service data

    Returns:
        List of results from all service calls

    Example:
        results = await batch_service_calls(
            client,
            "light",
            "turn_on",
            ["light.1", "light.2", "light.3"],
            brightness=255
        )
    """
    logger.debug(f"Batching {len(entity_ids)} service calls into batches of {batch_size}")

    results = []
    for i in range(0, len(entity_ids), batch_size):
        batch = entity_ids[i : i + batch_size]
        service_data = {"entity_id": batch, **kwargs}

        logger.debug(f"Executing batch {i // batch_size + 1} with {len(batch)} entities")
        result = await client.call_service(domain, service, service_data)
        results.append(result)

    logger.info(f"Completed {len(results)} batched service calls")
    return results


async def concurrent_state_fetch(
    client: Any,
    entity_ids: list[str],
    max_concurrent: int = 10,
) -> dict[str, dict[str, Any]]:
    """Fetch states for multiple entities concurrently.

    This is more efficient than fetching states sequentially when you need
    detailed information about specific entities (not available in bulk states).

    Args:
        client: The Home Assistant client
        entity_ids: List of entity IDs to fetch
        max_concurrent: Maximum concurrent requests (default: 10)

    Returns:
        Dictionary mapping entity_id to state data

    Example:
        states = await concurrent_state_fetch(
            client,
            ["light.1", "light.2", "switch.1"]
        )
    """
    logger.debug(f"Fetching {len(entity_ids)} entity states concurrently")

    # Create tasks for all entity state fetches
    tasks = [client.get_state(entity_id) for entity_id in entity_ids]

    # Execute with concurrency limit
    results = await gather_with_concurrency(max_concurrent, *tasks)

    # Build result dictionary
    state_dict = dict(zip(entity_ids, results, strict=False))

    logger.info(f"Fetched {len(state_dict)} entity states concurrently")
    return state_dict


class PerformanceMonitor:
    """Monitor and log performance metrics for API calls.

    This class tracks timing and success/failure rates for API operations
    to help identify performance bottlenecks.
    """

    def __init__(self) -> None:
        """Initialize the performance monitor."""
        self.call_times: dict[str, list[float]] = {}
        self.call_counts: dict[str, int] = {}
        self.error_counts: dict[str, int] = {}

    def record_call(self, operation: str, duration: float, success: bool = True) -> None:
        """Record a timed operation.

        Args:
            operation: Name of the operation (e.g., "get_states", "call_service")
            duration: Duration in seconds
            success: Whether the operation succeeded
        """
        if operation not in self.call_times:
            self.call_times[operation] = []
            self.call_counts[operation] = 0
            self.error_counts[operation] = 0

        self.call_times[operation].append(duration)
        self.call_counts[operation] += 1

        if not success:
            self.error_counts[operation] += 1

    def get_stats(self, operation: str | None = None) -> dict[str, Any]:
        """Get performance statistics.

        Args:
            operation: Optional operation name to get stats for.
                      If None, returns stats for all operations.

        Returns:
            Dictionary containing performance statistics
        """
        if operation:
            if operation not in self.call_times:
                return {"error": f"No data for operation: {operation}"}

            times = self.call_times[operation]
            return {
                "operation": operation,
                "total_calls": self.call_counts[operation],
                "errors": self.error_counts[operation],
                "avg_time": sum(times) / len(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
            }

        # Return stats for all operations
        all_stats = {}
        for op in self.call_times.keys():
            all_stats[op] = self.get_stats(op)

        return all_stats

    def log_stats(self) -> None:
        """Log performance statistics for all operations."""
        stats = self.get_stats()
        logger.info("Performance Statistics:")
        for operation, data in stats.items():
            if isinstance(data, dict) and "avg_time" in data:
                logger.info(
                    f"  {operation}: {data['total_calls']} calls, "
                    f"avg={data['avg_time']:.3f}s, "
                    f"min={data['min_time']:.3f}s, "
                    f"max={data['max_time']:.3f}s, "
                    f"errors={data['errors']}"
                )


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance.

    Returns:
        The global PerformanceMonitor instance
    """
    return _performance_monitor
