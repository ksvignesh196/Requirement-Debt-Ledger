"""
Requirement Debt Ledger (RDL) - Debts Router
REST endpoints for debt management, retrieval, risk calculation, sensitivity, and lifecycle actions.
"""
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.database import get_db
from app.models.debt_item import (
    DebtItemCreate,
    DebtItemUpdate,
    DebtItemResolve,
    DebtItemResponse,
    RiskBreakdown,
)
from app.services.debt_service import (
    get_all_debts,
    get_debt_by_id,
    create_debt,
    update_debt,
    resolve_debt,
    delete_debt,
)
from app.services.risk_engine import evaluate_debt_risk, evaluate_risk_sensitivity

router = APIRouter(prefix="/api/debts", tags=["Requirement Debts"])

class RiskSimulationRequest(BaseModel):
    business_impact: int = Field(default=3, ge=1, le=5)
    arch_impact: int = Field(default=3, ge=1, le=5)
    safety_impact: int = Field(default=3, ge=1, le=5)
    occurrence_prob: int = Field(default=3, ge=1, le=5)
    detection_difficulty: int = Field(default=3, ge=1, le=5)
    created_date: str = Field(..., description="YYYY-MM-DD")
    review_date: str = Field(..., description="YYYY-MM-DD")
    grace_period_days: Optional[int] = Field(default=14, ge=0, le=365)
    daily_interest_rate: Optional[float] = Field(default=0.008, ge=0.001, le=0.05)

    @field_validator("created_date", "review_date")
    @classmethod
    def validate_dates(cls, value: str) -> str:
        try:
            parsed = date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Date must be a valid YYYY-MM-DD calendar date.") from exc
        if parsed.isoformat() != value:
            raise ValueError("Date must use the YYYY-MM-DD format.")
        return value

class RiskSensitivityRequest(BaseModel):
    business_impact: int = Field(default=3, ge=1, le=5)
    arch_impact: int = Field(default=3, ge=1, le=5)
    safety_impact: int = Field(default=3, ge=1, le=5)
    occurrence_prob: int = Field(default=3, ge=1, le=5)
    detection_difficulty: int = Field(default=3, ge=1, le=5)
    created_date: str = Field(..., description="YYYY-MM-DD")
    review_date: str = Field(..., description="YYYY-MM-DD")
    rates: Optional[List[float]] = None

    @field_validator("created_date", "review_date")
    @classmethod
    def validate_dates(cls, value: str) -> str:
        try:
            parsed = date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Date must be a valid YYYY-MM-DD calendar date.") from exc
        if parsed.isoformat() != value:
            raise ValueError("Date must use the YYYY-MM-DD format.")
        return value

    @field_validator("rates")
    @classmethod
    def validate_rates(cls, values: Optional[List[float]]) -> Optional[List[float]]:
        if values is not None and any(rate < 0.001 or rate > 0.05 for rate in values):
            raise ValueError("Interest rates must be between 0.001 and 0.05.")
        return values

@router.get("", response_model=List[DebtItemResponse])
def list_debts(
    module: Optional[str] = None,
    status: Optional[str] = None,
    risk_tier: Optional[str] = None,
    escalation_level: Optional[str] = None,
    milestone: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="debt_priority_index"),
    sort_order: str = Query(default="desc"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Retrieve all requirement debts with dynamic calculated metrics."""
    return get_all_debts(
        conn=conn,
        module=module,
        status=status,
        risk_tier=risk_tier,
        escalation_level=escalation_level,
        milestone=milestone,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

@router.post("", response_model=DebtItemResponse, status_code=201)
def create_debt_item(
    data: DebtItemCreate,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Create a new requirement debt record."""
    return create_debt(conn, data)

@router.get("/{debt_id}", response_model=DebtItemResponse)
def get_debt_item(
    debt_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Retrieve full details of a requirement debt including explainable risk breakdown."""
    return get_debt_by_id(conn, debt_id)

@router.patch("/{debt_id}", response_model=DebtItemResponse)
def update_debt_item(
    debt_id: str,
    data: DebtItemUpdate,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Update fields on a requirement debt record."""
    return update_debt(conn, debt_id, data)

@router.post("/{debt_id}/resolve", response_model=DebtItemResponse)
def resolve_debt_item(
    debt_id: str,
    data: DebtItemResolve,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Formally resolve a requirement debt with evidence and justification."""
    return resolve_debt(conn, debt_id, data)

@router.delete("/{debt_id}")
def delete_debt_item(
    debt_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Delete a requirement debt record and its associations."""
    return delete_debt(conn, debt_id)

@router.post("/simulate/risk", response_model=RiskBreakdown)
def simulate_risk(data: RiskSimulationRequest):
    """Simulate risk and debt interest calculations interactively."""
    return evaluate_debt_risk(
        business_impact=data.business_impact,
        arch_impact=data.arch_impact,
        safety_impact=data.safety_impact,
        occurrence_prob=data.occurrence_prob,
        detection_difficulty=data.detection_difficulty,
        created_date_str=data.created_date,
        review_date_str=data.review_date,
        grace_period_days=data.grace_period_days or 14,
        daily_interest_rate=data.daily_interest_rate or 0.008,
    )

@router.post("/simulate/sensitivity")
def simulate_sensitivity(data: RiskSensitivityRequest) -> Dict[str, Any]:
    """Test risk calculation sensitivity across conservative (0.4%), standard (0.8%), and aggressive (1.2%) rates."""
    return evaluate_risk_sensitivity(
        business_impact=data.business_impact,
        arch_impact=data.arch_impact,
        safety_impact=data.safety_impact,
        occurrence_prob=data.occurrence_prob,
        detection_difficulty=data.detection_difficulty,
        created_date_str=data.created_date,
        review_date_str=data.review_date,
        rates=data.rates,
    )
