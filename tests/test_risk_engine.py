"""
Unit tests for Mathematical Explainable Risk Engine
"""
from datetime import date, timedelta
from app.services.risk_engine import (
    calculate_base_risk,
    evaluate_debt_risk,
)

def test_calculate_base_risk_minimum_and_maximum():
    # Minimum values: all 1s
    sev_min, base_min = calculate_base_risk(1, 1, 1, 1, 1)
    assert sev_min == 1.0
    # (1 * 1 * 1 / 125) * 100 = 0.8
    assert base_min == 0.8

    # Maximum values: all 5s
    sev_max, base_max = calculate_base_risk(5, 5, 5, 5, 5)
    assert sev_max == 5.0
    # (5 * 5 * 5 / 125) * 100 = 100.0
    assert base_max == 100.0

def test_evaluate_debt_risk_within_grace_period():
    today = date(2026, 10, 16)
    # Created 5 days ago (grace period is 14 days)
    created = (today - timedelta(days=5)).isoformat()
    review = (today + timedelta(days=20)).isoformat()

    risk = evaluate_debt_risk(
        business_impact=3,
        arch_impact=3,
        safety_impact=3,
        occurrence_prob=3,
        detection_difficulty=3,
        created_date_str=created,
        review_date_str=review,
        as_of_date=today,
    )

    assert risk.elapsed_days == 5
    assert risk.days_past_grace == 0
    assert risk.interest_factor == 1.0
    assert risk.accrued_interest_percent == 0.0
    assert not risk.is_overdue
    assert risk.overdue_penalty_factor == 1.0
    # Dynamic risk should equal base risk
    assert risk.dynamic_risk_score == risk.base_risk_score
    assert "within the 14-day grace period" in risk.explanation

def test_evaluate_debt_risk_past_grace_period_interest_compounding():
    today = date(2026, 10, 16)
    # Created 34 days ago (20 days past 14-day grace)
    created = (today - timedelta(days=34)).isoformat()
    review = (today + timedelta(days=10)).isoformat()

    risk = evaluate_debt_risk(
        business_impact=4,
        arch_impact=4,
        safety_impact=4,
        occurrence_prob=4,
        detection_difficulty=3,
        created_date_str=created,
        review_date_str=review,
        as_of_date=today,
    )

    assert risk.elapsed_days == 34
    assert risk.days_past_grace == 20
    # Interest: (1.008)^20 = ~1.1728
    assert risk.interest_factor > 1.15
    assert risk.accrued_interest_percent > 15.0
    assert risk.dynamic_risk_score > risk.base_risk_score
    assert "accruing" in risk.explanation

def test_evaluate_debt_risk_overdue_penalty():
    today = date(2026, 10, 16)
    created = (today - timedelta(days=30)).isoformat()
    # Review date was 15 days ago
    review = (today - timedelta(days=15)).isoformat()

    risk = evaluate_debt_risk(
        business_impact=4,
        arch_impact=4,
        safety_impact=4,
        occurrence_prob=4,
        detection_difficulty=3,
        created_date_str=created,
        review_date_str=review,
        as_of_date=today,
    )

    assert risk.is_overdue is True
    assert risk.overdue_days == 15
    # Overdue penalty: 1.0 + (15/30)*0.25 = 1.125
    assert risk.overdue_penalty_factor > 1.10
    assert "REVIEW OVERDUE by 15 days" in risk.explanation
    assert risk.dynamic_risk_score > (risk.base_risk_score * risk.interest_factor)

def test_evaluate_debt_risk_capped_at_100():
    today = date(2026, 10, 16)
    # Severe max impact, created 100 days ago, 60 days overdue
    created = (today - timedelta(days=100)).isoformat()
    review = (today - timedelta(days=60)).isoformat()

    risk = evaluate_debt_risk(
        business_impact=5,
        arch_impact=5,
        safety_impact=5,
        occurrence_prob=5,
        detection_difficulty=5,
        created_date_str=created,
        review_date_str=review,
        as_of_date=today,
    )

    assert risk.dynamic_risk_score == 100.0
    assert risk.risk_tier == "Critical"
