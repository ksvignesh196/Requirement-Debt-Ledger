"""
Pydantic schemas for Explainable, Effort-Aware Resolution Recommendations
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RecommendationFactorBreakdown(BaseModel):
    accumulated_risk_score: float
    accumulated_risk_contrib: float
    cascaded_unblock_score: float
    cascaded_unblock_contrib: float
    business_value_score: float
    business_value_contrib: float
    urgency_score: float
    urgency_contrib: float
    gross_remediation_benefit: float
    estimated_effort: int
    effort_elasticity_factor: float
    remediation_roi: float
    recommendation_score: float

class RecommendationItem(BaseModel):
    rank: int
    debt_id: str
    title: str
    module: str
    status: str
    estimated_effort: int
    dynamic_risk: float
    risk_tier: str
    downstream_blocked_count: int
    days_to_deadline: int
    escalation_level: str
    factors: RecommendationFactorBreakdown
    rationale_headline: str
    detailed_explanation: str

class RecommendationResponse(BaseModel):
    total_evaluated_debts: int
    weights_applied: Dict[str, float]
    recommendations: List[RecommendationItem]
    methodology_statement: str

class PairwiseExplanationRequest(BaseModel):
    debt_id_a: str = Field(..., min_length=3)
    debt_id_b: str = Field(..., min_length=3)

class PairwiseExplanationResponse(BaseModel):
    higher_ranked_id: str
    lower_ranked_id: str
    score_delta: float
    contrastive_narrative: str
    comparison_matrix: Dict[str, Any]
