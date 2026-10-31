"""
Requirement Debt Ledger (RDL) - Analytics & Dashboard Router
Computes high-level aggregated portfolio metrics, distributions, and executive KPIs.
"""
import sqlite3
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from collections import Counter

from app.database import get_db
from app.services.debt_service import get_all_debts

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Dashboard"])

@router.get("/dashboard")
def get_dashboard_metrics(conn: sqlite3.Connection = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve all metrics and distributions needed for the executive overview."""
    debts = get_all_debts(conn)

    total_count = len(debts)
    active_debts = [d for d in debts if d.status.lower() not in ("resolved", "accepted permanent")]
    resolved_count = total_count - len(active_debts)

    critical_count = sum(1 for d in active_debts if d.risk.risk_tier == "Critical")
    high_count = sum(1 for d in active_debts if d.risk.risk_tier == "High")
    overdue_count = sum(1 for d in active_debts if d.escalation_level in ("OVERDUE_REVIEW", "CRITICAL_BREACH"))
    upcoming_review_count = sum(1 for d in active_debts if d.escalation_level == "UPCOMING_REVIEW")

    total_risk = round(sum(d.risk.dynamic_risk_score for d in active_debts), 2)
    avg_risk = round(total_risk / len(active_debts), 2) if active_debts else 0.0

    # Risk tier distribution
    tier_counts = Counter(d.risk.risk_tier for d in active_debts)
    risk_distribution = {
        "Critical": tier_counts.get("Critical", 0),
        "High": tier_counts.get("High", 0),
        "Moderate": tier_counts.get("Moderate", 0),
        "Low": tier_counts.get("Low", 0),
    }

    # Deferral reasons distribution
    reason_counts = Counter(d.deferral_reason for d in debts)
    reason_distribution = dict(reason_counts.most_common(10))

    # Module distribution
    module_counts = Counter(d.module for d in active_debts)
    module_distribution = dict(module_counts.most_common(10))

    # Milestone distribution
    milestone_counts = Counter(d.target_milestone for d in active_debts)
    milestone_distribution = dict(milestone_counts.most_common(10))

    # Escalation level breakdown
    escalation_counts = Counter(d.escalation_level for d in active_debts)
    escalation_distribution = {
        "OK": escalation_counts.get("OK", 0),
        "UPCOMING_REVIEW": escalation_counts.get("UPCOMING_REVIEW", 0),
        "OVERDUE_REVIEW": escalation_counts.get("OVERDUE_REVIEW", 0),
        "CRITICAL_BREACH": escalation_counts.get("CRITICAL_BREACH", 0),
    }

    # Top 5 urgent debts by Priority Index
    sorted_active = sorted(active_debts, key=lambda x: x.debt_priority_index, reverse=True)
    top_urgent = [
        {
            "debt_id": d.debt_id,
            "title": d.title,
            "module": d.module,
            "risk_score": d.risk.dynamic_risk_score,
            "risk_tier": d.risk.risk_tier,
            "debt_priority_index": d.debt_priority_index,
            "escalation_level": d.escalation_level,
            "downstream_blocked_count": d.dependency_impact.downstream_blocked_count,
        }
        for d in sorted_active[:5]
    ]

    return {
        "total_debts": total_count,
        "active_debts": len(active_debts),
        "resolved_debts": resolved_count,
        "critical_debts": critical_count,
        "high_debts": high_count,
        "overdue_debts": overdue_count,
        "upcoming_review_debts": upcoming_review_count,
        "total_dynamic_risk": total_risk,
        "average_dynamic_risk": avg_risk,
        "risk_distribution": risk_distribution,
        "reason_distribution": reason_distribution,
        "module_distribution": module_distribution,
        "milestone_distribution": milestone_distribution,
        "escalation_distribution": escalation_distribution,
        "top_urgent_debts": top_urgent,
    }
