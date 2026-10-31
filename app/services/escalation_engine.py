"""
Requirement Debt Ledger (RDL) - Escalation Engine
Evaluates deadlines, review schedules, breach severity levels, and automated alert scanning.
"""
from datetime import date
from typing import Dict, Any, Tuple
from app.config import ESCALATION_WARNING_DAYS
from app.services.risk_engine import parse_date

def get_escalation_status(
    review_date_str: str,
    deadline_date_str: str,
    status: str,
    as_of_date: date = None,
) -> Tuple[str, int, int]:
    """
    Returns (escalation_level, days_to_review, days_to_deadline).
    Levels:
    - 'RESOLVED': Debt already closed
    - 'CRITICAL_BREACH': Past resolution deadline date
    - 'OVERDUE_REVIEW': Past review date (no review conducted)
    - 'UPCOMING_REVIEW': Within 7 days of review date
    - 'OK': Healthy schedule
    """
    if status.lower() in ("resolved", "accepted permanent"):
        return "RESOLVED", 0, 0

    current_date = as_of_date or date.today()
    review_date = parse_date(review_date_str)
    deadline_date = parse_date(deadline_date_str)

    days_to_review = (review_date - current_date).days
    days_to_deadline = (deadline_date - current_date).days

    if days_to_deadline < 0:
        level = "CRITICAL_BREACH"
    elif days_to_review < 0:
        level = "OVERDUE_REVIEW"
    elif days_to_review <= ESCALATION_WARNING_DAYS:
        level = "UPCOMING_REVIEW"
    else:
        level = "OK"

    return level, days_to_review, days_to_deadline
