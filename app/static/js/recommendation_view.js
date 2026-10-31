/**
 * Requirement Debt Ledger (RDL) - Recommendation View Module
 * Explainable, Effort-Aware Remediation Prioritization & Pairwise Contrastive Explanations
 */
const RecommendationView = {
  recommendations: [],
  weights: {},
  milestone: "",

  async init() {
    this.bindEvents();
  },

  bindEvents() {
    const milestoneSelect = document.getElementById("rec-filter-milestone");
    if (milestoneSelect) {
      milestoneSelect.addEventListener("change", (e) => {
        this.milestone = e.target.value;
        this.loadRecommendations();
      });
    }

    const compareBtn = document.getElementById("btn-run-pairwise-compare");
    if (compareBtn) {
      compareBtn.addEventListener("click", () => this.runPairwiseComparison());
    }
  },

  async loadRecommendations() {
    const container = document.getElementById("recommendations-list");
    if (!container) return;

    container.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-muted);">Calculating multi-criteria effort-aware recommendations...</div>`;

    try {
      const data = await API.getRecommendations(this.milestone || null);
      this.recommendations = data.recommendations || [];
      this.weights = data.weights_applied || {};

      this.populateMilestoneFilter();
      this.populatePairwiseSelects();
      this.renderWeightsBanner();
      this.renderList();
    } catch (err) {
      console.error("Failed to load recommendations:", err);
      container.innerHTML = `<div style="padding:2rem;color:var(--danger);">Error loading recommendations: ${escapeHtml(err.message)}</div>`;
    }
  },

  populateMilestoneFilter() {
    const select = document.getElementById("rec-filter-milestone");
    if (!select || select.options.length > 1) return;

    if (typeof DebtsView !== "undefined" && DebtsView.debts) {
      const milestones = Array.from(new Set(DebtsView.debts.map((d) => d.target_milestone).filter(Boolean))).sort();
      milestones.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        select.appendChild(opt);
      });
    }
  },

  populatePairwiseSelects() {
    const selA = document.getElementById("pairwise-debt-a");
    const selB = document.getElementById("pairwise-debt-b");
    if (!selA || !selB) return;

    const options = this.recommendations
      .map((r) => `<option value="${escapeHtml(r.debt_id)}">#${r.rank} ${escapeHtml(r.debt_id)} - ${escapeHtml(r.title.slice(0, 45))}... (${r.estimated_effort} pts)</option>`)
      .join("");

    selA.innerHTML = options;
    selB.innerHTML = options;

    if (this.recommendations.length >= 2) {
      selA.selectedIndex = 0;
      selB.selectedIndex = 1;
    }
  },

  renderWeightsBanner() {
    const el = document.getElementById("rec-weights-banner");
    if (!el) return;

    el.innerHTML = `
      <div style="background:var(--bg-surface);border:1px solid var(--border-color);border-radius:var(--radius);padding:1rem;margin-bottom:1.5rem;font-size:0.85rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.75rem;">
          <div>
            <strong style="color:var(--primary);">How recommendations are ranked:</strong>
            <span style="color:var(--text-secondary);margin-left:0.5rem;">
              Score = [0.35 &times; Risk + 0.30 &times; Unblock + 0.20 &times; BizValue + 0.15 &times; Urgency] &divide; (Effort<sup>0.70</sup>)
            </span>
          </div>
          <div style="display:flex;gap:0.5rem;">
            <button class="btn btn-sm btn-primary" onclick="RecommendationView.openPairwiseModal()">Compare priorities</button>
          </div>
        </div>
      </div>
    `;
  },

  renderList() {
    const container = document.getElementById("recommendations-list");
    if (!container) return;

    if (this.recommendations.length === 0) {
      container.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-muted);">No active deferred requirements eligible for resolution recommendations.</div>`;
      return;
    }

    container.innerHTML = this.recommendations
      .map((r) => {
        const f = r.factors;
        return `
        <div class="card" style="margin-bottom:1.25rem;border-left:4px solid ${r.rank === 1 ? "var(--warning)" : "var(--primary)"};">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;margin-bottom:0.75rem;">
            <div style="display:flex;align-items:center;gap:0.75rem;">
              <span style="background:${r.rank === 1 ? "var(--warning)" : "var(--bg-surface)"};color:${r.rank === 1 ? "#000" : "var(--primary)"};font-weight:800;font-size:1.1rem;padding:0.25rem 0.65rem;border-radius:var(--radius);border:1px solid var(--border-color);">
                #${r.rank}
              </span>
              <div>
                <h3 style="font-size:1.05rem;font-weight:700;">
                  <span style="color:var(--primary);margin-right:0.35rem;">${escapeHtml(r.debt_id)}</span>
                  ${r.title}
                </h3>
                <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:2px;">
                  Module: <strong>${escapeHtml(r.module)}</strong> &bull; Status: <span class="badge badge-status ${escapeHtml(r.status.toLowerCase())}" >${escapeHtml(r.status)}</span> &bull; Escalation: <span class="badge-esc ${escapeHtml(r.escalation_level.toLowerCase())}" >${escapeHtml(r.escalation_level)}</span>
                </div>
              </div>
            </div>

            <div style="text-align:right;">
              <div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;">Benefit per effort</div>
              <div style="font-size:1.4rem;font-weight:800;color:var(--success);">${f.remediation_roi}</div>
              <div style="font-size:0.75rem;color:var(--text-secondary);">Score: ${f.recommendation_score} pts</div>
            </div>
          </div>

          <!-- Rationale Callout -->
          <div style="background:rgba(56,189,248,0.07);border-left:3px solid var(--primary);padding:0.6rem 0.9rem;border-radius:4px;font-size:0.85rem;margin-bottom:1rem;">
            <strong>Reason for recommendation:</strong> ${escapeHtml(r.rationale_headline)}
            <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.25rem;">${escapeHtml(r.detailed_explanation)}</div>
          </div>

          <!-- Factor Contribution Breakdown Bars -->
          <div style="background:var(--bg-surface);border:1px solid var(--border-color);border-radius:var(--radius);padding:0.85rem;margin-bottom:0.75rem;">
            <div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:0.6rem;font-weight:600;display:flex;justify-content:space-between;">
              <span>Factors contributing to the score (${f.gross_remediation_benefit} pts)</span>
              <span>Estimated Effort: <strong style="color:var(--text-primary);">${r.estimated_effort} Story Points</strong> (Effort adjustment: &divide;${f.effort_elasticity_factor})</span>
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:0.75rem;">
              <div>
                <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:3px;">
                  <span>Accumulated Risk (35%)</span>
                  <strong>+${f.accumulated_risk_contrib} pts</strong>
                </div>
                <div style="height:6px;background:var(--bg-input);border-radius:3px;overflow:hidden;">
                  <div style="height:100%;width:${Math.min(100, f.accumulated_risk_score)}%;background:var(--critical);"></div>
                </div>
              </div>

              <div>
                <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:3px;">
                  <span>Downstream unblocking (30%)</span>
                  <strong>+${f.cascaded_unblock_contrib} pts</strong>
                </div>
                <div style="height:6px;background:var(--bg-input);border-radius:3px;overflow:hidden;">
                  <div style="height:100%;width:${Math.min(100, f.cascaded_unblock_score)}%;background:var(--accent);"></div>
                </div>
              </div>

              <div>
                <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:3px;">
                  <span>Business Impact (20%)</span>
                  <strong>+${f.business_value_contrib} pts</strong>
                </div>
                <div style="height:6px;background:var(--bg-input);border-radius:3px;overflow:hidden;">
                  <div style="height:100%;width:${Math.min(100, f.business_value_score)}%;background:var(--warning);"></div>
                </div>
              </div>

              <div>
                <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:3px;">
                  <span>Schedule Urgency (15%)</span>
                  <strong>+${f.urgency_contrib} pts</strong>
                </div>
                <div style="height:6px;background:var(--bg-input);border-radius:3px;overflow:hidden;">
                  <div style="height:100%;width:${Math.min(100, f.urgency_score)}%;background:var(--primary);"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Actions -->
          <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.8rem;color:var(--text-muted);padding-top:0.4rem;">
            <div>
              Dynamic Risk: <strong style="color:var(--text-primary);">${r.dynamic_risk}</strong> &bull; Blocks: <strong style="${r.downstream_blocked_count > 0 ? "color:var(--danger);" : ""}">${r.downstream_blocked_count} requirement(s)</strong> &bull; Deadline: <strong>${r.days_to_deadline < 0 ? `${Math.abs(r.days_to_deadline)}d overdue` : `${r.days_to_deadline}d remaining`}</strong>
            </div>
            <div style="display:flex;gap:0.5rem;">
              <button class="btn btn-sm" onclick="RecommendationView.openCompareWith('${r.debt_id}')">Compare</button>
              <button class="btn btn-sm btn-primary" onclick="DebtsView.openDetailModal('${r.debt_id}')">View details</button>
            </div>
          </div>
        </div>
      `;
      })
      .join("");
  },

  openPairwiseModal() {
    const modal = document.getElementById("modal-pairwise");
    if (modal) modal.classList.add("active");
  },

  openCompareWith(debtId) {
    this.openPairwiseModal();
    const selA = document.getElementById("pairwise-debt-a");
    if (selA) selA.value = debtId;
    this.runPairwiseComparison();
  },

  async runPairwiseComparison() {
    const debtA = document.getElementById("pairwise-debt-a").value;
    const debtB = document.getElementById("pairwise-debt-b").value;
    const outputContainer = document.getElementById("pairwise-comparison-result");

    if (!debtA || !debtB) {
      showToast("Please select two requirements to compare", "warning");
      return;
    }

    if (debtA === debtB) {
      showToast("Cannot compare a requirement to itself. Select two distinct requirements.", "warning");
      return;
    }

    outputContainer.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text-muted);">Preparing comparison...</div>`;

    try {
      const res = await API.explainPairwise({ debt_id_a: debtA, debt_id_b: debtB });
      const mat = res.comparison_matrix;
      const higher = mat[res.higher_ranked_id];
      const lower = mat[res.lower_ranked_id];

      outputContainer.innerHTML = `
        <div style="background:rgba(52,211,153,0.08);border:1px solid var(--success);border-radius:var(--radius);padding:1rem;margin-bottom:1.25rem;">
          <div style="font-size:0.75rem;text-transform:uppercase;color:var(--success);font-weight:700;letter-spacing:0.05em;margin-bottom:0.35rem;">
            Comparison result
          </div>
          <p style="font-size:0.95rem;line-height:1.6;color:var(--text-primary);">
            ${escapeHtml(res.contrastive_narrative)}
          </p>
          <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.5rem;">
            Difference in priority score: <strong style="color:var(--success);">+${res.score_delta} recommendation score points</strong>
          </div>
        </div>

        <table style="width:100%;font-size:0.85rem;border-collapse:collapse;">
          <thead>
            <tr style="border-bottom:1px solid var(--border-color);background:var(--bg-surface);">
              <th style="padding:0.75rem;text-align:left;">Comparison factor</th>
              <th style="padding:0.75rem;text-align:left;color:var(--success);">${escapeHtml(res.higher_ranked_id)} (Higher)</th>
              <th style="padding:0.75rem;text-align:left;color:var(--text-muted);">${escapeHtml(res.lower_ranked_id)} (Lower)</th>
              <th style="padding:0.75rem;text-align:left;">Advantage Rationale</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:0.6rem 0.75rem;"><strong>Benefit per effort</strong></td>
              <td style="padding:0.6rem 0.75rem;color:var(--success);font-weight:700;">${higher.remediation_roi}</td>
              <td style="padding:0.6rem 0.75rem;">${lower.remediation_roi}</td>
              <td style="padding:0.6rem 0.75rem;color:var(--text-secondary);">
                ${higher.remediation_roi > lower.remediation_roi ? "Higher yield per unit effort" : "Balanced by composite benefit"}
              </td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:0.6rem 0.75rem;"><strong>Risk score</strong></td>
              <td style="padding:0.6rem 0.75rem;font-weight:600;">${higher.dynamic_risk}</td>
              <td style="padding:0.6rem 0.75rem;">${lower.dynamic_risk}</td>
              <td style="padding:0.6rem 0.75rem;color:var(--text-secondary);">
                ${higher.dynamic_risk >= lower.dynamic_risk ? "More critical exposure" : "Standalone risk offset by ROI/cascade"}
              </td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:0.6rem 0.75rem;"><strong>Blocked Downstream Items</strong></td>
              <td style="padding:0.6rem 0.75rem;font-weight:600;">${higher.blocked_dependencies}</td>
              <td style="padding:0.6rem 0.75rem;">${lower.blocked_dependencies}</td>
              <td style="padding:0.6rem 0.75rem;color:var(--text-secondary);">
                ${higher.blocked_dependencies > lower.blocked_dependencies ? "Unblocks more dependent requirements" : "Direct impact prioritized"}
              </td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:0.6rem 0.75rem;"><strong>Estimated Effort</strong></td>
              <td style="padding:0.6rem 0.75rem;font-weight:600;">${higher.effort_points} pts</td>
              <td style="padding:0.6rem 0.75rem;">${lower.effort_points} pts</td>
              <td style="padding:0.6rem 0.75rem;color:var(--text-secondary);">
                ${higher.effort_points <= lower.effort_points ? "Lower implementation barrier" : "Higher effort justified by high risk payoff"}
              </td>
            </tr>
            <tr>
              <td style="padding:0.6rem 0.75rem;"><strong>Urgency score</strong></td>
              <td style="padding:0.6rem 0.75rem;font-weight:600;">${higher.urgency_score}</td>
              <td style="padding:0.6rem 0.75rem;">${lower.urgency_score}</td>
              <td style="padding:0.6rem 0.75rem;color:var(--text-secondary);">
                Proximity to review milestone & breach status
              </td>
            </tr>
          </tbody>
        </table>
      `;
    } catch (err) {
      outputContainer.innerHTML = `<div style="padding:1.5rem;color:var(--danger);">Comparison failed: ${escapeHtml(err.message)}</div>`;
    }
  },
};
