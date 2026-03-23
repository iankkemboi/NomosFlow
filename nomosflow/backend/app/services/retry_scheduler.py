import calendar
from datetime import date, timedelta
from typing import Optional


def _safe_day(year: int, month: int, day: int) -> int:
    """Return the last valid day of the given month if day exceeds it."""
    return min(day, calendar.monthrange(year, month)[1])


def classify_failure_reason_rules(
    retry_count: int,
    contract_age_days: int,
    salary_day: Optional[int],
    day_of_month_failed: int,
    existing_reason: Optional[str] = None,
) -> dict:
    """
    Instant rule-based failure classification — no AI, no latency.
    Used in the dunning cycle. AI classification is available on-demand separately.
    """
    if existing_reason and existing_reason != "unknown":
        return {"failure_reason": existing_reason, "confidence": 0.7, "source": "existing"}

    # New contract (<60 days) — likely bank block on new SEPA mandate
    if contract_age_days < 60:
        return {"failure_reason": "bank_block", "confidence": 0.8, "source": "rules"}

    # Older contract with multiple retries — SEPA mandate likely revoked
    if retry_count >= 2:
        return {"failure_reason": "sepa_reject", "confidence": 0.75, "source": "rules"}

    # Failed well after salary day — insufficient funds
    if salary_day and day_of_month_failed > salary_day + 5:
        return {"failure_reason": "insufficient_funds", "confidence": 0.8, "source": "rules"}

    # Failed just before salary day — also likely insufficient funds
    if salary_day and day_of_month_failed < salary_day:
        return {"failure_reason": "insufficient_funds", "confidence": 0.75, "source": "rules"}

    # Contract age > 11 months — possibly expired card
    if contract_age_days > 330:
        return {"failure_reason": "expired_card", "confidence": 0.7, "source": "rules"}

    return {"failure_reason": "unknown", "confidence": 0.5, "source": "rules"}


def calculate_next_retry(
    failure_reason: str,
    retry_count: int,
    salary_day: Optional[int] = None,
    failed_date: Optional[date] = None,
) -> date:
    today = failed_date or date.today()

    if failure_reason == "insufficient_funds":
        if salary_day:
            # Retry just after next salary day — use the actual last valid day of the month
            candidate = today.replace(day=_safe_day(today.year, today.month, salary_day))
            if candidate <= today:
                # Push to next month
                next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
                candidate = next_month.replace(day=_safe_day(next_month.year, next_month.month, salary_day))
            return candidate + timedelta(days=2)
        else:
            return today + timedelta(days=7)

    elif failure_reason == "expired_card":
        return today + timedelta(days=14)

    elif failure_reason == "bank_block":
        # Give customer time to resolve with bank
        return today + timedelta(days=5)

    elif failure_reason == "sepa_reject":
        # Needs manual intervention — longer window
        return today + timedelta(days=10)

    else:
        # Exponential back-off for unknown
        wait_days = [3, 7, 14][min(retry_count, 2)]
        return today + timedelta(days=wait_days)


def get_dunning_stage(retry_count: int, failure_reason: str) -> str:
    if retry_count == 0:
        return "initial_notice"
    elif retry_count == 1:
        return "follow_up"
    elif retry_count == 2:
        return "suspension_warning"
    else:
        return "final_notice"
