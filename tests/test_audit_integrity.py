"""
Automated unit and integration tests for Cryptographic Tamper-Evident Audit Logging.
"""
from app.services.audit_service import log_audit, verify_audit_integrity

def test_audit_chain_valid_on_seeded_db(db_conn):
    """Test that audit log verification succeeds on untampered log."""
    res = verify_audit_integrity(db_conn)
    assert res["is_valid"] is True
    assert res["tampered_count"] == 0
    assert len(res["tampered_entries"]) == 0
    assert res["total_entries"] > 0
    assert res["latest_hash"] is not None

def test_audit_chain_tamper_detection(db_conn):
    """
    Test that tampering with an audit record's content directly in SQLite
    breaks the SHA-256 hash chain and is immediately detected.
    """
    # 1. Add legitimate log entry
    inserted_id = log_audit(
        conn=db_conn,
        debt_id="REQ-DEBT-001",
        action="TEST_ACTION",
        performed_by="Tester",
        details="Original legitimate audit detail",
    )

    # Verify log is valid before tampering
    res_before = verify_audit_integrity(db_conn)
    assert res_before["is_valid"] is True

    # 2. Tamper with the details directly in SQL without updating the cryptographic hash
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE audit_log SET details = 'MALICIOUS UNAUTHORIZED MODIFICATION' WHERE id = ?",
        (inserted_id,),
    )
    db_conn.commit()

    # 3. Verify integrity check flags the tampered record
    res_after = verify_audit_integrity(db_conn)
    assert res_after["is_valid"] is False
    assert res_after["tampered_count"] >= 1
    flagged_ids = [e["id"] for e in res_after["tampered_entries"]]
    assert inserted_id in flagged_ids

def test_audit_verify_api(client):
    """Test the GET /api/audit/verify endpoint."""
    res = client.get("/api/audit/verify")
    assert res.status_code == 200
    data = res.json()
    assert "is_valid" in data
    assert "total_entries" in data
    assert "summary" in data
