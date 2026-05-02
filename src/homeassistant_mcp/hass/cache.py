"""State caching for Home Assistant API responses."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached value with expiration.

    Attributes:
        data: The cached data
        expires_at: Timestamp when this entry expires
    """

    data: Any
    expires_at: datetime


class StateCache:
    """Simple in-memory cache with TTL support.

    This cache stores Home Assistant state data with time-based expiration.
    It supports pattern-based invalidation for clearing related cache entries
    when state changes occur.

    The cache is thread-safe for basic operations but is designed for
    single-threaded async usage.
    """

    def __init__(self) -> None:
        """Initialize an empty cache."""
        self._cache: dict[str, CacheEntry] = {}
        logger.debug("Initialized StateCache")

    def get(self, key: str) -> Any | None:
        """Get a cached value if not expired.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found and not expired, None otherwise
        """
        entry = self._cache.get(key)

        if entry is None:
            logger.debug(f"Cache miss: {key}")
            return None

        # Check if entry has expired
        if datetime.now() >= entry.expires_at:
            logger.debug(f"Cache expired: {key}")
            # Remove expired entry
            del self._cache[key]
            return None

        logger.debug(f"Cache hit: {key}")
        return entry.data

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set a cached value with TTL.

        Args:
            key: The cache key
            value: The value to cache
            ttl_seconds: Time-to-live in seconds
        """
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self._cache[key] = CacheEntry(data=value, expires_at=expires_at)

        logger.debug(f"Cached: {key} (TTL: {ttl_seconds}s, expires: {expires_at.isoformat()})")

    def invalidate(self, pattern: str | None = None) -> int:
        """Invalidate cache entries matching pattern.

        If no pattern is provided, clears all cache entries.
        The pattern supports basic wildcard matching with '*'.

        Args:
            pattern: Optional regex pattern to match keys for invalidation.
                    If None, all entries are invalidated.

        Returns:
            Number of entries invalidated
        """
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Invalidated all cache entries ({count} entries)")
            return count

        # Convert simple wildcard pattern to regex
        # Replace * with .* for regex matching
        regex_pattern = pattern.replace("*", ".*")
        regex = re.compile(regex_pattern)

        # Find matching keys
        keys_to_remove = [key for key in self._cache.keys() if regex.match(key)]

        # Remove matching entries
        for key in keys_to_remove:
            del self._cache[key]

        if keys_to_remove:
            logger.info(
                f"Invalidated {len(keys_to_remove)} cache entries " f"matching pattern: {pattern}"
            )
        else:
            logger.debug(f"No cache entries matched pattern: {pattern}")

        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries.

        This is equivalent to invalidate() with no pattern.
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared all cache entries ({count} entries)")

    def size(self) -> int:
        """Get the current number of cached entries.

        Returns:
            Number of entries in the cache (including expired ones)
        """
        return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of expired entries removed
        """
        now = datetime.now()
        expired_keys = [key for key, entry in self._cache.items() if now >= entry.expires_at]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)
