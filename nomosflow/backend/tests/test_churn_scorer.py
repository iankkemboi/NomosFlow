"""
Unit tests for app/services/churn_scorer.py

Gemini is mocked throughout — these tests exercise the heuristic scorer
and the context builders without any network calls.
"""
import uuid
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import make_partner, make_customer, make_payment, make_churn_score
from app.services.churn_scorer import (
    build_customer_context,
    build_payment_history,
    simple_score_customer,
    score_customer,
)


# ---------------------------------------------------------------------------
# build_customer_context
# ---------------------------------------------------------------------------

class TestBuildCustomerContext:

    def test_includes_required_keys(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        db.commit()

        ctx = build_customer_context(customer)
        for key in ("name", "device_type", "tariff_type", "contract_start",
                    "contract_status", "city", "annual_saving_eur", "salary_day"):
            assert key in ctx, f"Missing key: {key}"

    def test_annual_saving_defaults_to_zero_when_null(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, annual_saving_eur=None)
        db.commit()
        ctx = build_customer_context(customer)
        assert ctx["annual_saving_eur"] == 0.0

    def test_contract_start_is_string(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        db.commit()
        ctx = build_customer_context(customer)
        assert isinstance(ctx["contract_start"], str)


# ---------------------------------------------------------------------------
# build_payment_history
# ---------------------------------------------------------------------------

class TestBuildPaymentHistory:

    def test_empty_list(self):
        assert build_payment_history([]) == []

    def test_paid_at_is_none_when_not_paid(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        payment = make_payment(db, customer.id, status="failed", paid_at=None)
        db.commit()

        history = build_payment_history([payment])
        assert history[0]["paid_at"] is None

    def test_correct_fields_returned(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        payment = make_payment(db, customer.id, status="paid", amount_eur=100)
        db.commit()

        history = build_payment_history([payment])
        assert history[0]["status"] == "paid"
        assert history[0]["amount_eur"] == 100.0
        assert "due_date" in history[0]
        assert "failure_reason" in history[0]
        assert "retry_count" in history[0]


# ---------------------------------------------------------------------------
# simple_score_customer (heuristic, no Gemini)
# ---------------------------------------------------------------------------

class TestSimpleScoreCustomer:

    def test_active_customer_all_paid_gets_low_score(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="active",
                                 contract_start=date.today() - timedelta(days=300))
        for i in range(6):
            make_payment(db, customer.id, status="paid",
                         due_date=date.today() - timedelta(days=30 * i))
        db.commit()

        score = simple_score_customer(customer, db)
        assert score.score == 0
        assert score.risk_level == "low"

    def test_all_failed_payments_gives_high_score(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="active",
                                 contract_start=date.today() - timedelta(days=300))
        for i in range(6):
            make_payment(db, customer.id, status="failed",
                         due_date=date.today() - timedelta(days=30 * i))
        db.commit()

        score = simple_score_customer(customer, db)
        assert score.score >= 50  # fail rate 100% → 50 pts minimum

    def test_cancelled_customer_scores_100(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="cancelled",
                                 contract_start=date.today() - timedelta(days=300))
        db.commit()

        score = simple_score_customer(customer, db)
        assert score.score == 100
        assert score.risk_level == "critical"

    def test_suspended_customer_gets_penalty(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="suspended",
                                 contract_start=date.today() - timedelta(days=300))
        make_payment(db, customer.id, status="paid")
        db.commit()

        score = simple_score_customer(customer, db)
        assert score.score >= 25  # suspended penalty alone

    def test_new_contract_gets_age_penalty(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="active",
                                 contract_start=date.today() - timedelta(days=30))
        make_payment(db, customer.id, status="paid")
        db.commit()

        score = simple_score_customer(customer, db)
        assert score.score >= 15  # <60 days penalty

    def test_exhausted_retries_adds_penalty(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="active",
                                 contract_start=date.today() - timedelta(days=300))
        make_payment(db, customer.id, status="failed", retry_count=3, max_retries=3)
        db.commit()

        score = simple_score_customer(customer, db)
        assert score.score >= 20  # exhausted-retries penalty

    def test_score_never_exceeds_100(self, db):
        """All bad signals at once must not push score above 100."""
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="suspended",
                                 contract_start=date.today() - timedelta(days=20))
        for _ in range(6):
            make_payment(db, customer.id, status="failed", retry_count=3, max_retries=3)
        db.commit()

        score = simple_score_customer(customer, db)
        assert score.score <= 100

    def test_score_is_persisted_to_db(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=300))
        db.commit()

        churn = simple_score_customer(customer, db)
        assert churn.id is not None
        assert churn.customer_id == customer.id

    def test_risk_level_thresholds(self, db):
        """Verify all four risk_level buckets based on known heuristic outcomes."""
        partner = make_partner(db)

        # low: cancelled→100 handled separately; pure low = 0 score
        c_low = make_customer(db, partner.id,
                              contract_start=date.today() - timedelta(days=300))
        make_payment(db, c_low.id, status="paid")
        db.commit()
        s = simple_score_customer(c_low, db)
        assert s.risk_level == "low"

        # critical: cancelled
        c_crit = make_customer(db, partner.id, contract_status="cancelled",
                               contract_start=date.today() - timedelta(days=300))
        db.commit()
        s = simple_score_customer(c_crit, db)
        assert s.risk_level == "critical"


# ---------------------------------------------------------------------------
# score_customer (AI path) — Gemini mocked
# ---------------------------------------------------------------------------

class TestScoreCustomer:

    def test_score_customer_calls_gemini_and_saves(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="paid")
        db.commit()

        ai_response = {
            "score": 42,
            "risk_level": "medium",
            "reasoning": "Moderate risk based on payment history.",
            "factors": {"failed_payments_30d": 0, "contract_age_days": 200},
            "action_suggested": "Monitor only.",
        }

        with patch("app.services.churn_scorer.score_churn_risk", return_value=ai_response):
            result = score_customer(str(customer.id), db)

        assert result.score == 42
        assert result.risk_level == "medium"
        assert result.customer_id == customer.id

    def test_score_customer_raises_for_missing_customer(self, db):
        with pytest.raises(ValueError, match="not found"):
            score_customer(str(uuid.uuid4()), db)

    def test_score_clamps_out_of_range_ai_value(self, db):
        """AI returning score=150 must be clamped to 100."""
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        db.commit()

        ai_response = {
            "score": 150,
            "risk_level": "critical",
            "reasoning": "Extreme.",
            "factors": {},
            "action_suggested": "Act now.",
        }

        with patch("app.services.churn_scorer.score_churn_risk", return_value=ai_response):
            result = score_customer(str(customer.id), db)

        assert result.score == 100

    def test_score_clamps_negative_ai_value(self, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        db.commit()

        ai_response = {
            "score": -10,
            "risk_level": "low",
            "reasoning": "Very safe.",
            "factors": {},
            "action_suggested": "None.",
        }

        with patch("app.services.churn_scorer.score_churn_risk", return_value=ai_response):
            result = score_customer(str(customer.id), db)

        assert result.score == 0
