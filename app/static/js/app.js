/**
 * Requirement Debt Ledger (RDL) - Main SPA Controller
 */
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";
  if (type === "danger") toast.style.borderColor = "var(--danger)";
  if (type === "success") toast.style.borderColor = "var(--success)";

  const text = document.createElement("div");
  text.textContent = String(message ?? "");
  toast.append(text);
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

const App = {
  activeTab: "dashboard",

  init() {
    this.bindNavigation();
    this.bindGlobalActions();
    this.initModules();
  },

  bindNavigation() {
    const tabBtns = document.querySelectorAll(".tab-nav .tab-btn");
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.tab;
        this.switchTab(target);
      });
    });
  },

  switchTab(tabId) {
    const previousTab = this.activeTab;
    this.activeTab = tabId;

    // Update buttons
    document.querySelectorAll(".tab-nav .tab-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.tab === tabId);
    });

    // Update content views
    document.querySelectorAll(".tab-content").forEach((c) => {
      c.classList.toggle("active", c.id === `tab-${tabId}`);
    });

    // Lazy load or refresh tab contents
    if (tabId === "dashboard" && typeof Dashboard !== "undefined") {
      Dashboard.loadData();
    } else if (tabId === "debts" && typeof DebtsView !== "undefined") {
      DebtsView.loadDebts();
    } else if (tabId === "recommendations" && typeof RecommendationView !== "undefined") {
      RecommendationView.loadRecommendations();
    } else if (
      tabId === "simulator" &&
      previousTab !== "simulator" &&
      typeof SimulationView !== "undefined"
    ) {
      // Refresh source data only when entering Planning Tools from another tab.
      // Clicking the already-active tab must not repeat the same simulation.
      SimulationView.loadReferenceData();
    } else if (tabId === "graph" && typeof GraphView !== "undefined") {
      GraphView.loadGraph();
    } else if (tabId === "release" && typeof ReleaseView !== "undefined") {
      ReleaseView.loadGates();
    } else if (tabId === "audit") {
      this.loadAuditTrail();
    }
  },

  bindGlobalActions() {
    // Reset seed data
    document.getElementById("btn-reset-data").addEventListener("click", async () => {
      if (confirm("Reset database to initial realistic demonstration seed data? This will overwrite manual changes.")) {
        try {
          await API.resetSeedData();
          showToast("Database successfully restored to demonstration seed data!", "success");
          this.switchTab(this.activeTab);
        } catch (err) {
          showToast("Reset failed: " + err.message, "danger");
        }
      }
    });

    // Modal close buttons (with data-close attribute)
    document.querySelectorAll("[data-close]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const modalId = btn.dataset.close;
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove("active");
      });
    });

    // Forms
    const createForm = document.getElementById("form-create-debt");
    if (createForm) createForm.addEventListener("submit", (e) => DebtsView.submitCreate(e));

    const reviewForm = document.getElementById("form-review-debt");
    if (reviewForm) reviewForm.addEventListener("submit", (e) => DebtsView.submitReview(e));

    const resolveForm = document.getElementById("form-resolve-debt");
    if (resolveForm) resolveForm.addEventListener("submit", (e) => DebtsView.submitResolve(e));

    // Audit refresh
    const refreshAuditBtn = document.getElementById("btn-refresh-audit");
    if (refreshAuditBtn) refreshAuditBtn.addEventListener("click", () => this.loadAuditTrail());

    // Audit verify
    const verifyAuditBtn = document.getElementById("btn-verify-audit");
    if (verifyAuditBtn) verifyAuditBtn.addEventListener("click", () => this.verifyAuditChain());
  },

  async loadAuditTrail() {
    try {
      const logs = await API.getAuditLogs(null, 100);
      const tbody = document.getElementById("audit-tbody");
      if (!logs || logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:2rem;">No audit events recorded.</td></tr>`;
        return;
      }

      tbody.innerHTML = logs
        .map(
          (l) => `
        <tr>
          <td><span style="font-size:0.75rem;color:var(--text-muted);">${escapeHtml(l.created_at.slice(0, 19).replace("T", " "))}</span></td>
          <td><strong style="color:var(--primary);">${escapeHtml(l.debt_id || "SYSTEM")}</strong></td>
          <td><span class="badge badge-status">${escapeHtml(l.action)}</span></td>
          <td>${escapeHtml(l.performed_by)}</td>
          <td style="font-size:0.8rem;color:var(--text-secondary);">${escapeHtml(l.details)}</td>
          <td style="font-family:monospace;font-size:0.75rem;">
            ${l.entry_hash ? `<span title="Full Hash: ${escapeHtml(l.entry_hash)} (Prev: ${escapeHtml(l.prev_hash || "GENESIS")})" style="color:var(--accent);background:var(--bg-card);padding:2px 5px;border-radius:3px;">${escapeHtml(l.entry_hash.slice(0, 10))}...</span>` : `<span style="color:var(--text-muted);">legacy</span>`}
          </td>
        </tr>
      `
        )
        .join("");
    } catch (err) {
      showToast("Error loading audit trail: " + err.message, "danger");
    }
  },

  async verifyAuditChain() {
    const statusContainer = document.getElementById("audit-verification-status");
    if (!statusContainer) return;

    statusContainer.innerHTML = `<div style="padding:0.75rem;color:var(--text-secondary);">Checking audit history...</div>`;

    try {
      const res = await API.verifyAuditIntegrity();
      if (res.is_valid) {
        statusContainer.innerHTML = `
          <div style="background:rgba(52,211,153,0.1);border:1px solid var(--success);border-radius:var(--radius);padding:0.85rem 1.25rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.75rem;">
            <div style="display:flex;align-items:center;gap:0.75rem;">
              <span style="font-size:1.5rem;"></span>
              <div>
                <strong style="color:var(--success);">Cryptographic Integrity Verified: Audit history verified</strong>
                <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:2px;">
                  All ${res.total_entries} audit records passed the integrity check.
                </div>
              </div>
            </div>
            <div style="font-family:monospace;font-size:0.75rem;color:var(--accent);">
              Latest Block Hash: <strong>${escapeHtml(res.latest_hash ? res.latest_hash.slice(0, 16) : "N/A")}...</strong>
            </div>
          </div>
        `;
        showToast("Audit history verified.", "success");
      } else {
        statusContainer.innerHTML = `
          <div style="background:rgba(239,68,68,0.15);border:1px solid var(--danger);border-radius:var(--radius);padding:0.85rem 1.25rem;display:flex;align-items:center;gap:0.75rem;">
            <span style="font-size:1.5rem;"></span>
            <div>
              <strong style="color:var(--danger);">Audit history integrity check failed.</strong>
              <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:2px;">
                The integrity check found ${res.tampered_count} invalid audit record(s).
              </div>
            </div>
          </div>
        `;
        showToast("Audit history integrity check failed.", "danger");
      }
    } catch (err) {
      statusContainer.innerHTML = `<div style="padding:0.75rem;color:var(--danger);">Verification failed: ${escapeHtml(err.message)}</div>`;
    }
  },

  initModules() {
    Dashboard.init();
    DebtsView.init();
    RiskCalculator.init();
    GraphView.init();
    ReleaseView.init();
    RecommendationView.init();
    SimulationView.init();
  },
};

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
