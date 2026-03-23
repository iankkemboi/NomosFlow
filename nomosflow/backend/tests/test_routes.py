"""
Integration tests for all FastAPI routes.

Uses TestClient with an in-memory SQLite database (via conftest.py fixtures).
Gemini is mocked where routes trigger AI calls.
"""
import json
import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from tests.conftest import make_partner, make_customer, make_payment, make_churn_score
from app.models.dunning_action import DunningAction


# ===========================================================================
# Health
# ===========================================================================

class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ===========================================================================
# Partners
# ===========================================================================

class TestPartnersRoutes:

    def test_list_partners_empty(self, client):
        resp = client.get("/api/partners")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_partner(self, client):
        payload = {"name": "VoltDrive", "slug": "voltdrive", "device_type": "ev"}
        resp = client.post("/api/partners", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["slug"] == "voltdrive"
        assert data["customer_count"] == 0

    def test_list_partners_includes_customer_count(self, client, db):
        partner = make_partner(db)
        make_customer(db, partner.id)
        make_customer(db, partner.id)
        db.commit()

        resp = client.get("/api/partners")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["customer_count"] == 2

    def test_get_partner_by_id(self, client, db):
        partner = make_partner(db)
        db.commit()

        resp = client.get(f"/api/partners/{partner.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(partner.id)

    def test_get_partner_not_found(self, client):
        resp = client.get(f"/api/partners/{uuid.uuid4()}")
        assert resp.status_code == 404


# ===========================================================================
# Customers
# ===========================================================================

class TestCustomersRoutes:

    def test_list_customers_empty(self, client):
        resp = client.get("/api/customers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_customer(self, client, db):
        partner = make_partner(db)
        db.commit()

        payload = {
            "partner_id": str(partner.id),
            "name": "Hans Meier",
            "email": "hans@example.com",
            "device_type": "ev",
            "tariff_type": "dynamic",
            "contract_start": "2024-01-01",
            "contract_status": "active",
        }
        resp = client.post("/api/customers", json=payload)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Hans Meier"

    def test_get_customer_by_id(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        db.commit()

        resp = client.get(f"/api/customers/{customer.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(customer.id)

    def test_get_customer_not_found(self, client):
        resp = client.get(f"/api/customers/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_filter_by_device_type(self, client, db):
        partner = make_partner(db)
        make_customer(db, partner.id, device_type="ev")
        make_customer(db, partner.id, device_type="heat_pump")
        db.commit()

        resp = client.get("/api/customers?device_type=ev")
        assert resp.status_code == 200
        customers = resp.json()
        assert len(customers) == 1
        assert customers[0]["device_type"] == "ev"

    def test_filter_by_contract_status(self, client, db):
        partner = make_partner(db)
        make_customer(db, partner.id, contract_status="active")
        make_customer(db, partner.id, contract_status="suspended")
        db.commit()

        resp = client.get("/api/customers?contract_status=suspended")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filter_by_risk_level(self, client, db):
        partner = make_partner(db)
        c1 = make_customer(db, partner.id)
        c2 = make_customer(db, partner.id)
        make_churn_score(db, c1.id, risk_level="critical")
        make_churn_score(db, c2.id, risk_level="low")
        db.commit()

        resp = client.get("/api/customers?risk_level=critical")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert str(c1.id) in ids
        assert str(c2.id) not in ids

    def test_update_customer(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id, contract_status="active")
        db.commit()

        resp = client.patch(f"/api/customers/{customer.id}", json={"contract_status": "suspended"})
        assert resp.status_code == 200
        assert resp.json()["contract_status"] == "suspended"

    def test_update_customer_not_found(self, client):
        resp = client.patch(f"/api/customers/{uuid.uuid4()}", json={"contract_status": "suspended"})
        assert resp.status_code == 404

    def test_full_profile(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        make_payment(db, customer.id, status="paid")
        make_payment(db, customer.id, status="failed")
        make_churn_score(db, customer.id, score=70, risk_level="high")
        db.commit()

        resp = client.get(f"/api/customers/{customer.id}/full-profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_payments_count"] == 2
        assert data["failed_payments_count"] == 1
        assert data["latest_risk_level"] == "high"
        assert data["latest_churn_score"] == 70

    def test_full_profile_not_found(self, client):
        resp = client.get(f"/api/customers/{uuid.uuid4()}/full-profile")
        assert resp.status_code == 404


# ===========================================================================
# Payments
# ===========================================================================

class TestPaymentsRoutes:

    def test_list_payments_empty(self, client):
        resp = client.get("/api/payments")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_by_status(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        make_payment(db, customer.id, status="paid")
        make_payment(db, customer.id, status="failed")
        db.commit()

        resp = client.get("/api/payments?status=failed")
        assert resp.status_code == 200
        payments = resp.json()
        assert all(p["status"] == "failed" for p in payments)

    def test_get_payment_by_id(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        payment = make_payment(db, customer.id, status="paid")
        db.commit()

        resp = client.get(f"/api/payments/{payment.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(payment.id)

    def test_get_payment_not_found(self, client):
        resp = client.get(f"/api/payments/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_get_customer_payments(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        make_payment(db, customer.id, status="paid")
        make_payment(db, customer.id, status="failed")
        db.commit()

        resp = client.get(f"/api/payments/customer/{customer.id}")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


# ===========================================================================
# Dunning
# ===========================================================================

class TestDunningRoutes:

    def _ai_classify_success(self, item):
        return {**item, "classification": {
            "failure_reason": "insufficient_funds",
            "confidence": 0.8,
            "explanation": "Low balance.",
        }, "ai_error": None}

    def test_dunning_queue_empty(self, client):
        resp = client.get("/api/dunning/queue")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_dunning_queue_lists_failed_payments(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        make_payment(db, customer.id, status="failed")
        db.commit()

        resp = client.get("/api/dunning/queue")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_dunning_queue_excludes_paid(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        make_payment(db, customer.id, status="paid")
        db.commit()

        resp = client.get("/api/dunning/queue")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_dunning_timeline_empty(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        db.commit()

        resp = client.get(f"/api/dunning/timeline/{customer.id}")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_dunning_timeline_not_found(self, client):
        resp = client.get(f"/api/dunning/timeline/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_run_cycle_returns_completed_status(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="failed")
        db.commit()

        with patch("app.services.dunning_engine._ai_classify", side_effect=self._ai_classify_success):
            resp = client.post("/api/dunning/run-cycle")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["processed"] == 1

    def test_run_cycle_on_empty_queue(self, client):
        resp = client.post("/api/dunning/run-cycle")
        assert resp.status_code == 200
        assert resp.json()["processed"] == 0


# ===========================================================================
# Churn
# ===========================================================================

class TestChurnRoutes:

    def test_churn_scores_empty(self, client):
        resp = client.get("/api/churn/scores")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_score_single_customer_heuristic(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=300))
        make_payment(db, customer.id, status="paid")
        db.commit()

        resp = client.post(f"/api/churn/score/{customer.id}?use_ai=false")
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert data["risk_level"] in ("low", "medium", "high", "critical")

    def test_score_single_customer_not_found(self, client):
        resp = client.post(f"/api/churn/score/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_score_all_customers(self, client, db):
        partner = make_partner(db)
        make_customer(db, partner.id, contract_start=date.today() - timedelta(days=300))
        make_customer(db, partner.id, contract_start=date.today() - timedelta(days=300))
        db.commit()

        resp = client.post("/api/churn/score-all?use_ai=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["scored"] == 2
        assert data["errors"] == []

    def test_churn_scores_listed_after_scoring(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=300))
        make_churn_score(db, customer.id, score=80, risk_level="critical")
        db.commit()

        resp = client.get("/api/churn/scores")
        assert resp.status_code == 200
        scores = resp.json()
        assert len(scores) == 1
        assert scores[0]["score"] == 80

    def test_churn_scores_filter_by_risk_level(self, client, db):
        partner = make_partner(db)
        c1 = make_customer(db, partner.id, contract_start=date.today() - timedelta(days=300))
        c2 = make_customer(db, partner.id, contract_start=date.today() - timedelta(days=300))
        make_churn_score(db, c1.id, risk_level="critical")
        make_churn_score(db, c2.id, risk_level="low")
        db.commit()

        resp = client.get("/api/churn/scores?risk_level=critical")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["risk_level"] == "critical"


# ===========================================================================
# AI routes
# ===========================================================================

class TestAIRoutes:

    def test_dashboard_summary_zeros_on_empty_db(self, client):
        resp = client.get("/api/ai/dashboard-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_customers"] == 0
        assert data["failed_payments"] == 0
        assert data["at_risk_customers"] == 0
        assert data["revenue_at_risk_eur"] == 0.0

    def test_dashboard_summary_counts_correctly(self, client, db):
        partner = make_partner(db)
        c1 = make_customer(db, partner.id)
        c2 = make_customer(db, partner.id)
        make_payment(db, c1.id, status="failed", amount_eur=100)
        make_payment(db, c2.id, status="retrying", amount_eur=50)
        make_payment(db, c1.id, status="paid", amount_eur=90)
        make_churn_score(db, c1.id, risk_level="critical")
        make_churn_score(db, c2.id, risk_level="high")
        db.commit()

        resp = client.get("/api/ai/dashboard-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_customers"] == 2
        assert data["failed_payments"] == 2
        assert data["at_risk_customers"] == 2
        assert data["revenue_at_risk_eur"] == 150.0

    def test_classify_failure_customer_not_found(self, client):
        resp = client.post("/api/ai/classify-failure", json={
            "customer_id": str(uuid.uuid4()),
            "payment_id": str(uuid.uuid4()),
        })
        assert resp.status_code == 404
        assert "Customer" in resp.json()["detail"]

    def test_classify_failure_payment_not_found(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id)
        db.commit()

        resp = client.post("/api/ai/classify-failure", json={
            "customer_id": str(customer.id),
            "payment_id": str(uuid.uuid4()),
        })
        assert resp.status_code == 404
        assert "Payment" in resp.json()["detail"]

    def test_classify_failure_calls_gemini(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        payment = make_payment(db, customer.id, status="failed")
        db.commit()

        ai_result = {"failure_reason": "expired_card", "confidence": 0.7, "explanation": "Old card."}
        with patch("app.routes.ai.classify_payment_failure", return_value=ai_result):
            resp = client.post("/api/ai/classify-failure", json={
                "customer_id": str(customer.id),
                "payment_id": str(payment.id),
            })

        assert resp.status_code == 200
        assert resp.json()["failure_reason"] == "expired_card"

    def test_classify_failure_payment_history_summary_not_hardcoded(self, client, db):
        """Bug fix verification: the prompt must contain real payment history."""
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        payment = make_payment(db, customer.id, status="failed")
        db.commit()

        captured_customer_ctx = {}

        def capture_and_return(customer_ctx, payment_ctx):
            captured_customer_ctx.update(customer_ctx)
            return {"failure_reason": "unknown", "confidence": 0.5, "explanation": "x"}

        with patch("app.routes.ai.classify_payment_failure", side_effect=capture_and_return):
            client.post("/api/ai/classify-failure", json={
                "customer_id": str(customer.id),
                "payment_id": str(payment.id),
            })

        summary = captured_customer_ctx.get("payment_history_summary", "")
        assert "See payment records" not in summary, (
            "payment_history_summary must not be the hardcoded placeholder"
        )
        assert "succeeded" in summary or "failed" in summary

    def test_retention_message_customer_not_found(self, client):
        resp = client.post("/api/ai/retention-message", json={
            "customer_id": str(uuid.uuid4()),
        })
        assert resp.status_code == 404

    def test_retention_message_returns_message(self, client, db):
        partner = make_partner(db)
        customer = make_customer(db, partner.id,
                                 contract_start=date.today() - timedelta(days=200))
        make_payment(db, customer.id, status="failed")
        make_churn_score(db, customer.id)
        db.commit()

        ai_msg = {
            "subject": "Your EV charging tariff",
            "body": "Dear Test Customer,\n\nWe noticed...",
            "tone": "empathetic",
            "highlight_phrase": "saving you €480 per year",
        }
        with patch("app.services.message_generator.generate_retention_message", return_value=ai_msg):
            resp = client.post("/api/ai/retention-message", json={
                "customer_id": str(customer.id),
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["subject"] == "Your EV charging tariff"
        assert "highlight_phrase" in data
