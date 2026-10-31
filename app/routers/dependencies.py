"""
Requirement Debt Ledger (RDL) - Dependencies Router
Manages requirement debt interdependencies, cycle detection, and graph data for visualizers.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models.dependency import (
    DependencyCreate,
    DependencyResponse,
    GraphResponse,
    GraphNode,
    GraphEdge,
)
from app.services.dependency_engine import load_graph, DependencyGraph
from app.services.debt_service import get_all_debts
from app.services.audit_service import log_audit

router = APIRouter(prefix="/api/dependencies", tags=["Dependencies & Graph"])

@router.get("", response_model=List[DependencyResponse])
def list_dependencies(conn: sqlite3.Connection = Depends(get_db)):
    """List all registered dependency relationships."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM debt_dependencies ORDER BY id ASC")
    rows = cursor.fetchall()
    return [dict(r) for r in rows]

@router.post("", response_model=DependencyResponse, status_code=201)
def add_dependency(
    data: DependencyCreate,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Register a dependency link: 'debt_id' depends on 'depends_on_debt_id'.
    (i.e., 'depends_on_debt_id' blocks 'debt_id').
    """
    if data.debt_id == data.depends_on_debt_id:
        raise HTTPException(status_code=400, detail="A requirement debt cannot depend on itself.")

    cursor = conn.cursor()

    # Validate existence of both nodes
    cursor.execute("SELECT debt_id FROM requirement_debts WHERE debt_id IN (?, ?)", (data.debt_id, data.depends_on_debt_id))
    existing_ids = {r["debt_id"] for r in cursor.fetchall()}
    if data.debt_id not in existing_ids:
        raise HTTPException(status_code=404, detail=f"Debt '{data.debt_id}' does not exist.")
    if data.depends_on_debt_id not in existing_ids:
        raise HTTPException(status_code=404, detail=f"Debt '{data.depends_on_debt_id}' does not exist.")

    # Check for duplicate
    cursor.execute(
        "SELECT id FROM debt_dependencies WHERE debt_id = ? AND depends_on_debt_id = ?",
        (data.debt_id, data.depends_on_debt_id),
    )
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="This dependency relationship already exists.")

    # Cycle Detection check before inserting
    current_graph = load_graph(conn)
    current_graph.depends_on[data.debt_id].add(data.depends_on_debt_id)
    has_cycle, cycles = current_graph.detect_cycles()
    if has_cycle:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add dependency: It creates a cyclic dependency loop: {' -> '.join(cycles[0])}",
        )

    now_iso = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO debt_dependencies (debt_id, depends_on_debt_id, dependency_type, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (data.debt_id, data.depends_on_debt_id, data.dependency_type, data.notes, now_iso),
    )
    conn.commit()
    inserted_id = cursor.lastrowid

    log_audit(
        conn=conn,
        debt_id=data.debt_id,
        action="DEPENDENCY_ADDED",
        performed_by=data.created_by or "System",
        details=f"Added dependency: '{data.debt_id}' depends on '{data.depends_on_debt_id}' ({data.dependency_type}).",
    )

    return DependencyResponse(
        id=inserted_id,
        debt_id=data.debt_id,
        depends_on_debt_id=data.depends_on_debt_id,
        dependency_type=data.dependency_type,
        notes=data.notes,
        created_at=now_iso,
    )

@router.delete("/{dep_id}")
def delete_dependency(
    dep_id: int,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Remove a dependency relationship."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM debt_dependencies WHERE id = ?", (dep_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Dependency link ID {dep_id} not found.")

    cursor.execute("DELETE FROM debt_dependencies WHERE id = ?", (dep_id,))
    conn.commit()

    log_audit(
        conn=conn,
        debt_id=row["debt_id"],
        action="DEPENDENCY_REMOVED",
        performed_by="System",
        details=f"Removed dependency: '{row['debt_id']}' no longer depends on '{row['depends_on_debt_id']}'.",
    )
    return {"message": "Dependency removed successfully.", "id": dep_id}

@router.get("/graph", response_model=GraphResponse)
def get_dependency_graph(conn: sqlite3.Connection = Depends(get_db)):
    """Generate node-link graph data for visualizer."""
    debts = get_all_debts(conn)
    graph = load_graph(conn)
    has_cycle, cycles = graph.detect_cycles()

    nodes: List[GraphNode] = []
    for d in debts:
        nodes.append(
            GraphNode(
                id=d.debt_id,
                title=d.title,
                module=d.module,
                status=d.status,
                risk_score=d.risk.dynamic_risk_score,
                risk_tier=d.risk.risk_tier,
                priority_index=d.debt_priority_index,
                downstream_blocked_count=d.dependency_impact.downstream_blocked_count,
            )
        )

    cursor = conn.cursor()
    cursor.execute("SELECT id, debt_id, depends_on_debt_id, dependency_type, notes FROM debt_dependencies")
    dep_rows = cursor.fetchall()

    edges: List[GraphEdge] = []
    for r in dep_rows:
        edges.append(
            GraphEdge(
                id=str(r["id"]),
                source=r["depends_on_debt_id"],  # from blocker
                target=r["debt_id"],            # to blocked
                dependency_type=r["dependency_type"],
                notes=r["notes"],
            )
        )

    # Find longest critical path
    max_depth = -1
    critical_start = None
    for d in debts:
        depth = d.dependency_impact.critical_path_depth
        if depth > max_depth:
            max_depth = depth
            critical_start = d.debt_id

    critical_path: List[str] = []
    if critical_start and max_depth > 0:
        critical_path = [critical_start]
        curr = critical_start
        while True:
            blocked_items = list(graph.blocks.get(curr, []))
            if not blocked_items:
                break
            # Pick child with highest depth
            best_child = max(blocked_items, key=lambda c: graph.get_critical_path_depth(c))
            critical_path.append(best_child)
            curr = best_child

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        has_cycle=has_cycle,
        cycles=cycles,
        critical_path=critical_path,
    )
