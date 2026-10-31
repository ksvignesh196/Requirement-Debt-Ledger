"""
Requirement Debt Ledger (RDL) - Empirical Evaluation Harness
Reproducible Benchmarking against FIFO and Static Severity Baselines across Realistic Dependency Topologies
"""
import time
import math
import sqlite3
import random
from typing import List, Dict, Any, Tuple
from datetime import date, timedelta

# Import RDL internal services
from app.services.risk_engine import evaluate_debt_risk
from app.services.dependency_engine import DependencyGraph

def create_synthetic_item(
    item_id: str,
    title: str,
    base_severity: int,
    occurrence: int,
    detection: int,
    elapsed_days: int,
    overdue_days: int,
    effort: int,
    milestone: str = "Release 1.0",
) -> Dict[str, Any]:
    """Creates a synthetic requirement debt record."""
    created_str = str(date.today() - timedelta(days=elapsed_days))
    review_str = str(date.today() - timedelta(days=overdue_days))

    risk_info = evaluate_debt_risk(
        business_impact=base_severity,
        arch_impact=base_severity,
        safety_impact=base_severity,
        occurrence_prob=occurrence,
        detection_difficulty=detection,
        created_date_str=created_str,
        review_date_str=review_str,
    )
    return {
        "debt_id": item_id,
        "title": title,
        "module": "SyntheticCore",
        "requirement_type": "Functional",
        "deferral_reason": "Time Constraint",
        "deferral_phase": "Development",
        "decision_maker": "Architect",
        "owner": "Core Squad",
        "target_milestone": milestone,
        "resolution_criteria": "Unit tests pass",
        "status": "Deferred",
        "created_date": created_str,
        "review_date": review_str,
        "deadline_date": str(date.today() + timedelta(days=30)),
        "business_impact": base_severity,
        "arch_impact": base_severity,
        "safety_impact": base_severity,
        "occurrence_prob": occurrence,
        "detection_difficulty": detection,
        "cost_of_delay": base_severity,
        "estimated_effort": effort,
        "dynamic_risk": risk_info.dynamic_risk_score,
        "base_risk": risk_info.base_risk_score,
        "elapsed_days": elapsed_days,
        "overdue_days": overdue_days,
    }

def build_benchmark_project() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]]]:
    """
    Constructs a 15-node benchmark project containing:
    - 1 Diamond dependency cluster (DEBT-101 blocks 102 & 103, both block 104, 104 blocks 105)
    - 1 Deep linear cascade (DEBT-201 -> 202 -> 203 -> 204)
    - Independent quick-wins (high ROI, low effort)
    - Independent large low-risk epics (high effort, low risk)
    """
    items = {
        # Diamond Cluster
        "DEBT-101": create_synthetic_item("DEBT-101", "Core Message Bus", 5, 4, 3, 45, 15, 8),
        "DEBT-102": create_synthetic_item("DEBT-102", "Billing Event Producer", 4, 3, 3, 30, 0, 5),
        "DEBT-103": create_synthetic_item("DEBT-103", "Audit Event Producer", 4, 3, 3, 30, 0, 5),
        "DEBT-104": create_synthetic_item("DEBT-104", "Central Event Stream Consumer", 4, 4, 4, 20, 0, 8),
        "DEBT-105": create_synthetic_item("DEBT-105", "Analytics Dashboard Realtime Feed", 3, 2, 2, 10, 0, 13),

        # Linear Cascade
        "DEBT-201": create_synthetic_item("DEBT-201", "Auth Token Validator", 5, 5, 4, 60, 25, 5),
        "DEBT-202": create_synthetic_item("DEBT-202", "Role-Based Access Guard", 4, 4, 3, 35, 5, 8),
        "DEBT-203": create_synthetic_item("DEBT-203", "Tenant Scoping Middleware", 4, 3, 3, 25, 0, 5),
        "DEBT-204": create_synthetic_item("DEBT-204", "Cross-Tenant Audit Reporter", 3, 2, 2, 15, 0, 8),

        # Quick Wins (High ROI, Low Effort)
        "DEBT-301": create_synthetic_item("DEBT-301", "API Rate Limiter Fix", 4, 4, 3, 40, 10, 3),
        "DEBT-302": create_synthetic_item("DEBT-302", "Session Timeout Config", 3, 3, 2, 20, 0, 2),

        # Heavy Low-Risk Epics (High Effort, Low Immediate Risk)
        "DEBT-401": create_synthetic_item("DEBT-401", "Legacy DB Schema Normalization", 2, 2, 2, 15, 0, 21),
        "DEBT-402": create_synthetic_item("DEBT-402", "Bulk Export PDF Re-Skinning", 2, 1, 1, 10, 0, 13),

        # Miscellaneous Moderate Items
        "DEBT-501": create_synthetic_item("DEBT-501", "Webhook Retry Backoff", 3, 3, 3, 28, 0, 5),
        "DEBT-502": create_synthetic_item("DEBT-502", "Cache Eviction Policy", 3, 3, 3, 25, 0, 5),
    }

    graph = {k: [] for k in items}
    # Diamond: 101 blocks 102 & 103; 102 blocks 104; 103 blocks 104; 104 blocks 105
    graph["DEBT-101"] = ["DEBT-102", "DEBT-103"]
    graph["DEBT-102"] = ["DEBT-104"]
    graph["DEBT-103"] = ["DEBT-104"]
    graph["DEBT-104"] = ["DEBT-105"]

    # Linear: 201 blocks 202; 202 blocks 203; 203 blocks 204
    graph["DEBT-201"] = ["DEBT-202"]
    graph["DEBT-202"] = ["DEBT-203"]
    graph["DEBT-203"] = ["DEBT-204"]

    return items, graph

