"""
Pydantic schemas for Review Sessions and Audit Logs
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import date
from pydantic import BaseModel, Field, field_validator

class ReviewSessionCreate(BaseModel):
    debt_id: str
    reviewer_name: str = Field(..., min_length=2)
    reviewer_role: str = Field(..., min_length=2)
    outcome: Literal["Retain Debt", "Extend Review Date", "Escalate Priority", "Initiate Remediation", "Accept Risk Permanently"]
    notes: str = Field(..., min_length=5)
    new_review_date: Optional[str] = None
    review_date: Optional[str] = None

    @field_validator("new_review_date", "review_date")
    @classmethod
    def check_dates(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            parsed = date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Date must be a valid YYYY-MM-DD calendar date.") from exc
        if parsed.isoformat() != value:
            raise ValueError("Date must use the YYYY-MM-DD format.")
        return value

class ReviewSessionResponse(BaseModel):
    id: int
    debt_id: str
    review_date: str
    reviewer_name: str
    reviewer_role: str
    outcome: str
    notes: str
    new_review_date: Optional[str] = None
    created_at: str

class AuditLogResponse(BaseModel):
    id: int
    debt_id: Optional[str] = None
    action: str
    performed_by: str
    details: str
    created_at: str
    prev_hash: Optional[str] = None
    entry_hash: Optional[str] = None

class AuditIntegrityResponse(BaseModel):
    is_valid: bool
    total_entries: int
    tampered_count: int
    tampered_entries: List[Dict[str, Any]]
    latest_hash: Optional[str] = None
    summary: str
