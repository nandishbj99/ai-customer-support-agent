import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter with per-key tracking and automatic expiry."""

    def __init__(self, default_limit_per_minute: int = 60):
        self.default_limit = default_limit_per_minute
        self._history: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(
        self,
        key: str,
        limit: Optional[int] = None,
        window_seconds: int = 60,
    ) -> Tuple[bool, int]:
        """Check if request for `key` is allowed within `window_seconds`.
        
        Returns:
            Tuple[bool, int]: (allowed, retry_after_seconds)
        """
        now = time.time()
        max_requests = limit or self.default_limit
        cutoff = now - window_seconds

        # Prune old timestamps
        timestamps = [t for t in self._history[key] if t > cutoff]
        self._history[key] = timestamps

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, retry_after

        # Record this request
        self._history[key].append(now)
        return True, 0

    def reset(self, key: Optional[str] = None):
        """Reset history for a key or clear all."""
        if key:
            self._history.pop(key, None)
        else:
            self._history.clear()


rate_limiter = SlidingWindowRateLimiter()
