"""Small process-local fixed-window limiter for single-instance deployments.

The production Compose file runs one API instance. Do not scale it horizontally
without replacing this limiter with shared storage or edge-level enforcement.
"""

from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass
class _Window:
    started_at: float
    request_count: int
    duration_seconds: int


class FixedWindowRateLimiter:
    def __init__(self, max_clients: int = 20_000) -> None:
        self._windows: OrderedDict[str, _Window] = OrderedDict()
        self._max_clients = max_clients
        self._lock = Lock()

    def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> tuple[bool, int]:
        current_time = monotonic() if now is None else now
        with self._lock:
            window = self._windows.get(key)
            if window is None or current_time - window.started_at >= window_seconds:
                self._windows[key] = _Window(current_time, 1, window_seconds)
                self._windows.move_to_end(key)
                self._prune(current_time)
                return True, 0

            if window.request_count >= limit:
                retry_after = max(
                    1, int(window_seconds - (current_time - window.started_at) + 0.999)
                )
                return False, retry_after

            window.request_count += 1
            self._windows.move_to_end(key)
            return True, 0

    def _prune(self, now: float) -> None:
        expired = [
            key
            for key, window in self._windows.items()
            if now - window.started_at >= window.duration_seconds
        ]
        for key in expired:
            self._windows.pop(key, None)
        while len(self._windows) > self._max_clients:
            self._windows.popitem(last=False)
