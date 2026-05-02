"""Tests for performance optimization utilities."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from homeassistant_mcp.hass.performance import (
    PerformanceMonitor,
    batch_service_calls,
    concurrent_state_fetch,
    gather_with_concurrency,
    get_performance_monitor,
)


@pytest.mark.asyncio
async def test_gather_with_concurrency():
    """Test concurrent execution with concurrency limit."""
    # Track execution order
    execution_order = []

    async def task(n: int, delay: float = 0.01) -> int:
        execution_order.append(f"start_{n}")
        await asyncio.sleep(delay)
        execution_order.append(f"end_{n}")
        return n * 2

    # Execute 5 tasks with max concurrency of 2
    results = await gather_with_concurrency(
        2,
        task(1),
        task(2),
        task(3),
        task(4),
        task(5),
    )

    # Verify results
    assert results == [2, 4, 6, 8, 10]

    # Verify that tasks were executed (we can't guarantee exact order due to timing)
    assert len(execution_order) == 10  # 5 starts + 5 ends


@pytest.mark.asyncio
async def test_gather_with_concurrency_exceptions():
    """Test that exceptions are properly propagated."""

    async def failing_task() -> int:
        raise ValueError("Task failed")

    async def success_task() -> int:
        return 42

    # Should raise the exception from failing task
    with pytest.raises(ValueError, match="Task failed"):
        await gather_with_concurrency(
            2,
            success_task(),
            failing_task(),
            success_task(),
        )


@pytest.mark.asyncio
async def test_batch_service_calls():
    """Test batching of service calls."""
    mock_client = AsyncMock()
    mock_client.call_service = AsyncMock(return_value={"success": True})

    entity_ids = [f"light.{i}" for i in range(25)]

    results = await batch_service_calls(
        mock_client,
        "light",
        "turn_on",
        entity_ids,
        batch_size=10,
        brightness=255,
    )

    # Should have 3 batches (10 + 10 + 5)
    assert len(results) == 3
    assert mock_client.call_service.call_count == 3

    # Verify batch calls
    calls = mock_client.call_service.call_args_list

    # First batch: 10 entities
    assert len(calls[0][0][2]["entity_id"]) == 10
    assert calls[0][0][2]["brightness"] == 255

    # Second batch: 10 entities
    assert len(calls[1][0][2]["entity_id"]) == 10

    # Third batch: 5 entities
    assert len(calls[2][0][2]["entity_id"]) == 5


@pytest.mark.asyncio
async def test_concurrent_state_fetch():
    """Test concurrent fetching of entity states."""
    mock_client = AsyncMock()

    # Mock get_state to return different states
    async def mock_get_state(entity_id: str) -> dict:
        return {
            "entity_id": entity_id,
            "state": "on" if "light" in entity_id else "off",
            "attributes": {},
        }

    mock_client.get_state = mock_get_state

    entity_ids = ["light.1", "light.2", "switch.1"]

    states = await concurrent_state_fetch(mock_client, entity_ids, max_concurrent=2)

    # Verify all states were fetched
    assert len(states) == 3
    assert "light.1" in states
    assert "light.2" in states
    assert "switch.1" in states

    # Verify state values
    assert states["light.1"]["state"] == "on"
    assert states["light.2"]["state"] == "on"
    assert states["switch.1"]["state"] == "off"


def test_performance_monitor_record_call():
    """Test recording performance metrics."""
    monitor = PerformanceMonitor()

    # Record some calls
    monitor.record_call("test_operation", 0.1, success=True)
    monitor.record_call("test_operation", 0.2, success=True)
    monitor.record_call("test_operation", 0.15, success=False)

    # Get stats
    stats = monitor.get_stats("test_operation")

    assert stats["operation"] == "test_operation"
    assert stats["total_calls"] == 3
    assert stats["errors"] == 1
    assert stats["avg_time"] == pytest.approx(0.15, rel=0.01)
    assert stats["min_time"] == 0.1
    assert stats["max_time"] == 0.2


def test_performance_monitor_multiple_operations():
    """Test monitoring multiple operations."""
    monitor = PerformanceMonitor()

    # Record calls for different operations
    monitor.record_call("get_states", 0.5, success=True)
    monitor.record_call("get_state", 0.1, success=True)
    monitor.record_call("call_service", 0.3, success=True)

    # Get all stats
    all_stats = monitor.get_stats()

    assert len(all_stats) == 3
    assert "get_states" in all_stats
    assert "get_state" in all_stats
    assert "call_service" in all_stats


def test_performance_monitor_no_data():
    """Test getting stats for non-existent operation."""
    monitor = PerformanceMonitor()

    stats = monitor.get_stats("nonexistent")

    assert "error" in stats
    assert "No data for operation" in stats["error"]


def test_get_performance_monitor_singleton():
    """Test that get_performance_monitor returns the same instance."""
    monitor1 = get_performance_monitor()
    monitor2 = get_performance_monitor()

    assert monitor1 is monitor2


def test_performance_monitor_log_stats(caplog):
    """Test logging of performance statistics."""
    import logging

    caplog.set_level(logging.INFO)

    monitor = PerformanceMonitor()

    # Record some calls
    monitor.record_call("test_op", 0.1, success=True)
    monitor.record_call("test_op", 0.2, success=True)

    # Log stats
    monitor.log_stats()

    # Verify log output
    assert "Performance Statistics" in caplog.text
    assert "test_op" in caplog.text
    assert "2 calls" in caplog.text


@pytest.mark.asyncio
async def test_batch_service_calls_empty_list():
    """Test batching with empty entity list."""
    mock_client = AsyncMock()

    results = await batch_service_calls(
        mock_client,
        "light",
        "turn_on",
        [],
        batch_size=10,
    )

    # Should return empty list
    assert results == []
    assert mock_client.call_service.call_count == 0


@pytest.mark.asyncio
async def test_concurrent_state_fetch_single_entity():
    """Test concurrent fetch with single entity."""
    mock_client = AsyncMock()

    async def mock_get_state(entity_id: str) -> dict:
        return {"entity_id": entity_id, "state": "on"}

    mock_client.get_state = mock_get_state

    states = await concurrent_state_fetch(mock_client, ["light.1"])

    assert len(states) == 1
    assert states["light.1"]["state"] == "on"


@pytest.mark.asyncio
async def test_gather_with_concurrency_single_task():
    """Test gather with single task."""

    async def task() -> int:
        return 42

    results = await gather_with_concurrency(1, task())

    assert results == [42]
