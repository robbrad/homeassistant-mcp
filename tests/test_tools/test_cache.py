"""Unit tests for the StateCache class."""

import time
from datetime import datetime, timedelta

from src.homeassistant_mcp.hass.cache import CacheEntry, StateCache


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        data = {"test": "value"}
        expires_at = datetime.now() + timedelta(seconds=30)

        entry = CacheEntry(data=data, expires_at=expires_at)

        assert entry.data == data
        assert entry.expires_at == expires_at


class TestStateCache:
    """Tests for StateCache class."""

    def test_cache_initialization(self):
        """Test cache initializes empty."""
        cache = StateCache()

        assert cache.size() == 0

    def test_set_and_get(self):
        """Test setting and getting a cached value."""
        cache = StateCache()

        cache.set("test_key", "test_value", ttl_seconds=30)

        result = cache.get("test_key")
        assert result == "test_value"
        assert cache.size() == 1

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist returns None."""
        cache = StateCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_cache_expiration(self):
        """Test that expired entries return None."""
        cache = StateCache()

        # Set with very short TTL
        cache.set("test_key", "test_value", ttl_seconds=1)

        # Should be available immediately
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        result = cache.get("test_key")
        assert result is None

        # Expired entry should be removed
        assert cache.size() == 0

    def test_cache_overwrite(self):
        """Test that setting the same key overwrites the value."""
        cache = StateCache()

        cache.set("test_key", "value1", ttl_seconds=30)
        cache.set("test_key", "value2", ttl_seconds=30)

        result = cache.get("test_key")
        assert result == "value2"
        assert cache.size() == 1

    def test_clear(self):
        """Test clearing all cache entries."""
        cache = StateCache()

        cache.set("key1", "value1", ttl_seconds=30)
        cache.set("key2", "value2", ttl_seconds=30)
        cache.set("key3", "value3", ttl_seconds=30)

        assert cache.size() == 3

        cache.clear()

        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_invalidate_all(self):
        """Test invalidating all entries with no pattern."""
        cache = StateCache()

        cache.set("key1", "value1", ttl_seconds=30)
        cache.set("key2", "value2", ttl_seconds=30)
        cache.set("key3", "value3", ttl_seconds=30)

        count = cache.invalidate()

        assert count == 3
        assert cache.size() == 0

    def test_invalidate_with_pattern(self):
        """Test invalidating entries matching a pattern."""
        cache = StateCache()

        cache.set("state:light.living_room", "on", ttl_seconds=30)
        cache.set("state:light.bedroom", "off", ttl_seconds=30)
        cache.set("state:switch.kitchen", "on", ttl_seconds=30)
        cache.set("states:all", [], ttl_seconds=30)

        # Invalidate all light entities
        count = cache.invalidate("state:light.*")

        assert count == 2
        assert cache.get("state:light.living_room") is None
        assert cache.get("state:light.bedroom") is None
        assert cache.get("state:switch.kitchen") == "on"
        assert cache.get("states:all") == []

    def test_invalidate_with_exact_match(self):
        """Test invalidating with exact key match."""
        cache = StateCache()

        cache.set("state:light.living_room", "on", ttl_seconds=30)
        cache.set("state:light.bedroom", "off", ttl_seconds=30)

        count = cache.invalidate("state:light.living_room")

        assert count == 1
        assert cache.get("state:light.living_room") is None
        assert cache.get("state:light.bedroom") == "off"

    def test_invalidate_no_matches(self):
        """Test invalidating with pattern that matches nothing."""
        cache = StateCache()

        cache.set("state:light.living_room", "on", ttl_seconds=30)

        count = cache.invalidate("state:climate.*")

        assert count == 0
        assert cache.get("state:light.living_room") == "on"

    def test_invalidate_complex_pattern(self):
        """Test invalidating with more complex patterns."""
        cache = StateCache()

        cache.set("state:light.living_room", "on", ttl_seconds=30)
        cache.set("state:light.bedroom", "off", ttl_seconds=30)
        cache.set("state:climate.living_room", "heat", ttl_seconds=30)
        cache.set("states:all", [], ttl_seconds=30)

        # Invalidate all state: entries (but not states:)
        count = cache.invalidate("state:.*")

        assert count == 3
        assert cache.get("states:all") == []

    def test_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = StateCache()

        # Set some entries with different TTLs
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=30)
        cache.set("key3", "value3", ttl_seconds=1)

        assert cache.size() == 3

        # Wait for some to expire
        time.sleep(1.1)

        # Cleanup expired entries
        count = cache.cleanup_expired()

        assert count == 2
        assert cache.size() == 1
        assert cache.get("key2") == "value2"

    def test_cache_with_complex_data(self):
        """Test caching complex data structures."""
        cache = StateCache()

        complex_data = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "color_temp": 370, "rgb_color": [255, 200, 150]},
            "last_changed": "2024-01-01T12:00:00Z",
        }

        cache.set("test_entity", complex_data, ttl_seconds=30)

        result = cache.get("test_entity")
        assert result == complex_data
        assert result["attributes"]["brightness"] == 255

    def test_cache_with_list_data(self):
        """Test caching list data."""
        cache = StateCache()

        list_data = [
            {"entity_id": "light.1", "state": "on"},
            {"entity_id": "light.2", "state": "off"},
            {"entity_id": "light.3", "state": "on"},
        ]

        cache.set("all_lights", list_data, ttl_seconds=30)

        result = cache.get("all_lights")
        assert result == list_data
        assert len(result) == 3

    def test_multiple_operations(self):
        """Test multiple cache operations in sequence."""
        cache = StateCache()

        # Set multiple entries
        cache.set("key1", "value1", ttl_seconds=30)
        cache.set("key2", "value2", ttl_seconds=30)
        cache.set("key3", "value3", ttl_seconds=30)

        # Get some entries
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        # Invalidate one
        cache.invalidate("key2")

        # Verify state
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"

        # Add more
        cache.set("key4", "value4", ttl_seconds=30)

        # Clear all
        cache.clear()

        # Verify all gone
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key4") is None