def evaluate_baseline_fifo(items: Dict[str, Dict[str, Any]]) -> List[str]:
    """Baseline 1: Prioritizes by age / creation date (oldest first)."""
    sorted_items = sorted(items.values(), key=lambda x: x["elapsed_days"], reverse=True)
    return [x["debt_id"] for x in sorted_items]

def evaluate_baseline_static_severity(items: Dict[str, Dict[str, Any]]) -> List[str]:
    """Baseline 2: Prioritizes purely by static base risk / severity."""
    sorted_items = sorted(items.values(), key=lambda x: x["base_risk"], reverse=True)
    return [x["debt_id"] for x in sorted_items]

def evaluate_proposed_rdl(items: Dict[str, Dict[str, Any]], graph: Dict[str, List[str]]) -> List[str]:
    """Proposed RDL: Prioritizes using Effort-Aware MCDM recommendation score."""
    scored = []
    for debt_id, item in items.items():
        # BFS downstream impact with diamond deduplication
        visited = set()
        queue = [(debt_id, 0)]
        while queue:
            curr, dist = queue.pop(0)
            for neighbor in graph.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        downstream_count = len(visited)

        # Dynamic risk score
        dyn_risk = item["dynamic_risk"]
        effort = item["estimated_effort"]

        # MCDM Factors: Risk (35%), Cascade Unblock (30%), Business Impact (20%), Urgency (15%)
        risk_score = min(100.0, dyn_risk)
        unblock_score = min(100.0, downstream_count * 25.0)
        biz_score = min(100.0, item["business_impact"] * 20.0)
        urg_score = min(100.0, max(0.0, item["overdue_days"] * 5.0 + 20.0))

        gross_benefit = (
            0.35 * risk_score +
            0.30 * unblock_score +
            0.20 * biz_score +
            0.15 * urg_score
        )
        effort_factor = round(effort ** 0.70, 2)
        roi = round((gross_benefit / effort_factor) * 5.0, 2)
        scored.append((debt_id, roi))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in scored]


def count_newly_unblocked(
    resolved_ids: List[str],
    items: Dict[str, Dict[str, Any]],
    graph: Dict[str, List[str]],
) -> int:
    """Count dependent requirements whose complete prerequisite set is resolved by the selected work."""
    selected = set(resolved_ids)
    already_resolved = {
        debt_id for debt_id, item in items.items()
        if str(item.get("status", "")).lower() in ("resolved", "accepted permanent")
    }
    resolved_after = already_resolved | selected
    prerequisites: Dict[str, set] = {}
    for blocker_id, dependent_ids in graph.items():
        for dependent_id in dependent_ids:
            prerequisites.setdefault(dependent_id, set()).add(blocker_id)

    newly_unblocked = 0
    for dependent_id, required_ids in prerequisites.items():
        if dependent_id in selected:
            continue
        blocked_before = any(req_id not in already_resolved for req_id in required_ids)
        blocked_after = any(req_id not in resolved_after for req_id in required_ids)
        if blocked_before and not blocked_after:
            newly_unblocked += 1
    return newly_unblocked

def simulate_budget_execution(
    ranking: List[str],
    items: Dict[str, Dict[str, Any]],
    graph: Dict[str, List[str]],
    effort_budget: int = 35,
) -> Dict[str, Any]:
    """
    Simulates remediation of requirements within an effort budget (e.g. 35 story points).
    Tracks:
    - Total risk points eliminated
    - Total story points spent
    - Risk reduction efficiency (Risk eliminated / Effort spent)
    - Total downstream requirements unblocked
    - Number of resolved items
    """
    spent_effort = 0
    eliminated_risk = 0.0
    resolved_ids = []
    for debt_id in ranking:
        item = items[debt_id]
        if spent_effort + item["estimated_effort"] <= effort_budget:
            spent_effort += item["estimated_effort"]
            eliminated_risk += item["dynamic_risk"]
            resolved_ids.append(debt_id)


    unblocked_count = count_newly_unblocked(resolved_ids, items, graph)
    efficiency = round(eliminated_risk / spent_effort, 3) if spent_effort > 0 else 0.0

    return {
        "resolved_count": len(resolved_ids),
        "resolved_ids": resolved_ids,
        "spent_effort": spent_effort,
        "eliminated_risk": round(eliminated_risk, 1),
        "efficiency_ratio": efficiency,
        "unblocked_count": unblocked_count,
    }

