"""
Automated unit and integration tests for Effort-Aware Resolution Recommendations
and Pairwise Explainability.
"""
from app.services.recommendation_engine import (
    generate_recommendations,
    explain_pairwise_recommendation,
)

def test_recommendation_ranking_and_factors(client):
    """Test recommendation generation, ranking, and explainable factor breakdown."""
    res = client.get("/api/recommendations")
    assert res.status_code == 200
    data = res.json()
    assert data["total_evaluated_debts"] > 0
    assert "weights_applied" in data
    recs = data["recommendations"]

    # Verify ranks are ordered 1, 2, ...
    for idx, r in enumerate(recs, 1):
        assert r["rank"] == idx
        if idx > 1:
            # Score must be descending
            assert recs[idx - 2]["factors"]["recommendation_score"] >= r["factors"]["recommendation_score"]

    first = recs[0]
    f = first["factors"]
    # Check that contributions sum up to gross benefit
    expected_gross = round(
        f["accumulated_risk_contrib"]
        + f["cascaded_unblock_contrib"]
        + f["business_value_contrib"]
        + f["urgency_contrib"],
        2,
    )
    assert abs(f["gross_remediation_benefit"] - expected_gross) <= 0.05
    assert first["estimated_effort"] >= 1
    assert "detailed_explanation" in first

def test_pairwise_explanation_api(client):
    """Test contrastive pairwise explanation between two requirement debts."""
    res = client.post(
        "/api/recommendations/pairwise-explain",
        json={"debt_id_a": "REQ-DEBT-002", "debt_id_b": "REQ-DEBT-007"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "higher_ranked_id" in data
    assert "lower_ranked_id" in data
    assert data["score_delta"] >= 0
    assert "contrastive_narrative" in data
    assert "comparison_matrix" in data
    assert data["higher_ranked_id"] in data["comparison_matrix"]
    assert data["lower_ranked_id"] in data["comparison_matrix"]
