"""
Unit tests for Dependency Graph Engine and Debt Priority Index
"""
from datetime import date, timedelta
from app.services.dependency_engine import (
    DependencyGraph,
    calculate_priority_index,
)

def test_dependency_graph_cycle_detection():
    # Acyclic graph: A depends on B, B depends on C
    acyclic_edges = [("A", "B"), ("B", "C")]
    graph = DependencyGraph(acyclic_edges)
    has_cycle, cycles = graph.detect_cycles()
    assert not has_cycle
    assert len(cycles) == 0

    # Cyclic graph: A depends on B, B depends on C, C depends on A
    cyclic_edges = [("A", "B"), ("B", "C"), ("C", "A")]
    c_graph = DependencyGraph(cyclic_edges)
    has_cycle, cycles = c_graph.detect_cycles()
    assert has_cycle
    assert len(cycles) > 0

def test_downstream_blocked_traversal():
    # A depends on B, C depends on B, D depends on A
    # Therefore B blocks A, C, and transitively D!
    edges = [("A", "B"), ("C", "B"), ("D", "A")]
    graph = DependencyGraph(edges)

    blocked_by_b = graph.get_downstream_blocked("B")
    assert blocked_by_b == {"A", "C", "D"}

    blocked_by_a = graph.get_downstream_blocked("A")
    assert blocked_by_a == {"D"}

    blocked_by_d = graph.get_downstream_blocked("D")
    assert blocked_by_d == set()

def test_critical_path_depth():
    # Path: D -> C -> B -> A (D depends on C, C depends on B, B depends on A)
    # Block direction: A blocks B blocks C blocks D (depth 3)
    edges = [("B", "A"), ("C", "B"), ("D", "C")]
    graph = DependencyGraph(edges)

    assert graph.get_critical_path_depth("A") == 3
    assert graph.get_critical_path_depth("B") == 2
    assert graph.get_critical_path_depth("C") == 1
    assert graph.get_critical_path_depth("D") == 0

def test_calculate_priority_index():
    today = date(2026, 10, 16)
    # Deadline in 5 days (urgent: score 80)
    deadline = (today + timedelta(days=5)).isoformat()

    dpi = calculate_priority_index(
        dynamic_risk=50.0,
        downstream_blocked_count=2,
        deadline_date_str=deadline,
        cost_of_delay=4,
        as_of_date=today,
    )

    # 0.45 * 50 = 22.5
    # 0.25 * min(100, 2 * 20) = 0.25 * 40 = 10.0
    # 0.20 * 80 = 16.0
    # 0.10 * (4 * 20) = 8.0
    # Total = 22.5 + 10.0 + 16.0 + 8.0 = 56.5
    assert dpi == 56.5
