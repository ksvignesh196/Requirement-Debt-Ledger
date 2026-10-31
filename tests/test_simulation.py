"""
Automated unit and integration tests for Dependency Impact Simulation,
What-If Release Planning, and Risk Forecasting.
"""
from datetime import date, timedelta
from app.services.dependency_engine import simulate_dependency_impact, DependencyGraph
from app.services.simulation_engine import (
    evaluate_plan_in_sandbox,
    run_what_if_release_planning,
    apply_what_if_plan,
    run_risk_forecasting,
)
from app.models.simulation import WhatIfReleasePlanRequest, RiskForecastRequest

def test_diamond_dependency_no_double_counting():
    """
    Test diamond dependency:
    A blocks B and C. Both B and C block D.
    A's downstream affected requirements must be {B, C, D} (exactly 3 unique, no duplicates).
    Direct: {B, C} (distance 1)
    Indirect: {D} (distance 2)
    """
    edges = [
        ("B", "A"),
        ("C", "A"),
        ("D", "B"),
        ("D", "C"),
    ]
    graph = DependencyGraph(edges)
    info = graph.get_detailed_downstream_impact("A")

    assert info["direct_nodes"] == {"B", "C"}
    assert info["indirect_nodes"] == {"D"}
    assert info["all_unique_nodes"] == {"B", "C", "D"}
    assert len(info["all_unique_nodes"]) == 3
    assert info["distances"]["B"] == 1
    assert info["distances"]["C"] == 1
    assert info["distances"]["D"] == 2
    assert info["max_depth"] == 2

def test_dependency_simulation_api(client):
    """Test dependency impact simulation endpoint."""
    res = client.post(
        "/api/simulations/dependency-impact",
        json={"debt_id": "REQ-DEBT-003", "additional_delay_days": 30},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["target_debt_id"] == "REQ-DEBT-003"
    assert data["direct_blocked_count"] >= 1
    assert data["total_unique_affected_count"] >= 1
    assert data["simulated_portfolio_risk"] >= data["current_portfolio_risk"]
    assert "summary_narrative" in data
    assert not data["has_cycle"]

def test_what_if_release_planning_isolation(client, db_conn):
    """
    Test what-if release planning:
    Simulations must evaluate alternatives without modifying actual database records!
    """
    # Count open debts before simulation
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM requirement_debts WHERE status = 'Deferred'")
    deferred_before = cursor.fetchone()[0]

    res = client.post(
        "/api/simulations/what-if-release",
        json={
            "target_milestone": "Release 1.0",
            "effort_capacity_budget": 25,
            "custom_plan_name": "Custom Candidate",
            "custom_resolved_debt_ids": ["REQ-DEBT-001", "REQ-DEBT-003"],
        },
    )
    assert res.status_code == 200
    plan_data = res.json()
    assert plan_data["target_milestone"] == "Release 1.0"
    assert len(plan_data["candidate_plans"]) >= 3
    assert "isolation_guarantee" in plan_data

    # Verify database state was NOT modified
    cursor.execute("SELECT COUNT(*) FROM requirement_debts WHERE status = 'Deferred'")
    deferred_after = cursor.fetchone()[0]
    assert deferred_before == deferred_after

def test_apply_what_if_plan(client, db_conn):
    """Test explicitly applying a what-if plan updates records and writes an audit event."""
    res = client.post(
        "/api/simulations/apply-plan",
        json={
            "target_milestone": "Release 2.0",
            "resolved_debt_ids": ["REQ-DEBT-006"],
            "actor_name": "Release Manager",
            "rationale": "Verified automated circuit breaker tests passed.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "Started remediation" in data["message"]
    assert data["updated_count"] == 1

    # Applying a plan starts work; it must not falsely claim implementation is verified.
    cursor = db_conn.cursor()
    cursor.execute("SELECT status, resolution_type, resolved_date FROM requirement_debts WHERE debt_id = 'REQ-DEBT-006'")
    row = cursor.fetchone()
    assert row["status"] == "Remediating"
    assert row["resolution_type"] is None
    assert row["resolved_date"] is None

def test_risk_forecasting_portfolio(client):
    """Test portfolio-wide risk forecast under status quo and timely review scenarios."""
    res = client.post(
        "/api/simulations/risk-forecast",
        json={
            "horizons_days": [0, 30, 60, 90],
            "scenario": "status_quo",
            "daily_interest_rate": 0.008,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["trajectory"]) == 4
    # Status quo risk should grow monotonically over time
    risks = [p["aggregate_risk"] for p in data["trajectory"]]
    assert risks[3] >= risks[0]
    assert "assumptions_and_limitations" in data


def test_dependency_simulation_counts_fully_unblocked_nodes_only():
    from evaluation import count_newly_unblocked

    items = {
        "A": {"status": "Deferred"},
        "B": {"status": "Deferred"},
        "C": {"status": "Deferred"},
        "D": {"status": "Deferred"},
    }
    graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}

    # Resolving A removes the blocker from B and C, but not from D.
    assert count_newly_unblocked(["A"], items, graph) == 2
    # Resolving only B is not enough to unblock D because C remains unresolved.
    assert count_newly_unblocked(["B"], items, graph) == 0
    # Resolving both B and C fully unblocks D once, not twice.
    assert count_newly_unblocked(["B", "C"], items, graph) == 1
