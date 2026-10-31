# Requirement Debt Ledger (RDL): REST API Specifications

*Comprehensive API Reference for Backend Endpoints*

The RDL provides an OpenAPI 3.0 compliant REST API implemented with FastAPI. Interactive API documentation routes are disabled in the presentation build. The application interface is available at `http://127.0.0.1:8000`.

---

## 1. Requirement Debt Endpoints

### 1.1 List Requirement Debts
- **Route:** `GET /api/debts`
- **Description:** Retrieves all requirement debts enriched with dynamically calculated base risk, compounding interest, overdue status, dependency impact, and Debt Priority Index (DPI).
- **Query Parameters:**
  - `module` (optional string): Filter by subsystem (e.g. `Payment Gateway`).
  - `status` (optional string): Filter by status (`Deferred`, `Under Review`, `Remediating`, `Resolved`).
  - `risk_tier` (optional string): Filter by computed risk tier (`Low`, `Moderate`, `High`, `Critical`).
  - `escalation_level` (optional string): Filter by escalation (`OK`, `UPCOMING_REVIEW`, `OVERDUE_REVIEW`, `CRITICAL_BREACH`).
  - `milestone` (optional string): Filter by target release milestone.
  - `search` (optional string): Case-insensitive search across debt_id, title, and description.
  - `sort_by` (default: `debt_priority_index`): Sort field (`debt_priority_index`, `dynamic_risk_score`, `days_to_review`, `created_date`, `title`).
  - `sort_order` (default: `desc`): `asc` or `desc`.
- **Response:** `200 OK` (Array of `DebtItemResponse` objects)

### 1.2 Get Single Debt Details
- **Route:** `GET /api/debts/{debt_id}`
- **Description:** Retrieves full record of a debt item, including the complete step-by-step explainable risk breakdown.
- **Response:** `200 OK` or `404 Not Found`

```json
{
  "id": 1,
  "debt_id": "REQ-DEBT-001",
  "title": "Automated Multi-Currency Foreign Exchange Rate Reconciliation",
  "module": "Payment Gateway",
  "status": "Deferred",
  "created_date": "2026-09-01",
  "review_date": "2026-10-08",
  "deadline_date": "2026-10-31",
  "risk": {
    "base_severity": 4.0,
    "base_occurrence": 4,
    "base_detection": 3,
    "base_risk_score": 38.4,
    "elapsed_days": 45,
    "grace_period_days": 14,
    "days_past_grace": 31,
    "interest_factor": 1.2801,
    "accrued_interest_percent": 28.01,
    "is_overdue": true,
    "overdue_days": 8,
    "overdue_penalty_factor": 1.0667,
    "dynamic_risk_score": 52.43,
    "risk_tier": "Moderate",
    "explanation": "Base risk score of 38.4/100 derived from composite severity 4.00/5, occurrence 4/5, and detection difficulty 3/5. Debt aged 45 days (31 days beyond 14-day grace period), accruing 28.0% debt interest. REVIEW OVERDUE by 8 days past review date (2026-10-08), triggering a x1.07 overdue penalty. Dynamic effective risk is 52.4 (Moderate)."
  },
  "dependency_impact": {
    "direct_dependencies_count": 1,
    "downstream_blocked_count": 0,
    "critical_path_depth": 0,
    "is_in_cycle": false
  },
  "debt_priority_index": 57.6,
  "escalation_level": "OVERDUE_REVIEW",
  "days_to_review": -8,
  "days_to_deadline": 15
}
```

### 1.3 Create Requirement Debt
- **Route:** `POST /api/debts`
- **Status:** `201 Created`
- **Request Body:**
```json
{
  "title": "OAuth2 Token Revocation List Distribution",
  "description": "JWT tokens cannot be immediately revoked before natural expiration without distributed blacklist.",
  "module": "Auth & Identity",
  "requirement_type": "Security",
  "deferral_reason": "Time Constraint / Scope Reduction",
  "deferral_phase": "Sprint Planning",
  "decision_maker": "Security Lead (A. Joseph)",
  "owner": "Identity Squad",
  "target_milestone": "Release 1.0",
  "resolution_criteria": "Implement Redis Bloom Filter with 15-minute token revocation propagation.",
  "created_date": "2026-10-16",
  "review_date": "2026-10-30",
  "deadline_date": "2026-11-20",
  "business_impact": 4,
  "arch_impact": 4,
  "safety_impact": 5,
  "occurrence_prob": 3,
  "detection_difficulty": 3,
  "cost_of_delay": 4
}
```

### 1.4 Update Requirement Debt
- **Route:** `PATCH /api/debts/{debt_id}`
- **Request Body:** Any subset of debt fields, plus optional `updated_by` and `rationale`.
- **Response:** `200 OK`

