"""
Unit tests for app/services/retry_scheduler.py

These tests are pure-Python — no database, no network, no Gemini.
"""
from datetime import date, timedelta

import pytest

from app.services.retry_scheduler import (
    calculate_next_retry,
    classify_failure_reason_rules,
    get_dunning_stage,
)


# ---------------------------------------------------------------------------
# classify_failure_reason_rules
# ---------------------------------------------------------------------------

class TestClassifyFailureReasonRules:

    def test_returns_existing_reason_when_already_classified(self):
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=100,
            salary_day=15,
            day_of_month_failed=10,
            existing_reason="expired_card",
        )
        assert result["failure_reason"] == "expired_card"
        assert result["source"] == "existing"

    def test_does_not_short_circuit_on_unknown_existing_reason(self):
        """existing_reason='unknown' must NOT cause early return — reclassify instead."""
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=200,  # not new contract
            salary_day=15,
            day_of_month_failed=25,  # well after salary day → insufficient_funds
            existing_reason="unknown",
        )
        assert result["failure_reason"] != "unknown"

    def test_does_not_short_circuit_on_none_existing_reason(self):
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=400,
            salary_day=None,
            day_of_month_failed=10,
            existing_reason=None,
        )
        # Should reach expired_card branch (age > 330)
        assert result["failure_reason"] == "expired_card"

    def test_new_contract_classified_as_bank_block(self):
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=30,
            salary_day=15,
            day_of_month_failed=10,
        )
        assert result["failure_reason"] == "bank_block"
        assert result["confidence"] == 0.8

    def test_multiple_retries_classified_as_sepa_reject(self):
        result = classify_failure_reason_rules(
            retry_count=2,
            contract_age_days=200,
            salary_day=15,
            day_of_month_failed=10,
        )
        assert result["failure_reason"] == "sepa_reject"
        assert result["confidence"] == 0.75

    def test_failed_after_salary_day_is_insufficient_funds(self):
        # day 25 > salary_day 15 + 5
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=200,
            salary_day=15,
            day_of_month_failed=25,
        )
        assert result["failure_reason"] == "insufficient_funds"
        assert result["confidence"] == 0.8

    def test_failed_before_salary_day_is_insufficient_funds(self):
        # day 10 < salary_day 15
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=200,
            salary_day=15,
            day_of_month_failed=10,
        )
        assert result["failure_reason"] == "insufficient_funds"
        assert result["confidence"] == 0.75

    def test_old_contract_no_salary_day_is_expired_card(self):
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=400,
            salary_day=None,
            day_of_month_failed=10,
        )
        assert result["failure_reason"] == "expired_card"
        assert result["confidence"] == 0.7

    def test_insufficient_signal_returns_unknown(self):
        # contract_age between 60-330, retry_count < 2, no salary_day info to match
        result = classify_failure_reason_rules(
            retry_count=1,
            contract_age_days=200,
            salary_day=None,
            day_of_month_failed=20,
        )
        assert result["failure_reason"] == "unknown"
        assert result["confidence"] == 0.5

    def test_boundary_contract_age_exactly_60_days(self):
        """contract_age_days == 60 should NOT match the < 60 bank_block branch."""
        result = classify_failure_reason_rules(
            retry_count=0,
            contract_age_days=60,
            salary_day=None,
            day_of_month_failed=20,
        )
        assert result["failure_reason"] != "bank_block"

    def test_boundary_retry_count_exactly_2_triggers_sepa(self):
        result = classify_failure_reason_rules(
            retry_count=2,
            contract_age_days=100,
            salary_day=15,
            day_of_month_failed=20,
        )
        assert result["failure_reason"] == "sepa_reject"


# ---------------------------------------------------------------------------
# calculate_next_retry
# ---------------------------------------------------------------------------

class TestCalculateNextRetry:

    def test_insufficient_funds_retries_after_salary_day(self):
        # salary day 15, failed on the 5th — next retry should be after the 15th
        failed = date(2024, 3, 5)
        result = calculate_next_retry("insufficient_funds", retry_count=0, salary_day=15, failed_date=failed)
        assert result > failed
        assert result.day >= 15

    def test_insufficient_funds_pushes_to_next_month_when_past_salary_day(self):
        # salary day 10, failed on the 20th — this month's salary day has passed
        failed = date(2024, 3, 20)
        result = calculate_next_retry("insufficient_funds", retry_count=0, salary_day=10, failed_date=failed)
        assert result.month == 4  # pushed to April
        assert result > failed

    def test_insufficient_funds_without_salary_day_adds_7_days(self):
        failed = date(2024, 3, 15)
        result = calculate_next_retry("insufficient_funds", retry_count=0, salary_day=None, failed_date=failed)
        assert result == failed + timedelta(days=7)

    def test_expired_card_adds_14_days(self):
        failed = date(2024, 3, 1)
        result = calculate_next_retry("expired_card", retry_count=0, failed_date=failed)
        assert result == failed + timedelta(days=14)

    def test_bank_block_adds_5_days(self):
        failed = date(2024, 3, 1)
        result = calculate_next_retry("bank_block", retry_count=0, failed_date=failed)
        assert result == failed + timedelta(days=5)

    def test_sepa_reject_adds_10_days(self):
        failed = date(2024, 3, 1)
        result = calculate_next_retry("sepa_reject", retry_count=0, failed_date=failed)
        assert result == failed + timedelta(days=10)

    def test_unknown_retry0_adds_3_days(self):
        failed = date(2024, 3, 1)
        result = calculate_next_retry("unknown", retry_count=0, failed_date=failed)
        assert result == failed + timedelta(days=3)

    def test_unknown_retry1_adds_7_days(self):
        failed = date(2024, 3, 1)
        result = calculate_next_retry("unknown", retry_count=1, failed_date=failed)
        assert result == failed + timedelta(days=7)

    def test_unknown_retry2_or_more_adds_14_days(self):
        failed = date(2024, 3, 1)
        for retry in (2, 3, 5):
            result = calculate_next_retry("unknown", retry_count=retry, failed_date=failed)
            assert result == failed + timedelta(days=14), f"retry_count={retry}"

    def test_result_is_always_after_failed_date(self):
        """Retry date must never precede the failure date."""
        failed = date(2024, 3, 15)
        for reason in ("insufficient_funds", "expired_card", "bank_block", "sepa_reject", "unknown"):
            result = calculate_next_retry(reason, retry_count=0, salary_day=10, failed_date=failed)
            assert result > failed, f"reason={reason} returned {result} <= {failed}"

    def test_uses_today_when_no_failed_date(self):
        today = date.today()
        result = calculate_next_retry("bank_block", retry_count=0, failed_date=None)
        assert result == today + timedelta(days=5)

    def test_salary_day_high_value_clamped_to_28(self):
        """salary_day=31 should be clamped to 28 without error."""
        failed = date(2024, 2, 1)
        result = calculate_next_retry("insufficient_funds", retry_count=0, salary_day=31, failed_date=failed)
        assert result is not None
        assert result > failed


# ---------------------------------------------------------------------------
# get_dunning_stage
# ---------------------------------------------------------------------------

class TestGetDunningStage:

    @pytest.mark.parametrize("retry_count,expected", [
        (0, "initial_notice"),
        (1, "follow_up"),
        (2, "suspension_warning"),
        (3, "final_notice"),
        (10, "final_notice"),
    ])
    def test_stages(self, retry_count, expected):
        assert get_dunning_stage(retry_count, "unknown") == expected
