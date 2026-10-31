import pytest
from fastapi.testclient import TestClient

def test_cors_trusted_origin(client: TestClient):
    """Verify that requests from an explicitly configured trusted origin receive CORS allow headers."""
    response = client.options(
        "/api/debts/",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:8000"

def test_cors_untrusted_origin_rejected(client: TestClient):
    """Verify that untrusted arbitrary origins do not receive CORS allow headers."""
    response = client.options(
        "/api/debts/",
        headers={
            "Origin": "http://evil-attacker.example.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    # When an origin is untrusted, CORS middleware does not attach access-control-allow-origin
    assert response.headers.get("access-control-allow-origin") != "http://evil-attacker.example.com"

def test_input_validation_negative_values(client: TestClient):
    """Verify that negative impact, probability, or effort are rejected with 422 Unprocessable Entity."""
    # Negative business impact
    bad_payload = {
        "title": "Invalid Negative Impact Item",
        "description": "Should fail validation",
        "deferred_requirement": "Req spec",
        "deferral_reason": "Testing validation",
        "responsible_party": "Test Engineer",
        "resolution_condition": "Fix it",
        "target_resolution_date": "2026-12-31",
        "business_impact": -5,
        "probability_of_default": 0.5,
        "estimated_effort": 8
    }
    resp = client.post("/api/debts/", json=bad_payload)
    assert resp.status_code == 422

    # Probability > 1.0
    bad_payload["business_impact"] = 50
    bad_payload["probability_of_default"] = 1.5
    resp = client.post("/api/debts/", json=bad_payload)
    assert resp.status_code == 422

    # Negative effort
    bad_payload["probability_of_default"] = 0.5
    bad_payload["estimated_effort"] = -10
    resp = client.post("/api/debts/", json=bad_payload)
    assert resp.status_code == 422

    # Effort > 100
    bad_payload["estimated_effort"] = 250
    resp = client.post("/api/debts/", json=bad_payload)
    assert resp.status_code == 422

def test_input_validation_invalid_date_format(client: TestClient):
    """Verify that invalid date formats are rejected."""
    bad_date_payload = {
        "title": "Invalid Date Item",
        "description": "Testing date format",
        "deferred_requirement": "Req spec",
        "deferral_reason": "Testing validation",
        "responsible_party": "Test Engineer",
        "resolution_condition": "Fix it",
        "target_resolution_date": "12/31/2026", # Invalid format (not YYYY-MM-DD)
        "business_impact": 50,
        "probability_of_default": 0.5,
        "estimated_effort": 8
    }
    resp = client.post("/api/debts/", json=bad_date_payload)
    assert resp.status_code == 422

def test_404_error_handling_for_missing_records(client: TestClient):
    """Verify that querying or operating on missing records returns structured 404."""
    # Non-existent debt GET
    resp = client.get("/api/debts/999999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

    # Non-existent debt DELETE
    resp = client.delete("/api/debts/999999")
    assert resp.status_code == 404

    # Non-existent debt Resolve
    resp = client.post("/api/debts/999999/resolve", json={
        "resolution_type": "Implemented & Verified",
        "resolution_notes": "Implemented and verified in staging",
        "resolved_by": "Test Lead"
    })
    assert resp.status_code == 404

    # Non-existent debt Review
    resp = client.post("/api/reviews/", json={
        "debt_id": "DEBT-DOES-NOT-EXIST-999",
        "reviewer_name": "Alice QA",
        "reviewer_role": "QA Lead",
        "outcome": "Retain Debt",
        "notes": "Testing review on missing record"
    })
    assert resp.status_code == 404

    # Non-existent debt Dependency Simulation
    resp = client.post("/api/simulations/dependency", json={
        "debt_id": 999999,
        "additional_delay_days": 30
    })
    assert resp.status_code == 404

def test_pairwise_recommendation_identical_ids_rejected(client: TestClient):
    """Verify that comparing a debt to itself in pairwise explanation returns 400."""
    resp = client.post(
        "/api/recommendations/pairwise-explain",
        json={"debt_id_a": "DEBT-AUTH-001", "debt_id_b": "DEBT-AUTH-001"}
    )
    assert resp.status_code == 400
    assert "different" in resp.json()["detail"].lower()
