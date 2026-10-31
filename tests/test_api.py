"""
End-to-end API integration tests for FastAPI endpoints
"""
from datetime import date, timedelta

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

def test_api_list_debts(client):
    res = client.get("/api/debts")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 10
    # Check fields
    first = data[0]
    assert "debt_id" in first
    assert "risk" in first
    assert "dynamic_risk_score" in first["risk"]
    assert "dependency_impact" in first
    assert "debt_priority_index" in first

def test_api_filter_debts(client):
    res = client.get("/api/debts?status=Resolved")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2
    for item in data:
        assert item["status"] == "Resolved"

def test_api_create_and_delete_debt(client):
    today = date.today()
    payload = {
        "title": "Automated Kafka Event Schema Validation",
        "description": "Avro schemas are currently not strictly enforced at producer boundary.",
        "module": "Event Bus",
        "requirement_type": "Architectural",
        "deferral_reason": "Technical Uncertainty",
        "deferral_phase": "Development",
        "decision_maker": "Data Architect",
        "owner": "Streaming Squad",
        "target_milestone": "Release 2.0",
        "resolution_criteria": "Integrate Confluent Schema Registry with CI pre-commit hooks.",
        "created_date": today.isoformat(),
        "review_date": (today + timedelta(days=14)).isoformat(),
        "deadline_date": (today + timedelta(days=30)).isoformat(),
        "business_impact": 3,
        "arch_impact": 4,
        "safety_impact": 3,
        "occurrence_prob": 3,
        "detection_difficulty": 3,
        "cost_of_delay": 3,
    }

    res = client.post("/api/debts", json=payload)
    assert res.status_code == 201
    created = res.json()
    debt_id = created["debt_id"]
    assert debt_id.startswith("REQ-DEBT-")

    # Fetch created
    res2 = client.get(f"/api/debts/{debt_id}")
    assert res2.status_code == 200
    assert res2.json()["title"] == payload["title"]

    # Delete
    res3 = client.delete(f"/api/debts/{debt_id}")
    assert res3.status_code == 200

    # Verify not found
    res4 = client.get(f"/api/debts/{debt_id}")
    assert res4.status_code == 404

def test_api_resolve_debt(client):
    res = client.post(
        "/api/debts/REQ-DEBT-001/resolve",
        json={
            "resolution_type": "Implemented & Verified",
            "resolution_notes": "Integrated Bloomberg FX real-time ticker; passed multi-currency automated reconciliation suite.",
            "resolved_by": "Senior Architect",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Resolved"
    assert data["resolution_type"] == "Implemented & Verified"

def test_api_dependency_cycle_prevention(client):
    # REQ-001 depends on REQ-003, REQ-003 depends on REQ-005
    # If we attempt to make REQ-005 depend on REQ-001, it must be rejected!
    res = client.post(
        "/api/dependencies",
        json={
            "debt_id": "REQ-DEBT-005",
            "depends_on_debt_id": "REQ-DEBT-001",
            "dependency_type": "Blocks",
            "notes": "Testing cycle detection",
        },
    )
    assert res.status_code == 400
    assert "cyclic dependency loop" in res.json()["detail"].lower()

def test_api_dependency_graph(client):
    res = client.get("/api/dependencies/graph")
    assert res.status_code == 200
    graph = res.json()
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) >= 10
    assert len(graph["edges"]) >= 3
    assert not graph["has_cycle"]

def test_api_record_review(client):
    today = date.today()
    res = client.post(
        "/api/reviews",
        json={
            "debt_id": "REQ-DEBT-005",
            "reviewer_name": "Security Auditor",
            "reviewer_role": "External Pen Tester",
            "outcome": "Extend Review Date",
            "notes": "Agreed to postpone RBAC token migration until after microservice proxy refactor.",
            "new_review_date": (today + timedelta(days=20)).isoformat(),
        },
    )
    assert res.status_code == 201
    assert res.json()["outcome"] == "Extend Review Date"

def test_api_audit_log(client):
    res = client.get("/api/audit")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert "action" in logs[0]
    assert "performed_by" in logs[0]

def test_api_dashboard_analytics(client):
    res = client.get("/api/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_debts" in data
    assert "active_debts" in data
    assert "critical_debts" in data
    assert "risk_distribution" in data
    assert "top_urgent_debts" in data

def test_api_risk_simulation(client):
    res = client.post(
        "/api/debts/simulate/risk",
        json={
            "business_impact": 5,
            "arch_impact": 5,
            "safety_impact": 5,
            "occurrence_prob": 5,
            "detection_difficulty": 5,
            "created_date": "2026-08-01",
            "review_date": "2026-09-01",
        },
    )
    assert res.status_code == 200
    sim = res.json()
    assert sim["base_risk_score"] == 100.0
    assert sim["dynamic_risk_score"] == 100.0
    assert sim["risk_tier"] == "Critical"
    assert "explanation" in sim

def test_api_export_csv(client):
    res = client.get("/api/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "Debt ID,Title" in res.text
