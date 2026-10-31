# Requirement Debt Ledger (RDL): User Demonstration Manual & Viva Guide

*Step-by-Step Live Demonstration Walkthrough and Defense Notes for Academic Review*

---

## 1. Quick Demonstration Setup

To run the live application on a Windows laptop:

1. Open PowerShell in the project directory (`c:\Users\Kishore\Documents\Vig PJT`).
2. Run the application:
   ```powershell
   python run.py
   ```
3. Open your browser and navigate to:
   - **Dashboard & User Interface:** `http://127.0.0.1:8000`

> [!TIP]
> If at any time during the demonstration you wish to restore the clean state, simply click the **"🔄 Reset Demo Data"** button on the top-right header!

---

## 2. Step-by-Step Viva Demonstration Script

### Act 1: The Executive Dashboard (Tab 1)
1. **Show the 5 KPI Cards:**
   - Explain: *"Here we see 8 active requirement debts, 1 critical risk debt, 3 overdue items, and an aggregate portfolio risk of ~280 points."*
   - Highlight: Notice that 2 debts are already resolved (`REQ-DEBT-009` and `REQ-DEBT-010`), demonstrating that the ledger tracks the complete lifecycle from deferral to verified resolution.
2. **Show the 3 SVG Charts:**
   - **Risk Tier Distribution Donut:** Visualizes active debts across Critical, High, Moderate, and Low tiers.
   - **Top Deferral Reasons Bar Chart:** Demonstrates taxonomy breakdown (Time Constraint, Technical Uncertainty, Third-Party Dependency, etc.).
   - **Debt Concentration by Module:** Identifies high-risk subsystems (Payment Gateway and Security & Compliance have the highest concentration).
3. **Show Priority Focus Table:**
   - Point to the items with the highest **Debt Priority Index (DPI)**: explains why a moderate risk item that blocks 3 downstream features might have higher remediation priority than an isolated high-risk item.

---

### Act 2: The Debt Ledger & Explainable Risk (Tab 2)
1. **Live Filtering & Search:**
   - Type `"payment"` in the search bar to demonstrate real-time filtering.
   - Filter by Status (`Deferred`), Module (`Payment Gateway`), and Risk Tier (`Critical`).
2. **Click "🔍 Details" on `REQ-DEBT-001`:**
   - Walk the examiner through the **Explainable Dynamic Risk Breakdown**:
     - *Base Static Risk:* Derived from Composite Severity (Business: 4, Arch: 4, Compliance: 4), Occurrence (4), Detection (3) $\rightarrow$ Base Risk = 38.4/100.
     - *Compounding Debt Interest:* Aged 45 days (31 days past 14-day grace period). At 0.8% daily, accrued interest is **+28.0%**.
     - *Overdue Schedule Penalty:* Review date was 8 days ago $\rightarrow$ **x1.07 penalty multiplier**.
     - *Effective Dynamic Risk:* Scaled to **52.4 (Moderate)**.
   - Show the human-readable explanation sentence generated dynamically by the engine.
3. **Record a Review Session:**
   - Click **"📋 Review"** on `REQ-DEBT-003`.
   - Enter Reviewer Name (`Principal Architect`), Outcome (`Extend Review Date`), and new date.
   - Click Save: Note the toast confirmation and check the updated review date.
4. **Formally Resolve a Debt:**
   - Click **"✅ Resolve"** on `REQ-DEBT-001`.
   - Select Resolution Type (`Implemented & Verified`), provide verification test notes, and click **"Verify & Close Debt"**.
   - Show that the item transitions to `Resolved`, badge turns green, and dashboard KPIs update immediately.

---

### Act 3: Explainable, Effort-Aware Recommendations & Pairwise Contrast Tool
1. **Navigate to the "💡 Resolution Recommendations" Tab:**
   - Explain: *"Unlike flat task lists, RDL uses an Explainable Multi-Criteria Decision Model (MCDM) that balances dynamic risk (35%), cascaded unblocking (30%), business value (20%), and deadline urgency (15%), divided by sublinear effort elasticity ($E^{0.70}$)."*
   - Show the ranked list with **Remediation ROI** scores and factor contribution breakdown progress bars.
