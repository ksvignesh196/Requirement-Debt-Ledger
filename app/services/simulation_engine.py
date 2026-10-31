"""
Requirement Debt Ledger (RDL) - What-If Release Planning & Risk Forecasting Service
Provides isolated sandbox simulations for release readiness planning and deterministic risk projections.
"""
import sqlite3
from typing import List, Dict, Any, Optional, Set
from datetime import date, datetime, timedelta
from fastapi import HTTPException

from app.models.simulation import (
    WhatIfPlanEvaluationResult,
    WhatIfReleasePlanRequest,
    WhatIfReleasePlanResponse,
    RiskForecastRequest,
    RiskForecastResponse,
    RiskForecastPoint,
)
from app.services.debt_service import get_all_debts
from app.services.dependency_engine import load_graph
from app.services.release_evaluator import evaluate_release_readiness
from app.services.risk_engine import evaluate_debt_risk, parse_date
from app.services.audit_service import log_audit

def evaluate_plan_in_sandbox(
    conn: sqlite3.Connection,
    target_milestone: str,
    plan_id: str,
    plan_name: str,
    description: str,
    resolved_debt_ids: List[str],
    as_of_date: Optional[date] = None,
) -> WhatIfPlanEvaluationResult:
    """
    Evaluates an isolated, in-memory what-if plan without altering persistent SQLite records.
    """
    debts = get_all_debts(conn, milestone=target_milestone, as_of_date=as_of_date)
    initial_unresolved = [d for d in debts if d.status.lower() not in ("resolved", "accepted permanent")]
    initial_risk = round(sum(d.risk.dynamic_risk_score for d in initial_unresolved), 2)
    initial_count = len(initial_unresolved)

    resolved_set = set(resolved_debt_ids)
    unresolved_ids = {item.debt_id for item in initial_unresolved}
    invalid_ids = sorted(resolved_set - unresolved_ids)
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Plan contains requirements that are not open in milestone '{target_milestone}': {', '.join(invalid_ids)}",
        )

    # In sandbox: filter out items marked resolved in this plan
    simulated_unresolved = [d for d in initial_unresolved if d.debt_id not in resolved_set]
    simulated_risk = round(sum(d.risk.dynamic_risk_score for d in simulated_unresolved), 2)
    risk_reduction_points = max(0.0, round(initial_risk - simulated_risk, 2))
    risk_reduction_pct = round((risk_reduction_points / initial_risk * 100.0), 2) if initial_risk > 0 else 0.0

    # Total effort points required for this plan
    total_effort = sum(getattr(d, "estimated_effort", 8) for d in initial_unresolved if d.debt_id in resolved_set)

    # Count downstream requirements that become fully unblocked, once each.
    graph = load_graph(conn)
    all_items = get_all_debts(conn, as_of_date=as_of_date)
    already_resolved = {
        item.debt_id for item in all_items
        if item.status.lower() in ("resolved", "accepted permanent")
    }
    resolved_after_plan = already_resolved | resolved_set
    prerequisites: Dict[str, Set[str]] = {}
    for blocker_id, dependent_ids in graph.blocks.items():
        for dependent_id in dependent_ids:
            prerequisites.setdefault(dependent_id, set()).add(blocker_id)

    unblocked_count = 0
    for dependent_id, prerequisite_ids in prerequisites.items():
        if dependent_id in resolved_set or not prerequisite_ids:
            continue
        blocked_before = any(item_id not in already_resolved for item_id in prerequisite_ids)
        blocked_after = any(item_id not in resolved_after_plan for item_id in prerequisite_ids)
        if blocked_before and not blocked_after:
            unblocked_count += 1

    # Run simulated release gate evaluation
    critical_unresolved = [d for d in simulated_unresolved if d.risk.risk_tier == "Critical"]
    high_unresolved = [d for d in simulated_unresolved if d.risk.risk_tier == "High"]

    violations_count = 0
    # Gate rules: 0 critical allowed, <= 1 high allowed, max aggregate risk <= 150
    if len(critical_unresolved) > 0:
        violations_count += len(critical_unresolved)
    if len(high_unresolved) > 1:
        violations_count += (len(high_unresolved) - 1)
    if simulated_risk > 150.0:
        violations_count += 1

    if len(critical_unresolved) > 0:
        sim_status = "BLOCKED"
        is_ready = False
    elif violations_count > 0:
        sim_status = "CONDITIONAL"
        is_ready = False
    else:
        sim_status = "PASSED"
        is_ready = True

    efficiency_ratio = round(risk_reduction_points / max(1, total_effort), 2)

    summary = (
        f"Plan '{plan_name}' resolves {len(resolved_set)} debts using {total_effort} effort points. "
        f"Reduces milestone debt risk by {risk_reduction_points:.1f} pts ({risk_reduction_pct:.1f}% reduction). "
        f"Simulated Release Gate verdict: {sim_status} ({violations_count} remaining policy violations)."
    )

    return WhatIfPlanEvaluationResult(
        plan_id=plan_id,
        plan_name=plan_name,
        description=description,
        target_milestone=target_milestone,
        resolved_debt_ids=sorted(list(resolved_set)),
        total_effort_points=total_effort,
        initial_unresolved_count=initial_count,
        remaining_unresolved_count=len(simulated_unresolved),
        unblocked_requirements_count=unblocked_count,
        initial_aggregate_risk=initial_risk,
        simulated_aggregate_risk=simulated_risk,
        risk_reduction_points=risk_reduction_points,
        risk_reduction_percent=risk_reduction_pct,
        simulated_gate_status=sim_status,
        is_ready_to_release=is_ready,
        remaining_violations_count=violations_count,
        efficiency_ratio=efficiency_ratio,
        summary=summary,
    )

