import json
import re
from datetime import datetime
import google.generativeai as genai
from app.config import settings
from app.services.gemini_quota import check_and_increment


def _sanitise(value: str, max_len: int = 200) -> str:
    """Strip control characters and truncate to prevent prompt injection."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return cleaned[:max_len]

_model = None


def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
    return _model


def _safe_json(text: str) -> dict:
    """Extract and parse JSON from a Gemini response, tolerating markdown code fences."""
    # Strip markdown fences: ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    cleaned = fence_match.group(1) if fence_match else text.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned non-JSON response: {exc}\nRaw text: {text!r}") from exc


def classify_payment_failure(customer: dict, payment: dict) -> dict:
    prompt = f"""
You are an expert operations analyst at a European energy retailer.

A customer's direct debit payment has failed. Based on the context below,
classify the most likely reason for the failure.

CUSTOMER CONTEXT:
- Name: {_sanitise(customer['name'])}
- Device type: {_sanitise(customer['device_type'])}
- Contract started: {_sanitise(customer['contract_start'])}
- Contract age (days): {customer['contract_age_days']}
- Payment history: {_sanitise(customer['payment_history_summary'])}
- Usual salary day: {customer.get('salary_day', 'unknown')}
- Current day of month payment failed: {payment['day_of_month_failed']}
- Amount (EUR): {payment['amount_eur']}
- Retry count so far: {payment['retry_count']}

POSSIBLE FAILURE REASONS:
1. insufficient_funds — account balance too low, common near end of month
2. expired_card — card on file has expired (more likely for older contracts)
3. bank_block — bank rejected the debit mandate (common for new contracts <60 days)
4. sepa_reject — SEPA mandate was revoked by the customer
5. unknown — not enough signal to classify

Respond ONLY as valid JSON:
{{
  "failure_reason": "<one of the 5 options above>",
  "confidence": <float 0.0-1.0>,
  "explanation": "<one sentence plain English explanation>"
}}
"""
    check_and_increment()
    response = _get_model().generate_content(prompt)
    return _safe_json(response.text)


def score_churn_risk(customer: dict, payment_history: list, dunning_actions: list) -> dict:
    payment_summary = f"{len([p for p in payment_history if p.get('status') == 'failed'])} failed, {len([p for p in payment_history if p.get('status') == 'paid'])} paid of {len(payment_history)} total"
    days_since_last_paid = "unknown"
    paid_payments = [p for p in payment_history if p.get('status') == 'paid' and p.get('paid_at')]
    if paid_payments:
        last_paid = max(paid_payments, key=lambda x: x['paid_at'])
        if last_paid.get('paid_at'):
            days_since_last_paid = (datetime.now() - datetime.fromisoformat(str(last_paid['paid_at']))).days

    prompt = f"""
You are a churn prevention analyst at a European energy retailer. Score this customer's churn risk.

CUSTOMER:
- Name: {_sanitise(customer['name'])}
- Device: {_sanitise(customer['device_type'])}
- Tariff: {_sanitise(customer['tariff_type'])}
- Contract start: {_sanitise(customer['contract_start'])}
- Contract status: {_sanitise(customer['contract_status'])}
- City: {_sanitise(customer.get('city', 'unknown'))}
- Annual saving vs fixed tariff: €{customer.get('annual_saving_eur', 0)}

PAYMENT HISTORY (last 6 months):
- Summary: {payment_summary}
- Days since last successful payment: {days_since_last_paid}
- Dunning actions taken: {len(dunning_actions)}

Score from 0 (no risk) to 100 (certain churn).
Risk levels: low (0-25), medium (26-50), high (51-75), critical (76-100)

Respond ONLY as valid JSON:
{{
  "score": <integer 0-100>,
  "risk_level": "<low|medium|high|critical>",
  "reasoning": "<2-3 sentences explaining the score>",
  "factors": {{
    "failed_payments_30d": <int>,
    "days_since_last_paid": <int or null>,
    "retry_exhaustion_pct": <float 0-1>,
    "contract_age_days": <int>,
    "device_type": "{customer['device_type']}",
    "is_dynamic_tariff": <bool>
  }},
  "action_suggested": "<specific recommended action for the ops team>"
}}
"""
    check_and_increment()
    response = _get_model().generate_content(prompt)
    return _safe_json(response.text)


def generate_retention_message(customer: dict, payment: dict, churn_score: dict) -> dict:
    device_context = {
        "ev": "electric vehicle charging — they rely on cheap overnight rates to charge their EV",
        "heat_pump": "heat pump — they save on heating bills through dynamic tariff pricing",
        "battery": "home battery storage — they optimise self-consumption and grid export timing"
    }.get(customer.get('device_type', ''), "smart energy device")

    prompt = f"""
You are a customer retention specialist at a European energy company. Write a personalised retention message.

CUSTOMER:
- Name: {_sanitise(customer['name'])}
- Device: {_sanitise(customer['device_type'])} ({_sanitise(device_context)})
- City: {_sanitise(customer.get('city', 'Europe'))}
- Annual savings vs fixed tariff: €{customer.get('annual_saving_eur', 0):.0f}
- Contract status: {_sanitise(customer['contract_status'])}

PAYMENT ISSUE:
- Failed amount: €{payment['amount_eur']}
- Failure reason: {_sanitise(payment.get('failure_reason', 'unknown'))}
- Retry count: {payment.get('retry_count', 0)}

CHURN RISK: {churn_score.get('risk_level', 'medium')} (score: {churn_score.get('score', 50)}/100)

Write a short, warm, personalised email that:
1. Acknowledges the payment issue without being accusatory
2. References their specific device and real savings they're getting
3. Gives a clear, easy next step
4. Feels like it's from their energy provider (not a generic bank)

Respond ONLY as valid JSON:
{{
  "subject": "<email subject line>",
  "body": "<email body, 3-4 short paragraphs, plain text>",
  "tone": "<friendly|urgent|empathetic>",
  "highlight_phrase": "<one key phrase from the body to highlight in the UI>"
}}
"""
    check_and_increment()
    response = _get_model().generate_content(prompt)
    return _safe_json(response.text)