2. **Demonstrate the "⚖️ Pairwise Contrast Tool":**
   - Click **"⚖️ Contrast vs Another"** on the #1 ranked item.
   - Select another candidate (e.g., comparing `DEBT-AUTH-001` vs `DEBT-OBS-001`).
   - Click **"Generate Contrastive Decision Explanation"**:
     - Walk through the auto-generated natural language contrastive rationale.
     - Show the side-by-side comparison matrix breaking down Risk, Blocked Dependencies, Story Point Effort, and ROI delta.

---

### Act 4: The Simulation & Forecasting Suite
1. **Sub-View 1: Dependency Impact Simulator:**
   - Select a requirement debt (e.g. `DEBT-AUTH-001`).
   - Adjust the **Additional Delay Duration** slider to 45 days. The value label updates while dragging, and the simulation refreshes automatically when the slider is released. Changing the selected requirement also refreshes the result. There is no separate Run button.
   - Point out the **Net Risk Delta** (+X points surge if postponed).
   - Point out **Direct vs Indirect affected items**.
   - Emphasize the **Diamond Graph Deduplication**: overlapping dependency paths are safely consolidated without double counting.
2. **Sub-View 2: What-If Release Planning Sandbox:**
   - Select target milestone (`Release 1.0 - Core Launch`). The plan comparison refreshes automatically when the milestone changes; there is no separate Compare Plans button.
   - Show the 4 candidate plans side-by-side:
     - *Status Quo (No intervention)* $\rightarrow$ Gate: `BLOCKED`
     - *Plan A (Blocker Triage)* $\rightarrow$ Resolves dependencies blocking others
     - *Plan B (Critical Risk Triage)* $\rightarrow$ Resolves critical risk items
     - *Plan C (Quick Wins under 35 pts budget)* $\rightarrow$ Resolves high-ROI items
   - Demonstrate the **Sandbox Isolation Guarantee**: simulation is 100% in-memory; live database records remain untouched.
   - Demonstrate **"Apply Plan to Actual Ledger"**: click the remediation action on a candidate plan to move selected open items to `Remediating` and log the decision. The application does not mark them `Resolved`; formal implementation and verification are still required.
3. **Sub-View 3: Multi-Horizon Risk Forecasting & Rate Sensitivity:**
   - Click the rate toggle buttons: **0.4% / day (Mild)**, **0.8% / day (Standard)**, and **1.2% / day (High)**. The forecast table refreshes automatically for the selected rate; there is no separate Forecast button.
   - Show the forecast table projecting risk at +15, +30, +60, +90, and +180 days ahead under the selected scenario (`status_quo` or `timely_review`) and the chosen daily interest-rate assumption.

---

### Act 5: The Dependency Graph Visualizer (Tab 4)
1. Show the interactive node-link network:
   - Nodes are colored by their dynamic risk tier.
   - Cyan glowing line highlights the **Critical Path**: `REQ-DEBT-005 ➔ REQ-DEBT-003 ➔ REQ-DEBT-001`.
2. Click any node (e.g. `REQ-DEBT-003`):
   - The inspector panel reveals that `REQ-DEBT-003` blocks `REQ-DEBT-001` and depends on `REQ-DEBT-005`.
3. **Demonstrate Cycle Prevention:**
   - Click **"+ Link Requirement Dependency"**.
   - Attempt to make `REQ-DEBT-005` depend on `REQ-DEBT-001` (which would create a cycle: 001 ➔ 003 ➔ 005 ➔ 001).
   - Click Save: Show that the backend **mathematically detects the cycle using DFS and rejects it**, displaying a clear warning to prevent architectural deadlocks.

---

### Act 6: Release Readiness Gates (Tab 6)
1. Point to **"Release 1.0 General Availability Gate"**:
   - Click **"⚡ Evaluate Gate"**.
   - The gate evaluates to **`BLOCKED`**.
   - Explain: *"Release 1.0 is blocked because it has a hard gate requirement of 0 Critical debts, but `REQ-DEBT-002` (PCI-DSS Tokenization) is currently Critical."*
2. Point to **"Release 2.0 Feature Milestone Gate"**:
   - Click **"⚡ Evaluate Gate"**.
   - The gate result is calculated from the current milestone data and configured thresholds; do not assume it is `PASSED` before clicking Evaluate.
3. Demonstrate **"✍️ Formal Sign-Off"**:
   - Click Sign-Off on a gate, enter signing authority and risk acceptance justification, and show the audit event generated. The hash chain is tamper-evident, not tamper-proof.

---

