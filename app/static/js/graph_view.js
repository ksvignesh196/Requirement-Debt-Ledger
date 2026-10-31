/**
 * Requirement Debt Ledger (RDL) - Dependency Graph Visualizer
 * Pure SVG interactive node-link graph with cycle detection alerts and critical path highlighting.
 */
const GraphView = {
  graphData: null,
  selectedNode: null,

  async init() {
    this.bindEvents();
    await this.loadGraph();
  },

  bindEvents() {
    document.getElementById("btn-add-dep").addEventListener("click", () => this.openAddDepModal());
    document.getElementById("form-add-dep").addEventListener("submit", (e) => this.submitAddDep(e));
  },

  async loadGraph() {
    try {
      this.graphData = await API.getDependencyGraph();
      this.renderGraph();
      this.updateCycleAlert();
    } catch (err) {
      console.error("Failed to load dependency graph:", err);
      showToast("Error loading graph: " + err.message, "danger");
    }
  },

  updateCycleAlert() {
    const alertEl = document.getElementById("graph-cycle-alert");
    if (this.graphData.has_cycle) {
      alertEl.style.display = "block";
      alertEl.innerHTML = `<strong>Circular dependency detected.</strong> Cycle path: ${escapeHtml(this.graphData.cycles[0].join(" -> "))}.`;
    } else {
      alertEl.style.display = "none";
    }
  },

  renderGraph() {
    const svg = document.getElementById("graph-svg");
    const container = document.getElementById("graph-canvas-container");
    const width = container.clientWidth || 900;
    const height = container.clientHeight || 550;

    const nodes = this.graphData.nodes || [];
    const edges = this.graphData.edges || [];
    const criticalPath = this.graphData.critical_path || [];

    if (nodes.length === 0) {
      svg.innerHTML = `<text x="${width / 2}" y="${height / 2}" text-anchor="middle" fill="var(--text-muted)">No requirement debt nodes found.</text>`;
      return;
    }

    // Auto layout: arrange nodes in a circular or multi-tier layout
    const nodePositions = {};
    const radiusX = width * 0.38;
    const radiusY = height * 0.36;
    const centerX = width / 2;
    const centerY = height / 2;

    nodes.forEach((node, idx) => {
      const angle = (idx / nodes.length) * 2 * Math.PI - Math.PI / 2;
      nodePositions[node.id] = {
        x: centerX + radiusX * Math.cos(angle),
        y: centerY + radiusY * Math.sin(angle),
        node: node,
      };
    });

    let defsHtml = `
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
        </marker>
        <marker id="arrow-critical" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#2f5f9f" />
        </marker>
      </defs>
    `;

    // Render Edges
    let edgesHtml = "";
    edges.forEach((edge) => {
      const sourcePos = nodePositions[edge.source];
      const targetPos = nodePositions[edge.target];
      if (!sourcePos || !targetPos) return;

      const isCritical = criticalPath.includes(edge.source) && criticalPath.includes(edge.target);
      const strokeColor = isCritical ? "#2f5f9f" : "#9aa6b2";
      const strokeWidth = isCritical ? "3" : "1.5";
      const marker = isCritical ? "url(#arrow-critical)" : "url(#arrow)";

      edgesHtml += `
        <line x1="${sourcePos.x}" y1="${sourcePos.y}" x2="${targetPos.x}" y2="${targetPos.y}"
              stroke="${strokeColor}" stroke-width="${strokeWidth}" marker-end="${marker}">
          <title>${escapeHtml(edge.source)} blocks ${escapeHtml(edge.target)} (${escapeHtml(edge.dependency_type)})</title>
        </line>
      `;
    });

    // Render Nodes
    let nodesHtml = "";
    nodes.forEach((node) => {
      const pos = nodePositions[node.id];
      const isCriticalPath = criticalPath.includes(node.id);
      
      let fillColor = "#ffffff";
      let strokeColor = "#9aa6b2";
      if (node.risk_tier === "Critical") strokeColor = "#ef4444";
      else if (node.risk_tier === "High") strokeColor = "#f97316";
      else if (node.risk_tier === "Moderate") strokeColor = "#f59e0b";
      else strokeColor = "#10b981";

      if (isCriticalPath) {
        fillColor = "rgba(47, 95, 159, 0.10)";
      }

      nodesHtml += `
        <g class="graph-node" transform="translate(${pos.x}, ${pos.y})" onclick="GraphView.selectNode('${node.id}')" style="cursor:pointer;">
          <circle r="24" fill="${fillColor}" stroke="${strokeColor}" stroke-width="${isCriticalPath ? "3" : "2"}" />
          <text text-anchor="middle" dy="4" fill="var(--text-primary)" font-size="9" font-weight="bold">${escapeHtml(node.id.replace("REQ-DEBT-", "#"))}</text>
          <text text-anchor="middle" dy="38" fill="var(--text-secondary)" font-size="10" font-weight="500">${escapeHtml(node.title.slice(0, 15))}...</text>
        </g>
      `;
    });

    svg.innerHTML = defsHtml + edgesHtml + nodesHtml;
  },

  selectNode(debtId) {
    this.selectedNode = debtId;
    const node = this.graphData.nodes.find((n) => n.id === debtId);
    if (!node) return;

    // Direct dependencies and blocked items
    const blockedByMe = this.graphData.edges.filter((e) => e.source === debtId).map((e) => e.target);
    const iDependOn = this.graphData.edges.filter((e) => e.target === debtId).map((e) => e.source);

    const infoPanel = document.getElementById("graph-node-details");
    infoPanel.innerHTML = `
      <div style="background:var(--bg-card);padding:1rem;border-radius:var(--radius);border:1px solid var(--border-color);font-size:0.85rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
          <strong style="color:var(--primary);font-size:1rem;">${escapeHtml(node.id)}: ${escapeHtml(node.title)}</strong>
          <span class="badge badge-${escapeHtml(node.risk_tier.toLowerCase())}">${escapeHtml(node.risk_tier)} (${node.risk_score})</span>
        </div>
        <div style="margin-bottom:0.5rem;">Module: <strong>${escapeHtml(node.module)}</strong> | Status: <strong>${escapeHtml(node.status)}</strong> | Priority Index: <strong>${node.priority_index}</strong></div>
        <div style="margin-top:0.75rem;">
          <div style="color:var(--danger);font-weight:600;">Blocks downstream requirements (${blockedByMe.length}):</div>
          <div>${blockedByMe.length > 0 ? blockedByMe.join(", ") : "None (Leaves of tree)"}</div>
        </div>
        <div style="margin-top:0.5rem;">
          <div style="color:var(--primary);font-weight:600;">Depends on (${iDependOn.length}):</div>
          <div>${iDependOn.length > 0 ? iDependOn.join(", ") : "None (Root requirement)"}</div>
        </div>
        <div style="margin-top:0.75rem;">
          <button class="btn btn-sm btn-primary" onclick="DebtsView.openDetailModal('${node.id}')">View details</button>
        </div>
      </div>
    `;
  },

  async openAddDepModal() {
    const debts = await API.getDebts();
    const activeDebts = debts.filter((d) => d.status.toLowerCase() !== "resolved");

    const dependentSelect = document.getElementById("dep-dependent-id");
    const blockerSelect = document.getElementById("dep-blocker-id");

    const options = activeDebts.map((d) => `<option value="${d.debt_id}">${escapeHtml(d.debt_id)}: ${escapeHtml(d.title.slice(0, 40))}...</option>`).join("");
    dependentSelect.innerHTML = options;
    blockerSelect.innerHTML = options;

    document.getElementById("modal-add-dep").classList.add("active");
  },

  async submitAddDep(e) {
    e.preventDefault();
    const dependentId = document.getElementById("dep-dependent-id").value;
    const blockerId = document.getElementById("dep-blocker-id").value;
    const depType = document.getElementById("dep-type").value;
    const notes = document.getElementById("dep-notes").value.trim();

    if (dependentId === blockerId) {
      showToast("A requirement debt cannot depend on itself!", "danger");
      return;
    }

    try {
      await API.addDependency({
        debt_id: dependentId,
        depends_on_debt_id: blockerId,
        dependency_type: depType,
        notes: notes,
      });
      showToast("Dependency registered successfully!", "success");
      DebtsView.closeModal("modal-add-dep");
      await this.loadGraph();
      if (typeof DebtsView !== "undefined") DebtsView.loadDebts();
    } catch (err) {
      showToast("Dependency failed: " + err.message, "danger");
    }
  },
};
