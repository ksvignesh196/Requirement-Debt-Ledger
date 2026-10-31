"""
Requirement Debt Ledger (RDL) - Dependency Engine
Graph traversal, cycle detection, downstream blocked impact analysis,
Debt Priority Index (DPI), and Dependency Impact Simulation.
"""
import sqlite3
from collections import defaultdict, deque
from datetime import date, timedelta
from typing import Dict, List, Set, Tuple, Any, Optional
from fastapi import HTTPException

from app.models.debt_item import DependencyImpact
from app.models.simulation import (
    DependencySimulationResponse,
    AffectedRequirementDetail,
)
from app.services.risk_engine import parse_date, evaluate_debt_risk

class DependencyGraph:
    def __init__(self, edges: List[Tuple[str, str]]):
        """
        edges: list of (debt_id, depends_on_debt_id)
        meaning: debt_id depends on depends_on_debt_id.
        Therefore, depends_on_debt_id blocks debt_id.
        """
        # forward: debt_id -> set of dependencies it requires
        self.depends_on = defaultdict(set)
        # reverse: debt_id -> set of items it blocks
        self.blocks = defaultdict(set)
        self.all_nodes = set()

        for d_id, dep_id in edges:
            self.depends_on[d_id].add(dep_id)
            self.blocks[dep_id].add(d_id)
            self.all_nodes.add(d_id)
            self.all_nodes.add(dep_id)

    def detect_cycles(self) -> Tuple[bool, List[List[str]]]:
        """
        Detect directed cycles using DFS with recursion stack marking.
        Edges directed from dependent -> dependency.
        """
        visited = {}  # 0: unvisited, 1: visiting, 2: visited
        cycles = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            for neighbor in self.depends_on.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    # Cycle found
                    idx = path.index(neighbor) if neighbor in path else 0
                    cycles.append(path[idx:] + [neighbor])
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path + [neighbor])
            visited[node] = 2

        for node in list(self.all_nodes):
            if visited.get(node, 0) == 0:
                dfs(node, [node])

        return len(cycles) > 0, cycles

    def get_downstream_blocked(self, debt_id: str) -> Set[str]:
        """
        Find all requirements transitively blocked if this debt_id remains unresolved.
        Follows 'blocks' direction. A set prevents double-counting.
        """
        visited = set()
        queue = deque([debt_id])
        while queue:
            curr = queue.popleft()
            for blocked in self.blocks.get(curr, []):
                if blocked not in visited:
                    visited.add(blocked)
                    queue.append(blocked)
        return visited

    def get_detailed_downstream_impact(self, debt_id: str) -> Dict[str, Any]:
        """
        Traverses downstream dependencies using level-order BFS.
        Classifies affected nodes into:
        - directly affected (distance = 1)
        - indirectly affected (distance >= 2)
        Guarantees NO double-counting of nodes reachable via overlapping/diamond dependency paths.
        """
        direct_nodes = set()
        indirect_nodes = set()
        distances = {}
        visited = {debt_id}
        queue = deque([(debt_id, 0)])

        while queue:
            curr, dist = queue.popleft()
            for blocked in self.blocks.get(curr, []):
                if blocked not in visited:
                    visited.add(blocked)
                    blocked_dist = dist + 1
                    distances[blocked] = blocked_dist
                    if blocked_dist == 1:
                        direct_nodes.add(blocked)
                    else:
                        indirect_nodes.add(blocked)
                    queue.append((blocked, blocked_dist))

        all_unique = direct_nodes.union(indirect_nodes)
        max_depth = max(distances.values()) if distances else 0

        return {
            "direct_nodes": direct_nodes,
            "indirect_nodes": indirect_nodes,
            "all_unique_nodes": all_unique,
            "distances": distances,
            "max_depth": max_depth,
        }

    def get_critical_path_depth(self, debt_id: str) -> int:
        """
        Calculates longest downstream chain of requirements blocked by this debt.
        Safely bounds recursion to avoid infinite loops if cycles exist.
        """
        memo = {}
        visited = set()

        def dfs_depth(node: str) -> int:
            if node in memo:
                return memo[node]
            if node in visited:
                return 0  # avoid infinite loop on cycle
            visited.add(node)
            max_depth = 0
            for child in self.blocks.get(node, []):
                max_depth = max(max_depth, 1 + dfs_depth(child))
            visited.remove(node)
            memo[node] = max_depth
            return max_depth

        return dfs_depth(debt_id)

    def is_node_in_cycle(self, debt_id: str, cycles: List[List[str]]) -> bool:
        """Check if debt_id belongs to any detected cycle."""
        for c in cycles:
            if debt_id in c:
                return True
        return False