def run_what_if_release_planning(
    conn: sqlite3.Connection,
    request: WhatIfReleasePlanRequest,
    as_of_date: Optional[date] = None,
) -> WhatIfReleasePlanResponse:
    """
    Compares candidate requirement debt resolution plans for a target release milestone.
    All evaluations are completely isolated in-memory until explicitly applied.
    """
    target_milestone = request.target_milestone
    debts = get_all_debts(conn, milestone=target_milestone, as_of_date=as_of_date)
    unresolved = [d for d in debts if d.status.lower() not in ("resolved", "accepted permanent")]

    if not unresolved:
        status_quo = evaluate_plan_in_sandbox(
            conn, target_milestone, "status_quo", "Status Quo", "No unresolved debts exist.", []
        )
        return WhatIfReleasePlanResponse(
            target_milestone=target_milestone,
            status_quo=status_quo,
            candidate_plans=[],
            recommended_plan_id="status_quo",
            comparative_analysis="Milestone has zero open requirement debts; already release ready.",
            isolation_guarantee="Simulation is read-only and has not altered database records.",
        )

    # 1. Baseline Status Quo
    status_quo = evaluate_plan_in_sandbox(
        conn, target_milestone, "status_quo", "Status Quo (No Action)", "Keep all current debts unaddressed.", []
    )

    # 2. Plan A: Blocker Triage (Prerequisites & Root Blockers First)
    graph = load_graph(conn)
    blocker_debts = [d.debt_id for d in unresolved if len(graph.blocks.get(d.debt_id, set())) > 0]
    plan_a = evaluate_plan_in_sandbox(
        conn=conn,
        target_milestone=target_milestone,
        plan_id="plan_a_blockers",
        plan_name="Plan A: Dependency Unblocking First",
        description="Prioritizes requirements that are currently blocking other downstream capabilities.",
        resolved_debt_ids=blocker_debts,
        as_of_date=as_of_date,
    )

    # 3. Plan B: Critical & High Risk Elimination
    crit_high_debts = [d.debt_id for d in unresolved if d.risk.risk_tier in ("Critical", "High")]
    plan_b = evaluate_plan_in_sandbox(
        conn=conn,
        target_milestone=target_milestone,
        plan_id="plan_b_critical",
        plan_name="Plan B: Severe Risk Elimination",
        description="Remediates all Critical and High risk requirement debts to eliminate gate blockers.",
        resolved_debt_ids=crit_high_debts,
        as_of_date=as_of_date,
    )

    # 4. Plan C: Quick Wins within Effort Budget
    budget = request.effort_capacity_budget or 30
    # Sort unresolved by ROI (Risk / Effort) descending
    sorted_by_roi = sorted(
        unresolved,
        key=lambda d: d.risk.dynamic_risk_score / max(1, getattr(d, "estimated_effort", 8)),
        reverse=True,
    )
    quick_wins = []
    accum_effort = 0
    for d in sorted_by_roi:
        e = getattr(d, "estimated_effort", 8)
        if accum_effort + e <= budget:
            quick_wins.append(d.debt_id)
            accum_effort += e

    plan_c = evaluate_plan_in_sandbox(
        conn=conn,
        target_milestone=target_milestone,
        plan_id="plan_c_quickwins",
        plan_name=f"Plan C: Quick Wins (Budget <= {budget} pts)",
        description=f"Selects highest risk-reduction-per-effort debts constrained by {budget} point capacity.",
        resolved_debt_ids=quick_wins,
        as_of_date=as_of_date,
    )

    candidate_plans = [plan_a, plan_b, plan_c]

    # Optional Custom Plan
    if request.custom_resolved_debt_ids:
        plan_custom = evaluate_plan_in_sandbox(
            conn=conn,
            target_milestone=target_milestone,
            plan_id="plan_custom",
            plan_name=request.custom_plan_name or "Custom User Plan",
            description="User-selected combination of requirement debts.",
            resolved_debt_ids=request.custom_resolved_debt_ids,
            as_of_date=as_of_date,
        )
        candidate_plans.append(plan_custom)

    # Pick Recommended Plan:
    # Prefer a plan that passes the release gate with highest efficiency ratio
    passing_plans = [p for p in candidate_plans if p.is_ready_to_release]
    if passing_plans:
        recommended = max(passing_plans, key=lambda p: p.efficiency_ratio)
    else:
        # Otherwise pick plan that minimizes remaining violations with best efficiency
        recommended = max(candidate_plans, key=lambda p: (p.risk_reduction_points, p.efficiency_ratio))

    comparative_analysis = (
        f"Evaluated {len(candidate_plans)} alternative remediation strategies for {target_milestone}. "
        f"'{recommended.plan_name}' is recommended as the optimal balance: achieves a "
        f"{recommended.risk_reduction_percent:.1f}% risk reduction ({recommended.simulated_gate_status} gate status) "
        f"at an efficiency ratio of {recommended.efficiency_ratio:.2f} risk points per story point."
    )

    return WhatIfReleasePlanResponse(
        target_milestone=target_milestone,
        status_quo=status_quo,
        candidate_plans=candidate_plans,
        recommended_plan_id=recommended.plan_id,
        comparative_analysis=comparative_analysis,
        isolation_guarantee="All plan simulations are strictly virtual and isolated from database records.",
    )

