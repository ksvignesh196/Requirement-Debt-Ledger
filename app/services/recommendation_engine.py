"""
Requirement Debt Ledger (RDL) - Explainable, Effort-Aware Recommendation Engine
Multi-criteria decision analysis (MCDM) for prioritizing requirement debt remediation
based on accumulated risk, downstream cascade unblocking, business value, urgency,
and estimated remediation effort.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import HTTPException

from app.config import (
    REC_WEIGHT_DYNAMIC_RISK,
    REC_WEIGHT_CASCADED_UNBLOCK,
    REC_WEIGHT_BUSINESS_VALUE,
    REC_WEIGHT_URGENCY,
    REC_EFFORT_ELASTICITY,
)
from app.models.recommendation import (
    RecommendationItem,
    RecommendationFactorBreakdown,
    RecommendationResponse,
    PairwiseExplanationResponse,
)
from app.services.debt_service import get_all_debts, get_debt_by_id

def compute_recommendation_item(debt, graph, all_debts_dict, rank: int = 1) -> RecommendationItem:
    """Computes effort-aware recommendation score and explainable factor breakdown for a single debt."""
    dynamic_risk = debt.risk.dynamic_risk_score
    risk_contrib = round(REC_WEIGHT_DYNAMIC_RISK * dynamic_risk, 2)

    # Cascaded unblocked risk
    blocked_ids = graph.get_downstream_blocked(debt.debt_id)
    cascaded_risk_sum = 0.0
    for b_id in blocked_ids:
        if b_id in all_debts_dict:
            cascaded_risk_sum += all_debts_dict[b_id].risk.dynamic_risk_score

    # Normalized unblock score (capped at 100)
    unblock_score = min(100.0, round((cascaded_risk_sum * 0.5) + (len(blocked_ids) * 15.0), 2))
    unblock_contrib = round(REC_WEIGHT_CASCADED_UNBLOCK * unblock_score, 2)

    # Business Value score (scale 20 to 100)
    biz_score = float(debt.business_impact * 20.0)
    biz_contrib = round(REC_WEIGHT_BUSINESS_VALUE * biz_score, 2)

    # Urgency Score
    if debt.escalation_level in ("CRITICAL_BREACH", "OVERDUE_REVIEW"):
        urgency_score = 100.0
    elif debt.escalation_level == "UPCOMING_REVIEW":
        urgency_score = 80.0
    elif debt.days_to_deadline <= 21:
        urgency_score = 50.0
    else:
        urgency_score = 25.0
    urgency_contrib = round(REC_WEIGHT_URGENCY * urgency_score, 2)

    # Gross Remediation Benefit (0-100)
    gross_benefit = round(risk_contrib + unblock_contrib + biz_contrib + urgency_contrib, 2)

    # Effort elasticity & ROI
    effort = max(1, getattr(debt, "estimated_effort", 8))
    effort_factor = round(effort ** REC_EFFORT_ELASTICITY, 2)
    # ROI: Benefit per effort elasticity unit, normalized to 0-100 scale
    remediation_roi = round((gross_benefit / effort_factor) * 5.0, 2)
    recommendation_score = min(100.0, remediation_roi)

    breakdown = RecommendationFactorBreakdown(
        accumulated_risk_score=dynamic_risk,
        accumulated_risk_contrib=risk_contrib,
        cascaded_unblock_score=unblock_score,
        cascaded_unblock_contrib=unblock_contrib,
        business_value_score=biz_score,
        business_value_contrib=biz_contrib,
        urgency_score=urgency_score,
        urgency_contrib=urgency_contrib,
        gross_remediation_benefit=gross_benefit,
        estimated_effort=effort,
        effort_elasticity_factor=effort_factor,
        remediation_roi=remediation_roi,
        recommendation_score=recommendation_score,
    )

    # Rationale generation
    headline_parts = []
    if debt.risk.risk_tier == "Critical":
        headline_parts.append("Critical risk exposure")
    if len(blocked_ids) > 0:
        headline_parts.append(f"unblocks {len(blocked_ids)} downstream dependencies")
    if effort <= 5:
        headline_parts.append(f"high efficiency quick-win ({effort} pts)")
    if debt.escalation_level in ("CRITICAL_BREACH", "OVERDUE_REVIEW"):
        headline_parts.append("deadline/review breached")

    headline = "; ".join(headline_parts) if headline_parts else "Standard scheduled remediation"

    explanation = (
        f"Remediation Score {recommendation_score:.1f}/100. Gross benefit of {gross_benefit:.1f} "
        f"comprising accumulated risk ({risk_contrib:.1f}), cascade unblocking ({unblock_contrib:.1f}), "
        f"business value ({biz_contrib:.1f}), and urgency ({urgency_contrib:.1f}). "
        f"With an estimated effort of {effort} story points (cost factor {effort_factor:.1f}), "
        f"this yields a Remediation ROI of {remediation_roi:.1f} points per effort unit."
    )

    return RecommendationItem(
        rank=rank,
        debt_id=debt.debt_id,
        title=debt.title,
        module=debt.module,
        status=debt.status,
        estimated_effort=effort,
        dynamic_risk=dynamic_risk,
        risk_tier=debt.risk.risk_tier,
        downstream_blocked_count=len(blocked_ids),
        days_to_deadline=debt.days_to_deadline,
        escalation_level=debt.escalation_level,
        factors=breakdown,
        rationale_headline=headline,
        detailed_explanation=explanation,
    )

def generate_recommendations(
    conn: sqlite3.Connection,
    target_milestone: Optional[str] = None,
    as_of_date: Optional[date] = None,
) -> RecommendationResponse:
    """
    Ranks all unaddressed requirement debts by effort-aware remediation priority.
    """
    from app.services.dependency_engine import load_graph

    debts = get_all_debts(conn, milestone=target_milestone, as_of_date=as_of_date)
    active_debts = [d for d in debts if d.status.lower() not in ("resolved", "accepted permanent")]

    graph = load_graph(conn)
    all_debts_dict = {d.debt_id: d for d in debts}

    items = [
        compute_recommendation_item(debt, graph, all_debts_dict)
        for debt in active_debts
    ]

    # Sort descending by recommendation_score
    items.sort(key=lambda x: x.factors.recommendation_score, reverse=True)

    # Re-assign ranks
    for idx, item in enumerate(items, 1):
        item.rank = idx

    weights_dict = {
        "dynamic_risk_weight": REC_WEIGHT_DYNAMIC_RISK,
        "cascaded_unblock_weight": REC_WEIGHT_CASCADED_UNBLOCK,
        "business_value_weight": REC_WEIGHT_BUSINESS_VALUE,
        "urgency_weight": REC_WEIGHT_URGENCY,
        "effort_elasticity_factor": REC_EFFORT_ELASTICITY,
    }

    methodology = (
        "Recommendations use an effort-aware Multi-Criteria Decision Model (MCDM). "
        "Gross remediation benefit combines dynamic accumulated risk (35%), downstream dependency unblocking (30%), "
        "business value impact (20%), and schedule urgency (15%). This benefit is divided by sub-linear estimated effort "
        "(effort^0.70) to yield an explainable, defensible Remediation ROI."
    )

    return RecommendationResponse(
        total_evaluated_debts=len(items),
        weights_applied=weights_dict,
        recommendations=items,
        methodology_statement=methodology,
    )

def explain_pairwise_recommendation(
    conn: sqlite3.Connection,
    debt_id_a: str,
    debt_id_b: str,
    as_of_date: Optional[date] = None,
) -> PairwiseExplanationResponse:
    """
    Generates a contrastive, natural-language explanation of why requirement A is ranked above or below requirement B.
    """
    from app.services.dependency_engine import load_graph

    if debt_id_a == debt_id_b:
        raise HTTPException(status_code=400, detail="Cannot compare a requirement debt to itself. Please provide two different requirement debts.")

    debts = get_all_debts(conn, as_of_date=as_of_date)
    all_debts_dict = {d.debt_id: d for d in debts}

    if debt_id_a not in all_debts_dict:
        raise HTTPException(status_code=404, detail=f"Requirement debt '{debt_id_a}' not found.")
    if debt_id_b not in all_debts_dict:
        raise HTTPException(status_code=404, detail=f"Requirement debt '{debt_id_b}' not found.")

    graph = load_graph(conn)
    rec_a = compute_recommendation_item(all_debts_dict[debt_id_a], graph, all_debts_dict)
    rec_b = compute_recommendation_item(all_debts_dict[debt_id_b], graph, all_debts_dict)

    if rec_a.factors.recommendation_score >= rec_b.factors.recommendation_score:
        higher, lower = rec_a, rec_b
    else:
        higher, lower = rec_b, rec_a

    score_delta = round(higher.factors.recommendation_score - lower.factors.recommendation_score, 2)

    # Narrative explanation of decisive factors
    reasons = []
    if higher.dynamic_risk > lower.dynamic_risk:
        reasons.append(f"higher dynamic risk ({higher.dynamic_risk} vs {lower.dynamic_risk})")
    elif higher.dynamic_risk < lower.dynamic_risk:
        reasons.append(f"despite lower standalone risk ({higher.dynamic_risk} vs {lower.dynamic_risk})")

    if higher.downstream_blocked_count > lower.downstream_blocked_count:
        reasons.append(f"unblocks {higher.downstream_blocked_count} downstream dependencies (vs {lower.downstream_blocked_count})")

    if higher.estimated_effort < lower.estimated_effort:
        reasons.append(f"requires significantly lower effort ({higher.estimated_effort} vs {lower.estimated_effort} pts)")
    elif higher.estimated_effort > lower.estimated_effort:
        reasons.append(f"even with higher effort ({higher.estimated_effort} vs {lower.estimated_effort} pts), its risk reduction payoff dominates")

    narrative = (
        f"{higher.debt_id} ('{higher.title}') is prioritized above {lower.debt_id} ('{lower.title}') "
        f"by +{score_delta} score points because of {', and '.join(reasons)}. "
        f"This produces a superior Remediation ROI ({higher.factors.remediation_roi} vs {lower.factors.remediation_roi})."
    )

    comparison_matrix = {
        higher.debt_id: {
            "title": higher.title,
            "recommendation_score": higher.factors.recommendation_score,
            "remediation_roi": higher.factors.remediation_roi,
            "dynamic_risk": higher.dynamic_risk,
            "blocked_dependencies": higher.downstream_blocked_count,
            "effort_points": higher.estimated_effort,
            "urgency_score": higher.factors.urgency_score,
        },
        lower.debt_id: {
            "title": lower.title,
            "recommendation_score": lower.factors.recommendation_score,
            "remediation_roi": lower.factors.remediation_roi,
            "dynamic_risk": lower.dynamic_risk,
            "blocked_dependencies": lower.downstream_blocked_count,
            "effort_points": lower.estimated_effort,
            "urgency_score": lower.factors.urgency_score,
        },
    }

    return PairwiseExplanationResponse(
        higher_ranked_id=higher.debt_id,
        lower_ranked_id=lower.debt_id,
        score_delta=score_delta,
        contrastive_narrative=narrative,
        comparison_matrix=comparison_matrix,
    )
