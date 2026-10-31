"""
Requirement Debt Ledger (RDL) - Release Gates Router
Manages Release Readiness Gates, policy violations, and release sign-offs.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models.release_gate import (
    ReleaseGateCreate,
    ReleaseGateEvaluation,
    ReleaseGateSignOff,
)
from app.services.release_evaluator import evaluate_release_readiness, sign_off_gate

router = APIRouter(prefix="/api/release-gates", tags=["Release Readiness Gates"])

@router.get("", response_model=List[Dict[str, Any]])
def list_release_gates(conn: sqlite3.Connection = Depends(get_db)):
    """List all configured release readiness gates."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM release_gates ORDER BY id DESC")
    rows = cursor.fetchall()
    return [dict(r) for r in rows]

@router.post("", status_code=201)
def create_release_gate(
    data: ReleaseGateCreate,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Define a new Release Readiness Gate."""
    now_iso = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO release_gates (gate_name, target_milestone, max_critical_debts, max_high_debts, max_aggregate_risk, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        """,
        (
            data.gate_name,
            data.target_milestone,
            data.max_critical_debts,
            data.max_high_debts,
            data.max_aggregate_risk,
            now_iso,
        ),
    )
    conn.commit()
    gate_id = cursor.lastrowid
    return {"message": "Release gate created successfully.", "id": gate_id}

@router.get("/{gate_id}/evaluate", response_model=ReleaseGateEvaluation)
def evaluate_gate(
    gate_id: int,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Run an automated evaluation against current live debt ledger state."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM release_gates WHERE id = ?", (gate_id,))
    gate = cursor.fetchone()
    if not gate:
        raise HTTPException(status_code=404, detail=f"Release gate {gate_id} not found.")

    eval_result = evaluate_release_readiness(
        conn=conn,
        target_milestone=gate["target_milestone"],
        max_critical_debts=gate["max_critical_debts"],
        max_high_debts=gate["max_high_debts"],
        max_aggregate_risk=gate["max_aggregate_risk"],
        gate_name=gate["gate_name"],
        gate_id=gate_id,
    )

    # Persist evaluation status to database
    cursor.execute(
        """
        UPDATE release_gates
        SET status = ?, evaluation_date = ?, evaluation_summary = ?,
            signoff_by = NULL, signoff_notes = NULL
        WHERE id = ?
        """,
        (eval_result.status, eval_result.evaluation_date, eval_result.summary, gate_id),
    )
    conn.commit()

    return eval_result

@router.post("/{gate_id}/signoff")
def sign_off(
    gate_id: int,
    data: ReleaseGateSignOff,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Formally sign off on a release gate."""
    return sign_off_gate(conn, gate_id, data)

@router.get("/evaluate-milestone/{milestone}", response_model=ReleaseGateEvaluation)
def evaluate_arbitrary_milestone(
    milestone: str,
    max_critical_debts: int = 0,
    max_high_debts: int = 1,
    max_aggregate_risk: float = 150.0,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Quickly evaluate readiness for any milestone without creating a saved gate."""
    return evaluate_release_readiness(
        conn=conn,
        target_milestone=milestone,
        max_critical_debts=max_critical_debts,
        max_high_debts=max_high_debts,
        max_aggregate_risk=max_aggregate_risk,
        gate_name=f"Ad-hoc Readiness for {milestone}",
    )
