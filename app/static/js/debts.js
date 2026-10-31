/**
 * Requirement Debt Ledger (RDL) - Debts Management Module
 * Handles the ledger table, filters, sorting, modals (Detail, Create, Review, Resolve).
 */
const DebtsView = {
  debts: [],

  async init() {
    this.bindEvents();
    await this.loadDebts();
  },

  bindEvents() {
    document.getElementById("debt-search").addEventListener("input", () => this.filterDebts());
    document.getElementById("filter-module").addEventListener("change", () => this.filterDebts());
    document.getElementById("filter-status").addEventListener("change", () => this.filterDebts());
    document.getElementById("filter-risk-tier").addEventListener("change", () => this.filterDebts());
    document.getElementById("filter-escalation").addEventListener("change", () => this.filterDebts());
    document.getElementById("sort-by").addEventListener("change", () => this.filterDebts());
  },

  async loadDebts() {
    try {
      this.debts = await API.getDebts();
      this.populateModuleFilter();
      this.renderTable(this.debts);
    } catch (err) {
      console.error("Failed to fetch debts:", err);
      showToast("Error loading requirement debts: " + err.message, "danger");
    }
  },

  populateModuleFilter() {
    const select = document.getElementById("filter-module");
    const modules = Array.from(new Set(this.debts.map((d) => d.module))).sort();
    select.innerHTML = '<option value="">All Modules</option>' + modules.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
  },

  async filterDebts() {
    const search = document.getElementById("debt-search").value.toLowerCase().trim();
    const module = document.getElementById("filter-module").value;
    const status = document.getElementById("filter-status").value;
    const riskTier = document.getElementById("filter-risk-tier").value;
    const escalation = document.getElementById("filter-escalation").value;
    const sortBy = document.getElementById("sort-by").value;

    let filtered = [...this.debts];

    if (search) {
      filtered = filtered.filter(
        (d) =>
          d.debt_id.toLowerCase().includes(search) ||
          d.title.toLowerCase().includes(search) ||
          d.description.toLowerCase().includes(search)
      );
    }
    if (module) filtered = filtered.filter((d) => d.module === module);
    if (status) filtered = filtered.filter((d) => d.status.toLowerCase() === status.toLowerCase());
    if (riskTier) filtered = filtered.filter((d) => d.risk.risk_tier.toLowerCase() === riskTier.toLowerCase());
    if (escalation) filtered = filtered.filter((d) => d.escalation_level.toLowerCase() === escalation.toLowerCase());

    // Sort
    if (sortBy === "debt_priority_index") {
      filtered.sort((a, b) => b.debt_priority_index - a.debt_priority_index);
    } else if (sortBy === "dynamic_risk_score") {
      filtered.sort((a, b) => b.risk.dynamic_risk_score - a.risk.dynamic_risk_score);
    } else if (sortBy === "days_to_review") {
      filtered.sort((a, b) => a.days_to_review - b.days_to_review);
    } else if (sortBy === "created_date") {
      filtered.sort((a, b) => new Date(b.created_date) - new Date(a.created_date));
    }

    this.renderTable(filtered);
  },

  renderTable(items) {
    const tbody = document.getElementById("debts-tbody");
    if (!items || items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--text-muted);">No requirement debts match the selected criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = items
      .map((d) => {
        const isResolved = d.status.toLowerCase() === "resolved";
        return `
        <tr>
          <td><strong style="color:var(--primary);">${escapeHtml(d.debt_id)}</strong></td>
          <td>
            <div style="font-weight:600;">${escapeHtml(d.title)}</div>
            <div style="font-size:0.75rem;color:var(--text-secondary);">${escapeHtml(d.module)} • ${escapeHtml(d.target_milestone)}</div>
          </td>
          <td><span class="badge badge-status ${escapeHtml(d.status.toLowerCase())}">${escapeHtml(d.status)}</span></td>
          <td>
            <span class="badge badge-${escapeHtml(d.risk.risk_tier.toLowerCase())}">${escapeHtml(d.risk.risk_tier)}</span>
            <div style="font-size:0.75rem;margin-top:2px;color:var(--text-secondary);">Score: <strong>${d.risk.dynamic_risk_score}</strong></div>
          </td>
          <td>
            <span class="badge-esc ${escapeHtml(d.escalation_level.toLowerCase())}">${escapeHtml(d.escalation_level)}</span>
            <div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;">
              ${d.days_to_review < 0 ? `${Math.abs(d.days_to_review)}d overdue` : `${d.days_to_review}d left`}
            </div>
          </td>
          <td>
            ${
              d.dependency_impact.downstream_blocked_count > 0
                ? `<span style="color:var(--danger);font-weight:600;">${d.dependency_impact.downstream_blocked_count} blocked</span>`
                : `<span style="color:var(--text-muted);">None</span>`
            }
          </td>
          <td><span class="badge" style="background:var(--bg-card);color:var(--text-primary);font-weight:600;">${d.estimated_effort || 8} pts</span></td>
          <td><strong style="font-size:1rem;color:var(--text-primary);">${d.debt_priority_index}</strong></td>
          <td>
            <div style="display:flex;gap:0.3rem;">
              <button class="btn btn-sm" onclick="DebtsView.openDetailModal('${d.debt_id}')" title="Inspect & Explain Risk">Details</button>
              ${
                !isResolved
                  ? `
                <button class="btn btn-sm btn-primary" onclick="DebtsView.openReviewModal('${d.debt_id}')" title="Conduct Review">Review</button>
                <button class="btn btn-sm btn-success" onclick="DebtsView.openResolveModal('${d.debt_id}')" title="Resolve Debt">Resolve</button>
              `
                  : `<button class="btn btn-sm" style="color:var(--success);" disabled>Verified</button>`
              }
            </div>
          </td>
        </tr>
      `;
      })
      .join("");
  },

  async openDetailModal(debtId) {
    try {
      const debt = await API.getDebt(debtId);
      const reviews = await API.getReviews(debtId);
      const audit = await API.getAuditLogs(debtId);

      document.getElementById("modal-detail-title").innerText = `${escapeHtml(debt.debt_id)}: ${escapeHtml(debt.title)}`;

      const body = document.getElementById("modal-detail-body");
      body.innerHTML = `
        <div style="margin-bottom:1.25rem;">
          <p style="font-size:0.95rem;color:var(--text-primary);margin-bottom:0.75rem;">${escapeHtml(debt.description)}</p>
          <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
            <span class="badge badge-status">${escapeHtml(debt.module)}</span>
            <span class="badge badge-status">${escapeHtml(debt.requirement_type)}</span>
            <span class="badge badge-status">${escapeHtml(debt.target_milestone)}</span>
            <span class="badge badge-status ${escapeHtml(debt.status.toLowerCase())}">${escapeHtml(debt.status)}</span>
            <span class="badge badge-${escapeHtml(debt.risk.risk_tier.toLowerCase())}" >${escapeHtml(debt.risk.risk_tier)} Risk (${debt.risk.dynamic_risk_score})</span>
            <span class="badge-esc ${escapeHtml(debt.escalation_level.toLowerCase())}">${escapeHtml(debt.escalation_level)}</span>
            <span class="badge badge-status" style="background:var(--bg-card);color:var(--text-primary);border:1px solid var(--border-color);">Effort: ${debt.estimated_effort || 8} pts</span>
          </div>
          <div style="margin-bottom:0.75rem;">
            <button class="btn btn-sm btn-primary" onclick="DebtsView.closeModal('modal-detail'); App.switchTab('simulator'); SimulationView.switchSubView('dep-sim'); document.getElementById('dep-sim-debt-select').value='${debt.debt_id}'; SimulationView.runDependencySimulation();">
              View dependency impact
            </button>
          </div>
        </div>

        <!-- Explainable Risk Engine Breakdown -->
        <div class="formula-card" style="margin-bottom:1.5rem;">
          <h4 style="color:var(--primary);margin-bottom:0.75rem;font-size:0.95rem;">Risk score breakdown</h4>
          <div class="formula-step">
            <strong>1. Base Risk (Static):</strong> Severity (${debt.risk.base_severity}/5) × Occurrence (${debt.risk.base_occurrence}/5) × Detection (${debt.risk.base_detection}/5)
            = <strong style="color:var(--primary);">${debt.risk.base_risk_score} / 100</strong>
          </div>
          <div class="formula-step">
            <strong>2. Time adjustment:</strong> Aged ${debt.risk.elapsed_days} days (${debt.risk.days_past_grace} past 14-day grace).
            Accumulated time adjustment: <strong style="color:var(--warning);">+${debt.risk.accrued_interest_percent}% (×${debt.risk.interest_factor})</strong>
          </div>
          <div class="formula-step">
            <strong>3. Deadline / Overdue Penalty:</strong> Review date: ${escapeHtml(debt.review_date)}.
            ${
              debt.risk.is_overdue
                ? `<span style="color:var(--danger);font-weight:600;">OVERDUE by ${debt.risk.overdue_days} days (Penalty multiplier: ×${debt.risk.overdue_penalty_factor})</span>`
                : `<span style="color:var(--success);">Within scheduled review window (Multiplier: ×1.0)</span>`
            }
          </div>
          <div class="formula-step">
            <strong>4. Final risk score:</strong> <span style="font-size:1.1rem;font-weight:bold;color:var(--text-primary);">${debt.risk.dynamic_risk_score} (${debt.risk.risk_tier})</span>
          </div>
          <div style="background:rgba(56,189,248,0.07);padding:0.75rem;border-radius:4px;margin-top:0.75rem;font-style:italic;color:var(--text-secondary);">
            "${escapeHtml(debt.risk.explanation)}"
          </div>
        </div>

        <!-- Governance & Traceability Details -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem;font-size:0.85rem;">
          <div style="background:var(--bg-card);padding:1rem;border-radius:var(--radius);border:1px solid var(--border-color);">
            <div style="color:var(--text-secondary);margin-bottom:0.25rem;">Deferral Reason</div>
            <strong>${escapeHtml(debt.deferral_reason)}</strong>
            <div style="color:var(--text-secondary);margin:0.5rem 0 0.25rem 0;">Phase & Decision Maker</div>
            <div>${escapeHtml(debt.deferral_phase)} • ${escapeHtml(debt.decision_maker)}</div>
            <div style="color:var(--text-secondary);margin:0.5rem 0 0.25rem 0;">Owner Team</div>
            <div>${escapeHtml(debt.owner)}</div>
          </div>
          <div style="background:var(--bg-card);padding:1rem;border-radius:var(--radius);border:1px solid var(--border-color);">
            <div style="color:var(--text-secondary);margin-bottom:0.25rem;">Resolution Criteria</div>
            <div style="color:var(--text-primary);">${escapeHtml(debt.resolution_criteria)}</div>
            <div style="color:var(--text-secondary);margin:0.5rem 0 0.25rem 0;">Key Milestones</div>
            <div>Created: ${escapeHtml(debt.created_date)} | Deadline: ${escapeHtml(debt.deadline_date)}</div>
          </div>
        </div>

        <!-- Review History -->
        <h4 style="margin-bottom:0.75rem;font-size:0.9rem;">Review Sessions (${reviews.length})</h4>
        ${
          reviews.length === 0
            ? `<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">No formal review sessions recorded yet.</p>`
            : reviews
                .map(
                  (r) => `
              <div style="background:var(--bg-card);padding:0.75rem 1rem;border-radius:var(--radius);border:1px solid var(--border-color);margin-bottom:0.5rem;font-size:0.82rem;">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem;">
                  <strong>${escapeHtml(r.reviewer_name)} (${escapeHtml(r.reviewer_role)})</strong>
                  <span style="color:var(--primary);">${escapeHtml(r.review_date)}</span>
                </div>
                <div>Outcome: <strong>${escapeHtml(r.outcome)}</strong> ${r.new_review_date ? `(New Review: ${escapeHtml(r.new_review_date)})` : ""}</div>
                <div style="color:var(--text-secondary);margin-top:0.25rem;">${escapeHtml(r.notes)}</div>
              </div>
            `
                )
                .join("")
        }

        <!-- Resolution Evidence (if resolved) -->
        ${
          debt.status.toLowerCase() === "resolved"
            ? `
          <div style="background:rgba(52,211,153,0.1);border:1px solid var(--success);padding:1rem;border-radius:var(--radius);margin-top:1rem;font-size:0.85rem;">
            <strong style="color:var(--success);">Resolution Verification & Sign-off:</strong>
            <div>Type: <strong>${escapeHtml(debt.resolution_type)}</strong> (Date: ${escapeHtml(debt.resolved_date)})</div>
            <div style="margin-top:0.25rem;color:var(--text-primary);">Notes: ${escapeHtml(debt.resolution_notes)}</div>
          </div>
        `
            : ""
        }
      `;

      document.getElementById("modal-detail").classList.add("active");
    } catch (err) {
      showToast("Error opening debt details: " + err.message, "danger");
    }
  },

  openCreateModal() {
    const today = new Date().toISOString().slice(0, 10);
    const reviewDate = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10);
    const deadlineDate = new Date(Date.now() + 45 * 86400000).toISOString().slice(0, 10);

    document.getElementById("create-created-date").value = today;
    document.getElementById("create-review-date").value = reviewDate;
    document.getElementById("create-deadline-date").value = deadlineDate;
    document.getElementById("modal-create").classList.add("active");
  },

  async submitCreate(e) {
    e.preventDefault();
    const payload = {
      title: document.getElementById("create-title").value.trim(),
      description: document.getElementById("create-description").value.trim(),
      module: document.getElementById("create-module").value.trim(),
      requirement_type: document.getElementById("create-type").value,
      deferral_reason: document.getElementById("create-reason").value,
      deferral_phase: document.getElementById("create-phase").value,
      decision_maker: document.getElementById("create-decision-maker").value.trim(),
      owner: document.getElementById("create-owner").value.trim(),
      target_milestone: document.getElementById("create-milestone").value.trim(),
      resolution_criteria: document.getElementById("create-resolution-criteria").value.trim(),
      created_date: document.getElementById("create-created-date").value,
      review_date: document.getElementById("create-review-date").value,
      deadline_date: document.getElementById("create-deadline-date").value,
      business_impact: parseInt(document.getElementById("create-business-impact").value, 10),
      arch_impact: parseInt(document.getElementById("create-arch-impact").value, 10),
      safety_impact: parseInt(document.getElementById("create-safety-impact").value, 10),
      occurrence_prob: parseInt(document.getElementById("create-occurrence-prob").value, 10),
      detection_difficulty: parseInt(document.getElementById("create-detection-difficulty").value, 10),
      cost_of_delay: parseInt(document.getElementById("create-cost-of-delay").value, 10),
      estimated_effort: parseInt(document.getElementById("create-effort") ? document.getElementById("create-effort").value : 8, 10) || 8,
    };

    try {
      const res = await API.createDebt(payload);
      showToast(`Created ${res.debt_id} successfully!`, "success");
      this.closeModal("modal-create");
      await this.loadDebts();
      if (typeof Dashboard !== "undefined") Dashboard.loadData();
    } catch (err) {
      showToast("Failed to create debt: " + err.message, "danger");
    }
  },

  openReviewModal(debtId) {
    document.getElementById("review-debt-id").value = debtId;
    document.getElementById("review-date-input").value = new Date().toISOString().slice(0, 10);
    const newRevDate = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10);
    document.getElementById("review-new-date").value = newRevDate;
    document.getElementById("modal-review-title").innerText = `Conduct Review for ${debtId}`;
    document.getElementById("modal-review").classList.add("active");
  },

  async submitReview(e) {
    e.preventDefault();
    const debtId = document.getElementById("review-debt-id").value;
    const payload = {
      debt_id: debtId,
      reviewer_name: document.getElementById("review-name").value.trim(),
      reviewer_role: document.getElementById("review-role").value.trim(),
      outcome: document.getElementById("review-outcome").value,
      notes: document.getElementById("review-notes").value.trim(),
      new_review_date: document.getElementById("review-new-date").value || null,
      review_date: document.getElementById("review-date-input").value,
    };

    try {
      await API.recordReview(payload);
      showToast(`Review recorded for ${debtId}!`, "success");
      this.closeModal("modal-review");
      await this.loadDebts();
      if (typeof Dashboard !== "undefined") Dashboard.loadData();
    } catch (err) {
      showToast("Failed to record review: " + err.message, "danger");
    }
  },

  openResolveModal(debtId) {
    document.getElementById("resolve-debt-id").value = debtId;
    document.getElementById("modal-resolve-title").innerText = `Formally Resolve ${debtId}`;
    document.getElementById("modal-resolve").classList.add("active");
  },

  async submitResolve(e) {
    e.preventDefault();
    const debtId = document.getElementById("resolve-debt-id").value;
    const payload = {
      resolution_type: document.getElementById("resolve-type").value,
      resolution_notes: document.getElementById("resolve-notes").value.trim(),
      resolved_by: document.getElementById("resolve-by").value.trim(),
    };

    try {
      await API.resolveDebt(debtId, payload);
      showToast(`${debtId} formally resolved!`, "success");
      this.closeModal("modal-resolve");
      await this.loadDebts();
      if (typeof Dashboard !== "undefined") Dashboard.loadData();
    } catch (err) {
      showToast("Failed to resolve debt: " + err.message, "danger");
    }
  },

  closeModal(modalId) {
    document.getElementById(modalId).classList.remove("active");
  },
};
