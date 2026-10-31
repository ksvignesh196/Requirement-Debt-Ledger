/**
 * Requirement Debt Ledger (RDL) - Executive Dashboard
 * Renders KPI cards and pure SVG charts (zero external dependency).
 */
const Dashboard = {
  async init() {
    await this.loadData();
  },

  async loadData() {
    try {
      const data = await API.getDashboardAnalytics();
      this.renderKPIs(data);
      this.renderRiskTierDonut(data.risk_distribution);
      this.renderReasonsBarChart(data.reason_distribution);
      this.renderModulesBarChart(data.module_distribution);
      this.renderTopUrgentTable(data.top_urgent_debts);
    } catch (err) {
      console.error("Failed to load dashboard metrics:", err);
      showToast("Error loading dashboard metrics: " + err.message, "danger");
    }
  },

  renderKPIs(data) {
    document.getElementById("kpi-active-debts").innerText = data.active_debts;
    document.getElementById("kpi-critical-debts").innerText = data.critical_debts;
    document.getElementById("kpi-overdue-debts").innerText = data.overdue_debts;
    document.getElementById("kpi-total-risk").innerText = data.total_dynamic_risk.toFixed(1);
    document.getElementById("kpi-resolved-debts").innerText = data.resolved_debts;
  },

  renderRiskTierDonut(dist) {
    const container = document.getElementById("chart-risk-donut");
    const total = (dist.Critical || 0) + (dist.High || 0) + (dist.Moderate || 0) + (dist.Low || 0);

    if (total === 0) {
      container.innerHTML = `<div style="color:var(--text-muted);font-size:0.9rem;">No active debt items.</div>`;
      return;
    }

    const segments = [
      { label: "Critical", count: dist.Critical || 0, color: "#ef4444" },
      { label: "High", count: dist.High || 0, color: "#f97316" },
      { label: "Moderate", count: dist.Moderate || 0, color: "#f59e0b" },
      { label: "Low", count: dist.Low || 0, color: "#10b981" },
    ];

    let cumulativePercent = 0;
    const paths = [];

    segments.forEach((seg) => {
      if (seg.count === 0) return;
      const percent = seg.count / total;
      const startAngle = cumulativePercent * 2 * Math.PI;
      cumulativePercent += percent;
      const endAngle = cumulativePercent * 2 * Math.PI;

      const x1 = 100 + 70 * Math.sin(startAngle);
      const y1 = 100 - 70 * Math.cos(startAngle);
      const x2 = 100 + 70 * Math.sin(endAngle);
      const y2 = 100 - 70 * Math.cos(endAngle);

      const largeArc = percent > 0.5 ? 1 : 0;
      const d = `M 100 100 L ${x1} ${y1} A 70 70 0 ${largeArc} 1 ${x2} ${y2} Z`;

      paths.push(`<path d="${d}" fill="${seg.color}" opacity="0.9"><title>${seg.label}: ${seg.count}</title></path>`);
    });

    const legend = segments
      .map(
        (s) =>
          `<div style="display:flex;align-items:center;gap:0.4rem;font-size:0.8rem;margin:0.2rem 0;">
            <span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${s.color};"></span>
            <span>${s.label}: <strong>${s.count}</strong></span>
          </div>`
      )
      .join("");

    container.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-around;width:100%;">
        <svg viewBox="0 0 200 200" width="160" height="160">
          ${paths.join("")}
          <circle cx="100" cy="100" r="42" fill="var(--bg-surface)" />
          <text x="100" y="96" text-anchor="middle" fill="var(--text-secondary)" font-size="11">TOTAL</text>
          <text x="100" y="118" text-anchor="middle" fill="var(--text-primary)" font-size="18" font-weight="bold">${total}</text>
        </svg>
        <div style="display:flex;flex-direction:column;justify-content:center;">${legend}</div>
      </div>
    `;
  },

  renderReasonsBarChart(dist) {
    const container = document.getElementById("chart-reasons-bar");
    const entries = Object.entries(dist);
    if (entries.length === 0) {
      container.innerHTML = `<div style="color:var(--text-muted);font-size:0.9rem;">No data available.</div>`;
      return;
    }

    const maxCount = Math.max(...entries.map(([_, count]) => count), 1);
    let html = `<div style="display:flex;flex-direction:column;gap:0.6rem;width:100%;padding:0.5rem 0;">`;

    entries.slice(0, 5).forEach(([reason, count]) => {
      const pct = Math.round((count / maxCount) * 100);
      html += `
        <div>
          <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:0.2rem;">
            <span style="max-width:80%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(reason)}">${escapeHtml(reason)}</span>
            <span style="color:var(--primary);font-weight:600;">${count}</span>
          </div>
          <div style="background:var(--bg-card);height:8px;border-radius:4px;overflow:hidden;">
            <div style="background:var(--primary);width:${pct}%;height:100%;border-radius:4px;"></div>
          </div>
        </div>
      `;
    });
    html += `</div>`;
    container.innerHTML = html;
  },

  renderModulesBarChart(dist) {
    const container = document.getElementById("chart-modules-bar");
    const entries = Object.entries(dist);
    if (entries.length === 0) {
      container.innerHTML = `<div style="color:var(--text-muted);font-size:0.9rem;">No data available.</div>`;
      return;
    }

    const maxCount = Math.max(...entries.map(([_, count]) => count), 1);
    let html = `<div style="display:flex;flex-direction:column;gap:0.6rem;width:100%;padding:0.5rem 0;">`;

    entries.slice(0, 5).forEach(([mod, count]) => {
      const pct = Math.round((count / maxCount) * 100);
      html += `
        <div>
          <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:0.2rem;">
            <span style="max-width:80%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(mod)}">${escapeHtml(mod)}</span>
            <span style="color:var(--accent);font-weight:600;">${count}</span>
          </div>
          <div style="background:var(--bg-card);height:8px;border-radius:4px;overflow:hidden;">
            <div style="background:var(--accent);width:${pct}%;height:100%;border-radius:4px;"></div>
          </div>
        </div>
      `;
    });
    html += `</div>`;
    container.innerHTML = html;
  },

  renderTopUrgentTable(debts) {
    const tbody = document.getElementById("top-urgent-tbody");
    if (!debts || debts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No urgent debts currently flagged.</td></tr>`;
      return;
    }

    tbody.innerHTML = debts
      .map(
        (d) => `
        <tr>
          <td><strong>${escapeHtml(d.debt_id)}</strong></td>
          <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(d.title)}</td>
          <td><span class="badge badge-${escapeHtml(d.risk_tier.toLowerCase())}">${escapeHtml(d.risk_tier)} (${d.risk_score})</span></td>
          <td><span class="badge-esc ${escapeHtml(d.escalation_level.toLowerCase())}">${escapeHtml(d.escalation_level)}</span></td>
          <td><strong style="color:var(--primary);">${d.debt_priority_index}</strong></td>
          <td>
            <button class="btn btn-sm btn-primary" onclick="DebtsView.openDetailModal('${d.debt_id}')">Inspect</button>
          </td>
        </tr>
      `
      )
      .join("");
  },
};
