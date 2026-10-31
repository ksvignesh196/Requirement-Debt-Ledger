"""
Requirement Debt Ledger (RDL) - Mathematical Explainable Risk Engine
Calculates base risk, dynamic time-decay/interest accrual, overdue penalties,
multi-rate sensitivity analysis, and future risk projections.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, Tuple, List, Optional
from app.config import (
    DEFAULT_WEIGHT_BUSINESS,
    DEFAULT_WEIGHT_ARCHITECTURE,
    DEFAULT_WEIGHT_SAFETY,
    DEFAULT_GRACE_PERIOD_DAYS,
    DEFAULT_DAILY_INTEREST_RATE,
    OVERDUE_PENALTY_RATE_PER_MONTH,
    MAX_OVERDUE_PENALTY_MULTIPLIER,
)
from app.models.debt_item import RiskBreakdown

def parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD string to date object with strict validation."""
    if isinstance(date_str, date):
        return date_str
    if not isinstance(date_str, str) or len(date_str) < 10:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")
    return datetime.strptime(date_str[:10], "%Y-%m-%d").date()

def calculate_base_risk(
    business_impact: int,
    arch_impact: int,
    safety_impact: int,
    occurrence_prob: int,
    detection_difficulty: int,
    w_b: float = DEFAULT_WEIGHT_BUSINESS,
    w_a: float = DEFAULT_WEIGHT_ARCHITECTURE,
    w_s: float = DEFAULT_WEIGHT_SAFETY,
) -> Tuple[float, float]:
    """
    Computes normalized base severity and unescalated base risk score (0-100).
    I = w_b * S_b + w_a * S_a + w_s * S_s (scale 1 to 5)
    Base Risk = (I * Occurrence * Detection / 125) * 100
    """
    # Enforce 1-5 boundary conditions
    b_imp = max(1, min(5, business_impact))
    a_imp = max(1, min(5, arch_impact))
    s_imp = max(1, min(5, safety_impact))
    occ = max(1, min(5, occurrence_prob))
    det = max(1, min(5, detection_difficulty))

    severity = (w_b * b_imp) + (w_a * a_imp) + (w_s * s_imp)
    # Max possible value is 5 * 5 * 5 = 125
    base_score = ((severity * occ * det) / 125.0) * 100.0
    return round(severity, 2), round(base_score, 2)

def calculate_overdue_penalty(
    overdue_days: int,
    rate_per_month: float = OVERDUE_PENALTY_RATE_PER_MONTH,
    max_multiplier: float = MAX_OVERDUE_PENALTY_MULTIPLIER,
) -> float:
    """
    Calculates overdue schedule breach penalty multiplier.
    - If overdue_days <= 0: multiplier = 1.0 (no penalty)
    - Penalty increases by rate_per_month (default +25%) per 30-day overdue epoch
      (e.g., at 30 days overdue -> 1.25x).
    - Asymptotically capped at max_multiplier (default 2.0x, i.e. +100% maximum surcharge).
    """
    if overdue_days <= 0:
        return 1.0
    max_additional = max(0.0, max_multiplier - 1.0)
    additional_surcharge = min(max_additional, (overdue_days / 30.0) * rate_per_month)
    return round(1.0 + additional_surcharge, 4)

def evaluate_debt_risk(
    business_impact: int,
    arch_impact: int,
    safety_impact: int,
    occurrence_prob: int,
    detection_difficulty: int,
    created_date_str: str,
    review_date_str: str,
    as_of_date: Optional[date] = None,
    grace_period_days: int = DEFAULT_GRACE_PERIOD_DAYS,
    daily_interest_rate: float = DEFAULT_DAILY_INTEREST_RATE,
    max_overdue_multiplier: float = MAX_OVERDUE_PENALTY_MULTIPLIER,
) -> RiskBreakdown:
    """
    Full dynamic risk evaluation including time-dependent debt interest and deadline escalation.
    """
    current_date = as_of_date or date.today()
    created_date = parse_date(created_date_str)
    review_date = parse_date(review_date_str)

    # 1. Base Risk Calculation
    severity, base_risk = calculate_base_risk(
        business_impact, arch_impact, safety_impact, occurrence_prob, detection_difficulty
    )

    # 2. Time Elapsed & Debt Interest Accumulation
    elapsed_days = max(0, (current_date - created_date).days)
    days_past_grace = max(0, elapsed_days - grace_period_days)

    # Compound interest: (1 + r)^t
    interest_factor = round((1.0 + daily_interest_rate) ** days_past_grace, 4)
    accrued_interest_percent = round((interest_factor - 1.0) * 100.0, 2)

    # 3. Deadline / Overdue Penalty
    overdue_days = max(0, (current_date - review_date).days)
    is_overdue = (current_date > review_date)
    overdue_penalty = calculate_overdue_penalty(
        overdue_days=overdue_days if is_overdue else 0,
        rate_per_month=OVERDUE_PENALTY_RATE_PER_MONTH,
        max_multiplier=max_overdue_multiplier,
    )

    # 4. Final Dynamic Risk Score
    dynamic_risk = base_risk * interest_factor * overdue_penalty
    dynamic_risk = min(100.0, round(dynamic_risk, 2))

    # 5. Risk Tier
    if dynamic_risk < 35.0:
        tier = "Low"
    elif dynamic_risk < 65.0:
        tier = "Moderate"
    elif dynamic_risk < 85.0:
        tier = "High"
    else:
        tier = "Critical"

    # 6. Human-readable explainable rationale
    explanation_parts = [
        f"Base risk score of {base_risk:.1f}/100 derived from composite severity {severity:.2f}/5, occurrence {occurrence_prob}/5, and detection difficulty {detection_difficulty}/5."
    ]
    if days_past_grace > 0:
        explanation_parts.append(
            f"Debt aged {elapsed_days} days ({days_past_grace} days beyond {grace_period_days}-day grace period), accruing {accrued_interest_percent:.1f}% debt interest (daily rate {daily_interest_rate * 100:.1f}%)."
        )
    else:
        explanation_parts.append(
            f"Debt is within the {grace_period_days}-day grace period ({elapsed_days} days elapsed); no compounding interest applied yet."
        )

    if is_overdue:
        explanation_parts.append(
            f"REVIEW OVERDUE by {overdue_days} days past review date ({review_date_str}), triggering a x{overdue_penalty:.2f} overdue penalty (capped at x{max_overdue_multiplier:.1f})."
        )
    else:
        explanation_parts.append(f"Review target ({review_date_str}) is currently on schedule.")

    explanation_parts.append(f"Dynamic effective risk is {dynamic_risk:.1f} ({tier}).")

    explanation = " ".join(explanation_parts)

    return RiskBreakdown(
        base_severity=severity,
        base_occurrence=occurrence_prob,
        base_detection=detection_difficulty,
        base_risk_score=base_risk,
        elapsed_days=elapsed_days,
        grace_period_days=grace_period_days,
        days_past_grace=days_past_grace,
        interest_rate_daily=daily_interest_rate,
        interest_factor=interest_factor,
        accrued_interest_percent=accrued_interest_percent,
        is_overdue=is_overdue,
        overdue_days=overdue_days,
        overdue_penalty_factor=overdue_penalty,
        dynamic_risk_score=dynamic_risk,
        risk_tier=tier,
        explanation=explanation,
    )

