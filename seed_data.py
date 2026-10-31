"""
Requirement Debt Ledger (RDL) - Seed Data Generator
Populates realistic software engineering requirement debts, dependencies, reviews, and release gates.
"""
import sys
import sqlite3
from datetime import date, timedelta
from app.config import DB_PATH
from app.database import init_db, get_connection
from app.services.audit_service import log_audit

def seed_database(db_file: str = None):
    """Populates realistic requirement debt data for live demonstration."""
    conn = get_connection(db_file)
    init_db(db_file)

    cursor = conn.cursor()
    # Clear existing data
    cursor.execute("DELETE FROM audit_log")
    cursor.execute("DELETE FROM review_sessions")
    cursor.execute("DELETE FROM debt_dependencies")
    cursor.execute("DELETE FROM release_gates")
    cursor.execute("DELETE FROM requirement_debts")
    conn.commit()

    today = date.today()

    debts_data = [
        {
            "debt_id": "REQ-DEBT-001",
            "title": "Automated Multi-Currency Foreign Exchange Rate Reconciliation",
            "description": "Cross-border checkout orders lack real-time currency reconciliation with international treasury providers, risking conversion variance losses during market volatility.",
            "module": "Payment Gateway",
            "requirement_type": "Functional",
            "deferral_reason": "Third-Party Dependency",
            "deferral_phase": "Sprint Planning",
            "decision_maker": "Lead Architect (P. Sharma)",
            "owner": "Payment Integration Squad",
            "target_milestone": "Release 1.0",
            "resolution_criteria": "Integrate with Bloomberg FX API and pass end-to-end multi-currency variance integration tests under 50ms latency.",
            "status": "Deferred",
            "created_date": (today - timedelta(days=45)).isoformat(),
            "review_date": (today - timedelta(days=8)).isoformat(),  # Overdue review!
            "deadline_date": (today + timedelta(days=15)).isoformat(),
            "business_impact": 4,
            "arch_impact": 4,
            "safety_impact": 4,
            "occurrence_prob": 4,
            "detection_difficulty": 3,
            "cost_of_delay": 4,
            "estimated_effort": 8,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-002",
            "title": "PCI-DSS Compliant Hardware Security Module (HSM) Tokenization",
            "description": "Credit card Primary Account Numbers (PANs) are temporarily held in an encrypted Redis cache rather than dedicated FIPS 140-2 Level 3 hardware security modules, creating compliance exposure.",
            "module": "Security & Compliance",
            "requirement_type": "Security",
            "deferral_reason": "Budget / Resource Limitation",
            "deferral_phase": "Inception",
            "decision_maker": "CISO (R. Verma)",
            "owner": "Security Ops",
            "target_milestone": "Release 1.0",
            "resolution_criteria": "Procure AWS CloudHSM cluster, migrate temporary PAN cache to zero-knowledge cryptographic token vault, and obtain signed QSA auditor sign-off.",
            "status": "Under Review",
            "created_date": (today - timedelta(days=60)).isoformat(),
            "review_date": (today - timedelta(days=5)).isoformat(),  # Overdue!
            "deadline_date": (today + timedelta(days=20)).isoformat(),
            "business_impact": 5,
            "arch_impact": 4,
            "safety_impact": 5,
            "occurrence_prob": 4,
            "detection_difficulty": 4,
            "cost_of_delay": 5,
            "estimated_effort": 13,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-003",
            "title": "Distributed Idempotency Layer for Payment Webhook Retries",
            "description": "Webhook ingestion lacks distributed Redis redlock mechanism to handle duplicate incoming charge events from payment providers, potentially causing double fulfillment.",
            "module": "Payment Gateway",
            "requirement_type": "Architectural",
            "deferral_reason": "Time Constraint / Scope Reduction",
            "deferral_phase": "Development",
            "decision_maker": "Tech Lead (A. Joseph)",
            "owner": "Backend Core",
            "target_milestone": "Release 1.0",
            "resolution_criteria": "Implement Redis distributed lock with 24-hour idempotency key TTL on Stripe/Razorpay webhook listeners.",
            "status": "Remediating",
            "created_date": (today - timedelta(days=28)).isoformat(),
            "review_date": (today + timedelta(days=3)).isoformat(),  # Upcoming review!
            "deadline_date": (today + timedelta(days=14)).isoformat(),
            "business_impact": 4,
            "arch_impact": 5,
            "safety_impact": 3,
            "occurrence_prob": 4,
            "detection_difficulty": 3,
            "cost_of_delay": 4,
            "estimated_effort": 5,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-004",
            "title": "Automated Customer GDPR Right-to-be-Forgotten Data Purging Pipeline",
            "description": "GDPR deletion requests are currently executed manually via DBA runbooks rather than an automated orchestration pipeline across microservice databases and backup archives.",
            "module": "Data & Privacy",
            "requirement_type": "Compliance",
            "deferral_reason": "Technical Uncertainty",
            "deferral_phase": "Architecture",
            "decision_maker": "Data Protection Officer (S. Nair)",
            "owner": "Data Engineering Team",
            "target_milestone": "Release 1.0",
            "resolution_criteria": "Async batch job that cascades deletion across Postgres user tables and S3 invoice archives while maintaining legally mandated audit records.",
            "status": "Deferred",
            "created_date": (today - timedelta(days=35)).isoformat(),
            "review_date": (today - timedelta(days=12)).isoformat(),  # Overdue review!
            "deadline_date": (today - timedelta(days=3)).isoformat(),   # Critical deadline breach!
            "business_impact": 4,
            "arch_impact": 3,
            "safety_impact": 5,
            "occurrence_prob": 4,
            "detection_difficulty": 4,
            "cost_of_delay": 5,
            "estimated_effort": 13,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-005",
            "title": "Granular Role-Based Access Control (RBAC) with Least Privilege Scopes",
            "description": "Internal administrative routes use monolithic superadmin access roles instead of fine-grained permission scopes (e.g., `refund:issue`, `order:cancel`).",
            "module": "Auth & Identity",
            "requirement_type": "Security",
            "deferral_reason": "Time Constraint / Scope Reduction",
            "deferral_phase": "Sprint Planning",
            "decision_maker": "Product Owner (M. Gupta)",
            "owner": "Identity Squad",
            "target_milestone": "Release 1.0",
            "resolution_criteria": "Replace binary admin flag with OAuth2 scope claims validated via API Gateway policy filters.",
            "status": "Deferred",
            "created_date": (today - timedelta(days=22)).isoformat(),
            "review_date": (today + timedelta(days=4)).isoformat(),  # Upcoming review!
            "deadline_date": (today + timedelta(days=25)).isoformat(),
            "business_impact": 3,
            "arch_impact": 4,
            "safety_impact": 4,
            "occurrence_prob": 3,
            "detection_difficulty": 3,
            "cost_of_delay": 3,
            "estimated_effort": 5,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-006",
            "title": "Circuit Breaker Pattern on Third-Party SMS Notification Gateway",
            "description": "Outgoing SMS OTP and notification requests lack circuit-breaker fault protection, leading to cascading HTTP thread starvation when the carrier experiences timeouts.",
            "module": "Notification Service",
            "requirement_type": "Performance",
            "deferral_reason": "Incomplete Specification",
            "deferral_phase": "Development",
            "decision_maker": "Senior SRE (K. Raman)",
            "owner": "DevOps Platform",
            "target_milestone": "Release 2.0",
            "resolution_criteria": "Implement circuit breaker with exponential backoff and fallback queueing to AWS SNS when primary provider error rate exceeds 5%.",
            "status": "Deferred",
            "created_date": (today - timedelta(days=8)).isoformat(),  # Inside grace period
            "review_date": (today + timedelta(days=22)).isoformat(),
            "deadline_date": (today + timedelta(days=60)).isoformat(),
            "business_impact": 2,
            "arch_impact": 3,
            "safety_impact": 2,
            "occurrence_prob": 2,
            "detection_difficulty": 2,
            "cost_of_delay": 2,
            "estimated_effort": 3,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-007",
            "title": "Full-Text OpenSearch Indexing for Historical Customer Order Search",
            "description": "Historical order lookup executes parameterized SQL `LIKE` queries against primary Postgres database, risking CPU spikes during peak traffic.",
            "module": "Search & Catalog",
            "requirement_type": "Functional",
            "deferral_reason": "Time Constraint / Scope Reduction",
            "deferral_phase": "Inception",
            "decision_maker": "Product Manager (T. Roy)",
            "owner": "Search Team",
            "target_milestone": "Release 2.0",
            "resolution_criteria": "Deploy OpenSearch cluster and establish Change Data Capture (CDC) pipeline to index historical order records.",
            "status": "Deferred",
            "created_date": (today - timedelta(days=12)).isoformat(),
            "review_date": (today + timedelta(days=16)).isoformat(),
            "deadline_date": (today + timedelta(days=45)).isoformat(),
            "business_impact": 3,
            "arch_impact": 2,
            "safety_impact": 1,
            "occurrence_prob": 3,
            "detection_difficulty": 2,
            "cost_of_delay": 2,
            "estimated_effort": 8,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-008",
            "title": "Real-Time WebSocket Inventory Stock Level Sync",
            "description": "Product catalog displays cached stock numbers refreshed on 5-minute cron instead of pushing live stock deltas to shoppers during checkout flash sales.",
            "module": "Inventory Management",
            "requirement_type": "Architectural",
            "deferral_reason": "Architectural Redesign",
            "deferral_phase": "Architecture",
            "decision_maker": "Solutions Architect (H. Mehta)",
            "owner": "Inventory Squad",
            "target_milestone": "Release 2.0",
            "resolution_criteria": "Broadcast Redis Pub/Sub inventory updates over secure WebSockets with client reconnection buffering.",
            "status": "Deferred",
            "created_date": (today - timedelta(days=5)).isoformat(),  # Very fresh
            "review_date": (today + timedelta(days=25)).isoformat(),
            "deadline_date": (today + timedelta(days=50)).isoformat(),
            "business_impact": 3,
            "arch_impact": 3,
            "safety_impact": 1,
            "occurrence_prob": 2,
            "detection_difficulty": 2,
            "cost_of_delay": 2,
            "estimated_effort": 5,
            "resolution_notes": None,
            "resolved_date": None,
            "resolution_type": None,
        },
        {
            "debt_id": "REQ-DEBT-009",
            "title": "Automated Database Read Replica Connection Pooling",
            "description": "Database connection exhaustion during high concurrent analytics queries caused intermittent 500 errors on the customer portal.",
            "module": "Infrastructure & Database",
            "requirement_type": "Non-Functional",
            "deferral_reason": "Time Constraint / Scope Reduction",
            "deferral_phase": "QA/Testing",
            "decision_maker": "Principal DBA (V. Iyer)",
            "owner": "Database Ops",
            "target_milestone": "Release 1.0",
            "resolution_criteria": "Configure PgBouncer transaction pooling with max 250 connections and verify load testing under 5,000 req/sec.",
            "status": "Resolved",
            "created_date": (today - timedelta(days=50)).isoformat(),
            "review_date": (today - timedelta(days=30)).isoformat(),
            "deadline_date": (today - timedelta(days=10)).isoformat(),
            "business_impact": 4,
            "arch_impact": 4,
            "safety_impact": 2,
            "occurrence_prob": 4,
            "detection_difficulty": 3,
            "cost_of_delay": 4,
            "estimated_effort": 8,
            "resolution_notes": "Configured PgBouncer transaction pooling with max 250 connections and verified load testing up to 5,000 req/sec under JMeter.",
            "resolved_date": (today - timedelta(days=8)).isoformat(),
            "resolution_type": "Implemented & Verified",
        },
        {
            "debt_id": "REQ-DEBT-010",
            "title": "End-to-End Synthetic Transaction Monitoring in Production",
            "description": "Lack of synthetic end-to-end checkout transactions meant partial payment provider degradation was only detected after customer complaints.",
            "module": "Monitoring & Observability",
            "requirement_type": "Non-Functional",
            "deferral_reason": "Budget / Resource Limitation",
            "deferral_phase": "Sprint Planning",
            "decision_maker": "Engineering Director (S. Kulkarni)",
            "owner": "Site Reliability Engineering",
            "target_milestone": "Release 1.0",
            "resolution_criteria": "Deploy synthetic canary runners that execute headless end-to-end checkout flow every 2 minutes.",
            "status": "Resolved",
            "created_date": (today - timedelta(days=40)).isoformat(),
            "review_date": (today - timedelta(days=20)).isoformat(),
            "deadline_date": (today - timedelta(days=5)).isoformat(),
            "business_impact": 3,
            "arch_impact": 3,
            "safety_impact": 2,
            "occurrence_prob": 3,
            "detection_difficulty": 3,
            "cost_of_delay": 3,
            "estimated_effort": 5,
            "resolution_notes": "Absorbed into Datadog Synthetic Canaries deployment; verified 1-minute interval synthetic checkout runs in staging.",
            "resolved_date": (today - timedelta(days=12)).isoformat(),
            "resolution_type": "Absorbed into Redesign",
        },
    ]

    for item in debts_data:
        cursor.execute(
            """
            INSERT INTO requirement_debts (
                debt_id, title, description, module, requirement_type,
                deferral_reason, deferral_phase, decision_maker, owner,
                target_milestone, resolution_criteria, status, created_date,
                review_date, deadline_date, business_impact, arch_impact,
                safety_impact, occurrence_prob, detection_difficulty,
                cost_of_delay, estimated_effort, resolution_notes, resolved_date, resolution_type,
                updated_at
            ) VALUES (
                :debt_id, :title, :description, :module, :requirement_type,
                :deferral_reason, :deferral_phase, :decision_maker, :owner,
                :target_milestone, :resolution_criteria, :status, :created_date,
                :review_date, :deadline_date, :business_impact, :arch_impact,
                :safety_impact, :occurrence_prob, :detection_difficulty,
                :cost_of_delay, :estimated_effort, :resolution_notes, :resolved_date, :resolution_type,
                :created_date
            )
            """,
            item,
        )

    # Insert Dependencies
    dependencies_data = [
        # REQ-001 (FX Recon) depends on REQ-003 (Idempotency)
        ("REQ-DEBT-001", "REQ-DEBT-003", "Blocks", "Idempotency layer is prerequisite for multi-currency automated reconciliation."),
        # REQ-003 (Idempotency) depends on REQ-005 (RBAC)
        ("REQ-DEBT-003", "REQ-DEBT-005", "Architectural Precondition", "Granular token scopes required for machine-to-machine webhook retry auth."),
        # REQ-004 (GDPR Purge) depends on REQ-002 (HSM Tokenization)
        ("REQ-DEBT-004", "REQ-DEBT-002", "Blocks", "GDPR deletion cannot purge PAN tokens until CloudHSM token vault is established."),
        # REQ-007 (Search) depends on REQ-008 (Inventory Sync)
        ("REQ-DEBT-007", "REQ-DEBT-008", "Data Dependency", "OpenSearch order indexing depends on inventory stock sync schema."),
    ]

    for d_id, dep_id, dep_type, notes in dependencies_data:
        cursor.execute(
            """
            INSERT INTO debt_dependencies (debt_id, depends_on_debt_id, dependency_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (d_id, dep_id, dep_type, notes, (today - timedelta(days=20)).isoformat()),
        )

    # Insert Review Sessions
    reviews_data = [
        (
            "REQ-DEBT-001",
            (today - timedelta(days=10)).isoformat(),
            "P. Sharma",
            "Lead Architect",
            "Extend Review Date",
            "Bloomberg sandbox credentials received; scheduled integration spike for next sprint.",
            (today - timedelta(days=8)).isoformat(),
        ),
        (
            "REQ-DEBT-002",
            (today - timedelta(days=15)).isoformat(),
            "R. Verma",
            "CISO",
            "Escalate Priority",
            "External audit flagged unhashed PAN in cache; escalated to Critical priority.",
            (today - timedelta(days=5)).isoformat(),
        ),
        (
            "REQ-DEBT-003",
            (today - timedelta(days=7)).isoformat(),
            "A. Joseph",
            "Tech Lead",
            "Initiate Remediation",
            "Allocated 2 backend engineers to implement Redis redlock algorithm.",
            (today + timedelta(days=3)).isoformat(),
        ),
    ]

    for d_id, rev_date, rev_name, rev_role, outcome, notes, new_rev in reviews_data:
        cursor.execute(
            """
            INSERT INTO review_sessions (debt_id, review_date, reviewer_name, reviewer_role, outcome, notes, new_review_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (d_id, rev_date, rev_name, rev_role, outcome, notes, new_rev, rev_date),
        )

    # Insert Release Gates
    release_gates_data = [
        ("Release 1.0 General Availability Gate", "Release 1.0", 0, 1, 150.0),
        ("Release 2.0 Feature Milestone Gate", "Release 2.0", 0, 2, 200.0),
    ]

    for g_name, milestone, max_crit, max_high, max_agg in release_gates_data:
        cursor.execute(
            """
            INSERT INTO release_gates (gate_name, target_milestone, max_critical_debts, max_high_debts, max_aggregate_risk, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'Pending', ?)
            """,
            (g_name, milestone, max_crit, max_high, max_agg, today.isoformat()),
        )

    conn.commit()

    # Log initial audit event with cryptographic hash chaining
    log_audit(
        conn=conn,
        debt_id=None,
        action="DATABASE_SEEDED",
        performed_by="System Seed Script",
        details="Seeded 10 enterprise software requirement debts with dependencies, review sessions, and release gates."
    )

    conn.close()
    print("Database successfully seeded with realistic requirement debt data!")

if __name__ == "__main__":
    seed_database()
