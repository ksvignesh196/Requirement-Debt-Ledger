"""
Requirement Debt Ledger (RDL) - Export & Data Management Router
Exporting CSV/JSON audit reports and reset-to-seed endpoints for live demonstration.
"""
import io
import csv
import sqlite3
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse

from app.database import get_db, init_db
from app.services.debt_service import get_all_debts

router = APIRouter(prefix="/api/export", tags=["Export & Data Management"])

def _safe_csv_value(value):
    """Prefix formula-like text, including text preceded by whitespace."""
    if isinstance(value, str):
        probe = value.lstrip(" \t\r\n\ufeff")
        if probe.startswith(("=", "+", "-", "@")):
            return "'" + value
    return value

@router.get("/csv")
def export_csv(conn: sqlite3.Connection = Depends(get_db)):
    """Export complete requirement debt ledger as CSV file."""
    debts = get_all_debts(conn)

    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        "Debt ID",
        "Title",
        "Module",
        "Type",
        "Status",
        "Target Milestone",
        "Deferral Reason",
        "Deferral Phase",
        "Decision Maker",
        "Owner",
        "Created Date",
        "Review Date",
        "Deadline Date",
        "Base Risk",
        "Dynamic Risk",
        "Risk Tier",
        "Accrued Interest %",
        "Overdue Penalty",
        "Blocked Dependencies",
        "Debt Priority Index",
        "Escalation Level",
        "Resolution Type",
        "Resolution Notes",
    ])

    for d in debts:
        writer.writerow([_safe_csv_value(value) for value in [
            d.debt_id,
            d.title,
            d.module,
            d.requirement_type,
            d.status,
            d.target_milestone,
            d.deferral_reason,
            d.deferral_phase,
            d.decision_maker,
            d.owner,
            d.created_date,
            d.review_date,
            d.deadline_date,
            d.risk.base_risk_score,
            d.risk.dynamic_risk_score,
            d.risk.risk_tier,
            d.risk.accrued_interest_percent,
            d.risk.overdue_penalty_factor,
            d.dependency_impact.downstream_blocked_count,
            d.debt_priority_index,
            d.escalation_level,
            d.resolution_type or "",
            d.resolution_notes or "",
        ]])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=requirement_debt_ledger.csv"},
    )

@router.get("/json")
def export_json(conn: sqlite3.Connection = Depends(get_db)):
    """Export complete requirement debt ledger as structured JSON."""
    debts = get_all_debts(conn)
    return [d.model_dump() for d in debts]

@router.post("/reset")
def reset_database_data():
    """Reset database to realistic enterprise demonstration seed data."""
    from seed_data import seed_database
    seed_database()
    return {"message": "Database reset to initial demo seed data successfully."}