### 1.5 Resolve Requirement Debt
- **Route:** `POST /api/debts/{debt_id}/resolve`
- **Request Body:**
```json
{
  "resolution_type": "Implemented & Verified",
  "resolution_notes": "Implemented Redis Bloom filter in PR #402; verified revocation latency under 20ms in test suite.",
  "resolved_by": "Senior Security Engineer"
}
```
- **Response:** `200 OK`

### 1.6 Delete Requirement Debt
- **Route:** `DELETE /api/debts/{debt_id}`
- **Response:** `200 OK` (`{"message": "Debt '...' deleted successfully."}`)

### 1.7 Simulate Risk & Interest Interactively
- **Route:** `POST /api/debts/simulate/risk`
- **Description:** Computes dynamic risk without storing in database. Used by the interactive laboratory in the frontend.

---

## 2. Dependency Endpoints

### 2.1 List All Dependencies
- **Route:** `GET /api/dependencies`
- **Response:** `200 OK` (Array of dependency records)

### 2.2 Add Dependency Link (with Cycle Prevention)
- **Route:** `POST /api/dependencies`
- **Request Body:**
```json
{
  "debt_id": "REQ-DEBT-001",
  "depends_on_debt_id": "REQ-DEBT-003",
  "dependency_type": "Blocks",
  "notes": "Idempotency layer is a prerequisite for FX reconciliation."
}
```
- **Response:** `201 Created`
- **Error:** `400 Bad Request` if a self-loop or cyclic dependency is detected.

### 2.3 Delete Dependency
- **Route:** `DELETE /api/dependencies/{dep_id}`
- **Response:** `200 OK`

### 2.4 Get Dependency Graph
- **Route:** `GET /api/dependencies/graph`
- **Response:**
```json
{
  "nodes": [...],
  "edges": [...],
  "has_cycle": false,
  "cycles": [],
  "critical_path": ["REQ-DEBT-005", "REQ-DEBT-003", "REQ-DEBT-001"]
}
```

---

## 3. Governance, Reviews, and Audit Endpoints

### 3.1 Get Reviews for a Debt
- **Route:** `GET /api/reviews/{debt_id}`
- **Response:** `200 OK`

### 3.2 Record Review Session
- **Route:** `POST /api/reviews`
- **Request Body:**
```json
{
  "debt_id": "REQ-DEBT-002",
  "reviewer_name": "R. Verma",
  "reviewer_role": "CISO",
  "outcome": "Extend Review Date",
  "notes": "Spike completed; extended review date to allow CloudHSM vendor negotiation.",
  "new_review_date": "2026-11-05"
}
```
- **Response:** `201 Created`

### 3.3 Get Audit Trail
- **Route:** `GET /api/audit?debt_id=REQ-DEBT-001&limit=50`
- **Response:** `200 OK` (Chronological list of audit events)

---

## 4. Release Readiness Gate Endpoints

### 4.1 List Release Gates
- **Route:** `GET /api/release-gates`
- **Response:** `200 OK`

### 4.2 Create Release Gate
- **Route:** `POST /api/release-gates`
- **Request Body:**
```json
{
  "gate_name": "Release 1.0 Production Gate",
  "target_milestone": "Release 1.0",
  "max_critical_debts": 0,
  "max_high_debts": 1,
  "max_aggregate_risk": 150.0
}
```
- **Response:** `201 Created`

### 4.3 Evaluate Release Gate
- **Route:** `GET /api/release-gates/{gate_id}/evaluate`
- **Description:** Evaluates current open debts against gate criteria.
- **Response:**
```json
{
  "gate_name": "Release 1.0 General Availability Gate",
  "target_milestone": "Release 1.0",
  "status": "BLOCKED",
  "is_ready_to_release": false,
  "max_critical_debts": 0,
  "actual_critical_debts": 1,
  "max_high_debts": 1,
  "actual_high_debts": 2,
  "max_aggregate_risk": 150.0,
  "actual_aggregate_risk": 182.4,
  "violations": [
    {
      "rule": "ZERO_CRITICAL_DEBT_GATE",
      "severity": "CRITICAL",
      "message": "Found 1 Critical requirement debts (maximum allowed: 0).",
      "culprit_debt_ids": ["REQ-DEBT-002"]
    }
  ],
  "summary": "RELEASE BLOCKED: 1 gate violation(s) including critical requirement debt."
}
```

### 4.4 Formally Sign Off Gate
- **Route:** `POST /api/release-gates/{gate_id}/signoff`
- **Request Body:**
```json
{
  "signoff_by": "Release Director (M. Jenkins)",
  "signoff_notes": "Accepted conditional risk with dedicated hotfix engineer on standby."
}
```
- **Response:** `200 OK`

---

## 5. Analytics & Export Endpoints

### 5.1 Get Dashboard Analytics
- **Route:** `GET /api/analytics/dashboard`
- **Response:** KPI counts, risk distributions, module concentrations, top urgent debts.

### 5.2 Export CSV
- **Route:** `GET /api/export/csv`
- **Response:** `text/csv` stream with complete debt ledger fields.

### 5.3 Export JSON
- **Route:** `GET /api/export/json`
- **Response:** `application/json` full dataset.

