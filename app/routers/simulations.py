"""
Requirement Debt Ledger (RDL) - Simulations Router
Endpoints for Dependency Impact Simulation, What-If Release Planning, and Risk Forecasting.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.simulation import (
    DependencySimulationRequest,
    DependencySimulationResponse,
    WhatIfReleasePlanRequest,
    WhatIfReleasePlanResponse,
    RiskForecastRequest,
    RiskForecastResponse,
)
from app.services.dependency_engine import simulate_dependency_impact
from app.services.simulation_engine import (
    run_what_if_release_planning,
    apply_what_if_plan,
    run_risk_forecasting,
)

router = APIRouter(prefix="/api/simulations", tags=["Simulations & Forecasting"])

class ApplyPlanPayload(BaseModel):
    target_milestone: str = Field(..., min_length=2)
    resolved_debt_ids: List[str] = Field(..., min_length=1)
    actor_name: str = Field(default="Release Engineer", min_length=2)
    rationale: str = Field(default="Approved simulated what-if release plan", min_length=5)

@router.post("/dependency-impact", response_model=DependencySimulationResponse)
def simulate_debt_dependency_impact(
    data: DependencySimulationRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Simulates the cascading blast-radius of postponing a requirement debt by additional days.
    Identifies direct and indirect affected requirements without double-counting.
    """
    return simulate_dependency_impact(
        conn=conn,
        debt_id=data.debt_id,
        additional_delay_days=data.additional_delay_days,
    )

@router.post("/what-if-release", response_model=WhatIfReleasePlanResponse)
def evaluate_what_if_release_plans(
    data: WhatIfReleasePlanRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Simulates and compares alternative requirement resolution plans for a release milestone.
    Simulations are strictly isolated in-memory and do not alter persistent records.
    """
    return run_what_if_release_planning(conn=conn, request=data)

@router.post("/apply-plan")
def apply_simulated_plan_to_actual(
    data: ApplyPlanPayload,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Explicitly applies an approved what-if release plan to the live requirement ledger records.
    """
    return apply_what_if_plan(
        conn=conn,
        target_milestone=data.target_milestone,
        resolved_debt_ids=data.resolved_debt_ids,
        actor_name=data.actor_name,
        rationale=data.rationale,
    )

@router.post("/risk-forecast", response_model=RiskForecastResponse)
def forecast_risk_trajectory(
    data: RiskForecastRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Forecasts deterministic future requirement debt risk trajectories under multiple scenarios.
    """
    return run_risk_forecasting(conn=conn, request=data)
