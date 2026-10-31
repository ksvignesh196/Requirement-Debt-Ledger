"""
Requirement Debt Ledger (RDL) - Reviews & Audit Router
Manages debt review sessions, date extensions, remediation decisions,
and audit trail retrieval with cryptographic integrity verification.
"""
import sqlite3
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.models.review import (
    ReviewSessionCreate,
    ReviewSessionResponse,
    AuditLogResponse,
    AuditIntegrityResponse,
)
from app.services.audit_service import log_audit, get_audit_trail, verify_audit_integrity

router = APIRouter(tags=["Reviews & Audit"])

@router.get("/api/reviews/{debt_id}", response_model=List[ReviewSessionResponse])
def get_debt_reviews(
    debt_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Retrieve all review meeting records for a debt item."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM review_sessions WHERE debt_id = ? ORDER BY id DESC", (debt_id,))
    rows = cursor.fetchall()
    return [dict(r) for r in rows]

@router.post("/api/reviews", response_model=ReviewSessionResponse, status_code=201)
def record_review_session(
    data: ReviewSessionCreate,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Record an official review session for a deferred requirement.
    If 'new_review_date' is provided, updates the target review date.
    If outcome is 'Initiate Remediation', updates status to 'Remediating'.
    If outcome is 'Accept Risk Permanently', updates status to 'Accepted Permanent'.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requirement_debts WHERE debt_id = ?", (data.debt_id,))
    debt = cursor.fetchone()
    if not debt:
        raise HTTPException(status_code=404, detail=f"Debt '{data.debt_id}' not found.")

    review_date_val = data.review_date or date.today().isoformat()
    now_iso = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO review_sessions (debt_id, review_date, reviewer_name, reviewer_role, outcome, notes, new_review_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.debt_id,
            review_date_val,
            data.reviewer_name,
            data.reviewer_role,
            data.outcome,
            data.notes,
            data.new_review_date,
            now_iso,
        ),
    )
    conn.commit()
    inserted_id = cursor.lastrowid

    # Apply outcome effects to debt item
    status_update = None
    if data.outcome == "Initiate Remediation":
        status_update = "Remediating"
    elif data.outcome == "Accept Risk Permanently":
        status_update = "Accepted Permanent"
    elif data.outcome == "Under Review":
        status_update = "Under Review"

    updates = []
    params = []
    if status_update:
        updates.append("status = ?")
        params.append(status_update)
    if data.new_review_date:
        updates.append("review_date = ?")
        params.append(data.new_review_date)

    if updates:
        updates.append("updated_at = ?")
        params.append(now_iso)
        params.append(data.debt_id)
        cursor.execute(f"UPDATE requirement_debts SET {', '.join(updates)} WHERE debt_id = ?", params)
        conn.commit()

    log_audit(
        conn=conn,
        debt_id=data.debt_id,
        action="REVIEW_CONDUCTED",
        performed_by=f"{data.reviewer_name} ({data.reviewer_role})",
        details=f"Review outcome: '{data.outcome}'. Notes: {data.notes}"
        + (f" New review date: {data.new_review_date}" if data.new_review_date else ""),
    )

    return ReviewSessionResponse(
        id=inserted_id,
        debt_id=data.debt_id,
        review_date=review_date_val,
        reviewer_name=data.reviewer_name,
        reviewer_role=data.reviewer_role,
        outcome=data.outcome,
        notes=data.notes,
        new_review_date=data.new_review_date,
        created_at=now_iso,
    )

@router.get("/api/audit", response_model=List[AuditLogResponse])
def get_audit_logs(
    debt_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Retrieve immutable audit trail records."""
    return get_audit_trail(conn, debt_id=debt_id, limit=limit)

@router.get("/api/audit/verify", response_model=AuditIntegrityResponse)
def verify_audit_log_chain(conn: sqlite3.Connection = Depends(get_db)):
    """
    Cryptographically verifies the SHA-256 hash chain of the entire audit log.
    Ensures that records have not been altered, inserted, or deleted outside authorized channels.
    """
    return verify_audit_integrity(conn)
