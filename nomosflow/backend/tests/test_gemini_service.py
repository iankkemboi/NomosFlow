"""
Unit tests for app/services/gemini_service.py

All Gemini API calls are mocked — no network, no real API key required.
Tests cover:
  - _safe_json parsing logic
  - classify_payment_failure
  - score_churn_risk
  - generate_retention_message
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.gemini_service import (
    _safe_json,
    classify_payment_failure,
    score_churn_risk,
    generate_retention_message,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_model_response(text: str):
    """Return a patched _get_model() whose generate_content() returns `text`."""
    mock_response = MagicMock()
    mock_response.text = text
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    return mock_model


SAMPLE_CUSTOMER = {
    "name": "Anna Müller",
    "device_type": "ev",
    "tariff_type": "dynamic",
    "contract_start": "2023-06-01",
    "contract_status": "active",
    "city": "Munich",
    "annual_saving_eur": 480,
    "salary_day": 15,
    "contract_age_days": 300,
    "payment_history_summary": "5 of 6 succeeded, 1 failed",
}

SAMPLE_PAYMENT = {
    "amount_eur": 89.50,
    "day_of_month_failed": 22,
    "retry_count": 0,
}


# ---------------------------------------------------------------------------
# _safe_json
# ---------------------------------------------------------------------------

class TestSafeJson:

    def test_parses_plain_json(self):
        raw = '{"score": 42, "reason": "test"}'
        result = _safe_json(raw)
        assert result == {"score": 42, "reason": "test"}

    def test_parses_json_with_markdown_fence(self):
        raw = '```json\n{"score": 42}\n```'
        result = _safe_json(raw)
        assert result == {"score": 42}

    def test_parses_json_with_plain_fence(self):
        raw = '```\n{"score": 42}\n```'
        result = _safe_json(raw)
        assert result == {"score": 42}

    def test_parses_json_with_leading_text_before_fence(self):
        """Gemini sometimes emits prose before the code fence."""
        raw = 'Here is the answer:\n```json\n{"failure_reason": "bank_block"}\n```'
        result = _safe_json(raw)
        assert result["failure_reason"] == "bank_block"

    def test_raises_value_error_on_malformed_json(self):
        with pytest.raises(ValueError, match="non-JSON"):
            _safe_json("this is not json at all")

    def test_raises_value_error_on_truncated_json(self):
        with pytest.raises(ValueError, match="non-JSON"):
            _safe_json('{"key": ')

    def test_raises_value_error_on_fenced_malformed_json(self):
        with pytest.raises(ValueError):
            _safe_json("```json\nnot valid json\n```")

    def test_handles_nested_objects(self):
        raw = '{"factors": {"a": 1, "b": true}, "score": 55}'
        result = _safe_json(raw)
        assert result["factors"]["a"] == 1
        assert result["score"] == 55


# ---------------------------------------------------------------------------
# classify_payment_failure
# ---------------------------------------------------------------------------

class TestClassifyPaymentFailure:

    def test_returns_parsed_classification(self):
        expected = {
            "failure_reason": "insufficient_funds",
            "confidence": 0.85,
            "explanation": "Account balance too low near month end.",
        }
        mock_model = _mock_model_response(json.dumps(expected))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            result = classify_payment_failure(SAMPLE_CUSTOMER, SAMPLE_PAYMENT)

        assert result["failure_reason"] == "insufficient_funds"
        assert result["confidence"] == 0.85
        assert "explanation" in result

    def test_handles_markdown_wrapped_response(self):
        payload = {"failure_reason": "expired_card", "confidence": 0.7, "explanation": "Card expired."}
        raw = f"```json\n{json.dumps(payload)}\n```"
        mock_model = _mock_model_response(raw)

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            result = classify_payment_failure(SAMPLE_CUSTOMER, SAMPLE_PAYMENT)

        assert result["failure_reason"] == "expired_card"

    def test_raises_on_invalid_json_from_gemini(self):
        mock_model = _mock_model_response("I cannot classify this payment.")

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            with pytest.raises(ValueError, match="non-JSON"):
                classify_payment_failure(SAMPLE_CUSTOMER, SAMPLE_PAYMENT)

    def test_prompt_includes_customer_name(self):
        payload = {"failure_reason": "unknown", "confidence": 0.5, "explanation": "No signal."}
        mock_model = _mock_model_response(json.dumps(payload))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            classify_payment_failure(SAMPLE_CUSTOMER, SAMPLE_PAYMENT)

        call_args = mock_model.generate_content.call_args[0][0]
        assert "Anna Müller" in call_args

    def test_prompt_includes_payment_amount(self):
        payload = {"failure_reason": "unknown", "confidence": 0.5, "explanation": "x"}
        mock_model = _mock_model_response(json.dumps(payload))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            classify_payment_failure(SAMPLE_CUSTOMER, SAMPLE_PAYMENT)

        call_args = mock_model.generate_content.call_args[0][0]
        assert "89.5" in call_args


# ---------------------------------------------------------------------------
# score_churn_risk
# ---------------------------------------------------------------------------

class TestScoreChurnRisk:

    def _make_payment_history(self, n_failed=2, n_paid=4):
        history = [{"status": "failed", "amount_eur": 90, "due_date": "2024-01-01", "paid_at": None,
                    "failure_reason": "insufficient_funds", "retry_count": 1}] * n_failed
        history += [{"status": "paid", "amount_eur": 90, "due_date": "2024-02-01",
                     "paid_at": "2024-02-02T10:00:00", "failure_reason": None, "retry_count": 0}] * n_paid
        return history

    def test_returns_parsed_score(self):
        expected = {
            "score": 65,
            "risk_level": "high",
            "reasoning": "Two failed payments.",
            "factors": {"failed_payments_30d": 2, "contract_age_days": 300},
            "action_suggested": "Call customer.",
        }
        mock_model = _mock_model_response(json.dumps(expected))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            result = score_churn_risk(SAMPLE_CUSTOMER, self._make_payment_history(), [])

        assert result["score"] == 65
        assert result["risk_level"] == "high"

    def test_handles_empty_payment_history(self):
        expected = {"score": 30, "risk_level": "medium", "reasoning": "Limited history.",
                    "factors": {}, "action_suggested": "Monitor."}
        mock_model = _mock_model_response(json.dumps(expected))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            result = score_churn_risk(SAMPLE_CUSTOMER, [], [])

        assert result["score"] == 30

    def test_raises_on_bad_gemini_response(self):
        mock_model = _mock_model_response("error occurred")

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            with pytest.raises(ValueError):
                score_churn_risk(SAMPLE_CUSTOMER, self._make_payment_history(), [])

    def test_prompt_includes_device_type(self):
        expected = {"score": 20, "risk_level": "low", "reasoning": "Good.",
                    "factors": {}, "action_suggested": "None."}
        mock_model = _mock_model_response(json.dumps(expected))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            score_churn_risk(SAMPLE_CUSTOMER, [], [])

        prompt = mock_model.generate_content.call_args[0][0]
        assert "ev" in prompt


# ---------------------------------------------------------------------------
# generate_retention_message
# ---------------------------------------------------------------------------

class TestGenerateRetentionMessage:

    SAMPLE_CHURN = {"score": 70, "risk_level": "high"}

    def test_returns_parsed_message(self):
        expected = {
            "subject": "Your energy savings update",
            "body": "Dear Anna, we noticed...",
            "tone": "empathetic",
            "highlight_phrase": "saving €480 per year",
        }
        mock_model = _mock_model_response(json.dumps(expected))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            result = generate_retention_message(SAMPLE_CUSTOMER, SAMPLE_PAYMENT, self.SAMPLE_CHURN)

        assert result["subject"] == "Your energy savings update"
        assert result["tone"] == "empathetic"
        assert "highlight_phrase" in result

    def test_ev_device_context_in_prompt(self):
        payload = {"subject": "s", "body": "b", "tone": "friendly", "highlight_phrase": "x"}
        mock_model = _mock_model_response(json.dumps(payload))

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            generate_retention_message(SAMPLE_CUSTOMER, SAMPLE_PAYMENT, self.SAMPLE_CHURN)

        prompt = mock_model.generate_content.call_args[0][0]
        assert "electric vehicle" in prompt

    def test_heat_pump_device_context_in_prompt(self):
        payload = {"subject": "s", "body": "b", "tone": "friendly", "highlight_phrase": "x"}
        mock_model = _mock_model_response(json.dumps(payload))
        customer = {**SAMPLE_CUSTOMER, "device_type": "heat_pump"}

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            generate_retention_message(customer, SAMPLE_PAYMENT, self.SAMPLE_CHURN)

        prompt = mock_model.generate_content.call_args[0][0]
        assert "heat pump" in prompt

    def test_battery_device_context_in_prompt(self):
        payload = {"subject": "s", "body": "b", "tone": "friendly", "highlight_phrase": "x"}
        mock_model = _mock_model_response(json.dumps(payload))
        customer = {**SAMPLE_CUSTOMER, "device_type": "battery"}

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            generate_retention_message(customer, SAMPLE_PAYMENT, self.SAMPLE_CHURN)

        prompt = mock_model.generate_content.call_args[0][0]
        assert "battery" in prompt

    def test_unknown_device_type_uses_fallback(self):
        payload = {"subject": "s", "body": "b", "tone": "friendly", "highlight_phrase": "x"}
        mock_model = _mock_model_response(json.dumps(payload))
        customer = {**SAMPLE_CUSTOMER, "device_type": "solar_panel"}

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            generate_retention_message(customer, SAMPLE_PAYMENT, self.SAMPLE_CHURN)

        prompt = mock_model.generate_content.call_args[0][0]
        assert "smart energy device" in prompt

    def test_raises_on_bad_gemini_response(self):
        mock_model = _mock_model_response("Sorry, cannot help.")

        with patch("app.services.gemini_service._get_model", return_value=mock_model):
            with pytest.raises(ValueError):
                generate_retention_message(SAMPLE_CUSTOMER, SAMPLE_PAYMENT, self.SAMPLE_CHURN)
