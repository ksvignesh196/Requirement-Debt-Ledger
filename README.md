# Requirement Debt Ledger (RDL)

### *Design and Implementation of a Risk-Aware, Time-Bound Requirement Debt Ledger for Software Requirements Management*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite-3-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-66_Passed-brightgreen.svg)](https://docs.pytest.org/)
[![UI](https://img.shields.io/badge/Frontend-Vanilla_HTML5_CSS3_JS-E34F26.svg)]()

A local-first Software Engineering application and academic demonstrator that implements a structured, mathematically explainable methodology for managing deferred software requirements across the Software Development Life Cycle (SDLC).

---

## 1. Project Overview & Core Innovations

During agile software development, requirements are routinely postponed due to sprint schedule compression, technical uncertainties, third-party dependency delays, budget limitations, or evolving specifications. In traditional practice, teams track these deferred items in ordinary, flat task backlogs (such as Jira or Trello) or static traceability spreadsheets (such as IBM DOORS).

However, **deferred requirements behave like financial debt**:
- As time elapses and downstream architecture is constructed upon incomplete foundations, the effort and friction required to integrate the missing capability **compound dynamically over time ("accruing interest")**.
- Unaddressed compliance or security debts silently increase vulnerability exposure as user adoption grows.
- Unmonitored requirement interdependencies create hidden **cascade bottlenecks and circular deadlocks** that jeopardize release schedules.

The **Requirement Debt Ledger (RDL)** treats unresolved requirements as managed debt items with:
1. **Structured Deferral Records:** Formal deferral taxonomy, responsible decision-maker, owner squad, milestone targets, estimated story points, and explicit verifiable resolution criteria.
2. **Explainable, Time-Dependent Dynamic Risk:** Base multi-factor severity ($I$), probability ($O$), detection difficulty ($D$), 14-day grace period, daily compounding interest rate ($0.8\%/\text{day}$, with sensitivity toggles for 0.4% and 1.2%), and clarified 30-day epoch overdue breach penalties (capping at 2.0x).
3. **Dependency Impact Simulator (Distinctive Feature A):** Level-order BFS cascade traversal with diamond graph deduplication (zero double-counting of overlapping paths), DFS cycle deadlock prevention, and portfolio risk delta calculation.
4. **Explainable, Effort-Aware Resolution Recommendations (Distinctive Feature B):** Multi-Criteria Decision Model (MCDM) prioritizing remediation by dynamic risk (35%), cascaded unblocking (30%), business value (20%), and urgency (15%), divided by sublinear effort elasticity ($E^{0.70}$). Includes an interactive Pairwise Contrast Tool with natural-language contrastive rationale.
5. **What-If Release Planning Sandbox (Distinctive Feature C):** 100% in-memory sandbox evaluating candidate remediation plans (Blocker Triage, Critical Triage, Quick Wins under budget, and Custom) against target milestones without mutating the live SQLite database until explicitly applied.
6. **Multi-Horizon Risk Forecasting (Distinctive Feature D):** Projects dynamic risk across selected future horizons under the supported Status Quo and Timely Review assumptions, with a configurable daily interest-rate input.
7. **Tamper-Evident Cryptographic Audit Ledger:** SHA-256 hash chaining across every audit entry with an automated verification API (`GET /api/audit/verify`) detecting direct SQL manipulation.
8. **Release-Readiness Quality Gates:** Automated gate checks enforcing zero-critical debt tolerances, aggregate capacity limits, and formal sign-off governance.

---

## 2. Technology Stack

The project is built entirely on a lightweight, zero-cloud, beginner-friendly local stack:

- **Frontend:** Pure HTML5, modern CSS3 (custom properties, responsive grid, light theme), and Vanilla JavaScript (ES6+). Zero external framework dependencies, zero npm builds.
- **Backend:** Python 3.10+ with FastAPI and Uvicorn.
- **Database:** SQLite persistent database with foreign keys enabled (`PRAGMA foreign_keys = ON;`) and indexing.
- **Testing:** Pytest with FastAPI TestClient (56 automated unit and integration tests in the current project version).
- **Architecture Diagrams:** diagrams.net / draw.io editable XML (`.drawio`) and rendered vector graphics (`.svg`).

---

## 3. Directory Structure

```
requirement-debt-ledger\
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI entrypoint, middleware, static mounts
│   ├── config.py                   # Model constants, weights, and file paths
│   ├── database.py                 # SQLite connection manager and DDL schema
│   ├── models/                     # Pydantic v2 data models
│   │   ├── __init__.py
│   │   ├── debt_item.py            # Debt item schemas & risk breakdown
│   │   ├── dependency.py          # Dependency edge & graph schemas
│   │   ├── review.py              # Review session & audit trail schemas
│   │   └── release_gate.py        # Release gate criteria & sign-off schemas
│   ├── services/                   # Mathematical domain service engines
│   │   ├── __init__.py
│   │   ├── debt_service.py         # CRUD, filtering, search, and enrichment
│   │   ├── risk_engine.py          # Multi-factor risk & compounding interest
│   │   ├── dependency_engine.py    # DFS cycle detection, blocked cascade & DPI
│   │   ├── escalation_engine.py    # Review schedules & breach status
│   │   ├── release_evaluator.py    # Quality gate evaluation & sign-offs
│   │   └── audit_service.py        # Immutable audit logging
│   ├── routers/                    # REST API endpoints
│   │   ├── __init__.py
│   │   ├── debts.py                # Debt CRUD & simulation
│   │   ├── dependencies.py         # Dependencies & graph visualizer
│   │   ├── reviews.py              # Review sessions & audit logs
│   │   ├── release_gates.py        # Release gate checks
│   │   ├── analytics.py            # Dashboard metrics & distributions
│   │   └── export.py               # CSV/JSON export & demo reset
│   └── static/                     # Frontend Single Page Application (SPA)
│       ├── index.html              # Main HTML container with all views & modals
│       ├── css/
│       │   └── style.css           # Responsive light theme
│       └── js/
│           ├── api.js              # REST fetch client wrapper
│           ├── dashboard.js        # KPI counters & pure SVG charts
│           ├── debts.js            # Ledger table, live search, filters, modals
│           ├── risk_calculator.js  # Interactive risk laboratory with math derivations
│           ├── graph_view.js       # Interactive SVG dependency graph visualizer
│           ├── release_view.js     # Release readiness gate inspector & sign-off
│           ├── simulation_view.js  # Auto-updating simulations and risk forecasts
│           └── app.js              # SPA coordinator and toast notifications
├── docs/                           # Comprehensive documentation
│   ├── METHODOLOGY.md              # Mathematical formulations & literature review
│   ├── ARCHITECTURE.md             # 4-tier design, data dictionary & schema
│   ├── API_DOCUMENTATION.md        # Complete REST endpoint specifications
│   ├── USER_MANUAL.md              # Demonstration walkthrough & viva questions
│   └── diagrams/                   # Editable .drawio and rendered .svg diagrams
│       ├── system_architecture.drawio
│       ├── system_architecture.svg
│       ├── debt_lifecycle.drawio
│       ├── debt_lifecycle.svg
│       ├── risk_interest_model.drawio
│       ├── risk_interest_model.svg
│       ├── er_diagram.drawio
│       └── er_diagram.svg
├── tests/                          # Automated Pytest suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures and test database setup
│   ├── test_risk_engine.py         # Base risk, compounding interest, overdue
│   ├── test_dependency_engine.py   # Cycle detection, blocked cascade, DPI
│   ├── test_escalation_engine.py   # Review schedules & breach severity
│   ├── test_release_evaluator.py   # Release gate checks & blockers
│   └── test_api.py                 # End-to-end REST API integration tests
├── data/
│   └── rdl.db                      # Persistent SQLite database
├── seed_data.py                    # Realistic enterprise demonstration seed script
├── run.py                          # Application launcher script
├── requirements.txt                # Python dependencies
└── README.md                       # Main project manual
```

---

## 4. Quick Start & Execution Guide

### Step 1: Install Dependencies
Open PowerShell or Command Prompt in the project directory:
```powershell
pip install -r requirements.txt
```

### Step 2: Seed the Database
Populate the SQLite database with 10 realistic enterprise software requirement debts (e-commerce payment gateway, PCI-DSS compliance, GDPR purging, distributed idempotency):
```powershell
python seed_data.py
```

**Note:** This command clears and recreates the demonstration records. Back up `data/rdl.db` first if you have entered data you need to keep.

### Step 3: Run the Application Server
```powershell
python run.py
```
The web application will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 5. Running Automated Tests

Run the complete test suite using Pytest:
```powershell
python -m pytest -v
```

### Test Coverage Summary:
- **66 Automated Tests Passed in the current project version**
- Covers:
  - Base severity weighting & static risk normalization
  - Compounding debt interest beyond the 14-day grace period
  - Review schedule overdue penalty factors (1.25x epoch step, 2.0x ceiling)
  - Directed graph DFS cycle detection & prevention
  - Transitive downstream blocked requirements traversal with diamond deduplication
  - Debt Priority Index (DPI) calculation
  - Multi-Criteria Decision Model (MCDM) recommendation ranking & factor contribution breakdown
  - Pairwise contrastive explanation generation
  - What-If Release Planning sandbox isolation & atomic plan application
  - Multi-horizon risk forecasting (15 to 180 days)
  - Cryptographic SHA-256 audit hash-chain integrity & tamper detection
  - Trusted CORS origin enforcement & strict Pydantic v2 input validations
  - Escalation schedule states (`OK`, `UPCOMING_REVIEW`, `OVERDUE_REVIEW`, `CRITICAL_BREACH`)
  - Release readiness evaluation, policy violations, and sign-offs that re-check the gate before recording approval
  - End-to-end REST API endpoints (FastAPI TestClient)
  - Simulation UI auto-refresh triggers, redundant-button removal, and stale-response guards

---

## 6. Reproducible Empirical Evaluation

Execute the automated benchmarking suite comparing RDL against FIFO and Static Severity baselines:
```powershell
python evaluation.py
```
The evaluation is based on a 15-item synthetic benchmark and reports FIFO, static-severity, and RDL ranking outcomes at three effort budgets. It does not demonstrate that RDL outperforms every baseline on every metric. See [docs/EVALUATION_REPORT.md](docs/EVALUATION_REPORT.md) for the actual run output, interpretation, and limitations.

---

## 7. Architecture & Methodology Diagrams

The original system, lifecycle, risk-model, and ER diagrams are available in editable Draw.io XML and SVG. Additional DFD and UML diagrams are provided as editable Draw.io files:

1. **System Architecture:**
   - SVG: [system_architecture.svg](docs/diagrams/system_architecture.svg)
   - Draw.io: [system_architecture.drawio](docs/diagrams/system_architecture.drawio)
2. **Debt Lifecycle State Machine:**
   - SVG: [debt_lifecycle.svg](docs/diagrams/debt_lifecycle.svg)
   - Draw.io: [debt_lifecycle.drawio](docs/diagrams/debt_lifecycle.drawio)
3. **Risk & Compounding Interest Model:**
   - SVG: [risk_interest_model.svg](docs/diagrams/risk_interest_model.svg)
   - Draw.io: [risk_interest_model.drawio](docs/diagrams/risk_interest_model.drawio)
4. **Database Entity Relationship Diagram (ERD):**
   - SVG: [er_diagram.svg](docs/diagrams/er_diagram.svg)
   - Draw.io: [er_diagram.drawio](docs/diagrams/er_diagram.drawio)
5. **DFD Level 0:** [dfd_level_0.drawio](docs/diagrams/dfd_level_0.drawio)
6. **DFD Level 1:** [dfd_level_1.drawio](docs/diagrams/dfd_level_1.drawio)
7. **UML Use Case:** [uml_use_case.drawio](docs/diagrams/uml_use_case.drawio)
8. **UML Component:** [uml_component.drawio](docs/diagrams/uml_component.drawio)
9. **UML Sequence:** [uml_sequence.drawio](docs/diagrams/uml_sequence.drawio)

---

## 7. College Viva & Academic Defense Highlights

When demonstrating this project for academic review, emphasize these key innovations:
1. **Financial Debt Metaphor:** Explain how requirements accrue "operational and architectural interest" over time.
2. **Interactive Risk Laboratory (Tab 3):** Live demonstrate the sliders showing exact step-by-step mathematical derivation from severity to dynamic risk.
3. **Cycle Prevention in Directed Graph (Tab 4):** Show that the backend uses Depth-First Search to reject cyclic dependencies, avoiding deadlocks.
4. **Automated Release Readiness Gates (Tab 5):** Demonstrate how open Critical debts automatically block milestone releases until resolved or formally signed off.
5. **Full User Manual:** Refer to [docs/USER_MANUAL.md](docs/USER_MANUAL.md) for detailed viva Q&A and presentation talking points.

---

## 8. License

Developed for academic presentation and research demonstration in Software Engineering and Requirements Engineering. Free for educational and non-commercial development.
