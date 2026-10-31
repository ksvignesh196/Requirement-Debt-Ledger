"""Presentation-critical integration checks for the main application workflows."""


def test_main_application_and_static_assets_are_served(client):
    page = client.get("/")
    assert page.status_code == 200
    assert 'id="tab-dashboard"' in page.text
    assert 'id="tab-simulator"' in page.text

    for asset in (
        "/static/js/api.js",
        "/static/js/debts.js",
        "/static/js/simulation_view.js",
        "/static/js/release_view.js",
    ):
        response = client.get(asset)
        assert response.status_code == 200
        assert response.text


def test_all_presentation_feature_endpoints_return_expected_contracts(client):
    dashboard = client.get("/api/analytics/dashboard")
    assert dashboard.status_code == 200
    assert "active_debts" in dashboard.json()

    debts = client.get("/api/debts")
    assert debts.status_code == 200
    assert len(debts.json()) >= 2

    graph = client.get("/api/dependencies/graph")
    assert graph.status_code == 200
    assert "nodes" in graph.json() and "edges" in graph.json()

    recommendations = client.get("/api/recommendations/")
    assert recommendations.status_code == 200
    recs = recommendations.json()["recommendations"]
    assert len(recs) >= 2

    pairwise = client.post("/api/recommendations/pairwise-explain", json={
        "debt_id_a": recs[0]["debt_id"],
        "debt_id_b": recs[1]["debt_id"],
    })
    assert pairwise.status_code == 200
    assert "contrastive_narrative" in pairwise.json()

    dependency = client.post("/api/simulations/dependency-impact", json={
        "debt_id": debts.json()[0]["debt_id"],
        "additional_delay_days": 30,
    })
    assert dependency.status_code == 200
    assert "portfolio_risk_delta" in dependency.json()

    what_if = client.post("/api/simulations/what-if-release", json={
        "target_milestone": "Release 1.0",
        "effort_capacity_budget": 35,
    })
    assert what_if.status_code == 200
    assert len(what_if.json()["candidate_plans"]) >= 3
    assert "status_quo" in what_if.json()

    forecast = client.post("/api/simulations/risk-forecast", json={
        "horizons_days": [0, 15, 30, 60],
        "scenario": "status_quo",
        "daily_interest_rate": 0.008,
    })
    assert forecast.status_code == 200
    assert len(forecast.json()["trajectory"]) == 4

    gates = client.get("/api/release-gates")
    assert gates.status_code == 200 and len(gates.json()) >= 1

    audit = client.get("/api/audit/verify")
    assert audit.status_code == 200
    assert audit.json()["is_valid"] is True

    csv_export = client.get("/api/export/csv")
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]


def test_release_gate_signoff_only_succeeds_after_gate_passes(client):
    blocked_gate_id = 1
    blocked = client.get(f"/api/release-gates/{blocked_gate_id}/evaluate")
    assert blocked.status_code == 200
    if blocked.json()["status"] == "BLOCKED":
        rejected = client.post(f"/api/release-gates/{blocked_gate_id}/signoff", json={
            "signoff_by": "Demo Reviewer",
            "signoff_notes": "Attempted sign-off for a blocked gate.",
        })
        assert rejected.status_code == 409

    created = client.post("/api/release-gates", json={
        "gate_name": "Presentation Demo Gate",
        "target_milestone": "Presentation Demo Release",
        "max_critical_debts": 0,
        "max_high_debts": 1,
        "max_aggregate_risk": 150,
    })
    assert created.status_code == 201
    gate_id = created.json()["id"]

    evaluated = client.get(f"/api/release-gates/{gate_id}/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["status"] == "PASSED"

    signoff = client.post(f"/api/release-gates/{gate_id}/signoff", json={
        "signoff_by": "Demo Reviewer",
        "signoff_notes": "All configured release gate checks passed.",
    })
    assert signoff.status_code == 200
    assert signoff.json()["is_ready_to_release"] is True


def test_api_documentation_pages_are_not_exposed(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_presentation_ui_uses_light_theme_without_emoji_or_api_links(client):
    import re

    page = client.get("/")
    assert page.status_code == 200
    assert "Swagger" not in page.text
    assert "/docs" not in page.text
    assert 'id="btn-reset-data"' in page.text

    stylesheet = client.get("/static/css/style.css")
    assert stylesheet.status_code == 200
    assert "color-scheme: light" in stylesheet.text

    emoji_pattern = re.compile(
        r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF\u2139\uFE0F]"
    )
    assert emoji_pattern.search(page.text) is None
    for script in (
        "/static/js/app.js",
        "/static/js/debts.js",
        "/static/js/recommendation_view.js",
        "/static/js/release_view.js",
        "/static/js/graph_view.js",
    ):
        response = client.get(script)
        assert response.status_code == 200
        assert emoji_pattern.search(response.text) is None
