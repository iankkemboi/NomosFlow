"""
Unit tests for app/services/dunning_engine.py

All Gemini calls are mocked. The dunning engine's three-phase architecture
(DB read → parallel AI → DB write) is tested end-to-end using an in-memory
SQLite database and mock AI responses.
"""
import uuid
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import make_partner, make_customer, make_payment
from app.models.payment import Payment
from app.models.dunning_action import DunningAction
from app.models.customer import Customer
from app.services.dunning_engine import (
    _build_context,
    _apply_writes,
    run_dunning_cycle,
)


# ---------------------------------------------------------------------------
# _build_context
# ---------------------------------------------------------------------------

class TestBuildContext:

    def test_returns_none_for_missing_customer(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        payment = make_payment(db, customer.id, status="failed")
        # detach customer from payment by pointing to a random UUID
        payment.customer_id = uuid.uuid4()
        db.commit()

        result = _build_context(payment, db)
        assert result is None

    def test_builds_correct_context_keys(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        payment = make_payment(db, customer.id, status="failed")
        db.commit()

        ctx = _build_context(payment, db)
        assert ctx is not None
        assert "payment_id" in ctx
        assert "customer_ctx" in ctx
        assert "payment_ctx" in ctx
        assert "payment" in ctx
        assert "customer" in ctx

    def test_payment_history_summary_reflects_recent_payments(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        # 3 paid, 1 failed (the one we're processing)
        for i in range(3):
            make_payment(db, customer.id, status="paid",
                         due_date=date.today() - timedelta(days=30 * (i + 1)))
        failed = make_payment(db, customer.id, status="failed")
        db.commit()

        ctx = _build_context(failed, db)
        summary = ctx["customer_ctx"]["payment_history_summary"]
        assert "succeeded" in summary
        assert "failed" in summary

    def test_contract_age_days_is_positive(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=90))
        payment = make_payment(db, customer.id, status="failed")
        db.commit()

        ctx = _build_context(payment, db)
        assert ctx["customer_ctx"]["contract_age_days"] >= 90


# ---------------------------------------------------------------------------
# _apply_writes
# ---------------------------------------------------------------------------

class TestApplyWrites:

    def _make_result(self, db, classification=None, ai_error=None):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        payment = make_payment(db, customer.id, status="failed", retry_count=0, max_retries=3)
        db.commit()

        return {
            "payment_id": str(payment.id),
            "payment": payment,
            "customer": customer,
            "customer_ctx": {
                "contract_age_days": 200,
                "salary_day": 15,
            },
            "payment_ctx": {
                "day_of_month_failed": 20,
            },
            "classification": classification,
            "ai_error": ai_error,
        }

    def test_ai_classification_applied(self, db):
        classification = {
            "failure_reason": "insufficient_funds",
            "confidence": 0.85,
            "explanation": "Low balance.",
        }
        result = self._make_result(db, classification=classification)
        actions = _apply_writes(result, db)
        db.commit()

        action_types = [a["type"] for a in actions]
        assert "classified" in action_types
        assert any(a.get("reason") == "insufficient_funds" for a in actions if a["type"] == "classified")

    def test_fallback_to_rules_when_ai_fails(self, db):
        result = self._make_result(db, classification=None, ai_error="timeout")
        actions = _apply_writes(result, db)
        db.commit()

        classified = next(a for a in actions if a["type"] == "classified")
        assert classified["by"] == "rules"

    def test_payment_status_set_to_retrying(self, db):
        classification = {"failure_reason": "bank_block", "confidence": 0.8, "explanation": "Bank block."}
        result = self._make_result(db, classification=classification)
        _apply_writes(result, db)
        db.commit()

        payment = result["payment"]
        assert payment.status == "retrying"
        assert payment.next_retry_date is not None

    def test_retry_count_incremented_on_retry(self, db):
        classification = {"failure_reason": "bank_block", "confidence": 0.8, "explanation": "x"}
        result = self._make_result(db, classification=classification)
        original_retry = result["payment"].retry_count
        _apply_writes(result, db)
        db.commit()

        assert result["payment"].retry_count == original_retry + 1

    def test_written_off_when_max_retries_reached(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        payment = make_payment(db, customer.id, status="failed", retry_count=3, max_retries=3)
        db.commit()

        result = {
            "payment_id": str(payment.id),
            "payment": payment,
            "customer": customer,
            "customer_ctx": {"contract_age_days": 200, "salary_day": 15},
            "payment_ctx": {"day_of_month_failed": 20},
            "classification": {"failure_reason": "sepa_reject", "confidence": 0.75, "explanation": "x"},
            "ai_error": None,
        }
        actions = _apply_writes(result, db)
        db.commit()

        assert payment.status == "written_off"
        assert any(a["type"] == "suspended" for a in actions)

    def test_retry_count_not_incremented_on_write_off(self, db):
        """Bug fix verification: retry_count must not increment on write-off."""
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        payment = make_payment(db, customer.id, status="failed", retry_count=3, max_retries=3)
        db.commit()

        result = {
            "payment_id": str(payment.id),
            "payment": payment,
            "customer": customer,
            "customer_ctx": {"contract_age_days": 200, "salary_day": 15},
            "payment_ctx": {"day_of_month_failed": 20},
            "classification": {"failure_reason": "sepa_reject", "confidence": 0.75, "explanation": "x"},
            "ai_error": None,
        }
        _apply_writes(result, db)
        db.commit()

        assert payment.retry_count == 3  # must not be 4

    def test_customer_suspended_when_written_off(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="active",
                                 contract_start=date.today() - timedelta(days=200))
        payment = make_payment(db, customer.id, status="failed", retry_count=3, max_retries=3)
        db.commit()

        result = {
            "payment_id": str(payment.id),
            "payment": payment,
            "customer": customer,
            "customer_ctx": {"contract_age_days": 200, "salary_day": 15},
            "payment_ctx": {"day_of_month_failed": 20},
            "classification": {"failure_reason": "bank_block", "confidence": 0.8, "explanation": "x"},
            "ai_error": None,
        }
        _apply_writes(result, db)
        db.commit()

        assert customer.contract_status == "suspended"

    def test_already_suspended_customer_not_double_suspended(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="suspended",
                                 contract_start=date.today() - timedelta(days=200))
        payment = make_payment(db, customer.id, status="failed", retry_count=3, max_retries=3)
        db.commit()

        result = {
            "payment_id": str(payment.id),
            "payment": payment,
            "customer": customer,
            "customer_ctx": {"contract_age_days": 200, "salary_day": 15},
            "payment_ctx": {"day_of_month_failed": 20},
            "classification": {"failure_reason": "bank_block", "confidence": 0.8, "explanation": "x"},
            "ai_error": None,
        }
        _apply_writes(result, db)
        db.commit()

        assert customer.contract_status == "suspended"  # not "double_suspended" or changed

    def test_dunning_action_created_for_classification(self, db):
        classification = {"failure_reason": "expired_card", "confidence": 0.7, "explanation": "Old card."}
        result = self._make_result(db, classification=classification)
        payment = result["payment"]
        _apply_writes(result, db)
        db.commit()

        actions = db.query(DunningAction).filter(
            DunningAction.payment_id == payment.id,
            DunningAction.action_type == "ai_classify",
        ).all()
        assert len(actions) == 1
        assert actions[0].ai_failure_reason == "expired_card"


# ---------------------------------------------------------------------------
# run_dunning_cycle (full integration)
# ---------------------------------------------------------------------------

class TestRunDunningCycle:

    def _ai_classify_success(self, item: dict) -> dict:
        return {**item, "classification": {
            "failure_reason": "insufficient_funds",
            "confidence": 0.8,
            "explanation": "Mock AI response.",
        }, "ai_error": None}

    def test_processes_failed_payments(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="failed")
        make_payment(db, customer.id, status="failed")
        db.commit()

        with patch("app.services.dunning_engine._ai_classify", side_effect=self._ai_classify_success):
            result = run_dunning_cycle(db)

        assert result["processed"] == 2
        assert len(result["errors"]) == 0

    def test_processes_retrying_payments_too(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="retrying", retry_count=1)
        db.commit()

        with patch("app.services.dunning_engine._ai_classify", side_effect=self._ai_classify_success):
            result = run_dunning_cycle(db)

        assert result["processed"] == 1

    def test_skips_paid_payments(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="paid")
        db.commit()

        with patch("app.services.dunning_engine._ai_classify", side_effect=self._ai_classify_success):
            result = run_dunning_cycle(db)

        assert result["processed"] == 0

    def test_empty_queue_returns_zero_processed(self, db):
        result = run_dunning_cycle(db)
        assert result["processed"] == 0
        assert result["errors"] == []

    def test_partner_id_filter_isolates_payments(self, db):
        partner_a = make_partner(db, slug="partner-a")
        partner_b = make_partner(db, slug="partner-b")
        cust_a = make_customer(db, partner_a.id, contract_start=date.today() - timedelta(days=200))
        cust_b = make_customer(db, partner_b.id, contract_start=date.today() - timedelta(days=200))
        make_payment(db, cust_a.id, status="failed")
        make_payment(db, cust_b.id, status="failed")
        db.commit()

        with patch("app.services.dunning_engine._ai_classify", side_effect=self._ai_classify_success):
            result = run_dunning_cycle(db, partner_id=str(partner_a.id))

        assert result["processed"] == 1

    def test_ai_timeout_falls_back_to_rules(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="failed")
        db.commit()

        def ai_timeout(item):
            return {**item, "classification": None, "ai_error": "timeout"}

        with patch("app.services.dunning_engine._ai_classify", side_effect=ai_timeout):
            result = run_dunning_cycle(db)

        assert result["processed"] == 1
        classified = next(a for a in result["actions"] if a["type"] == "classified")
        assert classified["by"] == "rules"

    def test_limit_parameter_respected(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        for _ in range(10):
            make_payment(db, customer.id, status="failed")
        db.commit()

        with patch("app.services.dunning_engine._ai_classify", side_effect=self._ai_classify_success):
            result = run_dunning_cycle(db, limit=3)

        assert result["processed"] == 3

    def test_returns_actions_list(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="failed")
        db.commit()

        with patch("app.services.dunning_engine._ai_classify", side_effect=self._ai_classify_success):
            result = run_dunning_cycle(db)

        assert isinstance(result["actions"], list)
        assert len(result["actions"]) >= 1