def load_graph(conn: sqlite3.Connection) -> DependencyGraph:
    """Load all dependencies from the database and construct graph."""
    cursor = conn.cursor()
    cursor.execute("SELECT debt_id, depends_on_debt_id FROM debt_dependencies")
    rows = cursor.fetchall()
    edges = [(r["debt_id"], r["depends_on_debt_id"]) for r in rows]
    return DependencyGraph(edges)

def calculate_dependency_impact(debt_id: str, graph: DependencyGraph) -> DependencyImpact:
    """Return dependency metrics for a given debt_id."""
    has_cycles, cycles = graph.detect_cycles()
    direct_count = len(graph.depends_on.get(debt_id, set()))
    downstream_blocked = graph.get_downstream_blocked(debt_id)
    depth = graph.get_critical_path_depth(debt_id)
    in_cycle = graph.is_node_in_cycle(debt_id, cycles)

    return DependencyImpact(
        direct_dependencies_count=direct_count,
        downstream_blocked_count=len(downstream_blocked),
        critical_path_depth=depth,
        is_in_cycle=in_cycle,
    )

def calculate_priority_index(
    dynamic_risk: float,
    downstream_blocked_count: int,
    deadline_date_str: str,
    cost_of_delay: int,
    as_of_date: Optional[date] = None,
) -> float:
    """
    Computes holistic Debt Priority Index (DPI) (0-100).
    DPI = 0.45*DynamicRisk + 0.25*DownstreamScore + 0.20*UrgencyScore + 0.10*CostOfDelayScore
    """
    current_date = as_of_date or date.today()
    deadline = parse_date(deadline_date_str)
    days_to_deadline = (deadline - current_date).days

    if days_to_deadline < 0:
        urgency_score = 100.0  # Past deadline
    elif days_to_deadline <= 7:
        urgency_score = 80.0
    elif days_to_deadline <= 21:
        urgency_score = 50.0
    else:
        urgency_score = 25.0

    # Downstream score: 5 blocked items yields 100 score
    downstream_score = min(100.0, downstream_blocked_count * 20.0)

    # Cost of delay: 1 to 5 maps to 20 to 100
    cod_score = float(max(1, min(5, cost_of_delay)) * 20.0)

    dpi = (
        0.45 * dynamic_risk
        + 0.25 * downstream_score
        + 0.20 * urgency_score
        + 0.10 * cod_score
    )
    return round(min(100.0, dpi), 2)

