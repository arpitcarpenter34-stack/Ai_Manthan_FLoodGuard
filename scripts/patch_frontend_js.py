"""
Patch frontend/static/js/app.js to add Model Intelligence & Explainability (Task 3.8).
"""

from pathlib import Path

JS_FILE = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\static\js\app.js")
content = JS_FILE.read_text(encoding="utf-8")

# 1. Add model-intel to SCREEN_TITLES
old_screen_titles = """  history: {
    title: "History & Persistent Audit Logs",
    subtitle: "Query persistent SQLite analysis history permanently stored in data/hydro_guard.db"
  }
};"""

new_screen_titles = """  history: {
    title: "History & Persistent Audit Logs",
    subtitle: "Query persistent SQLite analysis history permanently stored in data/hydro_guard.db"
  },
  'model-intel': {
    title: "AI Model Intelligence & Scientific Explainability",
    subtitle: "Dataset Lineage • Training Dynamics • Residual Diagnostics • XAI & Permutation Importance • What-If Lab"
  }
};"""

if "'model-intel':" not in content:
    content = content.replace(old_screen_titles, new_screen_titles, 1)
    print("Added model-intel to SCREEN_TITLES")

# 2. Update pageTopBar hiding in navigateTo
old_page_top = 'pageTopBar.style.display = (screenId === "reports") ? "none" : "flex";'
new_page_top = 'pageTopBar.style.display = (screenId === "reports" || screenId === "model-intel") ? "none" : "flex";'
content = content.replace(old_page_top, new_page_top)

# 3. Add trigger in navigateTo
old_triggers = """  } else if (screenId === "simulator") {
    loadSimulatorOptimization();
  }"""

new_triggers = """  } else if (screenId === "simulator") {
    loadSimulatorOptimization();
  } else if (screenId === "model-intel") {
    loadModelIntelligenceDashboard();
  }"""

if 'screenId === "model-intel"' not in content:
    content = content.replace(old_triggers, new_triggers, 1)
    print("Added navigateTo trigger for model-intel")

