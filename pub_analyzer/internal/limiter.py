"""Rate limiter module."""

import asyncio
import time


class RateLimiter:
    """Rate limiter."""

    def __init__(self, rate: int, per_second: float = 1.0) -> None:
        self.rate = rate
        self.per = per_second
        self._tokens = float(rate)
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until new token is available."""
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._updated_at
                if elapsed > 0:
                    self._tokens = min(self.rate, self._tokens + elapsed * (self.rate / self.per))
                    self._updated_at = now

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

                missing = 1.0 - self._tokens
                wait_time = missing * (self.per / self.rate)

            await asyncio.sleep(wait_time)
