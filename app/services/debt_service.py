"""
Requirement Debt Ledger (RDL) - Core Debt Service
Handles CRUD operations, query filters, search, and dynamic metric enrichment.
"""
import sqlite3
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from app.models.debt_item import (
    DebtItemCreate,
    DebtItemUpdate,
    DebtItemResolve,
    DebtItemResponse,
)
from app.services.risk_engine import evaluate_debt_risk
from app.services.dependency_engine import (
    load_graph,
    calculate_dependency_impact,
    calculate_priority_index,
    DependencyGraph,
)
from app.services.escalation_engine import get_escalation_status
from app.services.audit_service import log_audit

def generate_next_debt_id(conn: sqlite3.Connection) -> str:
    """Generate sequential identifier like REQ-DEBT-001."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM requirement_debts ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    next_num = (row["id"] + 1) if row else 1
    return f"REQ-DEBT-{next_num:03d}"

def enrich_debt(
    row_dict: Dict[str, Any],
    graph: DependencyGraph,
    as_of_date: Optional[date] = None,
) -> DebtItemResponse:
    """
    Enriches a database record with dynamic risk calculation,
    graph-based dependency impact, priority index, and escalation status.
    """
    debt_id = row_dict["debt_id"]
    status = row_dict["status"]

    # 1. Dynamic Risk
    risk_info = evaluate_debt_risk(
        business_impact=row_dict["business_impact"],
        arch_impact=row_dict["arch_impact"],
        safety_impact=row_dict["safety_impact"],
        occurrence_prob=row_dict["occurrence_prob"],
        detection_difficulty=row_dict["detection_difficulty"],
        created_date_str=row_dict["created_date"],
        review_date_str=row_dict["review_date"],
        as_of_date=as_of_date,
    )

    # 2. Dependency Impact
    dep_impact = calculate_dependency_impact(debt_id, graph)

    # 3. Debt Priority Index (DPI)
    dpi = calculate_priority_index(
        dynamic_risk=risk_info.dynamic_risk_score,
        downstream_blocked_count=dep_impact.downstream_blocked_count,
        deadline_date_str=row_dict["deadline_date"],
        cost_of_delay=row_dict["cost_of_delay"],
        as_of_date=as_of_date,
    )

    # 4. Escalation status
    escalation_level, days_to_review, days_to_deadline = get_escalation_status(
        review_date_str=row_dict["review_date"],
        deadline_date_str=row_dict["deadline_date"],
        status=status,
        as_of_date=as_of_date,
    )

    return DebtItemResponse(
        id=row_dict["id"],
        debt_id=debt_id,
        title=row_dict["title"],
        description=row_dict["description"],
        module=row_dict["module"],
        requirement_type=row_dict["requirement_type"],
        deferral_reason=row_dict["deferral_reason"],
        deferral_phase=row_dict["deferral_phase"],
        decision_maker=row_dict["decision_maker"],
        owner=row_dict["owner"],
        target_milestone=row_dict["target_milestone"],
        resolution_criteria=row_dict["resolution_criteria"],
        status=status,
        created_date=row_dict["created_date"],
        review_date=row_dict["review_date"],
        deadline_date=row_dict["deadline_date"],
        business_impact=row_dict["business_impact"],
        arch_impact=row_dict["arch_impact"],
        safety_impact=row_dict["safety_impact"],
        occurrence_prob=row_dict["occurrence_prob"],
        detection_difficulty=row_dict["detection_difficulty"],
        cost_of_delay=row_dict["cost_of_delay"],
        estimated_effort=row_dict.get("estimated_effort", 8) or 8,
        resolution_notes=row_dict.get("resolution_notes"),
        resolved_date=row_dict.get("resolved_date"),
        resolution_type=row_dict.get("resolution_type"),
        updated_at=row_dict["updated_at"],
        risk=risk_info,
        dependency_impact=dep_impact,
        debt_priority_index=dpi,
        escalation_level=escalation_level,
        days_to_review=days_to_review,
        days_to_deadline=days_to_deadline,
    )

def get_all_debts(
    conn: sqlite3.Connection,
    module: Optional[str] = None,
    status: Optional[str] = None,
    risk_tier: Optional[str] = None,
    escalation_level: Optional[str] = None,
    milestone: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "debt_priority_index",
    sort_order: str = "desc",
    as_of_date: Optional[date] = None,
) -> List[DebtItemResponse]:
    """Retrieve all debt items enriched with dynamic metrics, filtered and sorted."""
    graph = load_graph(conn)
    cursor = conn.cursor()

    query = "SELECT * FROM requirement_debts WHERE 1=1"
    params = []

    if module:
        query += " AND module = ?"
        params.append(module)
    if status:
        query += " AND status = ?"
        params.append(status)
    if milestone:
        query += " AND target_milestone = ?"
        params.append(milestone)
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR debt_id LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    enriched_items = [enrich_debt(dict(r), graph, as_of_date) for r in rows]

    # Post-filtering on computed dynamic fields
    if risk_tier:
        enriched_items = [i for i in enriched_items if i.risk.risk_tier.lower() == risk_tier.lower()]
    if escalation_level:
        enriched_items = [i for i in enriched_items if i.escalation_level.lower() == escalation_level.lower()]

    # Sorting
    reverse = (sort_order.lower() == "desc")
    if sort_by == "debt_priority_index":
        enriched_items.sort(key=lambda x: x.debt_priority_index, reverse=reverse)
    elif sort_by == "dynamic_risk_score":
        enriched_items.sort(key=lambda x: x.risk.dynamic_risk_score, reverse=reverse)
    elif sort_by == "days_to_review":
        enriched_items.sort(key=lambda x: x.days_to_review, reverse=reverse)
    elif sort_by == "created_date":
        enriched_items.sort(key=lambda x: x.created_date, reverse=reverse)
    elif sort_by == "title":
        enriched_items.sort(key=lambda x: x.title.lower(), reverse=reverse)
    elif sort_by == "estimated_effort":
        enriched_items.sort(key=lambda x: x.estimated_effort, reverse=reverse)

    return enriched_items

def get_debt_by_id(
    conn: sqlite3.Connection,
    debt_id: str,
    as_of_date: Optional[date] = None,
) -> DebtItemResponse:
    """Retrieve single debt item by debt_id (e.g. REQ-DEBT-001)."""
    graph = load_graph(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requirement_debts WHERE debt_id = ?", (debt_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Requirement debt '{debt_id}' not found.")
    return enrich_debt(dict(row), graph, as_of_date)

def create_debt(
    conn: sqlite3.Connection,
    data: DebtItemCreate,
    as_of_date: Optional[date] = None,
) -> DebtItemResponse:
    """Create a new requirement debt record."""
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    debt_id = data.debt_id or generate_next_debt_id(conn)

    # Check for duplicate
    cursor.execute("SELECT id FROM requirement_debts WHERE debt_id = ?", (debt_id,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail=f"Debt ID '{debt_id}' already exists.")

    cursor.execute(
        """
        INSERT INTO requirement_debts (
            debt_id, title, description, module, requirement_type,
            deferral_reason, deferral_phase, decision_maker, owner,
            target_milestone, resolution_criteria, status, created_date,
            review_date, deadline_date, business_impact, arch_impact,
            safety_impact, occurrence_prob, detection_difficulty,
            cost_of_delay, estimated_effort, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, 'Deferred', ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?
        )
        """,
        (
            debt_id, data.title, data.description, data.module, data.requirement_type,
            data.deferral_reason, data.deferral_phase, data.decision_maker, data.owner,
            data.target_milestone, data.resolution_criteria, data.created_date,
            data.review_date, data.deadline_date, data.business_impact, data.arch_impact,
            data.safety_impact, data.occurrence_prob, data.detection_difficulty,
            data.cost_of_delay, data.estimated_effort, now_iso
        ),
    )
    conn.commit()

    log_audit(
        conn=conn,
        debt_id=debt_id,
        action="DEBT_CREATED",
        performed_by=data.decision_maker,
        details=f"Created deferred requirement '{debt_id}: {data.title}' in module '{data.module}' under milestone '{data.target_milestone}'. Reason: {data.deferral_reason}. Estimated Effort: {data.estimated_effort} pts."
    )

    return get_debt_by_id(conn, debt_id, as_of_date)

def update_debt(
    conn: sqlite3.Connection,
    debt_id: str,
    data: DebtItemUpdate,
    as_of_date: Optional[date] = None,
) -> DebtItemResponse:
    """Update fields on an existing requirement debt record."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requirement_debts WHERE debt_id = ?", (debt_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Requirement debt '{debt_id}' not found.")

    updates = []
    params = []
    changes_desc = []

    update_dict = data.model_dump(exclude_unset=True, exclude={"updated_by", "rationale"})
    for field, val in update_dict.items():
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
            changes_desc.append(f"{field} changed to '{val}'")

    if not updates:
        return get_debt_by_id(conn, debt_id, as_of_date)

    now_iso = datetime.now().isoformat()
    updates.append("updated_at = ?")
    params.append(now_iso)

    params.append(debt_id)
    query = f"UPDATE requirement_debts SET {', '.join(updates)} WHERE debt_id = ?"
    cursor.execute(query, params)
    conn.commit()

    rationale_text = f" Rationale: {data.rationale}" if data.rationale else ""
    log_audit(
        conn=conn,
        debt_id=debt_id,
        action="DEBT_UPDATED",
        performed_by=data.updated_by or "System User",
        details=f"Updated fields: {'; '.join(changes_desc)}.{rationale_text}"
    )

    return get_debt_by_id(conn, debt_id, as_of_date)

def resolve_debt(
    conn: sqlite3.Connection,
    debt_id: str,
    data: DebtItemResolve,
    as_of_date: Optional[date] = None,
) -> DebtItemResponse:
    """Mark a requirement debt as resolved with evidence and verification notes."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requirement_debts WHERE debt_id = ?", (debt_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Requirement debt '{debt_id}' not found.")

    resolved_date = data.resolved_date or date.today().isoformat()
    now_iso = datetime.now().isoformat()

    cursor.execute(
        """
        UPDATE requirement_debts
        SET status = 'Resolved',
            resolution_type = ?,
            resolution_notes = ?,
            resolved_date = ?,
            updated_at = ?
        WHERE debt_id = ?
        """,
        (data.resolution_type, data.resolution_notes, resolved_date, now_iso, debt_id),
    )
    conn.commit()

    log_audit(
        conn=conn,
        debt_id=debt_id,
        action="DEBT_RESOLVED",
        performed_by=data.resolved_by,
        details=f"Resolved as '{data.resolution_type}'. Verification Notes: {data.resolution_notes}"
    )

    return get_debt_by_id(conn, debt_id, as_of_date)

def delete_debt(conn: sqlite3.Connection, debt_id: str) -> Dict[str, Any]:
    """Delete a requirement debt and all its associated dependencies/reviews."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM requirement_debts WHERE debt_id = ?", (debt_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Debt '{debt_id}' not found.")

    title = row["title"]
    cursor.execute("DELETE FROM requirement_debts WHERE debt_id = ?", (debt_id,))
    conn.commit()

    log_audit(
        conn=conn,
        debt_id=debt_id,
        action="DEBT_DELETED",
        performed_by="Administrator",
        details=f"Permanently removed requirement debt '{debt_id}: {title}'."
    )
    return {"message": f"Debt '{debt_id}' deleted successfully."}