def evaluate_risk_sensitivity(
    business_impact: int,
    arch_impact: int,
    safety_impact: int,
    occurrence_prob: int,
    detection_difficulty: int,
    created_date_str: str,
    review_date_str: str,
    as_of_date: Optional[date] = None,
    rates: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Validates the 0.8% daily interest assumption against alternative values (e.g., 0.4% conservative, 0.8% standard, 1.2% aggressive).
    """
    test_rates = rates or [0.004, 0.008, 0.012]
    labels = {0.004: "Conservative (0.4%/day)", 0.008: "Baseline Standard (0.8%/day)", 0.012: "Aggressive (1.2%/day)"}

    results = []
    for r in test_rates:
        eval_res = evaluate_debt_risk(
            business_impact=business_impact,
            arch_impact=arch_impact,
            safety_impact=safety_impact,
            occurrence_prob=occurrence_prob,
            detection_difficulty=detection_difficulty,
            created_date_str=created_date_str,
            review_date_str=review_date_str,
            as_of_date=as_of_date,
            daily_interest_rate=r,
        )
        results.append({
            "daily_rate": r,
            "label": labels.get(r, f"Custom ({r * 100:.2f}%/day)"),
            "dynamic_risk_score": eval_res.dynamic_risk_score,
            "risk_tier": eval_res.risk_tier,
            "interest_factor": eval_res.interest_factor,
            "accrued_interest_percent": eval_res.accrued_interest_percent,
        })

    return {
        "created_date": created_date_str,
        "review_date": review_date_str,
        "sensitivity_results": results,
        "methodology_note": "Sensitivity analysis allows teams to verify portfolio risk resilience under varying decay hypotheses."
    }

def forecast_debt_risk(
    business_impact: int,
    arch_impact: int,
    safety_impact: int,
    occurrence_prob: int,
    detection_difficulty: int,
    created_date_str: str,
    review_date_str: str,
    horizons_days: Optional[List[int]] = None,
    scenario: str = "status_quo",
    daily_interest_rate: float = DEFAULT_DAILY_INTEREST_RATE,
    as_of_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Forecasts requirement debt risk trajectory across multiple future time horizons.
    Scenarios:
    - 'status_quo': No review conducted, overdue penalties compound past review_date.
    - 'timely_review': Reviews are assumed conducted on time, avoiding overdue penalties.
    """
    horizons = horizons_days or [0, 15, 30, 60, 90, 180]
    base_current_date = as_of_date or date.today()

    points = []
    for offset in horizons:
        future_date = base_current_date + timedelta(days=offset)

        if scenario == "timely_review":
            # Target review date is shifted so it is never overdue
            effective_review_str = (future_date + timedelta(days=14)).isoformat()
        else:
            effective_review_str = review_date_str

        risk_eval = evaluate_debt_risk(
            business_impact=business_impact,
            arch_impact=arch_impact,
            safety_impact=safety_impact,
            occurrence_prob=occurrence_prob,
            detection_difficulty=detection_difficulty,
            created_date_str=created_date_str,
            review_date_str=effective_review_str,
            as_of_date=future_date,
            daily_interest_rate=daily_interest_rate,
        )

        points.append({
            "horizon_days": offset,
            "projected_date": future_date.isoformat(),
            "dynamic_risk_score": risk_eval.dynamic_risk_score,
            "risk_tier": risk_eval.risk_tier,
            "interest_factor": risk_eval.interest_factor,
            "overdue_penalty_factor": risk_eval.overdue_penalty_factor,
            "is_overdue": risk_eval.is_overdue,
        })

    return points
