"""
Pydantic schemas for Requirement Debt Items and Explainable Risk Breakdown
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import date
from pydantic import BaseModel, Field, field_validator
import re

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def validate_iso_date(v: str) -> str:
    if not isinstance(v, str) or not DATE_REGEX.fullmatch(v):
        raise ValueError("Date must use the YYYY-MM-DD format.")
    try:
        date.fromisoformat(v)
    except ValueError as exc:
        raise ValueError("Date must be a valid calendar date.") from exc
    return v

class RiskBreakdown(BaseModel):
    base_severity: float
    base_occurrence: int
    base_detection: int
    base_risk_score: float
    elapsed_days: int
    grace_period_days: int
    days_past_grace: int
    interest_rate_daily: float
    interest_factor: float
    accrued_interest_percent: float
    is_overdue: bool
    overdue_days: int
    overdue_penalty_factor: float
    dynamic_risk_score: float
    risk_tier: str  # 'Low', 'Moderate', 'High', 'Critical'
    explanation: str

class DependencyImpact(BaseModel):
    direct_dependencies_count: int
    downstream_blocked_count: int
    critical_path_depth: int
    is_in_cycle: bool

class DebtItemBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    module: str = Field(..., min_length=2, max_length=100)
    requirement_type: str = Field(default="Functional")
    deferral_reason: str = Field(..., min_length=3)
    deferral_phase: str = Field(default="Development")
    decision_maker: str = Field(..., min_length=2)
    owner: str = Field(..., min_length=2)
    target_milestone: str = Field(..., min_length=1)
    resolution_criteria: str = Field(..., min_length=5)
    created_date: str = Field(..., description="YYYY-MM-DD")
    review_date: str = Field(..., description="YYYY-MM-DD")
    deadline_date: str = Field(..., description="YYYY-MM-DD")
    business_impact: int = Field(default=3, ge=1, le=5)
    arch_impact: int = Field(default=3, ge=1, le=5)
    safety_impact: int = Field(default=3, ge=1, le=5)
    occurrence_prob: int = Field(default=3, ge=1, le=5)
    detection_difficulty: int = Field(default=3, ge=1, le=5)
    cost_of_delay: int = Field(default=3, ge=1, le=5)
    estimated_effort: int = Field(default=8, ge=1, le=100, description="Estimated story points or person-days (1-100)")

    @field_validator("created_date", "review_date", "deadline_date")
    @classmethod
    def check_dates(cls, v: str) -> str:
        return validate_iso_date(v)

class DebtItemCreate(DebtItemBase):
    debt_id: Optional[str] = None

    @field_validator("debt_id")
    @classmethod
    def check_debt_id(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,39}", value):
            raise ValueError("Debt ID may contain only letters, numbers, hyphens, and underscores (2-40 characters).")
        return value

class DebtItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=5)
    module: Optional[str] = Field(default=None, min_length=2, max_length=100)
    requirement_type: Optional[str] = None
    deferral_reason: Optional[str] = Field(default=None, min_length=3)
    deferral_phase: Optional[str] = None
    decision_maker: Optional[str] = Field(default=None, min_length=2)
    owner: Optional[str] = Field(default=None, min_length=2)
    target_milestone: Optional[str] = Field(default=None, min_length=1)
    resolution_criteria: Optional[str] = Field(default=None, min_length=5)
    status: Optional[Literal["Deferred", "Under Review", "Remediating"]] = None
    review_date: Optional[str] = None
    deadline_date: Optional[str] = None
    business_impact: Optional[int] = Field(default=None, ge=1, le=5)
    arch_impact: Optional[int] = Field(default=None, ge=1, le=5)
    safety_impact: Optional[int] = Field(default=None, ge=1, le=5)
    occurrence_prob: Optional[int] = Field(default=None, ge=1, le=5)
    detection_difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    cost_of_delay: Optional[int] = Field(default=None, ge=1, le=5)
    estimated_effort: Optional[int] = Field(default=None, ge=1, le=100)
    updated_by: Optional[str] = "System User"
    rationale: Optional[str] = None

    @field_validator("review_date", "deadline_date")
    @classmethod
    def check_optional_dates(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_iso_date(v)
        return v

class DebtItemResolve(BaseModel):
    resolution_type: str = Field(..., description="e.g. Implemented & Verified, Absorbed into Redesign, Transferred to Technical Debt, Risk Formally Accepted")
    resolution_notes: str = Field(..., min_length=5)
    resolved_by: str = Field(default="Tech Lead")
    resolved_date: Optional[str] = None

    @field_validator("resolved_date")
    @classmethod
    def check_resolved_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_iso_date(v)
        return v

class DebtItemResponse(DebtItemBase):
    id: int
    debt_id: str
    status: str
    resolution_notes: Optional[str] = None
    resolved_date: Optional[str] = None
    resolution_type: Optional[str] = None
    updated_at: str
    risk: RiskBreakdown
    dependency_impact: DependencyImpact
    debt_priority_index: float
    escalation_level: str  # 'OK', 'UPCOMING_REVIEW', 'OVERDUE_REVIEW', 'CRITICAL_BREACH'
    days_to_review: int
    days_to_deadline: int
