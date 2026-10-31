"""
Pydantic schemas for Dependency Impact Simulator, What-If Release Planning, and Risk Forecasting
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

class AffectedRequirementDetail(BaseModel):
    debt_id: str
    title: str
    module: str
    distance: int
    dependency_relationship: str
    current_risk: float
    risk_tier: str
    status: str

class DependencySimulationRequest(BaseModel):
    debt_id: str = Field(..., description="Target requirement debt identifier to simulate delay for")
    additional_delay_days: int = Field(default=30, ge=0, le=365, description="Simulated days of additional deferral delay")
    scenario_notes: Optional[str] = None

class DependencySimulationResponse(BaseModel):
    target_debt_id: str
    target_title: str
    target_module: str
    target_current_risk: float
    target_current_risk_pressure: float

    additional_delay_days: int

    target_projected_risk: float
    target_projected_risk_pressure: float
    target_projected_tier: str
    direct_blocked_count: int
    indirect_blocked_count: int
    total_unique_affected_count: int
    affected_modules: List[str]
    affected_requirements: List[AffectedRequirementDetail]
    has_cycle: bool
    cycle_warning: Optional[str] = None
    cascaded_blocked_risk: float
    current_portfolio_risk: float
    simulated_portfolio_risk: float
    portfolio_risk_delta: float
    portfolio_risk_increase_percent: float
    summary_narrative: str

class WhatIfPlanEvaluationResult(BaseModel):
    plan_id: str
    plan_name: str
    description: str
    target_milestone: str
    resolved_debt_ids: List[str]
    total_effort_points: int
    initial_unresolved_count: int
    remaining_unresolved_count: int
    unblocked_requirements_count: int
    initial_aggregate_risk: float
    simulated_aggregate_risk: float
    risk_reduction_points: float
    risk_reduction_percent: float
    simulated_gate_status: str  # 'PASSED', 'CONDITIONAL', 'BLOCKED'
    is_ready_to_release: bool
    remaining_violations_count: int
    efficiency_ratio: float  # Risk reduction points per effort point
    summary: str

class WhatIfReleasePlanRequest(BaseModel):
    target_milestone: str = Field(..., min_length=2, description="Target release milestone to plan for")
    custom_plan_name: Optional[str] = "Custom Plan"
    custom_resolved_debt_ids: Optional[List[str]] = None
    effort_capacity_budget: Optional[int] = Field(default=30, ge=1, le=500, description="Team effort capacity (story points)")

class WhatIfReleasePlanResponse(BaseModel):
    target_milestone: str
    status_quo: WhatIfPlanEvaluationResult
    candidate_plans: List[WhatIfPlanEvaluationResult]
    recommended_plan_id: str
    comparative_analysis: str
    isolation_guarantee: str

class RiskForecastPoint(BaseModel):
    horizon_days: int
    projected_date: str
    aggregate_risk: float
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int

class RiskForecastRequest(BaseModel):
    debt_id: Optional[str] = None
    target_milestone: Optional[str] = None
    horizons_days: List[int] = Field(default=[0, 15, 30, 60, 90, 180], min_length=1, max_length=12)
    scenario: Literal["status_quo", "timely_review"] = Field(default="status_quo")
    daily_interest_rate: float = Field(default=0.008, ge=0.001, le=0.05)

    @field_validator("horizons_days")
    @classmethod
    def validate_horizons(cls, values: List[int]) -> List[int]:
        if any(value < 0 or value > 365 for value in values):
            raise ValueError("Forecast horizons must be between 0 and 365 days.")
        return sorted(set(values))

    @model_validator(mode="after")
    def validate_scope(self):
        if self.debt_id and self.target_milestone:
            raise ValueError("Choose either a single debt or a milestone, not both.")
        return self

class RiskForecastResponse(BaseModel):
    scope_description: str
    scenario: str
    daily_interest_rate: float
    assumptions_and_limitations: str
    trajectory: List[RiskForecastPoint]
