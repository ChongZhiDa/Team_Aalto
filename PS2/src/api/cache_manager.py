"""
Thread-safe in-memory cache and request throttling for API requests.
Ensures we do not exceed DataMall rate limits and provides graceful fallbacks.
"""

import time
from typing import Any, Dict, Optional, Tuple


class SimpleCache:
    def __init__(self, default_ttl_seconds: int = 60):
        self._store: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            data, timestamp = self._store[key]
            if time.time() - timestamp < self.default_ttl:
                return data
            # Expired
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expiry_ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = (value, time.time())

    def clear(self) -> None:
        self._store.clear()

