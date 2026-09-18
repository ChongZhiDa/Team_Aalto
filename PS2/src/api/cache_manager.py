"""
Thread-safe in-memory cache, LRU capacity bounding, and request rate-limiting for API requests.
Ensures we do not exceed DataMall rate limits and provides sub-millisecond local responses.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple, List


class SimpleCache:
    """
    Thread-safe in-memory cache with:
    - Per-key custom TTL support (falls back to default_ttl_seconds)
    - Capacity bounds with automatic eviction of expired / oldest items (prevents memory leaks)
    - True thread safety using reentrant locks (threading.RLock)
    """
    def __init__(self, default_ttl_seconds: int = 60, max_size: int = 1000):
        self._lock = threading.RLock()
        # Key -> (value, creation_timestamp, ttl_seconds, last_access_timestamp)
        self._store: Dict[str, Tuple[Any, float, float, float]] = {}
        self.default_ttl = float(default_ttl_seconds)
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a cached value if it has not expired."""
        with self._lock:
            if key in self._store:
                data, created_at, ttl, _ = self._store[key]
                now = time.time()
                if now - created_at < ttl:
                    # Update access timestamp for LRU
                    self._store[key] = (data, created_at, ttl, now)
                    return data
                # Expired -> cleanup
                del self._store[key]
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stores a value with optional custom TTL, enforcing max capacity."""
        item_ttl = float(ttl) if ttl is not None else self.default_ttl
        now = time.time()
        with self._lock:
            # If cache exceeds max_size, evict expired entries first, then oldest accessed
            if len(self._store) >= self.max_size and key not in self._store:
                self._evict_overflow(now)

            self._store[key] = (value, now, item_ttl, now)

    def _evict_overflow(self, now: float) -> None:
        """Evicts expired keys, or the least-recently accessed entry if full."""
        expired_keys = [k for k, (_, created_at, ttl, _) in self._store.items() if now - created_at >= ttl]
        for k in expired_keys:
            del self._store[k]

        # If still at or over capacity, evict the least recently accessed 10%
        if len(self._store) >= self.max_size:
            sorted_by_access = sorted(self._store.items(), key=lambda item: item[1][3])
            evict_count = max(1, len(self._store) // 10)
            for k, _ in sorted_by_access[:evict_count]:
                del self._store[k]

    def purge_expired(self) -> int:
        """Manually purges all expired keys from cache. Returns count of purged keys."""
        now = time.time()
        with self._lock:
            expired = [k for k, (_, created_at, ttl, _) in self._store.items() if now - created_at >= ttl]
            for k in expired:
                del self._store[k]
            return len(expired)

    def size(self) -> int:
        """Returns the current number of cached items."""
        with self._lock:
            return len(self._store)

    def clear(self) -> None:
        """Empties the cache."""
        with self._lock:
            self._store.clear()


class RateLimiter:
    """
    Thread-safe token-bucket rate limiter.
    Smooths outbound requests to prevent HTTP 429 Too Many Requests errors.
    """
    def __init__(self, max_calls: int = 60, period_seconds: float = 60.0):
        self._lock = threading.Lock()
        self.capacity = float(max_calls)
        self.tokens = float(max_calls)
        self.fill_rate = float(max_calls) / float(period_seconds)
        self.last_update = time.time()

    def acquire(self, blocking: bool = False, timeout: float = 0.0) -> bool:
        """
        Attempts to acquire 1 request token.
        If non-blocking, returns True immediately if token available, else False.
        If blocking, waits up to timeout seconds for a token to regenerate.
        """
        start_time = time.time()
        while True:
            with self._lock:
                now = time.time()
                elapsed = now - self.last_update
                self.last_update = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            if not blocking:
                return False

            if timeout > 0.0 and (time.time() - start_time) >= timeout:
                return False

            time.sleep(0.05)


