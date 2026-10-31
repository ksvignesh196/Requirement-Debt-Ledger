"""
Requirement Debt Ledger (RDL) - SQLite Database Access & Schema Initialization
"""
import sqlite3
import hashlib
from typing import Generator
from app.config import DB_PATH, AUDIT_GENESIS_PREV_HASH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS requirement_debts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debt_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    module TEXT NOT NULL,
    requirement_type TEXT NOT NULL,
    deferral_reason TEXT NOT NULL,
    deferral_phase TEXT NOT NULL,
    decision_maker TEXT NOT NULL,
    owner TEXT NOT NULL,
    target_milestone TEXT NOT NULL,
    resolution_criteria TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Deferred',
    created_date TEXT NOT NULL,
    review_date TEXT NOT NULL,
    deadline_date TEXT NOT NULL,
    business_impact INTEGER NOT NULL DEFAULT 3,
    arch_impact INTEGER NOT NULL DEFAULT 3,
    safety_impact INTEGER NOT NULL DEFAULT 3,
    occurrence_prob INTEGER NOT NULL DEFAULT 3,
    detection_difficulty INTEGER NOT NULL DEFAULT 3,
    cost_of_delay INTEGER NOT NULL DEFAULT 3,
    estimated_effort INTEGER NOT NULL DEFAULT 8,
    resolution_notes TEXT,
    resolved_date TEXT,
    resolution_type TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS debt_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debt_id TEXT NOT NULL,
    depends_on_debt_id TEXT NOT NULL,
    dependency_type TEXT NOT NULL DEFAULT 'Blocks',
    notes TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(debt_id, depends_on_debt_id),
    FOREIGN KEY(debt_id) REFERENCES requirement_debts(debt_id) ON DELETE CASCADE,
    FOREIGN KEY(depends_on_debt_id) REFERENCES requirement_debts(debt_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debt_id TEXT NOT NULL,
    review_date TEXT NOT NULL,
    reviewer_name TEXT NOT NULL,
    reviewer_role TEXT NOT NULL,
    outcome TEXT NOT NULL,
    notes TEXT NOT NULL,
    new_review_date TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(debt_id) REFERENCES requirement_debts(debt_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS release_gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_name TEXT NOT NULL,
    target_milestone TEXT NOT NULL,
    max_critical_debts INTEGER NOT NULL DEFAULT 0,
    max_high_debts INTEGER NOT NULL DEFAULT 1,
    max_aggregate_risk REAL NOT NULL DEFAULT 150.0,
    status TEXT NOT NULL DEFAULT 'Pending',
    evaluation_date TEXT,
    evaluation_summary TEXT,
    signoff_by TEXT,
    signoff_notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debt_id TEXT,
    action TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    details TEXT NOT NULL,
    created_at TEXT NOT NULL,
    prev_hash TEXT,
    entry_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_debts_status ON requirement_debts(status);
CREATE INDEX IF NOT EXISTS idx_debts_milestone ON requirement_debts(target_milestone);
CREATE INDEX IF NOT EXISTS idx_debts_review_date ON requirement_debts(review_date);
CREATE INDEX IF NOT EXISTS idx_deps_debt ON debt_dependencies(debt_id);
CREATE INDEX IF NOT EXISTS idx_deps_depends ON debt_dependencies(depends_on_debt_id);
CREATE INDEX IF NOT EXISTS idx_reviews_debt ON review_sessions(debt_id);
CREATE INDEX IF NOT EXISTS idx_audit_debt ON audit_log(debt_id);
"""

def get_connection(db_file: str = None) -> sqlite3.Connection:
    """Return a configured SQLite connection with foreign keys enabled."""
    target_path = db_file or str(DB_PATH)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _migrate_schema_if_needed(conn: sqlite3.Connection) -> None:
    """Safely apply non-destructive schema migrations for existing databases."""
    cursor = conn.cursor()

    # Check requirement_debts columns
    cursor.execute("PRAGMA table_info(requirement_debts);")
    debt_cols = {row["name"] for row in cursor.fetchall()}
    if "estimated_effort" not in debt_cols and len(debt_cols) > 0:
        cursor.execute("ALTER TABLE requirement_debts ADD COLUMN estimated_effort INTEGER NOT NULL DEFAULT 8;")

    # Check audit_log columns
    cursor.execute("PRAGMA table_info(audit_log);")
    audit_cols = {row["name"] for row in cursor.fetchall()}
    if len(audit_cols) > 0:
        if "prev_hash" not in audit_cols:
            cursor.execute("ALTER TABLE audit_log ADD COLUMN prev_hash TEXT;")
        if "entry_hash" not in audit_cols:
            cursor.execute("ALTER TABLE audit_log ADD COLUMN entry_hash TEXT;")

    conn.commit()

    # Backfill hash chain on any unhashed audit records
    _backfill_audit_hashes(conn)

def _backfill_audit_hashes(conn: sqlite3.Connection) -> None:
    """Backfills cryptographic hash chaining on any unhashed audit log entries."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, debt_id, action, performed_by, details, created_at, prev_hash, entry_hash FROM audit_log ORDER BY id ASC")
    rows = cursor.fetchall()

    prev_hash = AUDIT_GENESIS_PREV_HASH
    for r in rows:
        current_entry_hash = r["entry_hash"]
        current_prev_hash = r["prev_hash"]
        if not current_entry_hash or not current_prev_hash:
            # Generate deterministic hash
            raw_payload = f"{prev_hash}|{r['id']}|{r['debt_id'] or ''}|{r['action']}|{r['performed_by']}|{r['details']}|{r['created_at']}"
            entry_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
            cursor.execute(
                "UPDATE audit_log SET prev_hash = ?, entry_hash = ? WHERE id = ?",
                (prev_hash, entry_hash, r["id"]),
            )
            prev_hash = entry_hash
        else:
            prev_hash = current_entry_hash
    conn.commit()

def init_db(db_file: str = None) -> None:
    """Initialize the SQLite database schema if not present and apply migrations."""
    with get_connection(db_file) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        _migrate_schema_if_needed(conn)

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI Dependency for database connection."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
