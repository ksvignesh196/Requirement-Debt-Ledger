"""
Requirement Debt Ledger (RDL) - Traceable, Tamper-Evident Audit Service
Logs all state changes, risk recalculations, review meetings, and release gate actions
using cryptographic SHA-256 hash chaining to ensure tamper-evident verification.
"""
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import AUDIT_GENESIS_PREV_HASH

def _compute_entry_hash(
    prev_hash: str,
    entry_id: int,
    debt_id: Optional[str],
    action: str,
    performed_by: str,
    details: str,
    created_at: str,
) -> str:
    """Compute deterministic SHA-256 hash for an audit log entry."""
    payload = f"{prev_hash}|{entry_id}|{debt_id or ''}|{action}|{performed_by}|{details}|{created_at}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def log_audit(
    conn: sqlite3.Connection,
    debt_id: Optional[str],
    action: str,
    performed_by: str,
    details: str,
) -> int:
    """
    Insert a tamper-evident audit log event cryptographically linked to the previous entry.
    """
    now_iso = datetime.now().isoformat()
    cursor = conn.cursor()

    # Retrieve the hash of the latest entry
    cursor.execute("SELECT id, entry_hash FROM audit_log ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    prev_hash = last_row["entry_hash"] if last_row and last_row["entry_hash"] else AUDIT_GENESIS_PREV_HASH

    # Insert initial record to obtain auto-generated id
    cursor.execute(
        """
        INSERT INTO audit_log (debt_id, action, performed_by, details, created_at, prev_hash, entry_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (debt_id, action, performed_by, details, now_iso, prev_hash, ""),
    )
    inserted_id = cursor.lastrowid

    # Compute entry hash incorporating the inserted_id
    entry_hash = _compute_entry_hash(
        prev_hash=prev_hash,
        entry_id=inserted_id,
        debt_id=debt_id,
        action=action,
        performed_by=performed_by,
        details=details,
        created_at=now_iso,
    )

    # Commit entry hash
    cursor.execute(
        "UPDATE audit_log SET entry_hash = ? WHERE id = ?",
        (entry_hash, inserted_id),
    )
    conn.commit()
    return inserted_id

def get_audit_trail(
    conn: sqlite3.Connection,
    debt_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve audit events, optionally filtered by debt_id."""
    cursor = conn.cursor()
    if debt_id:
        cursor.execute(
            """
            SELECT id, debt_id, action, performed_by, details, created_at, prev_hash, entry_hash
            FROM audit_log
            WHERE debt_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (debt_id, limit),
        )
    else:
        cursor.execute(
            """
            SELECT id, debt_id, action, performed_by, details, created_at, prev_hash, entry_hash
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
    rows = cursor.fetchall()
    return [dict(r) for r in rows]

def verify_audit_integrity(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Verifies the cryptographic SHA-256 hash chain of the audit log from genesis to the latest record.
    Returns whether the ledger is intact and itemizes any tampered entries.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, debt_id, action, performed_by, details, created_at, prev_hash, entry_hash FROM audit_log ORDER BY id ASC"
    )
    rows = cursor.fetchall()

    if not rows:
        return {
            "is_valid": True,
            "total_entries": 0,
            "tampered_count": 0,
            "tampered_entries": [],
            "summary": "Audit log is empty; genesis state intact.",
        }

    tampered_entries = []
    expected_prev_hash = AUDIT_GENESIS_PREV_HASH

    for r in rows:
        # Check prev_hash linkage
        prev_hash_matches = (r["prev_hash"] == expected_prev_hash)

        # Recompute expected entry hash
        computed_hash = _compute_entry_hash(
            prev_hash=r["prev_hash"],
            entry_id=r["id"],
            debt_id=r["debt_id"],
            action=r["action"],
            performed_by=r["performed_by"],
            details=r["details"],
            created_at=r["created_at"],
        )
        entry_hash_matches = (r["entry_hash"] == computed_hash)

        if not prev_hash_matches or not entry_hash_matches:
            tampered_entries.append({
                "id": r["id"],
                "debt_id": r["debt_id"],
                "recorded_entry_hash": r["entry_hash"],
                "computed_entry_hash": computed_hash,
                "recorded_prev_hash": r["prev_hash"],
                "expected_prev_hash": expected_prev_hash,
                "reason": "Hash mismatch" if not entry_hash_matches else "Broken chain linkage",
            })

        # Advance pointer
        expected_prev_hash = r["entry_hash"] or computed_hash

    is_valid = len(tampered_entries) == 0
    return {
        "is_valid": is_valid,
        "total_entries": len(rows),
        "tampered_count": len(tampered_entries),
        "tampered_entries": tampered_entries,
        "latest_hash": rows[-1]["entry_hash"] if rows else None,
        "summary": "Cryptographic audit chain fully verified. Zero tamper events detected."
        if is_valid
        else f"TAMPER ALERT: {len(tampered_entries)} audit entries fail cryptographic verification.",
    }
