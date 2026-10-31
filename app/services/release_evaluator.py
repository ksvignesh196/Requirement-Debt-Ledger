"""
Requirement Debt Ledger (RDL) - Release Readiness Gate Evaluator
Assesses whether a target release milestone meets risk tolerances and release gate criteria.
"""
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from app.models.release_gate import (
    ReleaseGateCreate,
    ReleaseGateEvaluation,
    ReleaseGateViolation,
    ReleaseGateSignOff,
)
from app.services.debt_service import get_all_debts
from app.services.audit_service import log_audit

def evaluate_release_readiness(
    conn: sqlite3.Connection,
    target_milestone: str,
    max_critical_debts: int = 0,
    max_high_debts: int = 1,
    max_aggregate_risk: float = 150.0,
    gate_name: Optional[str] = None,
    gate_id: Optional[int] = None,
    as_of_date: Optional[date] = None,
) -> ReleaseGateEvaluation:
    """
    Evaluates release gate criteria against current dynamic debt metrics.
    """
    debts = get_all_debts(conn, milestone=target_milestone, as_of_date=as_of_date)
    unresolved = [d for d in debts if d.status.lower() not in ("resolved", "accepted permanent")]

    critical_debts = [d for d in unresolved if d.risk.risk_tier == "Critical"]
    high_debts = [d for d in unresolved if d.risk.risk_tier == "High"]
    aggregate_risk = round(sum(d.risk.dynamic_risk_score for d in unresolved), 2)

    violations: List[ReleaseGateViolation] = []

    # Check 1: Critical Debts
    if len(critical_debts) > max_critical_debts:
        violations.append(
            ReleaseGateViolation(
                rule="ZERO_CRITICAL_DEBT_GATE",
                severity="CRITICAL",
                message=f"Found {len(critical_debts)} Critical requirement debts (maximum allowed: {max_critical_debts}).",
                culprit_debt_ids=[d.debt_id for d in critical_debts],
            )
        )

    # Check 2: High Debts
    if len(high_debts) > max_high_debts:
        violations.append(
            ReleaseGateViolation(
                rule="HIGH_RISK_DEBT_TOLERANCE",
                severity="HIGH",
                message=f"Found {len(high_debts)} High risk requirement debts (maximum allowed: {max_high_debts}).",
                culprit_debt_ids=[d.debt_id for d in high_debts],
            )
        )

    # Check 3: Aggregate Risk Capacity
    if aggregate_risk > max_aggregate_risk:
        violations.append(
            ReleaseGateViolation(
                rule="AGGREGATE_DEBT_CAPACITY",
                severity="HIGH",
                message=f"Aggregate requirement debt score is {aggregate_risk:.1f}, exceeding tolerance limit of {max_aggregate_risk:.1f}.",
                culprit_debt_ids=[d.debt_id for d in unresolved],
            )
        )

    # Check 4: Overdue Review / Breach Check
    breached_debts = [d for d in unresolved if d.escalation_level in ("OVERDUE_REVIEW", "CRITICAL_BREACH")]
    if breached_debts:
        violations.append(
            ReleaseGateViolation(
                rule="OVERDUE_ESCALATION_CHECK",
                severity="MEDIUM",
                message=f"{len(breached_debts)} debts have unresolved deadline/review escalations.",
                culprit_debt_ids=[d.debt_id for d in breached_debts],
            )
        )

    # Determine Verdict
    has_critical_violation = any(v.severity == "CRITICAL" for v in violations)
    if has_critical_violation:
        status = "BLOCKED"
        is_ready = False
        summary = f"RELEASE BLOCKED: {len(violations)} gate violation(s) including critical requirement debt."
    elif len(violations) > 0:
        status = "CONDITIONAL"
        is_ready = False
        summary = f"CONDITIONAL APPROVAL REQUIRED: {len(violations)} moderate warning(s) detected. Requires formal sign-off."
    else:
        status = "PASSED"
        is_ready = True
        summary = f"RELEASE READY: All quality and debt gates passed successfully for {target_milestone}."

    evaluation_date = (as_of_date or date.today()).isoformat()

    # Look up existing signoff if gate_id provided
    signoff_by = None
    signoff_notes = None
    if gate_id:
        cursor = conn.cursor()
        cursor.execute("SELECT signoff_by, signoff_notes FROM release_gates WHERE id = ?", (gate_id,))
        row = cursor.fetchone()
        if row:
            signoff_by = row["signoff_by"]
            signoff_notes = row["signoff_notes"]

    return ReleaseGateEvaluation(
        id=gate_id,
        gate_name=gate_name or f"Release Gate for {target_milestone}",
        target_milestone=target_milestone,
        status=status,
        is_ready_to_release=is_ready,
        evaluation_date=evaluation_date,
        max_critical_debts=max_critical_debts,
        actual_critical_debts=len(critical_debts),
        max_high_debts=max_high_debts,
        actual_high_debts=len(high_debts),
        max_aggregate_risk=max_aggregate_risk,
        actual_aggregate_risk=aggregate_risk,
        total_unresolved_debts=len(unresolved),
        blocking_debts=[d.debt_id for d in critical_debts + high_debts],
        violations=violations,
        summary=summary,
        signoff_by=signoff_by,
        signoff_notes=signoff_notes,
    )

def sign_off_gate(
    conn: sqlite3.Connection,
    gate_id: int,
    signoff_data: ReleaseGateSignOff,
) -> Dict[str, Any]:
    """Record formal sign-off for a release gate."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM release_gates WHERE id = ?", (gate_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Release gate ID {gate_id} not found.")

    evaluation = evaluate_release_readiness(
        conn=conn,
        target_milestone=row["target_milestone"],
        max_critical_debts=row["max_critical_debts"],
        max_high_debts=row["max_high_debts"],
        max_aggregate_risk=row["max_aggregate_risk"],
        gate_name=row["gate_name"],
        gate_id=gate_id,
    )
    if evaluation.status == "BLOCKED":
        raise HTTPException(
            status_code=409,
            detail="Sign-off blocked: this release gate currently has critical policy violations. Resolve the blockers and evaluate again.",
        )

    final_status = "Passed (Signed Off)" if evaluation.status == "PASSED" else "Conditional (Signed Off)"
    cursor.execute(
        """
        UPDATE release_gates
        SET status = ?,
            evaluation_date = ?,
            evaluation_summary = ?,
            signoff_by = ?,
            signoff_notes = ?
        WHERE id = ?
        """,
        (final_status, evaluation.evaluation_date, evaluation.summary, signoff_data.signoff_by, signoff_data.signoff_notes, gate_id),
    )

    log_audit(
        conn=conn,
        debt_id=None,
        action="RELEASE_GATE_SIGNED_OFF",
        performed_by=signoff_data.signoff_by,
        details=f"Formally signed off Release Gate '{row['gate_name']}' for milestone '{row['target_milestone']}'. Notes: {signoff_data.signoff_notes}"
    )

    return {
        "message": "Release gate signed off successfully." if evaluation.status == "PASSED" else "Conditional sign-off recorded; the gate remains not release-ready.",
        "gate_id": gate_id,
        "status": final_status,
        "is_ready_to_release": evaluation.is_ready_to_release,
    }
