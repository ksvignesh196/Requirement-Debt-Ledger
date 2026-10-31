"""
Unit tests for Release Readiness Evaluator
"""
from datetime import date
from app.services.release_evaluator import evaluate_release_readiness, sign_off_gate
from app.models.release_gate import ReleaseGateSignOff

def test_release_readiness_blocked_on_critical_debts(db_conn):
    # Release 1.0 has REQ-002 and REQ-004 which are Critical/High
    res = evaluate_release_readiness(
        conn=db_conn,
        target_milestone="Release 1.0",
        max_critical_debts=0,
        max_high_debts=0,
        max_aggregate_risk=100.0,
    )
    assert res.status == "BLOCKED"
    assert not res.is_ready_to_release
    assert len(res.violations) > 0
    assert any(v.severity == "CRITICAL" for v in res.violations)

def test_release_readiness_passed_with_relaxed_tolerances(db_conn):
    # Release 2.0 debts are non-critical (low/moderate)
    res = evaluate_release_readiness(
        conn=db_conn,
        target_milestone="Release 2.0",
        max_critical_debts=0,
        max_high_debts=2,
        max_aggregate_risk=300.0,
    )
    assert res.status == "PASSED"
    assert res.is_ready_to_release
    assert len(res.violations) == 0

def test_release_gate_signoff_rechecks_current_readiness(db_conn):
    # Release 1.0 has a critical blocker and must never be signed off as passed.
    cursor = db_conn.cursor()
    cursor.execute("SELECT id FROM release_gates WHERE target_milestone = 'Release 1.0'")
    blocked_gate_id = cursor.fetchone()["id"]
    signoff_payload = ReleaseGateSignOff(
        signoff_by="Release Director",
        signoff_notes="Reviewed the current release readiness and outstanding blockers.",
    )
    from fastapi import HTTPException
    import pytest
    with pytest.raises(HTTPException) as exc:
        sign_off_gate(db_conn, blocked_gate_id, signoff_payload)
    assert exc.value.status_code == 409

    # Release 2.0 is ready under its configured policy and may be signed off.
    cursor.execute("SELECT id FROM release_gates WHERE target_milestone = 'Release 2.0'")
    ready_gate_id = cursor.fetchone()["id"]
    result = sign_off_gate(db_conn, ready_gate_id, signoff_payload)
    assert result["status"] == "Passed (Signed Off)"
    assert result["is_ready_to_release"] is True
    cursor.execute("SELECT status, signoff_by FROM release_gates WHERE id = ?", (ready_gate_id,))
    row = cursor.fetchone()
    assert row["status"] == "Passed (Signed Off)"
    assert row["signoff_by"] == "Release Director"