### Act 7: Tamper-Evident Audit Trail & Cryptographic Verification (Tab 7)
1. Show the chronological, cryptographically chained audit log:
   - Point out the **Block Hash (SHA-256)** column showing truncated hashes (`e.g. 5a1b...c98d`).
2. Demonstrate **"🛡️ Verify Cryptographic Chain"**:
   - Click the verification button:
   - Point to the green verification banner: *"Cryptographic Integrity Verified: All 12 audit records form an unbroken SHA-256 hash chain with valid genesis linkage."*
   - Explain to examiners: *"If anyone directly edits SQLite rows or tampers with historical sign-offs, the SHA-256 chain breaks immediately and the UI flags the exact compromised record."*

---

## 3. Frequently Asked Viva Questions & Answers

### Q1: "How is Requirement Debt different from ordinary Technical Debt?"
> **Answer:** *Technical debt (as coined by Cunningham) predominantly focuses on code-level issues—code smells, bad refactorings, low test coverage, and duplicate lines (tools like SonarQube). Requirement Debt is an upstream phenomenon: it represents functional, architectural, or regulatory requirements that were deliberately deferred or incompletely specified during design or sprint planning. While code technical debt measures how code was written, requirement debt measures what necessary system capabilities were postponed and how that postponement compounds architectural friction over time.*

### Q2: "Why not simply track these as backlog tickets in Jira?"
> **Answer:** *Jira is a flat task tracker where priorities are static labels. A "High Priority" ticket in Jira stays High whether it has been in the backlog for 2 days or 200 days. Jira lacks mathematical compounding interest, dynamic overdue breach penalties, transitive downstream impact scoring, and release readiness gates. In RDL, risk is an active time-dependent function that forces teams to confront aging debt before it creates architectural deadlocks.*

### Q3: "What prevents circular dependencies in the requirement graph?"
> **Answer:** *The RDL Dependency Engine models requirements as a directed graph $G=(V, E)$. Before any new dependency edge $(u, v)$ is committed to SQLite, a Depth-First Search (DFS) algorithm traverses from $v$ looking for a path to $u$. If $u$ is reachable, a directed cycle exists. The API immediately aborts the transaction with an HTTP 400 error and identifies the cycle path.*

### Q4: "How do you avoid double-counting in diamond dependency graphs?"
> **Answer:** *When requirement A blocks both B and C, and both B and C block D, a naive recursive traversal encounters D twice. RDL uses a level-order BFS with a strict `visited` set. Each node is recorded exactly once at its shortest topological distance. This guarantees that downstream blast radius and risk scores are mathematically exact without duplicate inflation.*

### Q5: "Why did you use sublinear effort elasticity (E^0.70) in recommendation scoring?"
> **Answer:** *Linear division by effort (Benefit / Effort) creates an extreme starvation bias where trivial 1-point tasks always beat essential 8-point architectural components. Conversely, ignoring effort leads to scheduling massive 40-point epics that exhaust capacity. Sublinear elasticity ($E^{0.70}$) dampens the effort penalty, allowing teams to balance efficient quick wins with critical architectural foundations.*

### Q6: "Is your audit trail truly tamper-proof?"
> **Answer:** *In standard software architectures with relational databases, claiming an absolute 'tamper-proof' audit trail without write-once-read-many (WORM) hardware or distributed consensus is technically incorrect. Instead, RDL implements tamper-evident cryptographic hash chaining: every audit row contains the SHA-256 hash of its predecessor. Any unauthorized SQL edit or row deletion severs the chain and is detected by the `/api/audit/verify` verification engine.*

### Q7: "Why did you choose vanilla HTML5/CSS3/JavaScript instead of React or Angular?"
> **Answer:** *The project prioritizes transparency, zero-dependency local execution, and academic auditability. Using modern vanilla JavaScript and CSS custom properties eliminates bloated node_modules, build pipelines, and compilation overhead, ensuring the application runs instantly and reliably on any browser without external runtime dependencies.*

### Q8: "How was the system empirically evaluated?"
> **Answer:** *We developed a reproducible synthetic evaluation harness (`evaluation.py`) comparing the RDL ranking rule with FIFO and static-severity baselines across 15 synthetic requirements and three effort budgets. The verified run showed that RDL changes which items are selected, but it did not outperform both baselines on every metric. For example, at 15 points it matched FIFO on risk removed and newly unblocked items; at 25 points it selected one additional item, while static severity removed slightly more risk and unblocked more items. The benchmark is illustrative and requires evaluation on real project histories before making general performance claims.*
