"""
Unit tests for app/services/gemini_quota.py

All tests reset the in-process counter before running so they are fully
independent of execution order.
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

import app.services.gemini_quota as quota_mod
from app.services.gemini_quota import (
    GeminiQuotaExceededError,
    check_and_increment,
    quota_status,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc)


def _reset(count: int = 0, window_start: datetime = None):
    """Directly reset the module-level quota state between tests."""
    quota_mod._call_count = count
    quota_mod._window_start = window_start or _now()


def _make_error(used=10, limit=10, seconds_left=3600) -> GeminiQuotaExceededError:
    resets_at = _now() + timedelta(seconds=seconds_left)
    return GeminiQuotaExceededError(used=used, limit=limit, resets_at=resets_at, seconds_left=seconds_left)


# ---------------------------------------------------------------------------
# GeminiQuotaExceededError
# ---------------------------------------------------------------------------

class TestGeminiQuotaExceededError:

    def test_message_contains_counts(self):
        err = _make_error(used=100, limit=100, seconds_left=9000)
        assert "100/100" in str(err)

    def test_message_contains_hours_remaining(self):
        err = _make_error(seconds_left=3 * 3600)   # exactly 3 hours
        assert "3h" in str(err)

    def test_message_shows_minutes_when_under_one_hour(self):
        err = _make_error(seconds_left=45 * 60)    # exactly 45 minutes
        assert "45m" in str(err)

    def test_attributes_accessible(self):
        resets_at = _now() + timedelta(hours=1)
        err = GeminiQuotaExceededError(used=7, limit=10, resets_at=resets_at, seconds_left=3600)
        assert err.used == 7
        assert err.limit == 10
        assert err.resets_at == resets_at


# ---------------------------------------------------------------------------
# check_and_increment — disabled guard
# ---------------------------------------------------------------------------

class TestCheckAndIncrementDisabled:

    def test_no_op_when_disabled(self):
        _reset(count=999)
        with patch("app.services.gemini_quota.settings") as mock_settings:
            mock_settings.gemini_limit_enabled = False
            mock_settings.gemini_daily_limit = 1
            mock_settings.gemini_window_hours = 24
            # Should not raise even though count >> limit
            check_and_increment()


# ---------------------------------------------------------------------------
# check_and_increment — normal counting
# ---------------------------------------------------------------------------

class TestCheckAndIncrementCounting:

    def setup_method(self):
        _reset()

    def test_increments_count(self):
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 10
            s.gemini_window_hours = 24
            check_and_increment()
            assert quota_mod._call_count == 1

    def test_allows_calls_up_to_limit(self):
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 5
            s.gemini_window_hours = 24
            for _ in range(5):
                check_and_increment()
            assert quota_mod._call_count == 5

    def test_raises_on_limit_exceeded(self):
        _reset(count=5)
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 5
            s.gemini_window_hours = 24
            with pytest.raises(GeminiQuotaExceededError) as exc_info:
                check_and_increment()
            assert exc_info.value.used == 5
            assert exc_info.value.limit == 5

    def test_count_not_incremented_when_limit_exceeded(self):
        _reset(count=5)
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 5
            s.gemini_window_hours = 24
            with pytest.raises(GeminiQuotaExceededError):
                check_and_increment()
        assert quota_mod._call_count == 5  # unchanged


# ---------------------------------------------------------------------------
# check_and_increment — window reset
# ---------------------------------------------------------------------------

class TestWindowReset:

    def test_resets_after_window_expires(self):
        # Simulate window that started 25 hours ago
        old_start = _now() - timedelta(hours=25)
        _reset(count=99, window_start=old_start)

        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 100
            s.gemini_window_hours = 24
            check_and_increment()  # should not raise — window expired, counter reset to 1

        assert quota_mod._call_count == 1

    def test_does_not_reset_within_window(self):
        start = _now() - timedelta(hours=12)
        _reset(count=50, window_start=start)

        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 100
            s.gemini_window_hours = 24
            check_and_increment()

        assert quota_mod._call_count == 51


# ---------------------------------------------------------------------------
# quota_status
# ---------------------------------------------------------------------------

class TestQuotaStatus:

    def setup_method(self):
        _reset()

    def test_returns_expected_keys(self):
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 100
            s.gemini_window_hours = 24
            status = quota_status()
        assert {"enabled", "limit", "window_hours", "used", "remaining", "resets_at"} <= status.keys()

    def test_remaining_decreases_after_increment(self):
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 10
            s.gemini_window_hours = 24
            check_and_increment()
            check_and_increment()
            status = quota_status()
        assert status["used"] == 2
        assert status["remaining"] == 8

    def test_remaining_never_negative(self):
        _reset(count=200)
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 10
            s.gemini_window_hours = 24
            status = quota_status()
        assert status["remaining"] == 0

    def test_resets_at_is_iso_format(self):
        with patch("app.services.gemini_quota.settings") as s:
            s.gemini_limit_enabled = True
            s.gemini_daily_limit = 10
            s.gemini_window_hours = 24
            status = quota_status()
        # isoformat() on a timezone-aware datetime gives "+00:00" suffix
        assert "+00:00" in status["resets_at"] or status["resets_at"].endswith("Z")


# ---------------------------------------------------------------------------
# HTTP 429 via route (integration)
# ---------------------------------------------------------------------------

class TestQuotaRouteIntegration:

    def test_quota_status_endpoint(self, client):
        resp = client.get("/api/ai/quota-status")
        assert resp.status_code == 200
        data = resp.json()
        assert "limit" in data
        assert "remaining" in data
        assert "resets_at" in data

    def test_classify_failure_returns_429_when_quota_exceeded(self, client, db):
        from tests.conftest import make_partner, make_customer, make_payment
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        payment = make_payment(db, customer.id, status="failed")
        db.commit()

        resets_at = _now() + timedelta(hours=24)
        exc = GeminiQuotaExceededError(used=100, limit=100, resets_at=resets_at, seconds_left=86400)

        with patch("app.routes.ai.classify_payment_failure", side_effect=exc):
            resp = client.post("/api/ai/classify-failure", json={
                "customer_id": str(customer.id),
                "payment_id": str(payment.id),
            })

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "gemini_quota_exceeded"
        assert "resets_at" in body["quota"]
        assert "refresh" in body["message"].lower() or "quota" in body["message"].lower()
