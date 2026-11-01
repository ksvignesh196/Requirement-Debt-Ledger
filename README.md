# Requirement Debt Ledger (RDL)

### Academic framing
**A Risk-Aware Framework for Managing Deferred Software Requirements**

A local-first Software Engineering application that demonstrates a structured way to record, assess, prioritise and review requirements that have been deferred during software development.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-66%20passed-brightgreen.svg)](https://docs.pytest.org/)

---

## 1. Overview

Software requirements are sometimes postponed because of limited time, cost, technical uncertainty, external dependencies or changing priorities. A normal task backlog can show that an item is still pending, but it may not show how the decision affects risk, dependent requirements or a future release.

The **Requirement Debt Ledger (RDL)** treats each deferred requirement as a debt record that can be reviewed throughout the Software Development Life Cycle (SDLC). The idea is similar to technical debt: leaving a requirement unresolved may create additional risk and make later work more difficult.

The application records information such as:

- The requirement and reason it was deferred.
- Business, architectural and safety impact.
- Occurrence probability and difficulty of detecting the issue.
- Responsible owner, estimated effort and target milestone.
- Review date, resolution deadline and closure criteria.
- Dependencies on other deferred requirements.

RDL then applies explicit rules and calculations to help users understand the current position and compare possible actions. It is a decision-support tool; it does not automatically write, interpret or approve software requirements.

### Academic framing of the work

This implementation explores a **risk-aware, time-bound approach to deferred software requirements**. It brings together time-based risk assessment, dependency analysis, effort-aware prioritisation, release planning and audit records in one workflow. The weights, interest rate and thresholds are model assumptions selected for this prototype; they have not been calibrated against historical project data.

The current application uses deterministic calculations and graph algorithms. **It does not use an AI or machine-learning model.**

---

## 2. Main Features

### Requirement ledger

Create and maintain deferred requirement records, including their reason for deferral, owner, impact ratings, effort estimate, milestone, dates and resolution criteria. Records can be searched, filtered and updated as their status changes.

### Dynamic risk assessment

Calculates a base risk score from impact, occurrence probability and detection difficulty. The score can increase after a 14-day grace period and when the review date has passed. A risk tier is assigned to each active item.

### Dependency analysis

Stores links between requirements and displays their relationships. Depth-First Search (DFS) is used to detect cycles. Breadth-First Search (BFS) follows downstream dependencies and identifies direct and indirect effects without counting the same requirement more than once.

### Debt Priority Index (DPI)

Calculates a 0–100 priority index using dynamic risk, downstream impact, deadline urgency and cost of delay. DPI is one prioritisation measure in the application.

### Effort-aware recommendations

A separate recommendation score estimates the benefit of resolving an item and adjusts that benefit by estimated effort. The application also provides a pairwise comparison view to explain why one requirement ranks above another.

### Planning tools

- **Dependency Impact:** compares current and projected risk when an unresolved item is delayed.
- **What-If Release Planning:** evaluates alternative remediation plans against a target milestone and effort budget.
- **Risk Forecast:** projects portfolio risk across future time horizons under selected assumptions.
- **Risk Calculator:** displays the factors used to calculate an individual requirement's risk.

What-if plans are evaluated in an isolated in-memory simulation. The persistent records are changed only when a user explicitly chooses to start remediation from a plan.

### Release readiness and escalation

Evaluates unresolved requirements against configurable limits for Critical items, High items and aggregate risk. It also considers overdue reviews and deadline breaches. Review and deadline dates produce schedule states such as `UPCOMING_REVIEW`, `OVERDUE_REVIEW` and `CRITICAL_BREACH`.

### Audit trail

Records important changes in a SHA-256 hash-linked audit history. The verification function recomputes entry hashes and checks the link to the previous entry. This makes uncoordinated changes detectable; it does **not** make the database tamper-proof against an attacker who can rewrite the entire chain.

---

## 3. Calculation Method

The formulas below describe the current implementation. The weights, interest rate and gate limits are configurable model assumptions, not empirically established industry standards.

### 3.1 Dynamic risk score

All five input ratings are constrained to a scale from 1 to 5:

- `B`: business impact
- `A`: architectural impact
- `S`: safety impact
- `O`: occurrence probability
- `D`: detection difficulty

**Composite impact**

```text
I = 0.35B + 0.35A + 0.30S
```

**Base risk**

```text
Base Risk = (I × O × D / 125) × 100
```

**Time-based interest**

The default grace period is 14 days. Interest is applied only to days beyond that period.

```text
t = max(0, elapsed_days - 14)
Interest Factor = (1 + r)^t
```

The default daily rate `r` is `0.008` (0.8%). Sensitivity analysis also provides 0.4% and 1.2% daily presets.

**Overdue review penalty**

```text
P = 1.0                                      if not overdue
P = min(2.0, 1 + (overdue_days / 30) × 0.25) if overdue
```

**Final dynamic risk**

```text
Dynamic Risk = min(100, Base Risk × Interest Factor × P)
```

Risk tiers are assigned as follows:

| Dynamic risk | Tier |
|---:|---|
| Below 35 | Low |
| 35 to below 65 | Moderate |
| 65 to below 85 | High |
| 85 to 100 | Critical |

The portfolio risk shown in the application is the sum of dynamic risk scores for active (unresolved) requirements.

### 3.2 Debt Priority Index (DPI)

DPI is calculated separately from the recommendation score.

**Downstream score**

```text
Downstream Score = min(100, downstream_blocked_count × 20)
```

**Urgency score**

| Deadline condition | Urgency score |
|---|---:|
| Deadline has passed | 100 |
| Deadline is within 7 days | 80 |
| Deadline is within 21 days | 50 |
| More than 21 days remain | 25 |

**Cost-of-delay score**

The input is limited to the range 1–5.

```text
Cost-of-Delay Score = clamped_cost_of_delay × 20
```

**DPI formula**

```text
DPI = min(100,
    0.45 × Dynamic Risk
  + 0.25 × Downstream Score
  + 0.20 × Urgency Score
  + 0.10 × Cost-of-Delay Score
)
```

### 3.3 Effort-aware recommendation score

This is a different score from DPI. It estimates the benefit of remediation and then adjusts it for effort.

**Weighted contributions**

```text
Risk Contribution       = 0.35 × Dynamic Risk
Cascade Score           = min(100, 0.5 × Downstream Risk Sum
                                  + 15 × Downstream Blocked Count)
Cascade Contribution    = 0.30 × Cascade Score
Business Value Score    = Business Impact × 20
Business Contribution   = 0.20 × Business Value Score
Urgency Contribution    = 0.15 × Urgency Score
```

The recommendation engine uses the current escalation state and deadline to determine urgency. It then calculates:

```text
Gross Benefit = sum of the four contributions
Effort Factor = max(1, Estimated Effort)^0.70
Remediation ROI = (Gross Benefit / Effort Factor) × 5
Recommendation Score = min(100, Remediation ROI)
```

Requirements are ranked by the final recommendation score, highest first. The exponent `0.70` is the implementation's effort adjustment parameter.

### 3.4 Dependency impact calculations

- DFS checks for directed cycles in the dependency graph.
- BFS traverses downstream dependencies and records the distance from the starting requirement.
- A visited set prevents duplicate counting when multiple paths reach the same requirement.
- Critical-path depth is based on the longest downstream chain.
- Cascaded blocked risk is the sum of the current dynamic risk scores of the affected requirements.

For an additional-delay simulation:

```text
Risk Delta = max(0, Projected Target Risk - Current Target Risk)
Projected Portfolio Risk = Current Portfolio Risk + Risk Delta
Risk Increase (%) = (Risk Delta / Current Portfolio Risk) × 100
```

The percentage is calculated only when the current portfolio risk is greater than zero. The simulator also shows uncapped risk pressure (`Base Risk × Interest Factor × Overdue Penalty`) so the underlying growth remains visible even when the displayed dynamic risk has reached its 100-point cap.

### 3.5 What-if release planning

The planner evaluates status quo and candidate remediation plans, including dependency-unblocking, critical-risk, quick-win and custom selections.

```text
Risk Reduction = Initial Aggregate Risk - Simulated Aggregate Risk
Risk Reduction (%) = (Risk Reduction / Initial Aggregate Risk) × 100
Total Effort = Sum of selected requirements' effort points
Efficiency = Risk Reduction Points / max(1, Total Effort)
```

The planner prefers the most efficient candidate that passes the simulated release checks. If none passes, it compares risk reduction first and efficiency second. Newly unblocked requirements are counted once. Starting remediation changes selected records to a remediation status; it does not mark the work as completed or verified.

### 3.6 Risk forecast

The forecast recalculates active requirement risk at future horizons. The default horizons are 0, 15, 30, 60, 90 and 180 days. The available scenarios are:

- **Status Quo:** requirements remain unresolved and their review dates are not moved forward.
- **Timely Review:** the forecast assumes reviews continue to be conducted on time, avoiding an overdue review penalty in the simulated horizon.

The daily interest rate can be varied. The API accepts a rate from 0.1% to 5% per day; the UI includes 0.4%, 0.8% and 1.2% presets.

### 3.7 Escalation and release gates

For unresolved items, the escalation engine applies the following order:

1. Past resolution deadline → `CRITICAL_BREACH`
2. Past review date → `OVERDUE_REVIEW`
3. Review due within 7 days → `UPCOMING_REVIEW`
4. Otherwise → `OK`

Resolved and accepted-permanent items are assigned `RESOLVED`.

The default release gate limits are:

| Gate condition | Default limit |
|---|---:|
| Critical unresolved requirements | 0 allowed |
| High unresolved requirements | At most 1 |
| Aggregate unresolved risk | At most 150 |

Unresolved review or deadline escalations are also reported. A Critical gate violation produces `BLOCKED`; other violations produce `CONDITIONAL`; no violations produces `PASSED`. A blocked gate cannot be signed off. Conditional sign-off does not mean that the release is fully ready.

### 3.8 SHA-256 audit verification

Each audit entry contains a previous hash and a new entry hash. The hash is calculated from the combined entry data:

```text
previous_hash | entry_id | debt_id | action | actor | details | timestamp
```

```text
entry_hash = SHA-256(combined_entry_data)
```

The first entry uses a fixed all-zero genesis hash. Verification recalculates each entry hash and checks that its recorded previous hash matches the preceding entry's hash.

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript | Browser interface and interactive views |
| Backend | Python 3.10+, FastAPI, Uvicorn | REST API and application logic |
| Data validation | Pydantic v2 | Request and response validation |
| Database | SQLite | Local persistence for requirements, dependencies, reviews, gates and audit records |
| Testing | Pytest, FastAPI TestClient, HTTPX | Unit and API integration tests |
| Diagrams | diagrams.net / Draw.io | Editable architecture and design diagrams |

The frontend does not require a JavaScript framework or an npm build step. The application runs locally and does not require a cloud service for its normal demo workflow.

---

## 5. System Structure

```text
requirement-debt-ledger/
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI application and router registration
│   ├── config.py                       # Risk, priority, release and CORS settings
│   ├── database.py                     # SQLite connection and schema setup
│   ├── models/                         # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── debt_item.py
│   │   ├── dependency.py
│   │   ├── recommendation.py
│   │   ├── release_gate.py
│   │   ├── review.py
│   │   └── simulation.py
│   ├── routers/                        # REST API routes
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── debts.py
│   │   ├── dependencies.py
│   │   ├── export.py
│   │   ├── recommendations.py
│   │   ├── release_gates.py
│   │   ├── reviews.py
│   │   └── simulations.py
│   ├── services/                       # Application and calculation logic
│   │   ├── __init__.py
│   │   ├── audit_service.py
│   │   ├── debt_service.py
│   │   ├── dependency_engine.py
│   │   ├── escalation_engine.py
│   │   ├── recommendation_engine.py
│   │   ├── release_evaluator.py
│   │   ├── risk_engine.py
│   │   └── simulation_engine.py
│   └── static/                         # Browser frontend
│       ├── index.html
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── api.js
│           ├── app.js
│           ├── dashboard.js
│           ├── debts.js
│           ├── graph_view.js
│           ├── recommendation_view.js
│           ├── release_view.js
│           ├── risk_calculator.js
│           └── simulation_view.js
├── data/
│   └── rdl.db                           # Included demonstration SQLite database
├── docs/
│   ├── API_DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   ├── EVALUATION_REPORT.md
│   ├── METHODOLOGY.md
│   ├── USER_MANUAL.md
│   └── diagrams/
│       ├── debt_lifecycle.drawio
│       ├── debt_lifecycle.svg
│       ├── dfd_level_0.drawio
│       ├── dfd_level_1.drawio
│       ├── er_diagram.drawio
│       ├── er_diagram.svg
│       ├── risk_interest_model.drawio
│       ├── risk_interest_model.svg
│       ├── system_architecture.drawio
│       ├── system_architecture.svg
│       ├── uml_component.drawio
│       ├── uml_sequence.drawio
│       └── uml_use_case.drawio
├── tests/                              # Automated test suite
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_audit_integrity.py
│   ├── test_dependency_engine.py
│   ├── test_escalation_engine.py
│   ├── test_presentation_smoke.py
│   ├── test_recommendation.py
│   ├── test_release_evaluator.py
│   ├── test_risk_engine.py
│   ├── test_security_cors.py
│   ├── test_simulation.py
│   ├── test_simulation_ui.py
│   └── test_validation_hardening.py
├── evaluation.py                       # Synthetic ranking and graph evaluation
├── requirements.txt
├── run.py                               # Local application launcher
├── seed_data.py                         # Recreates the demonstration dataset
└── README.md
```

---

## 6. Installation and Local Setup

### Prerequisites

- Python 3.10 or later
- pip
- Windows PowerShell, Command Prompt, macOS Terminal or Linux shell

### Step 1: Open the project folder

Open a terminal in the folder containing `run.py` and `requirements.txt`.

### Step 2: Create and activate a virtual environment (recommended)

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Start the application

```bash
python run.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser. The application initialises the SQLite schema when it starts.

### Demonstration data

The repository includes `data/rdl.db` with demonstration records. To recreate the seeded dataset, run:

```bash
python seed_data.py
```

**Important:** The seed script clears and recreates the demonstration data. Back up `data/rdl.db` before running it if you have added records that you want to keep.

### Optional CORS configuration

The application uses localhost origins by default. To allow a different trusted frontend origin, set `RDL_ALLOWED_ORIGINS` before starting the server. Multiple origins can be comma-separated.

**PowerShell example:**

```powershell
$env:RDL_ALLOWED_ORIGINS = "http://localhost:8000,http://127.0.0.1:8000"
python run.py
```

This setting is optional for the standard local setup. Do not commit secrets, credentials or private environment files to the repository. The current application does not require API keys for its normal operation.

---

## 7. Running the Tests

From the project root, with the virtual environment activated:

```bash
python -m pytest -v
```

The current project version was verified with **66 passing tests**. The tests cover:

- Base-risk weighting, risk limits and time-based interest.
- Overdue review penalty calculation and escalation states.
- Dependency traversal, cycle detection and duplicate-path handling.
- DPI and effort-aware recommendation calculations.
- Pairwise recommendation explanations.
- What-if planning isolation and plan application.
- Dependency impact simulations and multi-horizon forecasting.
- Release-gate evaluation and sign-off checks.
- SHA-256 audit-chain verification and tamper detection.
- API validation, CORS handling and frontend simulation behaviour.

Test results may vary if the code is changed. Run the command above to verify the version you have checked out.

---

## 8. Synthetic Evaluation

The project includes a small evaluation script that compares three prioritisation approaches:

- **FIFO:** older deferred items are selected first.
- **Static Severity:** higher base-risk items are selected first.
- **RDL:** the implementation's weighted risk, downstream, business-value and urgency contributions are adjusted by estimated effort.

Run it from the project root:

```bash
python evaluation.py
```

The current evaluation uses a **15-item synthetic dataset** and tests effort budgets of 15, 25 and 35 story points. It also measures selected in-memory graph operations.

The evaluation is exploratory. The results do not show that RDL outperforms every baseline on every metric. The dataset is synthetic, the weights are assumptions, and graph timings are local microbenchmarks rather than end-to-end application performance measurements. See [docs/EVALUATION_REPORT.md](docs/EVALUATION_REPORT.md) for the recorded results and limitations.

---

## 9. Documentation and Diagrams

The `docs/` folder contains additional project material:

- [Architecture](docs/ARCHITECTURE.md) — application layers, components and data structure.
- [Methodology](docs/METHODOLOGY.md) — model assumptions and calculation details.
- [API documentation](docs/API_DOCUMENTATION.md) — available REST endpoints.
- [User manual](docs/USER_MANUAL.md) — application walkthrough and usage guidance.
- [Evaluation report](docs/EVALUATION_REPORT.md) — synthetic evaluation results and limitations.

The `docs/diagrams/` folder contains editable Draw.io diagrams and SVG exports for the system architecture, debt lifecycle, risk-interest model, database ER diagram, data-flow diagrams and UML views.

---

## 10. Current Scope and Limitations

- The risk weights, 0.8% default daily interest rate, overdue penalty and release thresholds are model assumptions. They have not been calibrated using historical project data.
- Risk outputs depend on the quality of the ratings, dates, effort estimates and dependency links entered by the user.
- The evaluation uses a small synthetic dataset and does not establish performance on real project portfolios.
- The application is a local-first prototype. Multi-user authentication, hosted deployment, automated reminders and integrations with external project-management tools are not included in the current version.
- The SHA-256 audit chain is tamper-evident, not tamper-proof.

Possible next steps include calibrating the model with historical project data, adding user roles and access controls, integrating with tools such as Jira or Git, and providing scheduled review reminders and deployment support.

---

## 11. Academic Use

**Requirement Debt Ledger (RDL)** is developed as an academic Software Engineering implementation and demonstrator of a risk-aware method for managing deferred requirements.

The work focuses on the design of the record structure, risk and priority calculations, dependency analysis, remediation planning, release checks and audit traceability. All calculations are deterministic and can be inspected in the Python service modules under `app/services/`.

No separate open-source licence file is included in the current repository.
