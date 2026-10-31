"""
Requirement Debt Ledger (RDL) - Recommendations Router
Endpoints for Effort-Aware Remediation Prioritization and Pairwise Contrastive Explanations.
"""
import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.models.recommendation import (
    RecommendationResponse,
    PairwiseExplanationRequest,
    PairwiseExplanationResponse,
)
from app.services.recommendation_engine import (
    generate_recommendations,
    explain_pairwise_recommendation,
)

router = APIRouter(prefix="/api/recommendations", tags=["Remediation Recommendations"])

@router.get("", response_model=RecommendationResponse)
def get_remediation_recommendations(
    milestone: Optional[str] = Query(default=None, description="Optional target milestone filter"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Ranks unaddressed requirement debts by effort-aware remediation priority,
    considering dynamic risk, cascade unblocking, business value, urgency, and estimated effort.
    """
    return generate_recommendations(conn=conn, target_milestone=milestone)

@router.post("/pairwise-explain", response_model=PairwiseExplanationResponse)
def explain_pairwise_priority(
    data: PairwiseExplanationRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Provides an explainable, contrastive rationale of why requirement debt A is ranked above or below requirement debt B.
    """
    return explain_pairwise_recommendation(
        conn=conn,
        debt_id_a=data.debt_id_a,
        debt_id_b=data.debt_id_b,
    )
