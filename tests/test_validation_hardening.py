from datetime import date, timedelta


def _create_payload():
    today = date.today()
    return {
        "title": "Test requirement validation case",
        "description": "A sufficiently detailed test requirement description.",
        "module": "Test Module",
        "requirement_type": "Functional",
        "deferral_reason": "Testing validation rules",
        "deferral_phase": "Development",
        "decision_maker": "Test Lead",
        "owner": "Test Team",
        "target_milestone": "Release Test",
        "resolution_criteria": "Automated acceptance tests pass successfully.",
        "created_date": today.isoformat(),
        "review_date": (today + timedelta(days=7)).isoformat(),
        "deadline_date": (today + timedelta(days=14)).isoformat(),
    }


def test_create_rejects_impossible_calendar_date(client):
    payload = _create_payload()
    payload["review_date"] = "2026-02-30"
    response = client.post("/api/debts", json=payload)
    assert response.status_code == 422


def test_create_rejects_unsafe_custom_debt_id(client):
    payload = _create_payload()
    payload["debt_id"] = "<script>alert(1)</script>"
    response = client.post("/api/debts", json=payload)
    assert response.status_code == 422


def test_patch_rejects_unknown_status_and_direct_resolution(client):
    unknown = client.patch("/api/debts/REQ-DEBT-001", json={"status": "banana"})
    assert unknown.status_code == 422

    direct_resolve = client.patch("/api/debts/REQ-DEBT-001", json={"status": "Resolved"})
    assert direct_resolve.status_code == 422

    direct_accept = client.patch("/api/debts/REQ-DEBT-001", json={"status": "Accepted Permanent"})
    assert direct_accept.status_code == 422


def test_review_rejects_invalid_date_and_outcome(client):
    bad_date = client.post("/api/reviews", json={
        "debt_id": "REQ-DEBT-001",
        "reviewer_name": "Test Reviewer",
        "reviewer_role": "QA Lead",
        "outcome": "Retain Debt",
        "notes": "Review notes with enough detail.",
        "review_date": "2026-13-01",
    })
    assert bad_date.status_code == 422

    bad_outcome = client.post("/api/reviews", json={
        "debt_id": "REQ-DEBT-001",
        "reviewer_name": "Test Reviewer",
        "reviewer_role": "QA Lead",
        "outcome": "Mark Resolved",
        "notes": "Review notes with enough detail.",
        "review_date": date.today().isoformat(),
    })
    assert bad_outcome.status_code == 422


def test_forecast_rejects_invalid_horizon_and_scenario(client):
    bad_horizon = client.post("/api/simulations/risk-forecast", json={
        "horizons_days": [-1, 30],
        "scenario": "status_quo",
    })
    assert bad_horizon.status_code == 422

    bad_scenario = client.post("/api/simulations/risk-forecast", json={
        "horizons_days": [0, 30],
        "scenario": "invented_scenario",
    })
    assert bad_scenario.status_code == 422


def test_frontend_simulation_api_routes_match_backend(client):
    frontend = open("app/static/js/api.js", encoding="utf-8").read()
    assert '"/api/simulations/dependency-impact"' in frontend
    assert '"/api/simulations/risk-forecast"' in frontend

    dep = client.post("/api/simulations/dependency-impact", json={
        "debt_id": "REQ-DEBT-003",
        "additional_delay_days": 30,
    })
    assert dep.status_code == 200
    assert "portfolio_risk_delta" in dep.json()

    forecast = client.post("/api/simulations/risk-forecast", json={
        "horizons_days": [0, 30, 60],
        "scenario": "status_quo",
        "daily_interest_rate": 0.008,
    })
    assert forecast.status_code == 200
    assert len(forecast.json()["trajectory"]) == 3


def test_csv_export_neutralizes_formula_like_text(client, db_conn):
    from app.routers.export import _safe_csv_value

    assert _safe_csv_value("=1+1") == "'=1+1"
    assert _safe_csv_value("  =1+1") == "'  =1+1"
    assert _safe_csv_value("\t@SUM(A1:A2)") == "'\t@SUM(A1:A2)"
    assert _safe_csv_value("ordinary text") == "ordinary text"

    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Debt ID" in response.text
