"""
Unit tests for Deadline and Review Escalation Engine
"""
from datetime import date, timedelta
from app.services.escalation_engine import get_escalation_status

def test_escalation_status_resolved():
    today = date(2026, 10, 16)
    rev = (today - timedelta(days=20)).isoformat()
    dead = (today - timedelta(days=10)).isoformat()

    status, d_rev, d_dead = get_escalation_status(rev, dead, "Resolved", as_of_date=today)
    assert status == "RESOLVED"

def test_escalation_status_ok():
    today = date(2026, 10, 16)
    # Review is 14 days away, deadline 30 days
    rev = (today + timedelta(days=14)).isoformat()
    dead = (today + timedelta(days=30)).isoformat()

    status, d_rev, d_dead = get_escalation_status(rev, dead, "Deferred", as_of_date=today)
    assert status == "OK"
    assert d_rev == 14
    assert d_dead == 30

def test_escalation_status_upcoming_review():
    today = date(2026, 10, 16)
    # Review is 4 days away (<= 7 days)
    rev = (today + timedelta(days=4)).isoformat()
    dead = (today + timedelta(days=20)).isoformat()

    status, d_rev, d_dead = get_escalation_status(rev, dead, "Deferred", as_of_date=today)
    assert status == "UPCOMING_REVIEW"

def test_escalation_status_overdue_review():
    today = date(2026, 10, 16)
    # Review was 3 days ago, but deadline is 15 days in future
    rev = (today - timedelta(days=3)).isoformat()
    dead = (today + timedelta(days=15)).isoformat()

    status, d_rev, d_dead = get_escalation_status(rev, dead, "Deferred", as_of_date=today)
    assert status == "OVERDUE_REVIEW"

def test_escalation_status_critical_breach():
    today = date(2026, 10, 16)
    # Deadline was 2 days ago
    rev = (today - timedelta(days=10)).isoformat()
    dead = (today - timedelta(days=2)).isoformat()

    status, d_rev, d_dead = get_escalation_status(rev, dead, "Deferred", as_of_date=today)
    assert status == "CRITICAL_BREACH"