### 5.4 Reset Demo Seed Data
- **Route:** `POST /api/export/reset`
- **Response:** `{"message": "Database reset to initial demo seed data successfully."}`

---

## 6. Simulation & Risk Forecasting Endpoints

### 6.1 Simulate Dependency Impact
- **Route:** `POST /api/simulations/dependency-impact`
- **Description:** Simulates an additional deferral delay for one requirement and reports direct/indirect downstream impact, affected requirements, and the portfolio risk delta.
- **Request Body:**
```json
{
  "debt_id": "DEBT-AUTH-001",
  "additional_delay_days": 30,
  "scenario_notes": "Optional explanation"
}
```
- **Response:** `200 OK` with `target_projected_risk`, `direct_blocked_count`, `indirect_blocked_count`, `total_unique_affected_count`, `affected_requirements`, `portfolio_risk_delta`, and an explanatory summary.

### 6.2 What-If Release Planning Sandbox
- **Route:** `POST /api/simulations/what-if-release`
- **Description:** Evaluates the status quo and three candidate remediation strategies (dependency unblocking, severe-risk elimination, and effort-budget quick wins) in an isolated, read-only simulation. An optional custom plan can also be supplied.
- **Request Body:**
```json
{
  "target_milestone": "Release 1.0",
  "effort_capacity_budget": 35
}
```
- **Response:** `200 OK` with the status-quo result, candidate plan results, recommended plan ID, comparative summary, and isolation statement.

### 6.3 Apply What-If Plan to Actual Ledger
- **Route:** `POST /api/simulations/apply-plan`
- **Description:** After explicit confirmation, moves the selected open requirements in the specified milestone to `Remediating` and records an audit event. It does **not** mark requirements as `Resolved`; each item must still be implemented and formally verified through the resolution workflow. The endpoint rejects IDs outside the selected milestone and items that are already closed.
- **Request Body:**
```json
{
  "target_milestone": "Release 2.0",
  "resolved_debt_ids": ["REQ-DEBT-006"],
  "actor_name": "Release Manager",
  "rationale": "Started remediation after plan review."
}
```
- **Response:** `200 OK` with the updated count, IDs moved to remediation, and a message.

### 6.4 Risk Forecasting
- **Route:** `POST /api/simulations/risk-forecast`
- **Description:** Projects dynamic risk across requested future horizons. Supported scenarios are `status_quo` and `timely_review`; the current UI uses `status_quo`. The forecast can cover the full portfolio, a milestone, or one requirement.
- **Request Body:**
```json
{
  "horizons_days": [0, 15, 30, 60, 90, 180],
  "scenario": "status_quo",
  "daily_interest_rate": 0.008
}
```
- **Response:** `200 OK` with projected dates, aggregate risk, and risk-tier counts for each horizon.

### 6.5 Daily Interest Rate Sensitivity Analysis
- **Route:** `POST /api/debts/simulate/sensitivity`
- **Description:** Evaluates dynamic risk across low (0.4%), baseline (0.8%), and high (1.2%) daily interest rates.

---

## 7. Resolution Recommendations Endpoints

### 7.1 Get Remediation Recommendations
- **Route:** `GET /api/recommendations/`
- **Query Parameters:** `milestone` (optional string)
- **Description:** Ranks deferred requirements by multi-criteria decision modeling (MCDM) with sublinear effort elasticity. Returns detailed factor breakdown and natural language rationale.

### 7.2 Pairwise Contrastive Explanation
- **Route:** `POST /api/recommendations/pairwise-explain`
- **Description:** Generates an explainable comparative decomposition of why requirement debt A is ranked above or below requirement debt B.
- **Request Body:**
```json
{
  "debt_id_a": "DEBT-AUTH-001",
  "debt_id_b": "DEBT-OBS-001"
}
```
- **Response:** `200 OK`
```json
{
  "higher_ranked_id": "DEBT-AUTH-001",
  "lower_ranked_id": "DEBT-OBS-001",
  "score_delta": 24.6,
  "contrastive_narrative": "DEBT-AUTH-001 is prioritized above DEBT-OBS-001 by +24.6 score points because of unblocking 2 downstream dependencies and higher dynamic risk exposure.",
  "comparison_matrix": { ... }
}
```

---

## 8. Tamper-Evident Audit Verification Endpoint

### 8.1 Verify Audit Chain Integrity
- **Route:** `GET /api/audit/verify`
- **Description:** Recomputes sequential SHA-256 hash chains from genesis block across all audit entries. Detects any row insertions, updates, or deletions made directly in SQLite.
- **Response:** `200 OK`
```json
{
  "is_valid": true,
  "total_entries": 12,
  "tampered_count": 0,
  "tampered_entries": [],
  "latest_hash": "a4f89c02d1e57b3...",
  "summary": "Audit log cryptographic integrity verified: All 12 entries form an unbroken SHA-256 hash chain."
}
```

