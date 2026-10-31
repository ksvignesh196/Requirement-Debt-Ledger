function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
}

/**
 * Requirement Debt Ledger (RDL) - API Client
 */
const API = {
  async get(url) {
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API Request Failed");
    }
    return res.json();
  },

  async post(url, data) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API Request Failed");
    }
    return res.json();
  },

  async patch(url, data) {
    const res = await fetch(url, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API Request Failed");
    }
    return res.json();
  },

  async delete(url) {
    const res = await fetch(url, { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API Request Failed");
    }
    return res.json();
  },

  // Debt Services
  getDebts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/debts${query ? "?" + query : ""}`);
  },

  getDebt(debtId) {
    return this.get(`/api/debts/${debtId}`);
  },

  createDebt(payload) {
    return this.post("/api/debts", payload);
  },

  updateDebt(debtId, payload) {
    return this.patch(`/api/debts/${debtId}`, payload);
  },

  resolveDebt(debtId, payload) {
    return this.post(`/api/debts/${debtId}/resolve`, payload);
  },

  deleteDebt(debtId) {
    return this.delete(`/api/debts/${debtId}`);
  },

  simulateRisk(payload) {
    return this.post("/api/debts/simulate/risk", payload);
  },

  // Dependency Services
  getDependencies() {
    return this.get("/api/dependencies");
  },

  addDependency(payload) {
    return this.post("/api/dependencies", payload);
  },

  removeDependency(depId) {
    return this.delete(`/api/dependencies/${depId}`);
  },

  getDependencyGraph() {
    return this.get("/api/dependencies/graph");
  },

  // Reviews & Audit
  getReviews(debtId) {
    return this.get(`/api/reviews/${debtId}`);
  },

  recordReview(payload) {
    return this.post("/api/reviews", payload);
  },

  getAuditLogs(debtId = null, limit = 50) {
    const query = debtId ? `?debt_id=${debtId}&limit=${limit}` : `?limit=${limit}`;
    return this.get(`/api/audit${query}`);
  },

  verifyAuditIntegrity() {
    return this.get("/api/audit/verify");
  },

  // Distinctive Feature A: Dependency Impact Simulator
  simulateDependencyImpact(payload) {
    return this.post("/api/simulations/dependency-impact", payload);
  },

  // Distinctive Feature B: Recommendations
  getRecommendations(milestone = null) {
    const query = milestone ? `?milestone=${encodeURIComponent(milestone)}` : "";
    return this.get(`/api/recommendations/${query}`);
  },

  explainPairwise(payload) {
    return this.post("/api/recommendations/pairwise-explain", payload);
  },

  // Distinctive Feature C: What-If Release Planning
  runWhatIfReleasePlanning(payload) {
    return this.post("/api/simulations/what-if-release", payload);
  },

  applyWhatIfPlan(payload) {
    return this.post("/api/simulations/apply-plan", payload);
  },

  // Distinctive Feature D: Risk Forecasting & Sensitivity
  forecastRisk(payload) {
    return this.post("/api/simulations/risk-forecast", payload);
  },

  simulateRiskSensitivity(payload) {
    return this.post("/api/debts/simulate/sensitivity", payload);
  },

  // Release Gates
  getReleaseGates() {
    return this.get("/api/release-gates");
  },

  createReleaseGate(payload) {
    return this.post("/api/release-gates", payload);
  },

  evaluateGate(gateId) {
    return this.get(`/api/release-gates/${gateId}/evaluate`);
  },

  signOffGate(gateId, payload) {
    return this.post(`/api/release-gates/${gateId}/signoff`, payload);
  },

  evaluateMilestone(milestone) {
    return this.get(`/api/release-gates/evaluate-milestone/${encodeURIComponent(milestone)}`);
  },

  // Analytics
  getDashboardAnalytics() {
    return this.get("/api/analytics/dashboard");
  },

  // Seed / Reset
  async resetSeedData() {
    return this.post("/api/export/reset", {});
  },
};