def benchmark_graph_scalability() -> Dict[int, Dict[str, float]]:
    """
    Benchmarks algorithm execution time (cycle detection & BFS cascade traversal)
    across graph sizes: 50, 200, 500, 1000 nodes.
    """
    scales = [50, 200, 500, 1000]
    timings = {}

    for n in scales:
        # Generate random DAG (edges only from lower to higher index to ensure acyclic baseline)
        graph = {f"N_{i}": [] for i in range(n)}
        random.seed(42)
        edge_count = n * 2  # Average branching factor of 2

        for _ in range(edge_count):
            u = random.randint(0, n - 2)
            v = random.randint(u + 1, min(n - 1, u + 20))
            if f"N_{v}" not in graph[f"N_{u}"]:
                graph[f"N_{u}"].append(f"N_{v}")

        # Benchmark 1: Cycle Detection (DFS/BFS traversal)
        t0 = time.perf_counter()
        for i in range(50):
            # Test inserting an edge that might or might not form a cycle
            target = f"N_{i % n}"
            source = f"N_{(i + 5) % n}"
            # Check if reachable
            visited = set()
            q = [target]
            is_reachable = False
            while q:
                c = q.pop(0)
                if c == source:
                    is_reachable = True
                    break
                for nb in graph.get(c, []):
                    if nb not in visited:
                        visited.add(nb)
                        q.append(nb)
        t_cycle = (time.perf_counter() - t0) / 50 * 1000.0  # ms per check

        # Benchmark 2: Downstream Blast Radius Traversal (BFS with distance tracking)
        t0 = time.perf_counter()
        for i in range(50):
            root = f"N_{i % n}"
            visited = set()
            q = [(root, 0)]
            while q:
                c, d = q.pop(0)
                for nb in graph.get(c, []):
                    if nb not in visited:
                        visited.add(nb)
                        q.append((nb, d + 1))
        t_bfs = (time.perf_counter() - t0) / 50 * 1000.0  # ms per traversal

        timings[n] = {
            "node_count": n,
            "edge_count": edge_count,
            "cycle_detection_ms": round(t_cycle, 4),
            "bfs_cascade_ms": round(t_bfs, 4),
        }

    return timings

def run_evaluation():
    print("=" * 70)
    print("  REQUIREMENT DEBT LEDGER (RDL) - EMPIRICAL EVALUATION SUITE")
    print("=" * 70)

    items, graph = build_benchmark_project()
    total_project_risk = sum(item["dynamic_risk"] for item in items.values())
    print(f"\n1. Benchmark Synthetic Project Initialized:")
    print(f"   - Total Requirement Debt Items: {len(items)}")
    print(f"   - Aggregate Portfolio Dynamic Risk: {round(total_project_risk, 1)} pts")
    print(f"   - Dependency Topologies: Diamond Bottleneck, Linear Cascades, Disjoint Epics")

    # Evaluate Policies under various Sprint Effort Budgets
    budgets = [15, 25, 35]
    budget_results = {}

    for b in budgets:
        print(f"\n2. Evaluating Policies under Sprint Capacity Budget = {b} Story Points:")

        fifo_ranking = evaluate_baseline_fifo(items)
        fifo_res = simulate_budget_execution(fifo_ranking, items, graph, effort_budget=b)

        static_ranking = evaluate_baseline_static_severity(items)
        static_res = simulate_budget_execution(static_ranking, items, graph, effort_budget=b)

        rdl_ranking = evaluate_proposed_rdl(items, graph)
        rdl_res = simulate_budget_execution(rdl_ranking, items, graph, effort_budget=b)

        print(f"   [FIFO]   Resolved: {fifo_res['resolved_count']} | Risk Eliminated: {fifo_res['eliminated_risk']} pts | Unblocked: {fifo_res['unblocked_count']}")
        print(f"   [STATIC] Resolved: {static_res['resolved_count']} | Risk Eliminated: {static_res['eliminated_risk']} pts | Unblocked: {static_res['unblocked_count']}")
        print(f"   [RDL]    Resolved: {rdl_res['resolved_count']} | Risk Eliminated: {rdl_res['eliminated_risk']} pts | Unblocked: {rdl_res['unblocked_count']}")

        budget_results[b] = {
            "fifo": fifo_res,
            "static": static_res,
            "rdl": rdl_res,
        }

    # Scalability Timings
    print(f"\n4. Benchmarking Algorithmic Scalability (50 to 1,000 nodes):")
    timings = benchmark_graph_scalability()
    for n, data in timings.items():
        print(f"   - N={n:4d} nodes | Edges={data['edge_count']:4d} | Cycle Check: {data['cycle_detection_ms']:.4f} ms | BFS Traversal: {data['bfs_cascade_ms']:.4f} ms")

    return {
        "total_risk": total_project_risk,
        "budget_results": budget_results,
        "timings": timings,
    }

if __name__ == "__main__":
    results = run_evaluation()