# 4. Append complete Model Intelligence logic
MI_JS = """

// ==============================================================================
// TASK 3.8: AI MODEL INTELLIGENCE & SCIENTIFIC EXPLAINABILITY
// Ground-Truth Dataset Lineage, Training Analytics, Residual Diagnostics, XAI
// ==============================================================================

window.miState = {
  currentTab: 'lineage',
  lineageData: null,
  trainingData: null,
  evalData: null,
  importanceData: null,
  whatIfData: null,
  explorerData: null,
  whatIfTimer: null
};

async function loadModelIntelligenceDashboard() {
  console.log("[ModelIntel] Loading scientific dashboard data...");
  try {
    // 1. Fetch Lineage
    if (!window.miState.lineageData) {
      const resp = await fetch("/api/v1/model-intel/lineage");
      if (resp.ok) window.miState.lineageData = await resp.json();
    }
    renderLineageSection(window.miState.lineageData);

    // 2. Fetch Training Curves
    if (!window.miState.trainingData) {
      const resp = await fetch("/api/v1/model-intel/training-curves");
      if (resp.ok) window.miState.trainingData = await resp.json();
    }

    // 3. Fetch Evaluation & Residuals
    if (!window.miState.evalData) {
      const resp = await fetch("/api/v1/model-intel/evaluation");
      if (resp.ok) window.miState.evalData = await resp.json();
    }

    // 4. Fetch Feature Importance & XAI
    if (!window.miState.importanceData) {
      const resp = await fetch("/api/v1/model-intel/feature-importance");
      if (resp.ok) window.miState.importanceData = await resp.json();
    }

    // 5. Initial What-If Query
    if (!window.miState.whatIfData) {
      await fetchWhatIfData(45.0, 70.0, 2, 40.0);
    }

    // 6. Dataset Explorer Data
    if (!window.miState.explorerData) {
      const resp = await fetch("/api/v1/model-intel/dataset-explorer");
      if (resp.ok) window.miState.explorerData = await resp.json();
    }

    // Trigger rendering of currently active tab
    renderActiveModelIntelTab();
  } catch (err) {
    console.error("[ModelIntel] Error loading dashboard data:", err);
  }
}

function switchModelIntelTab(tabId, btnElem) {
  window.miState.currentTab = tabId;
  document.querySelectorAll(".mi-tab-btn").forEach(b => b.classList.remove("active"));
  if (btnElem) btnElem.classList.add("active");

  document.querySelectorAll(".mi-tab-content").forEach(p => {
    p.style.display = "none";
    p.classList.remove("active");
  });

  const targetPane = document.getElementById(`mi-tab-${tabId}`);
  if (targetPane) {
    targetPane.style.display = "block";
    targetPane.classList.add("active");
  }

  // Allow DOM to layout before canvas drawing
  setTimeout(() => {
    renderActiveModelIntelTab();
  }, 60);
}

function renderActiveModelIntelTab() {
  const tab = window.miState.currentTab;
  if (tab === 'lineage') {
    renderLineageSection(window.miState.lineageData);
  } else if (tab === 'training') {
    const sel = document.getElementById("mi-training-model-select");
    renderTrainingCurvesChart(sel ? sel.value : "Adaptive_Gated_DCRNN");
  } else if (tab === 'evaluation') {
    renderEvaluationSection(window.miState.evalData);
  } else if (tab === 'explainability') {
    renderExplainabilitySection(window.miState.importanceData);
  } else if (tab === 'whatif') {
    renderWhatIfSection(window.miState.whatIfData);
  } else if (tab === 'explorer') {
    const sel = document.getElementById("mi-explorer-dataset-select");
    renderDatasetExplorer(sel ? sel.value : "blue_heart");
  }
}

// -----------------------------------------------------------------------------
// 1. DATASET LINEAGE & MASTER PROVENANCE MATRIX
// -----------------------------------------------------------------------------
function renderLineageSection(data) {
  if (!data || !data.lineage_matrix) return;
  const grid = document.getElementById("mi-lineage-cards-grid");
  const tbody = document.getElementById("mi-provenance-table-body");
  if (!grid || !tbody) return;

  const badgeClasses = {
    "SUPERVISED_DEEP_LEARNING_TRAINING": "mi-badge-supervised",
    "PRIMARY_PRODUCTION_INFERENCE": "mi-badge-production",
    "PHYSICAL_HYDRODYNAMIC_GROUND_TRUTH": "mi-badge-physics",
    "BENCHMARK_PRETRAINING": "mi-badge-baseline",
    "DYNAMIC_WAVE_VALIDATION": "mi-badge-baseline",
    "MONSOON_HYETOGRAPH_CALIBRATION": "mi-badge-production"
  };

  // 1. Render Cards
  let cardsHtml = "";
  data.lineage_matrix.forEach(item => {
    const bClass = badgeClasses[item.role] || "mi-badge-baseline";
    cardsHtml += `
      <div class="mi-lineage-card">
        <div>
          <div class="mi-lc-header">
            <span class="mi-lc-badge ${bClass}">${item.role_badge}</span>
          </div>
          <div class="mi-lc-title">${item.dataset_name}</div>
          <div class="mi-lc-source">${item.source}</div>
          <div class="mi-lc-stat-row">
            <span class="mi-lc-label">Spatial Scale</span>
            <span class="mi-lc-val">${item.scale}</span>
          </div>
          <div class="mi-lc-stat-row">
            <span class="mi-lc-label">Target Metric</span>
            <span class="mi-lc-val">${item.target}</span>
          </div>
          <div class="mi-lc-stat-row">
            <span class="mi-lc-label">Trained Model</span>
            <span class="mi-lc-val text-cyan">${item.models_trained[0]}</span>
          </div>
        </div>
        <div style="margin-top: 12px; font-size: 11px; color: #94a3b8; line-height: 1.4; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px;">
          ${item.role_desc}
        </div>
      </div>
    `;
  });
  grid.innerHTML = cardsHtml;

  // 2. Render Table
  let rowsHtml = "";
  data.lineage_matrix.forEach(item => {
    const bClass = badgeClasses[item.role] || "mi-badge-baseline";
    rowsHtml += `
      <tr>
        <td><b>${item.dataset_name}</b></td>
        <td>${item.scale}</td>
        <td><span class="mi-lc-val">${item.raw_domain.substring(0, 45)}...</span></td>
        <td>${item.features_used.map(f => `<span style="display:inline-block; background:rgba(255,255,255,0.06); padding:2px 6px; border-radius:4px; margin:2px; font-size:11px;">${f}</span>`).join('')}</td>
        <td>${item.target}</td>
        <td><b class="text-cyan">${item.models_trained[0]}</b></td>
        <td><span class="mi-lc-badge ${bClass}">${item.role_badge}</span></td>
      </tr>
    `;
  });
  tbody.innerHTML = rowsHtml;
}

// -----------------------------------------------------------------------------
// 2. TRAINING DYNAMICS (CSV LOSS CURVES)
// -----------------------------------------------------------------------------
function renderTrainingCurvesChart(modelName) {
  const data = window.miState.trainingData;
  if (!data || !data.models) return;

  const canvas = document.getElementById("mi-canvas-loss-curves");
  if (!canvas) return;

  // Resize canvas to match display size
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * (window.devicePixelRatio || 1);
  canvas.height = rect.height * (window.devicePixelRatio || 1);

  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padLeft = 60, padRight = 30, padTop = 30, padBottom = 40;
  const plotW = W - padLeft - padRight;
  const plotH = H - padTop - padBottom;

  // Grid background
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const y = padTop + (plotH / 5) * i;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(W - padRight, y);
    ctx.stroke();
  }

  if (modelName === "ALL") {
    // Render validation curves for all 4 models
    const colors = {
      "Adaptive_Gated_DCRNN": "#00d2ff",
      "Res_Temporal_GRU": "#10b981",
      "Res_DCRNN": "#f59e0b",
      "Graph_WaveNet": "#a855f7"
    };
    let minLoss = 0.12, maxLoss = 0.65;
    
    Object.keys(data.models).forEach(m => {
      const mData = data.models[m];
      const color = colors[m] || "#ffffff";
      drawCurve(ctx, mData.epochs, mData.val_loss, minLoss, maxLoss, padLeft, padTop, plotW, plotH, color, 2.5);
    });

    // Legend
    const legend = document.getElementById("mi-training-legend");
    if (legend) {
      legend.innerHTML = Object.keys(data.models).map(m => `
        <div class="mi-legend-item">
          <span class="mi-legend-color" style="background:${colors[m]}"></span>
          <span>${m.replace(/_/g, ' ')}</span>
        </div>
      `).join('');
    }
  } else {
    // Render specific model Train vs Val Loss
    const mData = data.models[modelName];
    if (!mData) return;

    const allVals = [...mData.train_loss, ...mData.val_loss];
    const minLoss = Math.max(0.10, Math.min(...allVals) * 0.9);
    const maxLoss = Math.max(...allVals) * 1.05;

    // Y Axis Labels
    ctx.fillStyle = "#64748b";
    ctx.font = `${11 * (window.devicePixelRatio || 1)}px sans-serif`;
    ctx.textAlign = "right";
    for (let i = 0; i <= 5; i++) {
      const val = maxLoss - (i / 5) * (maxLoss - minLoss);
      const y = padTop + (plotH / 5) * i;
      ctx.fillText(val.toFixed(3), padLeft - 10, y + 4);
    }

    // X Axis Labels (Epochs)
    ctx.textAlign = "center";
    mData.epochs.forEach((ep, idx) => {
      const x = padLeft + (idx / Math.max(1, mData.epochs.length - 1)) * plotW;
      ctx.fillText(`Ep ${ep}`, x, H - padBottom + 20);
    });

    // Draw Train Loss (Cyan Line)
    drawCurve(ctx, mData.epochs, mData.train_loss, minLoss, maxLoss, padLeft, padTop, plotW, plotH, "#00d2ff", 2.5);

    // Draw Val Loss (Amber Line)
    drawCurve(ctx, mData.epochs, mData.val_loss, minLoss, maxLoss, padLeft, padTop, plotW, plotH, "#f59e0b", 2.5);

    // Mark Best Epoch Line
    const bestIdx = mData.epochs.indexOf(mData.best_epoch);
    if (bestIdx >= 0) {
      const bestX = padLeft + (bestIdx / Math.max(1, mData.epochs.length - 1)) * plotW;
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(bestX, padTop);
      ctx.lineTo(bestX, padTop + plotH);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = "#10b981";
      ctx.font = `bold ${11 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.fillText(`Best Ep ${mData.best_epoch} (${mData.best_val_loss})`, bestX, padTop - 10);
    }

    // Update Telemetry boxes
    const epElem = document.getElementById("mi-tele-best-epoch");
    const lossElem = document.getElementById("mi-tele-best-loss");
    if (epElem) epElem.textContent = `Epoch ${mData.best_epoch}`;
    if (lossElem) lossElem.textContent = mData.best_val_loss.toFixed(5);

    // Legend
    const legend = document.getElementById("mi-training-legend");
    if (legend) {
      legend.innerHTML = `
        <div class="mi-legend-item"><span class="mi-legend-color" style="background:#00d2ff"></span><span>Train Loss</span></div>
        <div class="mi-legend-item"><span class="mi-legend-color" style="background:#f59e0b"></span><span>Validation Loss</span></div>
        <div class="mi-legend-item"><span class="mi-legend-color" style="background:#10b981"></span><span>Optimal Early Stop (Ep ${mData.best_epoch})</span></div>
      `;
    }
  }
}

function drawCurve(ctx, xArr, yArr, minY, maxY, left, top, w, h, color, lineWidth) {
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.beginPath();
  const N = xArr.length;
  for (let i = 0; i < N; i++) {
    const x = left + (i / Math.max(1, N - 1)) * w;
    const normY = (yArr[i] - minY) / Math.max(1e-5, maxY - minY);
    const y = top + h - (normY * h);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Draw points
  ctx.fillStyle = color;
  for (let i = 0; i < N; i++) {
    const x = left + (i / Math.max(1, N - 1)) * w;
    const normY = (yArr[i] - minY) / Math.max(1e-5, maxY - minY);
    const y = top + h - (normY * h);
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  }
}

// -----------------------------------------------------------------------------
// 3. MODEL EVALUATION & RESIDUAL DIAGNOSTICS
// -----------------------------------------------------------------------------
function renderEvaluationSection(data) {
  if (!data) return;

  // 1. Draw Scatter Plot (Actual vs Predicted)
  const cScatter = document.getElementById("mi-canvas-scatter");
  if (cScatter && data.scatter_points) {
    const rect = cScatter.parentElement.getBoundingClientRect();
    cScatter.width = rect.width * (window.devicePixelRatio || 1);
    cScatter.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = cScatter.getContext("2d");
    const W = cScatter.width, H = cScatter.height;
    ctx.clearRect(0, 0, W, H);

    const pad = 45;
    const plotW = W - pad * 2, plotH = H - pad * 2;
    const maxVal = 1.4;

    // Grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const v = (i / 4) * maxVal;
      const x = pad + (i / 4) * plotW;
      const y = pad + plotH - (i / 4) * plotH;
      ctx.beginPath(); ctx.moveTo(x, pad); ctx.lineTo(x, pad + plotH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(pad + plotW, y); ctx.stroke();
      ctx.fillStyle = "#64748b";
      ctx.font = `${10 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.fillText(v.toFixed(1) + "m", x - 10, pad + plotH + 18);
      ctx.fillText(v.toFixed(1) + "m", pad - 35, y + 4);
    }

    // 1:1 Diagonal
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(0, 210, 255, 0.5)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(pad, pad + plotH);
    ctx.lineTo(pad + plotW, pad);
    ctx.stroke();
    ctx.setLineDash([]);

    // Plot Points
    data.scatter_points.forEach(pt => {
      const x = pad + (pt.actual_m / maxVal) * plotW;
      const y = pad + plotH - (pt.predicted_m / maxVal) * plotH;
      ctx.fillStyle = "rgba(0, 210, 255, 0.6)";
      ctx.beginPath();
      ctx.arc(x, y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // 2. Draw Residuals Histogram
  const cRes = document.getElementById("mi-canvas-residuals");
  if (cRes && data.residual_histogram) {
    const rect = cRes.parentElement.getBoundingClientRect();
    cRes.width = rect.width * (window.devicePixelRatio || 1);
    cRes.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = cRes.getContext("2d");
    const W = cRes.width, H = cRes.height;
    ctx.clearRect(0, 0, W, H);

    const pad = 40;
    const plotW = W - pad * 2, plotH = H - pad * 2;
    const bins = data.residual_histogram;
    const maxCount = Math.max(...bins.map(b => b.count));
    const binW = plotW / bins.length;

    bins.forEach((b, idx) => {
      const barH = (b.count / maxCount) * plotH;
      const x = pad + idx * binW;
      const y = pad + plotH - barH;

      // Color gradient based on distance from zero
      const distFromZero = Math.abs((b.bin_start_m + b.bin_end_m) / 2);
      ctx.fillStyle = distFromZero < 0.02 ? "#10b981" : (distFromZero < 0.05 ? "#00d2ff" : "#f59e0b");
      ctx.fillRect(x + 2, y, binW - 4, barH);
    });

    // Zero line
    const zeroX = pad + (plotW / 2);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(zeroX, pad);
    ctx.lineTo(zeroX, pad + plotH);
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.font = `bold ${10 * (window.devicePixelRatio || 1)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText("0 cm (Zero Error)", zeroX, pad + plotH + 18);
  }

  // 3. Fill Benchmark Table
  const tbody = document.getElementById("mi-benchmark-table-body");
  if (tbody && data.benchmark_summary) {
    const verdicts = {
      "Persistence": "High baseline auto-correlation on slow recession; cannot anticipate rain spikes.",
      "Residual_Ridge": "Linear formulation overfits high residuals; poor generalization to high-water.",
      "Res_Temporal_GRU": "Strong temporal tracking; misses spatial flood wave propagation across nodes.",
      "Res_DCRNN": "Rigid physical adjacency graph causes oversmoothing of localized gully surges.",
      "Adaptive_Gated_DCRNN": "BEST TRADE-OFF: Learns adaptive spatial weights while gating dry-weather noise.",
      "Graph_WaveNet": "Competitive multi-scale dilated convolutions; slightly higher parameter count."
    };

    let rowsHtml = "";
    Object.keys(data.benchmark_summary).forEach(m => {
      const b = data.benchmark_summary[m];
      const hw = (data.high_water_summary && data.high_water_summary[m]) ? data.high_water_summary[m] : {};
      const isCandidate = (m === "Adaptive_Gated_DCRNN");
      rowsHtml += `
        <tr style="${isCandidate ? 'background: rgba(0,210,255,0.08); font-weight: 600;' : ''}">
          <td><b class="${isCandidate ? 'text-cyan' : ''}">${m.replace(/_/g, ' ')}</b> ${isCandidate ? '<span class="mi-lc-badge mi-badge-supervised">Selected</span>' : ''}</td>
          <td>${b.valid_obs.mae.toFixed(4)} m</td>
          <td>${b.valid_obs.rmse.toFixed(4)} m</td>
          <td>${b.valid_obs.nse.toFixed(4)}</td>
          <td>${b.valid_obs.r2.toFixed(4)}</td>
          <td>${b.peak_dt.toFixed(1)} h</td>
          <td><b>${hw.mae ? hw.mae.toFixed(4) + ' m' : 'N/A'}</b></td>
          <td style="font-size: 11px; color: ${isCandidate ? '#00d2ff' : '#94a3b8'};">${verdicts[m] || 'Evaluated on held-out test split.'}</td>
        </tr>
      `;
    });
    tbody.innerHTML = rowsHtml;
  }
}

// -----------------------------------------------------------------------------
// 4. FEATURE IMPORTANCE & EXPLAINABLE AI (XAI)
// -----------------------------------------------------------------------------
function renderExplainabilitySection(data) {
  if (!data) return;

  // 1. Horizontal Bar Chart (Indore 12 Features)
  const canvas = document.getElementById("mi-canvas-importance");
  if (canvas && data.indore_feature_importance) {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const padLeft = 190, padRight = 80, padTop = 20, padBottom = 20;
    const plotW = W - padLeft - padRight;
    const feats = data.indore_feature_importance;
    const barH = (H - padTop - padBottom) / feats.length;

    feats.forEach((f, idx) => {
      const y = padTop + idx * barH;
      const barLen = (f.importance_pct / 32.0) * plotW;

      // Label
      ctx.fillStyle = "#e2e8f0";
      ctx.font = `${11 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.textAlign = "right";
      ctx.fillText(f.display_name.substring(0, 26), padLeft - 10, y + barH / 2 + 4);

      // Bar
      const grad = ctx.createLinearGradient(padLeft, 0, padLeft + barLen, 0);
      grad.addColorStop(0, "#0284c7");
      grad.addColorStop(1, idx < 3 ? "#00d2ff" : "#38bdf8");
      ctx.fillStyle = grad;
      ctx.fillRect(padLeft, y + 4, barLen, barH - 8);

      // Value text
      ctx.fillStyle = "#00d2ff";
      ctx.font = `bold ${11 * (window.devicePixelRatio || 1)}px 'JetBrains Mono', monospace`;
      ctx.textAlign = "left";
      ctx.fillText(`${f.importance_pct.toFixed(1)}% (+${f.delta_mae_cm.toFixed(1)}cm)`, padLeft + barLen + 8, y + barH / 2 + 4);
    });
  }

  // 2. Per-Node Sensitivity Table
  const tbody = document.getElementById("mi-node-sensitivity-tbody");
  if (tbody && data.per_node_sensitivity) {
    tbody.innerHTML = data.per_node_sensitivity.map(n => `
      <tr>
        <td><b>${n.name}</b></td>
        <td><span class="text-cyan">${n.rainfall_pct}%</span></td>
        <td><span class="text-amber">${n.upstream_pct}%</span></td>
        <td>${n.elevation_pct}%</td>
        <td><span class="text-green">${n.pumps_pct}%</span></td>
        <td>${n.saturation_pct}%</td>
      </tr>
    `).join('');
  }

  // 3. Temporal Lag Decay Canvas
  const cLag = document.getElementById("mi-canvas-temporal-lag");
  if (cLag && data.temporal_lag_weights) {
    const rect = cLag.parentElement.getBoundingClientRect();
    cLag.width = rect.width * (window.devicePixelRatio || 1);
    cLag.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = cLag.getContext("2d");
    const W = cLag.width, H = cLag.height;
    ctx.clearRect(0, 0, W, H);

    const pad = 25;
    const lags = data.temporal_lag_weights;
    const barW = (W - pad * 2) / lags.length;

    lags.forEach((l, idx) => {
      const barH = (l.weight / 0.30) * (H - pad * 2);
      const x = pad + idx * barW;
      const y = H - pad - barH;

      ctx.fillStyle = "rgba(0, 210, 255, 0.75)";
      ctx.fillRect(x + 4, y, barW - 8, barH);

      ctx.fillStyle = "#94a3b8";
      ctx.font = `${10 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.textAlign = "center";
      ctx.fillText(l.time_label, x + barW / 2, H - 8);

      ctx.fillStyle = "#ffffff";
      ctx.fillText(`${Math.round(l.weight * 100)}%`, x + barW / 2, y - 4);
    });
  }
}

// -----------------------------------------------------------------------------
// 5. WHAT-IF SCENARIO LAB & SENSITIVITY RESPONSE
// -----------------------------------------------------------------------------
async function fetchWhatIfData(rain, sat, pumps, cumul) {
  try {
    const resp = await fetch("/api/v1/model-intel/what-if", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rainfall_intensity_mmh: rain,
        soil_saturation_pct: sat,
        active_pumps: pumps,
        cumulative_rain_mm: cumul
      })
    });
    if (resp.ok) {
      window.miState.whatIfData = await resp.json();
      renderWhatIfSection(window.miState.whatIfData);
    }
  } catch (err) {
    console.error("[ModelIntel] What-If query failed:", err);
  }
}

function onWhatIfSliderChange() {
  const rain = parseFloat(document.getElementById("mi-input-rain").value);
  const sat = parseFloat(document.getElementById("mi-input-sat").value);
  const pumps = parseInt(document.getElementById("mi-input-pumps").value);
  const cumul = parseFloat(document.getElementById("mi-input-cumul").value);

  // Update Labels
  document.getElementById("mi-val-rain").textContent = `${rain} mm/h`;
  document.getElementById("mi-val-sat").textContent = `${sat}%`;
  document.getElementById("mi-val-pumps").textContent = `${pumps} Pumps`;
  document.getElementById("mi-val-cumul").textContent = `${cumul} mm`;

  clearTimeout(window.miState.whatIfTimer);
  window.miState.whatIfTimer = setTimeout(() => {
    fetchWhatIfData(rain, sat, pumps, cumul);
  }, 100);
}

function renderWhatIfSection(data) {
  if (!data) return;

  // 1. Draw Response Curve (Rain vs Inundation Depth)
  const canvas = document.getElementById("mi-canvas-whatif-response");
  if (canvas && data.rainfall_response_curve) {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const padLeft = 45, padRight = 30, padTop = 20, padBottom = 30;
    const plotW = W - padLeft - padRight;
    const plotH = H - padTop - padBottom;
    const curve = data.rainfall_response_curve;
    const maxDepth = 120.0;

    // Grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (plotH / 4) * i;
      ctx.beginPath(); ctx.moveTo(padLeft, y); ctx.lineTo(W - padRight, y); ctx.stroke();
      const depthVal = maxDepth - (i / 4) * maxDepth;
      ctx.fillStyle = "#64748b";
      ctx.font = `${10 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.textAlign = "right";
      ctx.fillText(`${depthVal.toFixed(0)}cm`, padLeft - 8, y + 4);
    }

    // Critical flood depth threshold (50 cm)
    const critY = padTop + plotH - (50.0 / maxDepth) * plotH;
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(239, 68, 68, 0.7)";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(padLeft, critY); ctx.lineTo(W - padRight, critY); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#ef4444";
    ctx.textAlign = "right";
    ctx.fillText("50cm Surcharge Hazard", W - padRight, critY - 6);

    // Draw Curve
    ctx.strokeStyle = "#00d2ff";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    curve.forEach((pt, idx) => {
      const x = padLeft + (pt.rainfall_mmh / 110.0) * plotW;
      const y = padTop + plotH - (pt.inundation_depth_cm / maxDepth) * plotH;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Mark current selected rainfall
    const curRain = data.inputs.rainfall_intensity_mmh;
    const curX = padLeft + (curRain / 110.0) * plotW;
    const curPt = curve.find(p => p.rainfall_mmh >= curRain) || curve[curve.length - 1];
    const curY = padTop + plotH - (curPt.inundation_depth_cm / maxDepth) * plotH;

    ctx.fillStyle = "#f59e0b";
    ctx.beginPath();
    ctx.arc(curX, curY, 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#f8fafc";
    ctx.font = `bold ${11 * (window.devicePixelRatio || 1)}px sans-serif`;
    ctx.textAlign = "left";
    ctx.fillText(`${curPt.inundation_depth_cm} cm (${curRain} mm/h)`, curX + 10, curY - 6);
  }

  // 2. Render Waterfall Decomposition
  const wfBox = document.getElementById("mi-waterfall-box");
  if (wfBox && data.waterfall_decomposition) {
    const wf = data.waterfall_decomposition;
    wfBox.innerHTML = wf.map(item => {
      const absVal = Math.abs(item.value);
      const barWidth = Math.min(100, (absVal / 50.0) * 100);
      return `
        <div class="mi-wf-row mi-wf-${item.type}">
          <span class="mi-wf-label">${item.factor}</span>
          <div class="mi-wf-bar-wrap">
            <div class="mi-wf-bar" style="width: ${barWidth}%;"></div>
          </div>
          <span class="mi-wf-val">${item.value > 0 ? '+' : ''}${item.value.toFixed(1)}%</span>
        </div>
      `;
    }).join('');
  }
}

// -----------------------------------------------------------------------------
// 6. DATASET STATISTICAL EXPLORER
// -----------------------------------------------------------------------------
function renderDatasetExplorer(datasetId) {
  const data = window.miState.explorerData;
  if (!data || !data.datasets) return;

  const ds = data.datasets.find(d => d.id === datasetId) || data.datasets[0];
  const container = document.getElementById("mi-explorer-content");
  if (!container || !ds) return;

  let tableRows = "";
  ds.feature_distributions.forEach(f => {
    tableRows += `
      <tr>
        <td><b>${f.feature}</b></td>
        <td><span class="mi-lc-badge mi-badge-supervised">${f.unit}</span></td>
        <td>${f.mean.toFixed(3)}</td>
        <td>${f.std.toFixed(3)}</td>
        <td>${f.min.toFixed(2)}</td>
        <td>${f.q25.toFixed(2)}</td>
        <td><b>${f.median.toFixed(2)}</b></td>
        <td>${f.q75.toFixed(2)}</td>
        <td>${f.max.toFixed(2)}</td>
      </tr>
    `;
  });

  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
      <div>
        <h3 style="color:#f8fafc; font-size:16px; font-weight:750;">${ds.title}</h3>
        <p style="font-size:12px; color:#94a3b8; margin-top:3px;">${ds.records_count.toLocaleString()} Usable Records • ${ds.nodes} Spatial Nodes</p>
      </div>
      <div style="text-align:right;">
        <span class="mi-lc-badge ${ds.missingness_rate_pct > 0 ? 'mi-badge-physics' : 'mi-badge-production'}">Missingness: ${ds.missingness_rate_pct}%</span>
        <div style="font-size:11px; color:#64748b; margin-top:4px;">${ds.missingness_note}</div>
      </div>
    </div>
    <div class="table-responsive">
      <table class="mi-table">
        <thead>
          <tr>
            <th>Feature Name</th>
            <th>Engineering Unit</th>
            <th>Mean (μ)</th>
            <th>Std Dev (σ)</th>
            <th>Min</th>
            <th>Q1 (25%)</th>
            <th>Median (50%)</th>
            <th>Q3 (75%)</th>
            <th>Max</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
    </div>
  `;
}
"""

if "TASK 3.8: AI MODEL INTELLIGENCE" not in content:
    content += MI_JS
    JS_FILE.write_text(content, encoding="utf-8")
    print(f"Appended Model Intelligence logic to {JS_FILE}")
else:
    print("JS logic already present.")
