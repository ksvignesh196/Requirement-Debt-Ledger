/**
 * Requirement Debt Ledger (RDL) - Interactive Risk & Debt Interest Simulator
 * Lets viva examiners and developers explore the mathematical model interactively.
 */
const RiskCalculator = {
  init() {
    this.bindInputs();
    this.calculate();
  },

  bindInputs() {
    const inputs = [
      "sim-biz",
      "sim-arch",
      "sim-safe",
      "sim-occ",
      "sim-det",
      "sim-days",
      "sim-overdue",
    ];
    inputs.forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener("input", (e) => {
          document.getElementById(id + "-val").innerText = e.target.value;
          this.calculate();
        });
      }
    });
  },

  calculate() {
    const biz = parseInt(document.getElementById("sim-biz").value, 10);
    const arch = parseInt(document.getElementById("sim-arch").value, 10);
    const safe = parseInt(document.getElementById("sim-safe").value, 10);
    const occ = parseInt(document.getElementById("sim-occ").value, 10);
    const det = parseInt(document.getElementById("sim-det").value, 10);
    const elapsedDays = parseInt(document.getElementById("sim-days").value, 10);
    const overdueDays = parseInt(document.getElementById("sim-overdue").value, 10);

    // 1. Severity: 0.35*biz + 0.35*arch + 0.30*safe
    const severity = (0.35 * biz + 0.35 * arch + 0.30 * safe);
    // 2. Base Risk: (severity * occ * det / 125) * 100
    const baseRisk = ((severity * occ * det) / 125.0) * 100.0;

    // 3. Time Interest: 14 days grace period, 0.8% daily
    const gracePeriod = 14;
    const daysPastGrace = Math.max(0, elapsedDays - gracePeriod);
    const interestFactor = Math.pow(1.0 + 0.008, daysPastGrace);
    const interestPercent = (interestFactor - 1.0) * 100.0;

    // 4. Overdue Penalty: +25% per 30 days overdue
    let overduePenalty = 1.0;
    if (overdueDays > 0) {
      overduePenalty = 1.0 + Math.min(1.0, (overdueDays / 30.0) * 0.25);
    }

    // 5. Dynamic Risk
    let dynamicRisk = baseRisk * interestFactor * overduePenalty;
    dynamicRisk = Math.min(100.0, dynamicRisk);

    // 6. Tier
    let tier = "Low";
    let tierColor = "#10b981";
    if (dynamicRisk >= 85) {
      tier = "Critical";
      tierColor = "#ef4444";
    } else if (dynamicRisk >= 65) {
      tier = "High";
      tierColor = "#f97316";
    } else if (dynamicRisk >= 35) {
      tier = "Moderate";
      tierColor = "#f59e0b";
    }

    // Update Meter
    const scoreEl = document.getElementById("sim-result-score");
    scoreEl.innerText = dynamicRisk.toFixed(1);
    scoreEl.style.color = tierColor;

    const tierEl = document.getElementById("sim-result-tier");
    tierEl.innerText = tier;
    tierEl.className = `badge badge-${tier.toLowerCase()}`;

    // Update Derivation Formula
    document.getElementById("sim-step-base").innerHTML = `
      <strong>Composite Severity (I):</strong> (0.35×${biz}) + (0.35×${arch}) + (0.30×${safe}) = <strong>${severity.toFixed(2)}/5</strong><br>
      <strong>Base Static Risk (R₀):</strong> (${severity.toFixed(2)} × ${occ} × ${det} ÷ 125) × 100 = <strong style="color:var(--primary);">${baseRisk.toFixed(1)} / 100</strong>
    `;

    document.getElementById("sim-step-interest").innerHTML = `
      <strong>Elapsed Time:</strong> ${elapsedDays} days (${daysPastGrace} days beyond 14-day grace period).<br>
      <strong>Compound Interest Factor:</strong> (1 + 0.008)^${daysPastGrace} = <strong style="color:var(--warning);">×${interestFactor.toFixed(3)} (+${interestPercent.toFixed(1)}%)</strong>
    `;

    document.getElementById("sim-step-overdue").innerHTML = `
      <strong>Review Status:</strong> ${
        overdueDays > 0
          ? `<span style="color:var(--danger);font-weight:600;">OVERDUE by ${overdueDays} days</span> (Penalty: <strong>×${overduePenalty.toFixed(3)}</strong>)`
          : `<span style="color:var(--success);">On schedule / Not overdue</span> (Multiplier: <strong>×1.000</strong>)`
      }
    `;

    document.getElementById("sim-step-final").innerHTML = `
      <strong>Dynamic Risk Formula:</strong> R(t) = min(100, R₀ × Interest × Overdue)<br>
      ${baseRisk.toFixed(1)} × ${interestFactor.toFixed(3)} × ${overduePenalty.toFixed(3)} = <strong style="font-size:1.15rem;color:${tierColor};">${dynamicRisk.toFixed(1)} (${tier})</strong>
    `;
  },
};