def apply_what_if_plan(
    conn: sqlite3.Connection,
    target_milestone: str,
    resolved_debt_ids: List[str],
    actor_name: str,
    rationale: str,
) -> Dict[str, Any]:
    """
    Explicitly applies a simulated what-if plan to the actual database records upon user confirmation.
    """
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat(timespec="seconds")
    requested_ids = sorted(set(resolved_debt_ids))
    if not requested_ids:
        raise HTTPException(status_code=400, detail="The plan does not contain any requirements to start.")

    placeholders = ",".join("?" for _ in requested_ids)
    cursor.execute(
        f"SELECT debt_id, status FROM requirement_debts WHERE target_milestone = ? AND debt_id IN ({placeholders})",
        [target_milestone, *requested_ids],
    )
    selected_rows = cursor.fetchall()
    selected = {row["debt_id"]: row["status"] for row in selected_rows}
    if set(selected) != set(requested_ids):
        raise HTTPException(status_code=400, detail="The plan includes a requirement that does not belong to the selected milestone.")
    already_closed = [key for key, value in selected.items() if value.lower() in ("resolved", "accepted permanent")]
    if already_closed:
        raise HTTPException(status_code=409, detail=f"These requirements are already closed: {', '.join(already_closed)}")

    cursor.execute(
        f"""
        UPDATE requirement_debts
        SET status = 'Remediating',
            resolution_type = NULL,
            resolution_notes = NULL,
            resolved_date = NULL,
            updated_at = ?
        WHERE target_milestone = ? AND debt_id IN ({placeholders})
        """,
        [now_iso, target_milestone, *requested_ids],
    )
    updated_count = cursor.rowcount

    log_audit(
        conn=conn,
        debt_id=None,
        action="WHAT_IF_PLAN_APPLIED",
        performed_by=actor_name,
        details=f"Applied What-If Release Plan to '{target_milestone}'. Moved {updated_count} debts to Remediating; implementation and verification are still required. Rationale: {rationale}",
    )

    return {
        "message": f"Started remediation for {updated_count} requirement debts. They remain open until implementation is verified.",
        "target_milestone": target_milestone,
        "remediating_debt_ids": requested_ids,
        "updated_count": updated_count,
    }

