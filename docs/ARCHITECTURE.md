# Requirement Debt Ledger (RDL): Technical Architecture Documentation

*Technical Architecture, Data Dictionary, and Component Specifications*

---

## 1. Architectural Philosophy & Design Principles

The Requirement Debt Ledger (RDL) is designed according to four core software engineering principles:
1. **Lightweight & Self-Contained:** Runs completely locally on a standard developer workstation or laptop without requiring cloud dependencies, remote AI APIs, Docker daemons, or npm build pipelines.
2. **Separation of Concerns (4-Tier Modularity):** Clear boundaries between Presentation (Vanilla SPA), Transport/Routing (FastAPI), Domain Mathematics (Service Engines), and Storage (SQLite).
3. **Persistent & Verifiable:** All debt records, dependency edges, review notes, release evaluations, and audit events are stored in a persistent relational SQLite database.
4. **Resilient & Defensible:** Mathematically bounded calculations, graph cycle prevention, and foreign key referential integrity ensure robust behavior during live demonstrations and college viva reviews.

---

## 2. 4-Tier Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                        1. PRESENTATION TIER (HTML5/CSS3/JS)                       |
|   Dashboard View  |  Ledger View  |  Risk Simulator  |  Graph Canvas  |  Gates    |
+-----------------------------------------------------------------------------------+
                                         │  HTTP / JSON (REST)
                                         ▼
+-----------------------------------------------------------------------------------+
|                     2. API & ROUTING TIER (Python FastAPI)                        |
|   /api/debts  |  /api/dependencies  |  /api/reviews  |  /api/release-gates  | ...  |
+-----------------------------------------------------------------------------------+
                                         │  Python Function Calls
                                         ▼
+-----------------------------------------------------------------------------------+
|                   3. MATHEMATICAL DOMAIN ENGINES (Python Services)                |
|   Risk Engine  |  Dependency Engine  |  Escalation Engine  |  Release Evaluator   |
+-----------------------------------------------------------------------------------+
                                         │  PRAGMA foreign_keys = ON;
                                         ▼
