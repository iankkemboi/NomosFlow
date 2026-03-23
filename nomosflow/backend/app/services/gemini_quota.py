"""
In-process Gemini quota guard.

Tracks API call counts in a rolling time window using a thread-safe in-memory
counter.  On process restart the counter resets — acceptable for a single-process
deployment.  For multi-process / multi-worker setups, swap _store for a Redis
backend without changing the public interface.

Configuration (all via environment / .env):
    GEMINI_LIMIT_ENABLED  — bool, default True
    GEMINI_DAILY_LIMIT    — int,  default 100  (calls per window)
    GEMINI_WINDOW_HOURS   — int,  default 24   (rolling window in hours)
"""

import threading
from datetime import datetime, timezone, timedelta

from app.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GeminiQuotaExceededError(Exception):
    """Raised when the configured Gemini call limit has been reached."""

    def __init__(self, used: int, limit: int, resets_at: datetime, seconds_left: int):
        self.used = used
        self.limit = limit
        self.resets_at = resets_at
        hours, remainder = divmod(max(0, seconds_left), 3600)
        minutes = remainder // 60
        human = f"{hours}h {minutes}m" if hours else f"{minutes}m"
        super().__init__(
            f"AI quota exceeded ({used}/{limit} calls used). "
            f"Quota will refresh in {human} "
            f"(at {resets_at.strftime('%H:%M UTC')})."
        )


# ---------------------------------------------------------------------------
# Internal state — never access directly outside this module
# ---------------------------------------------------------------------------
_lock = threading.Lock()
_window_start: datetime = _now()
_call_count: int = 0


def _reset_if_expired() -> None:
    """Must be called with _lock held."""
    global _window_start, _call_count
    if _now() - _window_start >= timedelta(hours=settings.gemini_window_hours):
        _window_start = _now()
        _call_count = 0


def check_and_increment() -> None:
    """
    Atomically check the quota and increment the counter.

    Raises GeminiQuotaExceededError if the limit has been reached.
    Is a no-op when GEMINI_LIMIT_ENABLED is False.
    """
    if not settings.gemini_limit_enabled:
        return

    global _call_count, _window_start
    with _lock:
        _reset_if_expired()
        if _call_count >= settings.gemini_daily_limit:
            resets_at = _window_start + timedelta(hours=settings.gemini_window_hours)
            seconds_left = int((resets_at - _now()).total_seconds())
            raise GeminiQuotaExceededError(
                used=_call_count,
                limit=settings.gemini_daily_limit,
                resets_at=resets_at,
                seconds_left=seconds_left,
            )
        _call_count += 1


def quota_status() -> dict:
    """Return current quota state — useful for health/debug endpoints."""
    with _lock:
        _reset_if_expired()
        resets_at = _window_start + timedelta(hours=settings.gemini_window_hours)
        return {
            "enabled": settings.gemini_limit_enabled,
            "limit": settings.gemini_daily_limit,
            "window_hours": settings.gemini_window_hours,
            "used": _call_count,
            "remaining": max(0, settings.gemini_daily_limit - _call_count),
            "resets_at": resets_at.isoformat(),
        }