def simulate_dependency_impact(
    conn: sqlite3.Connection,
    debt_id: str,
    additional_delay_days: int = 30,
    as_of_date: Optional[date] = None,
) -> DependencySimulationResponse:
    """
    Simulates the cascading consequences of leaving a requirement debt unresolved.
    - Accurately computes directly and indirectly blocked requirements without double-counting.
    - Prevents cyclic infinite loops.
    - Compares current vs simulated project portfolio risk.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requirement_debts WHERE debt_id = ?", (debt_id,))
    target_row = cursor.fetchone()
    if not target_row:
        raise HTTPException(status_code=404, detail=f"Requirement debt '{debt_id}' not found.")

    target = dict(target_row)
    current_date = as_of_date or date.today()

    # Load all debts to compute portfolio baseline
    cursor.execute("SELECT * FROM requirement_debts")
    all_rows = [dict(r) for r in cursor.fetchall()]

    graph = load_graph(conn)
    has_cycle, cycles = graph.detect_cycles()
    cycle_warning = None
    if has_cycle:
        cycle_warning = f"Circular dependency detected in graph: {' -> '.join(cycles[0])}. Transitive traversal safely bounded."

    # Compute current dynamic risk of target
    current_target_risk = evaluate_debt_risk(
        business_impact=target["business_impact"],
        arch_impact=target["arch_impact"],
        safety_impact=target["safety_impact"],
        occurrence_prob=target["occurrence_prob"],
        detection_difficulty=target["detection_difficulty"],
        created_date_str=target["created_date"],
        review_date_str=target["review_date"],
        as_of_date=current_date,
    )

    # Compute simulated dynamic risk of target with additional delay days
    simulated_as_of_date = current_date + timedelta(days=additional_delay_days)
    simulated_target_risk = evaluate_debt_risk(
        business_impact=target["business_impact"],
        arch_impact=target["arch_impact"],
        safety_impact=target["safety_impact"],
        occurrence_prob=target["occurrence_prob"],
        detection_difficulty=target["detection_difficulty"],
        created_date_str=target["created_date"],
        review_date_str=target["review_date"],
        as_of_date=simulated_as_of_date,
    )

    # Calculate uncapped risk pressure for simulation visibility
    current_target_risk_pressure = round(
        current_target_risk.base_risk_score
        * current_target_risk.interest_factor
        * current_target_risk.overdue_penalty_factor,
        2
    )

    simulated_target_risk_pressure = round(
        simulated_target_risk.base_risk_score
        * simulated_target_risk.interest_factor
        * simulated_target_risk.overdue_penalty_factor,
        2
    )

    # Detailed downstream impact analysis (no double-counting)
    downstream_info = graph.get_detailed_downstream_impact(debt_id)
    direct_nodes = downstream_info["direct_nodes"]
    indirect_nodes = downstream_info["indirect_nodes"]
    all_unique_affected = downstream_info["all_unique_nodes"]
    distances = downstream_info["distances"]

    debt_lookup = {r["debt_id"]: r for r in all_rows}

    affected_requirements: List[AffectedRequirementDetail] = []
    affected_modules = set()
    cascaded_blocked_risk = 0.0

    for aff_id in sorted(all_unique_affected):
        if aff_id in debt_lookup:
            row = debt_lookup[aff_id]
            aff_risk = evaluate_debt_risk(
                business_impact=row["business_impact"],
                arch_impact=row["arch_impact"],
                safety_impact=row["safety_impact"],
                occurrence_prob=row["occurrence_prob"],
                detection_difficulty=row["detection_difficulty"],
                created_date_str=row["created_date"],
                review_date_str=row["review_date"],
                as_of_date=current_date,
            )
            dist = distances.get(aff_id, 1)
            rel_type = "Direct Blocker (Distance 1)" if dist == 1 else f"Transitive Cascade (Distance {dist})"
            affected_modules.add(row["module"])
            cascaded_blocked_risk += aff_risk.dynamic_risk_score

            affected_requirements.append(
                AffectedRequirementDetail(
                    debt_id=aff_id,
                    title=row["title"],
                    module=row["module"],
                    distance=dist,
                    dependency_relationship=rel_type,
                    current_risk=aff_risk.dynamic_risk_score,
                    risk_tier=aff_risk.risk_tier,
                    status=row["status"],
                )
            )

    # Calculate baseline and simulated portfolio risk
    active_rows = [r for r in all_rows if r["status"].lower() not in ("resolved", "accepted permanent")]
    current_portfolio_risk = sum(
        evaluate_debt_risk(
            business_impact=r["business_impact"],
            arch_impact=r["arch_impact"],
            safety_impact=r["safety_impact"],
            occurrence_prob=r["occurrence_prob"],
            detection_difficulty=r["detection_difficulty"],
            created_date_str=r["created_date"],
            review_date_str=r["review_date"],
            as_of_date=current_date,
        ).dynamic_risk_score
        for r in active_rows
    )

    # In simulation: target's risk grows to simulated_target_risk
    portfolio_risk_delta = max(0.0, simulated_target_risk.dynamic_risk_score - current_target_risk.dynamic_risk_score)
    simulated_portfolio_risk = round(current_portfolio_risk + portfolio_risk_delta, 2)
    current_portfolio_risk = round(current_portfolio_risk, 2)

    pct_increase = 0.0
    if current_portfolio_risk > 0:
        pct_increase = round((portfolio_risk_delta / current_portfolio_risk) * 100.0, 2)

    # Construct plain-English summary narrative
    narrative = (
        f"Simulating an additional {additional_delay_days}-day deferral for {debt_id} ('{target['title']}') "
        f"increases its dynamic risk from {current_target_risk.dynamic_risk_score} ({current_target_risk.risk_tier}) "
        f"to {simulated_target_risk.dynamic_risk_score} ({simulated_target_risk.risk_tier}). "
        f"This directly blocks {len(direct_nodes)} requirements and indirectly cascades to block {len(indirect_nodes)} additional requirements "
        f"across {len(affected_modules)} modules, holding {cascaded_blocked_risk:.1f} total cascaded risk in architectural limbo. "
        f"Overall project portfolio risk increases by +{portfolio_risk_delta:.1f} points (+{pct_increase}%)."
    )

    return DependencySimulationResponse(
        target_debt_id=debt_id,
        target_title=target["title"],
        target_module=target["module"],
        target_current_risk=current_target_risk.dynamic_risk_score,
        target_current_risk_pressure=current_target_risk_pressure,
        additional_delay_days=additional_delay_days,
        target_projected_risk=simulated_target_risk.dynamic_risk_score,
        target_projected_risk_pressure=simulated_target_risk_pressure,
        target_projected_tier=simulated_target_risk.risk_tier,
        direct_blocked_count=len(direct_nodes),
        indirect_blocked_count=len(indirect_nodes),
        total_unique_affected_count=len(all_unique_affected),
        affected_modules=sorted(list(affected_modules)),
        affected_requirements=affected_requirements,
        has_cycle=has_cycle,
        cycle_warning=cycle_warning,
        cascaded_blocked_risk=round(cascaded_blocked_risk, 2),
        current_portfolio_risk=current_portfolio_risk,
        simulated_portfolio_risk=simulated_portfolio_risk,
        portfolio_risk_delta=round(portfolio_risk_delta, 2),
        portfolio_risk_increase_percent=pct_increase,
        summary_narrative=narrative,
    )