+-----------------------------------------------------------------------------------+
|                      4. PERSISTENCE TIER (SQLite 3.50.4)                          |
|   requirement_debts  |  debt_dependencies  |  review_sessions  |  release_gates   |
+-----------------------------------------------------------------------------------+
```

### Tier 1: Presentation Tier
- **Technology:** HTML5, CSS3, Vanilla JavaScript (ES6+).
- **Zero Build Step:** Native browser execution without Webpack, Vite, or Babel. Loads instantaneously in modern browsers (Chrome, Edge, Firefox).
- **Sub-modules:**
  - `app/static/index.html`: Unified Single-Page Application container.
  - `app/static/css/style.css`: Modern responsive stylesheet with CSS custom properties.
  - `app/static/js/api.js`: REST fetch client with unified error handling.
  - `app/static/js/dashboard.js`: Pure SVG donut and horizontal bar charts with KPI counters.
  - `app/static/js/debts.js`: Data table with live search, multiple filter dropdowns, and modal dialogs.
  - `app/static/js/risk_calculator.js`: Interactive laboratory with sliders and step-by-step mathematical derivation walkthrough.
  - `app/static/js/graph_view.js`: Node-edge network visualizer with cycle warning banners and critical path highlighting.
  - `app/static/js/release_view.js`: Release readiness gate evaluation cards and sign-off modal.
  - `app/static/js/app.js`: Tab switching and toast notification system.

### Tier 2: Application & Routing Tier
- **Technology:** FastAPI 0.143+, Uvicorn 0.54+.
- **Features:** strict Pydantic v2 input validation, CORS middleware, and static asset serving.
- **Routers:**
  - `app/routers/debts.py`: CRUD operations, filtering, search, and dynamic risk simulation.
  - `app/routers/dependencies.py`: Dependency edge management and graph data extraction.
  - `app/routers/recommendations.py`: Multi-criteria effort-aware prioritization and pairwise contrastive explanations.
  - `app/routers/simulations.py`: Downstream dependency blast radius simulation, what-if release planning sandbox, and risk forecasting.
  - `app/routers/reviews.py`: Review session logging, audit trail retrieval, and cryptographic hash verification.
  - `app/routers/release_gates.py`: Release gate configuration, evaluation, and formal sign-offs.
  - `app/routers/analytics.py`: Aggregated metrics, risk distributions, and priority focus items.
  - `app/routers/export.py`: CSV/JSON export and database reset endpoint.

### Tier 3: Mathematical Domain Services
- `app/services/risk_engine.py`: Encapsulates severity weighting ($w_b=0.35, w_a=0.35, w_s=0.30$), static base risk ($R_0$), compounding daily interest ($(1+0.008)^{\Delta t_g}$), schedule overdue penalties ($+25\%/30\text{d}$, cap 2.0x), multi-rate sensitivity analysis (0.4%, 0.8%, 1.2%), and plain-English explainable rationale generation.
- `app/services/dependency_engine.py`: Constructs directed dependency graph, runs DFS cycle detection algorithm, traverses transitive downstream blocked requirements with diamond graph deduplication, calculates critical path depth, computes the Debt Priority Index (DPI), and simulates dependency delay blast radius.
- `app/services/recommendation_engine.py`: Implements multi-criteria decision modeling (MCDM) integrating dynamic risk (35%), cascaded unblocking (30%), business value (20%), and urgency (15%) divided by sublinear effort elasticity ($E^{0.70}$). Generates pairwise contrastive explanations.
- `app/services/simulation_engine.py`: Evaluates what-if candidate release plans (Blockers, Critical, Quick Wins, Custom) in an isolated sandbox and forecasts dynamic risk across future horizons (15 to 180 days).
- `app/services/escalation_engine.py`: Inspects deadline dates and review schedules to classify items into `OK`, `UPCOMING_REVIEW`, `OVERDUE_REVIEW`, or `CRITICAL_BREACH`.
- `app/services/release_evaluator.py`: Evaluates quality gates against active requirement debts, checks for critical debt violations, and records formal stakeholder sign-offs.
- `app/services/audit_service.py`: Computes SHA-256 cryptographic hash chaining across audit entries and verifies ledger integrity.

### Tier 4: Persistence Tier
- **Technology:** SQLite 3.50+ stored at `data/rdl.db`.
- **Integrity Enforcement:** `PRAGMA foreign_keys = ON;` enabled on every connection. Foreign key constraints with `ON DELETE CASCADE` ensure referential consistency. B-tree indexes applied on `status`, `target_milestone`, `review_date`, and foreign keys for high query performance.

---

## 3. Data Dictionary & Schema Specifications

### Table 1: `requirement_debts`
Stores core deferred requirement records, evaluation parameters, and resolution status.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PRIMARY KEY AUTOINCREMENT | Internal synthetic primary key. |
| `debt_id` | `TEXT` | UNIQUE NOT NULL | Human-readable requirement debt identifier (e.g., `REQ-DEBT-001`). |
| `title` | `TEXT` | NOT NULL | Short title of the requirement debt. |
| `description` | `TEXT` | NOT NULL | Detailed description and context of the requirement deferral. |
| `module` | `TEXT` | NOT NULL | Target system subsystem (e.g., Payment Gateway, Auth & Identity). |
| `requirement_type` | `TEXT` | NOT NULL | Functional, Architectural, Security, Compliance, Performance, Non-Functional. |
| `deferral_reason` | `TEXT` | NOT NULL | Formal taxonomy classification reason. |
| `deferral_phase` | `TEXT` | NOT NULL | Inception, Sprint Planning, Architecture, Development, QA/Testing. |
| `decision_maker` | `TEXT` | NOT NULL | Individual and role responsible for the deferral decision. |
| `owner` | `TEXT` | NOT NULL | Engineering squad responsible for remediation. |
| `target_milestone` | `TEXT` | NOT NULL | Target release milestone (e.g., Release 1.0, Release 2.0). |
| `resolution_criteria` | `TEXT` | NOT NULL | Explicit verifiable conditions required to resolve the debt. |
| `status` | `TEXT` | NOT NULL DEFAULT 'Deferred' | Deferred, Under Review, Remediating, Resolved, Accepted Permanent. |
| `created_date` | `TEXT` | NOT NULL | ISO date string (YYYY-MM-DD). |
| `review_date` | `TEXT` | NOT NULL | Target date for formal governance review (YYYY-MM-DD). |
| `deadline_date` | `TEXT` | NOT NULL | Hard resolution deadline date (YYYY-MM-DD). |
| `business_impact` | `INTEGER` | NOT NULL DEFAULT 3 (1-5) | Business / stakeholder value impact. |
| `arch_impact` | `INTEGER` | NOT NULL DEFAULT 3 (1-5) | Structural / architectural blast radius. |
| `safety_impact` | `INTEGER` | NOT NULL DEFAULT 3 (1-5) | Security, safety, or regulatory exposure. |
| `occurrence_prob` | `INTEGER` | NOT NULL DEFAULT 3 (1-5) | Likelihood of defect induction or neglect. |
| `detection_difficulty` | `INTEGER` | NOT NULL DEFAULT 3 (1-5) | Invisibility / difficulty of detecting issues. |
| `cost_of_delay` | `INTEGER` | NOT NULL DEFAULT 3 (1-5) | Economic or technical penalty of postponement. |
| `estimated_effort` | `INTEGER` | NOT NULL DEFAULT 8 (1-100) | Story points required for remediation. |
| `resolution_notes` | `TEXT` | NULLABLE | Verification notes or PR links proving resolution. |
| `resolved_date` | `TEXT` | NULLABLE | Date debt was formally marked resolved. |
| `resolution_type` | `TEXT` | NULLABLE | Implemented & Verified, Absorbed into Redesign, etc. |
| `updated_at` | `TEXT` | NOT NULL | ISO timestamp of last update. |

### Table 2: `debt_dependencies`
Represents directed dependency edges between requirement debts.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PRIMARY KEY AUTOINCREMENT | Edge identifier. |
| `debt_id` | `TEXT` | NOT NULL, FK(`requirement_debts.debt_id`) | The dependent requirement debt. |
| `depends_on_debt_id` | `TEXT` | NOT NULL, FK(`requirement_debts.debt_id`) | The prerequisite requirement debt that blocks `debt_id`. |
| `dependency_type` | `TEXT` | NOT NULL DEFAULT 'Blocks' | Blocks, Architectural Precondition, Data Dependency. |
| `notes` | `TEXT` | NULLABLE | Explanatory rationale for the dependency. |
| `created_at` | `TEXT` | NOT NULL | ISO timestamp of edge creation. |

### Table 3: `review_sessions`
Chronicles formal review meetings, discussions, and schedule adjustments.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PRIMARY KEY AUTOINCREMENT | Review record identifier. |
| `debt_id` | `TEXT` | NOT NULL, FK(`requirement_debts.debt_id`) | Target debt item. |
| `review_date` | `TEXT` | NOT NULL | Date meeting was conducted. |
| `reviewer_name` | `TEXT` | NOT NULL | Reviewing authority. |
| `reviewer_role` | `TEXT` | NOT NULL | Title / organizational role. |
| `outcome` | `TEXT` | NOT NULL | Retain Debt, Extend Review Date, Escalate Priority, Initiate Remediation, etc. |
| `notes` | `TEXT` | NOT NULL | Meeting minutes and justifications. |
| `new_review_date` | `TEXT` | NULLABLE | Extended target review date if granted. |
| `created_at` | `TEXT` | NOT NULL | ISO timestamp. |

### Table 4: `release_gates`
Defines quality gate criteria and stores evaluation outcomes.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PRIMARY KEY AUTOINCREMENT | Gate identifier. |
| `gate_name` | `TEXT` | NOT NULL | Human-readable name (e.g., Release 1.0 GA Gate). |
| `target_milestone` | `TEXT` | NOT NULL | Milestone version to evaluate. |
| `max_critical_debts` | `INTEGER` | NOT NULL DEFAULT 0 | Maximum allowed Critical risk debts (default: 0). |
| `max_high_debts` | `INTEGER` | NOT NULL DEFAULT 1 | Maximum allowed High risk debts (default: 1). |
| `max_aggregate_risk` | `REAL` | NOT NULL DEFAULT 150.0 | Maximum allowed total portfolio risk score. |
| `status` | `TEXT` | NOT NULL DEFAULT 'Pending' | Pending, Passed, Conditional, Blocked, Passed (Signed Off). |
| `evaluation_date` | `TEXT` | NULLABLE | Date of last live evaluation. |
| `evaluation_summary` | `TEXT` | NULLABLE | Textual summary of evaluation results. |
| `signoff_by` | `TEXT` | NULLABLE | Signing authority name. |
| `signoff_notes` | `TEXT` | NULLABLE | Sign-off rationale and justifications. |
| `created_at` | `TEXT` | NOT NULL | ISO timestamp. |

### Table 5: `audit_log`
Immutable system audit ledger for complete governance traceability.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PRIMARY KEY AUTOINCREMENT | Audit log sequence number. |
| `debt_id` | `TEXT` | NULLABLE | Target debt ID (or NULL for system actions). |
| `action` | `TEXT` | NOT NULL | Event type (DEBT_CREATED, REVIEW_CONDUCTED, etc.). |
| `performed_by` | `TEXT` | NOT NULL | Actor name and role. |
| `details` | `TEXT` | NOT NULL | Explanatory description and diff of changes. |
| `created_at` | `TEXT` | NOT NULL | ISO timestamp. |
| `prev_hash` | `TEXT` | NULLABLE | SHA-256 hash of previous block (NULL for genesis block). |
| `entry_hash` | `TEXT` | NULLABLE | SHA-256 hash chaining all fields: `sha256(prev_hash + '|' + id + ...)`. |

---

## 4. Concurrency, Security, and Windows Portability

1. **SQLite Thread Safety:** SQLite is opened with `check_same_thread=False` and uses a context-managed connection pool in FastAPI dependencies. Write locks are fast and minimal.
2. **Restricted CORS Policy:** Cross-Origin Resource Sharing is strictly constrained to explicitly configured origins (`http://127.0.0.1:8000`, `http://localhost:8000`, or environment variable `RDL_ALLOWED_ORIGINS`). Arbitrary untrusted web origins are rejected.
3. **Cryptographic Tamper-Evidence:** All audit records are cryptographically hash-chained via SHA-256. Any modification or deletion of historic records severs the chain and is detected by `GET /api/audit/verify`.
4. **Offline Local Execution:** All CSS styles, SVG charts, and JavaScript modules are self-contained. The system requires zero internet access during execution.
5. **Cross-Platform Compatibility:** Paths are handled using Python's `pathlib.Path` with forward slashes for Windows compatibility.


## Additional Editable Design Diagrams

The `docs/diagrams/` directory also contains editable Draw.io files for DFD Level 0, DFD Level 1, UML Use Case, UML Component, and UML Sequence views. These diagrams describe the current local web application and its API, service, and SQLite data flows.
