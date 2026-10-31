
/**
 * Requirement Debt Ledger (RDL) - Simulation Suite
 * Dependency impact, what-if remediation planning, and risk forecasting.
 */
const SimulationView = {
  currentSubView: "dep-sim",
  debts: [],
  plans: [],
  referenceDataReady: false,
  referenceDataRequestId: 0,
  dependencyRequestId: 0,
  whatIfRequestId: 0,
  forecastRequestId: 0,

  init() {
    // Reference data is loaded only when the user opens Planning Tools.
    // This avoids a hidden startup request followed by the same request again
    // when the tab is first opened.
    this.bindEvents();
  },

  bindEvents() {
    document.querySelectorAll(".sim-subnav-btn").forEach((btn) => {
      btn.addEventListener("click", () => this.switchSubView(btn.dataset.subview));
    });

    const slider = document.getElementById("dep-sim-delay-slider");
    const debtSelect = document.getElementById("dep-sim-debt-select");

    if (slider) {
      // Update the displayed value while dragging. Run one simulation when the
      // user commits the new value, rather than sending a request for each tick.
      slider.addEventListener("input", (event) => {
        const value = document.getElementById("dep-sim-delay-val");
        if (value) value.textContent = `${event.target.value} days`;
        slider.setAttribute("aria-valuetext", `${event.target.value} days additional delay`);
      });

      slider.addEventListener("change", () => {
        if (this.currentSubView === "dep-sim") {
          this.runDependencySimulation();
        }
      });
    }

    if (debtSelect) {
      debtSelect.addEventListener("change", () => {
        if (this.currentSubView === "dep-sim") {
          this.runDependencySimulation();
        }
      });
    }

    // The dependency simulation, release-plan comparison, and forecast now
    // update from their inputs. Separate Run buttons are intentionally removed.
    document.querySelectorAll(".rate-sensitivity-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".rate-sensitivity-btn").forEach((item) => {
          item.classList.remove("active");
          item.setAttribute("aria-pressed", "false");
        });

        btn.classList.add("active");
        btn.setAttribute("aria-pressed", "true");
        this.runForecasting();
      });
    });

    document.getElementById("whatif-milestone-select")?.addEventListener(
      "change",
      () => this.runWhatIfPlanning()
    );
  },

  async loadReferenceData() {
    const requestId = ++this.referenceDataRequestId;

    try {
      const debts = await API.getDebts();
      if (requestId !== this.referenceDataRequestId) return;

      this.debts = Array.isArray(debts) ? debts : [];
      this.referenceDataReady = true;
      this.populateDebtSelects();
      this.populateMilestoneSelect();

      // Do not run hidden simulations during initial page startup. If the user
      // opened Planning Tools while data was loading, refresh it now.
      if (document.getElementById("tab-simulator")?.classList.contains("active")) {
        this.refreshCurrentSubView();
      }
    } catch (err) {
      if (requestId === this.referenceDataRequestId) {
        showToast(`Unable to load simulation data: ${err.message}`, "danger");
      }
    }
  },

  refreshCurrentSubView() {
    if (!this.referenceDataReady) return;

    if (this.currentSubView === "dep-sim") {
      this.populateDebtSelects();
      this.runDependencySimulation();
    } else if (this.currentSubView === "what-if") {
      this.populateMilestoneSelect();
      this.runWhatIfPlanning();
    } else if (this.currentSubView === "forecast") {
      this.runForecasting();
    }
  },

  switchSubView(subViewId) {
    const subviewChanged = this.currentSubView !== subViewId;
    this.currentSubView = subViewId;

    document.querySelectorAll(".sim-subnav-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.subview === subViewId);
    });

    document.querySelectorAll(".sim-subview-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `sim-panel-${subViewId}`);
    });

    if (subviewChanged) {
      this.refreshCurrentSubView();
    }
  },

  populateDebtSelects() {
    const select = document.getElementById("dep-sim-debt-select");
    if (!select) return;

    const active = this.debts.filter(
      (debt) => !["resolved", "accepted permanent"].includes(
        (debt.status || "").toLowerCase()
      )
    );

    const current = select.value;
    select.replaceChildren();

    active.forEach((debt) => {
      const option = document.createElement("option");
      option.value = debt.debt_id;
      option.textContent =
        `${debt.debt_id} - ${debt.title} (${debt.risk.risk_tier}, ${debt.risk.dynamic_risk_score})`;
      select.appendChild(option);
    });

    if (active.some((debt) => debt.debt_id === current)) {
      select.value = current;
    }

    if (!active.length) {
      select.innerHTML = '<option value="">No open requirements</option>';
    }
  },

  populateMilestoneSelect() {
    const select = document.getElementById("whatif-milestone-select");
    if (!select) return;

    const milestones = [
      ...new Set(
        this.debts.map((debt) => debt.target_milestone).filter(Boolean)
      )
    ].sort();

    const current = select.value;
    select.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = milestones.length
      ? "Select a milestone"
      : "No milestones available";
    select.appendChild(placeholder);

    milestones.forEach((milestone) => {
      const option = document.createElement("option");
      option.value = milestone;
      option.textContent = milestone;
      select.appendChild(option);
    });

    if (milestones.includes(current)) {
      select.value = current;
    } else if (milestones.length) {
      select.value = milestones[0];
    } else {
      select.value = "";
    }
  },

  formatNumber(value, digits = 2) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(digits) : "N/A";
  },

  async runDependencySimulation() {
    const requestId = ++this.dependencyRequestId;
    const debtId = document.getElementById("dep-sim-debt-select")?.value;
    const delayDays = Number.parseInt(
      document.getElementById("dep-sim-delay-slider")?.value || "30",
      10
    );
    const container = document.getElementById("dep-sim-results");

    if (!container) return;

    if (!debtId) {
      container.textContent = "No open requirements are available for dependency simulation.";
      container.setAttribute("aria-busy", "false");
      return;
    }

    container.textContent = "Updating dependency impact...";
    container.setAttribute("aria-busy", "true");

    try {
      const result = await API.simulateDependencyImpact({
        debt_id: debtId,
        additional_delay_days: delayDays
      });

      // Ignore an older response if the user changed the requirement or delay
      // while the previous request was still running.
      if (requestId !== this.dependencyRequestId) return;

      const affected = result.affected_requirements || [];
      const deltaColor = Number(result.portfolio_risk_delta) > 0
        ? "var(--danger)"
        : "var(--success)";
      const currentRisk = Number(result.target_current_risk);
      const projectedRisk = Number(result.target_projected_risk);
      const currentPressure = Number(result.target_current_risk_pressure);
      const projectedPressure = Number(result.target_projected_risk_pressure);
      const hasPressure = Number.isFinite(currentPressure) && Number.isFinite(projectedPressure);
      const pressureIncrease = hasPressure ? projectedPressure - currentPressure : null;
      const pressureColor = pressureIncrease > 0
        ? "var(--danger)"
        : "var(--success)";

      container.innerHTML = `
        <div class="grid-kpi"
             style="display:grid;
                    grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
                    gap:1rem;
                    margin-bottom:1.25rem;">
          <div class="kpi-card">
            <div class="kpi-title">Current Portfolio Risk</div>
            <div class="kpi-value">${this.formatNumber(result.current_portfolio_risk)}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Projected Portfolio Risk</div>
            <div class="kpi-value" style="color:${deltaColor};">${this.formatNumber(result.simulated_portfolio_risk)}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Risk Increase</div>
            <div class="kpi-value" style="color:${deltaColor};">
              ${Number(result.portfolio_risk_delta) > 0 ? "+" : ""}${this.formatNumber(result.portfolio_risk_delta)}
            </div>
            <div class="kpi-subtext">${this.formatNumber(result.portfolio_risk_increase_percent)}%</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Downstream Impact</div>
            <div class="kpi-value">${result.total_unique_affected_count}</div>
            <div class="kpi-subtext">${result.direct_blocked_count} direct · ${result.indirect_blocked_count} indirect</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Selected Requirement Risk</div>
            <div class="kpi-value">
              ${this.formatNumber(currentRisk)}
              <span style="font-size:.8rem;color:var(--text-secondary);">→ ${this.formatNumber(projectedRisk)}</span>
            </div>
            <div class="kpi-subtext">Official score, capped at 100</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">Uncapped Risk Pressure</div>
            ${hasPressure
              ? `<div class="kpi-value" style="color:${pressureColor};">${this.formatNumber(projectedPressure)}</div>
                 <div class="kpi-subtext">Current: ${this.formatNumber(currentPressure)} · Change: ${pressureIncrease >= 0 ? "+" : ""}${this.formatNumber(pressureIncrease)}</div>`
              : `<div class="kpi-value">Unavailable</div>
                 <div class="kpi-subtext">Backend pressure fields are missing.</div>`}
          </div>
        </div>

        <p style="font-size:.8rem;color:var(--text-secondary);margin-bottom:1rem;">
          The official risk score is capped at 100. Uncapped risk pressure shows how the underlying calculated risk continues to grow beyond that limit.
        </p>

        <div class="card" style="padding:1rem;">
          <h3 style="margin-bottom:.5rem;">Dependency impact for ${escapeHtml(result.target_debt_id)}</h3>
          <p style="color:var(--text-secondary);margin-bottom:1rem;">${escapeHtml(result.summary_narrative)}</p>
          ${result.cycle_warning ? `<p class="text-warning">${escapeHtml(result.cycle_warning)}</p>` : ""}
          ${affected.length
            ? `<div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;">
                  <thead><tr><th>ID</th><th>Requirement</th><th>Depth</th><th>Impact</th><th>Risk</th><th>Status</th></tr></thead>
                  <tbody>${affected.map((item) => `
                    <tr>
                      <td>${escapeHtml(item.debt_id)}</td>
                      <td>${escapeHtml(item.title)}</td>
                      <td>${item.distance}</td>
                      <td>${escapeHtml(item.dependency_relationship)}</td>
                      <td>${this.formatNumber(item.current_risk)} (${escapeHtml(item.risk_tier)})</td>
                      <td>${escapeHtml(item.status)}</td>
                    </tr>`).join("")}
                  </tbody>
                </table>
              </div>`
            : "<p>No downstream requirements currently depend on this item.</p>"}
        </div>`;
    } catch (err) {
      if (requestId === this.dependencyRequestId) {
        container.textContent = `Simulation failed: ${err.message}`;
      }
    } finally {
      if (requestId === this.dependencyRequestId) {
        container.setAttribute("aria-busy", "false");
      }
    }
  },

  async runWhatIfPlanning() {
    const requestId = ++this.whatIfRequestId;
    const select = document.getElementById("whatif-milestone-select");
    const milestone = select?.value;

    const container = document.getElementById("whatif-results-container");

    if (!container) return;

    if (!milestone) {
      this.plans = [];
      container.textContent =
        "No release milestones are available. Add a requirement with a target milestone first.";
      return;
    }

    container.textContent = "Evaluating alternative remediation plans...";

    try {
      const data = await API.runWhatIfReleasePlanning({
        target_milestone: milestone,
        effort_capacity_budget: 35
      });

      if (requestId !== this.whatIfRequestId) return;

      this.plans = [
        data.status_quo,
        ...(data.candidate_plans || [])
      ].filter(Boolean);

      const recommendedId = data.recommended_plan_id;

      container.innerHTML = `
        <div class="card" style="padding:1rem;margin-bottom:1rem;">
          <strong>Sandbox comparison — ${escapeHtml(data.target_milestone)}</strong>

          <p style="margin-top:.5rem;color:var(--text-secondary);">
            ${escapeHtml(data.comparative_analysis)}
          </p>

          <p style="font-size:.8rem;color:var(--text-muted);">
            ${escapeHtml(data.isolation_guarantee)}
          </p>
        </div>

        <div style="display:grid;
                    grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
                    gap:1rem;">

          ${this.plans.map((plan, index) => {
            const recommended = plan.plan_id === recommendedId;

            const statusClass =
              plan.simulated_gate_status === "PASSED"
                ? "badge-low"
                : plan.simulated_gate_status === "BLOCKED"
                  ? "badge-critical"
                  : "badge-high";

            return `
              <div class="card"
                   style="padding:1rem;
                          border-top:3px solid ${
                            recommended ? "var(--success)" : "var(--border-color)"
                          };">

                <div style="display:flex;
                            justify-content:space-between;
                            gap:.5rem;
                            align-items:center;">

                  <strong>${escapeHtml(plan.plan_name)}</strong>

                  ${
                    recommended
                      ? '<span class="badge badge-low">Recommended</span>'
                      : ""
                  }
                </div>

                <p style="margin:.65rem 0;
                          color:var(--text-secondary);
                          font-size:.85rem;">
                  ${escapeHtml(plan.description)}
                </p>

                <div style="display:grid;gap:.4rem;font-size:.85rem;">

                  <div>
                    Gate result:
                    <span class="badge ${statusClass}">
                      ${escapeHtml(plan.simulated_gate_status)}
                    </span>
                  </div>

                  <div>
                    Requirements selected:
                    <strong>${plan.resolved_debt_ids.length}</strong>
                  </div>

                  <div>
                    Estimated effort:
                    <strong>${plan.total_effort_points} points</strong>
                  </div>

                  <div>
                    Remaining unresolved:
                    <strong>${plan.remaining_unresolved_count}</strong>
                  </div>

                  <div>
                    Aggregate risk:
                    <strong>
                      ${plan.initial_aggregate_risk}
                      → ${plan.simulated_aggregate_risk}
                    </strong>
                  </div>

                  <div>
                    Risk reduction:
                    <strong>${plan.risk_reduction_percent}%</strong>
                  </div>

                  <div>
                    Newly unblocked requirements:
                    <strong>${plan.unblocked_requirements_count}</strong>
                  </div>
                </div>

                <p style="font-size:.78rem;
                          color:var(--text-muted);
                          margin-top:.75rem;">
                  ${escapeHtml(
                    plan.resolved_debt_ids.join(", ") ||
                    "No remediation selected"
                  )}
                </p>

                ${
                  plan.resolved_debt_ids.length
                    ? `
                      <button class="btn btn-primary btn-sm"
                              data-plan-index="${index}"
                              style="width:100%;margin-top:.5rem;">
                        Start Remediation for Selected Items
                      </button>
                    `
                    : ""
                }

              </div>
            `;
          }).join("")}

        </div>
      `;

      container.querySelectorAll("[data-plan-index]").forEach((button) => {
        button.addEventListener("click", () => {
          const plan = this.plans[Number(button.dataset.planIndex)];

          this.confirmApplyPlan(
            plan.plan_name,
            plan.resolved_debt_ids
          );
        });
      });

    } catch (err) {
      if (requestId === this.whatIfRequestId) {
        container.textContent = `What-if planning failed: ${err.message}`;
      }
    }
  },

  async confirmApplyPlan(planName, debtIds) {
    const milestone =
      document.getElementById("whatif-milestone-select")?.value;

    if (!milestone || !debtIds?.length) return;

    const confirmed = confirm(
      `Start remediation for ${debtIds.length} requirement(s) in '${planName}'? ` +
      "They will move to Remediating, not Resolved. Each item must still be implemented and verified before it can be closed."
    );

    if (!confirmed) return;

    try {
      const result = await API.applyWhatIfPlan({
        target_milestone: milestone,
        resolved_debt_ids: debtIds,
        actor_name: "Release Manager",
        rationale:
          `Started remediation using ${planName}. Implementation and verification are pending.`
      });

      showToast(result.message, "success");

      await DebtsView.loadDebts();
      await Dashboard.loadData();

      this.debts = await API.getDebts();

      await this.runWhatIfPlanning();

    } catch (err) {
      showToast(`Unable to apply plan: ${err.message}`, "danger");
    }
  },

  async runForecasting() {
    const requestId = ++this.forecastRequestId;
    const container =
      document.getElementById("forecast-results-container");

    if (!container) return;

    const activeBtn =
      document.querySelector(".rate-sensitivity-btn.active");

    const rate = activeBtn
      ? Number.parseFloat(activeBtn.dataset.rate)
      : 0.008;

    container.textContent =
      "Calculating the future risk trajectory...";

    try {
      const data = await API.forecastRisk({
        horizons_days: [0, 15, 30, 60, 90, 180],
        scenario: "status_quo",
        daily_interest_rate: rate
      });

      if (requestId !== this.forecastRequestId) return;

      const rows = data.trajectory || [];

      const currentRisk =
        rows.find((row) => row.horizon_days === 0)?.aggregate_risk ?? 0;

      container.innerHTML = `
        <div class="card" style="padding:1rem;margin-bottom:1rem;">

          <strong>
            Risk forecast — ${escapeHtml(data.scope_description)}
          </strong>

          <p style="color:var(--text-secondary);margin-top:.4rem;">
            Scenario: ${escapeHtml(data.scenario)}
            · Daily rate assumption:
            ${(data.daily_interest_rate * 100).toFixed(2)}%
          </p>

          <p style="font-size:.8rem;color:var(--text-muted);margin-top:.4rem;">
            ${escapeHtml(data.assumptions_and_limitations)}
          </p>

          <div style="margin-top:.6rem;">
            Current portfolio risk:
            <strong>${currentRisk}</strong>
          </div>

        </div>

        <div class="card" style="padding:1rem;overflow-x:auto;">

          <table style="width:100%;border-collapse:collapse;">

            <thead>
              <tr>
                <th>Horizon</th>
                <th>Projected date</th>
                <th>Aggregate risk</th>
                <th>Critical</th>
                <th>High</th>
                <th>Moderate</th>
                <th>Low</th>
              </tr>
            </thead>

            <tbody>
              ${rows.map((row) => `
                <tr>
                  <td>${row.horizon_days} days</td>
                  <td>${escapeHtml(row.projected_date)}</td>
                  <td><strong>${row.aggregate_risk}</strong></td>
                  <td>${row.critical_count}</td>
                  <td>${row.high_count}</td>
                  <td>${row.moderate_count}</td>
                  <td>${row.low_count}</td>
                </tr>
              `).join("")}
            </tbody>

          </table>
        </div>
      `;

    } catch (err) {
      if (requestId === this.forecastRequestId) {
        container.textContent = `Risk forecasting failed: ${err.message}`;
      }
    }
  }
};
