"""
Pydantic schemas for Release Readiness Assessment Gates
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ReleaseGateCreate(BaseModel):
    gate_name: str = Field(..., min_length=3)
    target_milestone: str = Field(..., min_length=2)
    max_critical_debts: int = Field(default=0, ge=0)
    max_high_debts: int = Field(default=1, ge=0)
    max_aggregate_risk: float = Field(default=150.0, ge=0.0)

class ReleaseGateSignOff(BaseModel):
    signoff_by: str = Field(..., min_length=2)
    signoff_notes: str = Field(..., min_length=5)

class ReleaseGateViolation(BaseModel):
    rule: str
    severity: str
    message: str
    culprit_debt_ids: List[str]

class ReleaseGateEvaluation(BaseModel):
    id: Optional[int] = None
    gate_name: str
    target_milestone: str
    status: str  # 'PASSED', 'CONDITIONAL', 'BLOCKED'
    is_ready_to_release: bool
    evaluation_date: str
    max_critical_debts: int
    actual_critical_debts: int
    max_high_debts: int
    actual_high_debts: int
    max_aggregate_risk: float
    actual_aggregate_risk: float
    total_unresolved_debts: int
    blocking_debts: List[str]
    violations: List[ReleaseGateViolation]
    summary: str
    signoff_by: Optional[str] = None
    signoff_notes: Optional[str] = None
