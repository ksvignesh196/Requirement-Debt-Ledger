/**
 * Requirement Debt Ledger (RDL) - Release Readiness Gates View
 */
const ReleaseView = {
  gates: [],

  async init() {
    this.bindEvents();
    await this.loadGates();
  },

  bindEvents() {
    document.getElementById("btn-new-gate")?.addEventListener("click", () => this.openCreateGateModal());
    document.getElementById("form-create-gate")?.addEventListener("submit", (event) => this.submitCreateGate(event));
    document.getElementById("form-signoff-gate")?.addEventListener("submit", (event) => this.submitSignOff(event));
  },

  async loadGates() {
    try {
      this.gates = await API.getReleaseGates();
      this.renderGates();
    } catch (err) {
      console.error("Failed to fetch release gates:", err);
      showToast(`Error loading release gates: ${err.message}`, "danger");
    }
  },

  renderGates() {
    const container = document.getElementById("release-gates-list");
    if (!this.gates.length) {
      container.textContent = 'No release gates configured yet. Click "Define Release Gate" to set one up.';
      return;
    }

    container.innerHTML = this.gates.map((gate) => {
      const statusClass = String(gate.status || "pending").toLowerCase().replace(/[^a-z]/g, "");
      return `
        <div class="gate-card" id="gate-card-${gate.id}">
          <div class="gate-header">
            <div>
              <h3 style="font-size:1.15rem;font-weight:700;">${escapeHtml(gate.gate_name)}</h3>
              <div style="font-size:0.8rem;color:var(--text-secondary);">Target Milestone: <strong>${escapeHtml(gate.target_milestone)}</strong></div>
            </div>
            <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;">
              <span class="gate-status-pill ${statusClass}">${escapeHtml(gate.status)}</span>
              <button class="btn btn-sm btn-primary" data-action="evaluate" data-id="${gate.id}">Evaluate</button>
              <button class="btn btn-sm btn-success" data-action="signoff" data-id="${gate.id}">Sign off</button>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.75rem;margin:1rem 0;font-size:0.82rem;background:var(--bg-card);padding:0.75rem;border-radius:var(--radius);">
            <div>Max Critical Debts Allowed: <strong>${gate.max_critical_debts}</strong></div>
            <div>Max High Debts Allowed: <strong>${gate.max_high_debts}</strong></div>
            <div>Max Aggregate Debt Capacity: <strong>${gate.max_aggregate_risk}</strong></div>
            <div>Last Evaluated: <strong>${escapeHtml(gate.evaluation_date || "Never")}</strong></div>
          </div>
          ${gate.evaluation_summary ? `<div style="font-size:0.85rem;margin-bottom:0.75rem;padding:0.5rem 0.75rem;border-radius:4px;background:#f8fafc;">${escapeHtml(gate.evaluation_summary)}</div>` : ""}
          ${gate.signoff_by ? `<div style="font-size:0.82rem;color:var(--success);margin-top:0.5rem;">Sign-off recorded by: <strong>${escapeHtml(gate.signoff_by)}</strong>. Notes: "${escapeHtml(gate.signoff_notes || "")}"</div>` : ""}
          <div id="gate-eval-results-${gate.id}"></div>
        </div>`;
    }).join("");

    container.querySelectorAll('[data-action="evaluate"]').forEach((button) => {
      button.addEventListener("click", () => this.evaluateGate(Number(button.dataset.id)));
    });
    container.querySelectorAll('[data-action="signoff"]').forEach((button) => {
      button.addEventListener("click", () => this.openSignOffModal(Number(button.dataset.id)));
    });
  },

  renderEvaluation(res) {
    const violationsHtml = res.violations?.length
      ? `<div style="margin-top:1rem;"><strong style="color:var(--danger);">Gate Policy Violations (${res.violations.length}):</strong>
          <ul class="violations-list">${res.violations.map((violation) => `
            <li class="violation-item">
              <strong>[${escapeHtml(violation.severity)}] ${escapeHtml(violation.rule)}:</strong> ${escapeHtml(violation.message)}
              ${violation.culprit_debt_ids.length ? `<div style="font-size:0.78rem;margin-top:0.25rem;color:var(--text-secondary);">Culprits: ${violation.culprit_debt_ids.map(escapeHtml).join(", ")}</div>` : ""}
            </li>`).join("")}</ul></div>`
      : `<div style="background:rgba(52,211,153,0.1);border-left:4px solid var(--success);padding:0.75rem 1rem;border-radius:var(--radius);margin-top:1rem;font-size:0.85rem;color:var(--success);">All release-gate checks passed with zero policy violations.</div>`;

    return `
      <div style="background:var(--bg-card);padding:1rem;border-radius:var(--radius);border:1px solid var(--border-color);margin-top:0.75rem;font-size:0.85rem;">
        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
          <strong>Live Evaluation Summary:</strong>
          <span class="badge ${res.is_ready_to_release ? "badge-low" : "badge-critical"}">${escapeHtml(res.status)}</span>
        </div>
        <div>Total Unresolved Milestone Debts: <strong>${res.total_unresolved_debts}</strong></div>
        <div>Actual Critical: <strong>${res.actual_critical_debts}</strong> (Max: ${res.max_critical_debts}) | Actual High: <strong>${res.actual_high_debts}</strong> (Max: ${res.max_high_debts})</div>
        <div>Actual Aggregate Risk Score: <strong>${res.actual_aggregate_risk}</strong> (Max: ${res.max_aggregate_risk})</div>
        ${violationsHtml}
      </div>`;
  },

  async evaluateGate(gateId) {
    try {
      const result = await API.evaluateGate(gateId);
      await this.loadGates();
      const output = document.getElementById(`gate-eval-results-${gateId}`);
      if (output) output.innerHTML = this.renderEvaluation(result);
      showToast(`Evaluation completed: ${result.status}`, result.is_ready_to_release ? "success" : "danger");
    } catch (err) {
      showToast(`Evaluation failed: ${err.message}`, "danger");
    }
  },

  openCreateGateModal() {
    document.getElementById("modal-create-gate").classList.add("active");
  },

  async submitCreateGate(event) {
    event.preventDefault();
    const payload = {
      gate_name: document.getElementById("gate-name-input").value.trim(),
      target_milestone: document.getElementById("gate-milestone-input").value.trim(),
      max_critical_debts: Number.parseInt(document.getElementById("gate-max-critical").value, 10),
      max_high_debts: Number.parseInt(document.getElementById("gate-max-high").value, 10),
      max_aggregate_risk: Number.parseFloat(document.getElementById("gate-max-risk").value),
    };

    try {
      await API.createReleaseGate(payload);
      showToast("Release gate created successfully!", "success");
      DebtsView.closeModal("modal-create-gate");
      await this.loadGates();
    } catch (err) {
      showToast(`Failed to create gate: ${err.message}`, "danger");
    }
  },

  openSignOffModal(gateId) {
    const gate = this.gates.find((item) => item.id === gateId);
    if (!gate) return;
    document.getElementById("signoff-gate-id").value = gateId;
    document.getElementById("modal-signoff-title").textContent = `Formal Sign-Off: ${gate.gate_name}`;
    document.getElementById("modal-signoff-gate").classList.add("active");
  },

  async submitSignOff(event) {
    event.preventDefault();
    const gateId = Number.parseInt(document.getElementById("signoff-gate-id").value, 10);
    const payload = {
      signoff_by: document.getElementById("signoff-by-input").value.trim(),
      signoff_notes: document.getElementById("signoff-notes-input").value.trim(),
    };

    try {
      const result = await API.signOffGate(gateId, payload);
      showToast(result.message, result.is_ready_to_release ? "success" : "warning");
      DebtsView.closeModal("modal-signoff-gate");
      await this.loadGates();
    } catch (err) {
      showToast(`Sign-off failed: ${err.message}`, "danger");
    }
  },
};