def run_risk_forecasting(
    conn: sqlite3.Connection,
    request: RiskForecastRequest,
    as_of_date: Optional[date] = None,
) -> RiskForecastResponse:
    """
    Forecasts portfolio or single-debt risk across multiple future horizons under deterministic mathematical assumptions.
    """
    cursor = conn.cursor()
    current_date = as_of_date or date.today()

    if request.debt_id:
        cursor.execute("SELECT * FROM requirement_debts WHERE debt_id = ?", (request.debt_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        if not rows:
            raise HTTPException(status_code=404, detail=f"Debt '{request.debt_id}' not found.")
        scope_desc = f"Single requirement debt: {request.debt_id} ('{rows[0]['title']}')"
    elif request.target_milestone:
        cursor.execute("SELECT * FROM requirement_debts WHERE target_milestone = ?", (request.target_milestone,))
        rows = [dict(r) for r in cursor.fetchall()]
        scope_desc = f"All requirement debts for milestone: {request.target_milestone} ({len(rows)} total items)"
    else:
        cursor.execute("SELECT * FROM requirement_debts")
        rows = [dict(r) for r in cursor.fetchall()]
        scope_desc = f"Entire project portfolio ({len(rows)} total debts)"

    active_rows = [r for r in rows if r["status"].lower() not in ("resolved", "accepted permanent")]

    trajectory: List[RiskForecastPoint] = []
    horizons = sorted(list(set(request.horizons_days)))

    for offset in horizons:
        future_date = current_date + timedelta(days=offset)
        agg_risk = 0.0
        crit_count = 0
        high_count = 0
        mod_count = 0
        low_count = 0

        for r in active_rows:
            if request.scenario == "timely_review":
                # Simulated review date extended into the future
                rev_date_str = (future_date + timedelta(days=14)).isoformat()
            else:
                rev_date_str = r["review_date"]

            risk_eval = evaluate_debt_risk(
                business_impact=r["business_impact"],
                arch_impact=r["arch_impact"],
                safety_impact=r["safety_impact"],
                occurrence_prob=r["occurrence_prob"],
                detection_difficulty=r["detection_difficulty"],
                created_date_str=r["created_date"],
                review_date_str=rev_date_str,
                as_of_date=future_date,
                daily_interest_rate=request.daily_interest_rate,
            )

            agg_risk += risk_eval.dynamic_risk_score
            tier = risk_eval.risk_tier
            if tier == "Critical":
                crit_count += 1
            elif tier == "High":
                high_count += 1
            elif tier == "Moderate":
                mod_count += 1
            else:
                low_count += 1

        trajectory.append(
            RiskForecastPoint(
                horizon_days=offset,
                projected_date=future_date.isoformat(),
                aggregate_risk=round(agg_risk, 2),
                critical_count=crit_count,
                high_count=high_count,
                moderate_count=mod_count,
                low_count=low_count,
            )
        )

    assumptions = (
        f"Forecast models deterministic growth using the compounding equation R(t) = min(100, R0 * (1+r)^Δt * F_overdue). "
        f"Assumes active debts remain unresolved over time. Daily interest rate is set to {request.daily_interest_rate * 100:.2f}%. "
        f"Scenario '{request.scenario}' determines whether review schedules are observed. "
        "Limitation: Models architectural debt accumulation assumptions rather than stochastic defect arrivals."
    )

    return RiskForecastResponse(
        scope_description=scope_desc,
        scenario=request.scenario,
        daily_interest_rate=request.daily_interest_rate,
        assumptions_and_limitations=assumptions,
        trajectory=trajectory,
    )
