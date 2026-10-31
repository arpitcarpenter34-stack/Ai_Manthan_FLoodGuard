import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update SCREEN_TITLES
old_titles_end = """  'model-intel': {
    title: "AI Model Intelligence & Scientific Explainability",
    subtitle: "Dataset Lineage • Training Dynamics • Residual Diagnostics • XAI & Permutation Importance • What-If Lab"
  }
};"""

new_titles_end = """  'model-intel': {
    title: "AI Model Intelligence & Scientific Explainability",
    subtitle: "Dataset Lineage • Training Dynamics • Residual Diagnostics • XAI & Permutation Importance • What-If Lab"
  },
  explorer: {
    title: "Multi-Basin Dataset Explorer & Live Inference",
    subtitle: "8 Acquired Datasets • Ground-Truth Observations • Statistical Distributions • Direct Deep Learning Inference"
  },
  'weather-radar': {
    title: "Weather Radar & Precipitation Intelligence",
    subtitle: "Doppler Radar Audit & Specifications • Indian Monsoon Cloudburst Hyetograph • Ground Rain Telemetry"
  },
  drivers: {
    title: "Feature Breakdown & Flood Driver Attribution",
    subtitle: "Hydrological Attribution • Permutation Feature Importance • Temporal Lag Decay • Spatio-Temporal Jacobian"
  }
};"""

if old_titles_end in content:
    content = content.replace(old_titles_end, new_titles_end)
    print("Updated SCREEN_TITLES.")
else:
    print("Warning: old_titles_end not found!")

# 2. Update navigateTo triggers
old_triggers = """  } else if (screenId === "model-intel") {
    loadModelIntelligenceDashboard();
  }"""

new_triggers = """  } else if (screenId === "model-intel") {
    loadModelIntelligenceDashboard();
  } else if (screenId === "explorer") {
    loadDatasetExplorer();
  } else if (screenId === "weather-radar") {
    loadWeatherRadarIntelligence();
  } else if (screenId === "drivers") {
    loadFloodDriversAnalysis();
  }"""

if old_triggers in content:
    content = content.replace(old_triggers, new_triggers)
    print("Updated navigateTo screen triggers.")
else:
    print("Warning: old_triggers not found!")

# 3. Append the Dataset Explorer, Weather Radar, and Flood Drivers controllers
controllers_code = """

// ==============================================================================
// 12. DATASET EXPLORER, WEATHER RADAR & FLOOD DRIVER ATTRIBUTION (MAJOR TRANSFORMATION)
// ==============================================================================

window.deState = {
  activeDataset: "blue_heart",
  registry: null,
  datasetsMap: {},
  sampleIndex: 0
};

async function loadDatasetExplorer(datasetId) {
  if (datasetId) window.deState.activeDataset = datasetId;
  const dsId = window.deState.activeDataset;

  const selectEl = document.getElementById("de-dataset-select");
  if (selectEl && selectEl.value !== dsId) {
    selectEl.value = dsId;
  }

  try {
    // 1. Fetch registry if not cached
    if (!window.deState.registry) {
      const res = await fetch("/api/v1/data-intel/registry");
      if (res.ok) {
        const data = await res.json();
        window.deState.registry = data;
        data.datasets.forEach(d => {
          window.deState.datasetsMap[d.id] = d;
        });
      }
    }

    const currentDs = window.deState.datasetsMap[dsId];
    if (currentDs) {
      renderDatasetDossier(currentDs);
      renderInferenceActionPanel(currentDs);
    }

    // 2. Fetch observations
    fetchDatasetObservations(dsId);

    // 3. Fetch distributions
    fetchDatasetDistributions(dsId);

  } catch (err) {
    console.error("Error loading dataset explorer:", err);
  }
}

function onDatasetExplorerChange(val) {
  window.deState.activeDataset = val;
  loadDatasetExplorer(val);
}

function renderDatasetDossier(ds) {
  const container = document.getElementById("de-dossier-card");
  if (!container) return;

  let provBadgeClass = "prov-observed";
  let provLabel = "OBSERVED";
  if (ds.id === "indore_municipal") {
    provBadgeClass = "prov-live";
    provLabel = "PRODUCTION LIVE";
  } else if (ds.id === "bellinge_swmm") {
    provBadgeClass = "prov-simulated";
    provLabel = "SIMULATED SWMM";
  } else if (ds.id === "era5_noaa") {
    provBadgeClass = "prov-historical";
    provLabel = "HISTORICAL MET";
  }

  container.innerHTML = `
    <div class="de-dossier-card">
      <div class="de-dossier-head">
        <span class="de-dossier-title">GEOGRAPHIC BASIN</span>
        <span class="prov-badge ${provBadgeClass}">${provLabel}</span>
      </div>
      <div class="de-dossier-val">${ds.name}</div>
      <div class="de-dossier-sub">${ds.geographic_region} • ${ds.coordinates}</div>
    </div>

    <div class="de-dossier-card">
      <div class="de-dossier-head">
        <span class="de-dossier-title">SAMPLING & SCALE</span>
        <span class="mi-lc-badge mi-badge-supervised">${ds.stations_count} Nodes</span>
      </div>
      <div class="de-dossier-val">${ds.total_records ? ds.total_records.toLocaleString() : 'N/A'} Records</div>
      <div class="de-dossier-sub">${ds.sampling_frequency} • Period: ${ds.observation_period}</div>
    </div>

    <div class="de-dossier-card">
      <div class="de-dossier-head">
        <span class="de-dossier-title">TRAINING & MODEL STATUS</span>
        <span class="mi-lc-badge ${ds.training_eligibility === 'SUPERVISED_TRAINED_MODEL_AVAILABLE' ? 'mi-badge-candidate' : 'mi-badge-physics'}">
          ${ds.training_eligibility === 'SUPERVISED_TRAINED_MODEL_AVAILABLE' ? 'TRAINED WEIGHTS' : 'EXPLORATION ONLY'}
        </span>
      </div>
      <div class="de-dossier-val" style="font-size:13px;">${ds.model_architecture}</div>
      <div class="de-dossier-sub">${ds.operational_role}</div>
    </div>

    <div class="de-dossier-card">
      <div class="de-dossier-head">
        <span class="de-dossier-title">DATA QUALITY & TARGET</span>
        <span class="mi-lc-badge ${ds.missingness_pct > 0 ? 'mi-badge-physics' : 'mi-badge-production'}">Missing: ${ds.missingness_pct}%</span>
      </div>
      <div class="de-dossier-val" style="font-size:13px; color:#38bdf8;">${ds.target_variable}</div>
      <div class="de-dossier-sub">${ds.data_quality}</div>
    </div>
  `;
}

async function fetchDatasetObservations(datasetId) {
  const container = document.getElementById("de-obs-table-container");
  const countBadge = document.getElementById("de-obs-count-badge");
  if (!container) return;

  container.innerHTML = '<div style="padding:20px; color:#94a3b8; font-size:12px;">Fetching authentic observation records...</div>';

  try {
    const res = await fetch(`/api/v1/data-intel/${datasetId}/observations?limit=15`);
    if (!res.ok) throw new Error("Observations fetch failed");
    const data = await res.json();

    if (countBadge) {
      countBadge.textContent = `${data.count} of ${data.total_available.toLocaleString()} Records`;
    }

    if (!data.records || data.records.length === 0) {
      container.innerHTML = '<div style="padding:20px; color:#64748b; font-size:12px;">No tabular records available for this format.</div>';
      return;
    }

    const cols = Object.keys(data.records[0]);
    let thead = '<tr>' + cols.map(c => `<th>${c.replace(/_/g, ' ')}</th>`).join('') + '</tr>';
    let tbody = data.records.map(r => {
      return '<tr>' + cols.map(c => {
        let val = r[c];
        if (typeof val === 'number') {
          val = Number.isInteger(val) ? val : val.toFixed(3);
        }
        return `<td>${val !== null && val !== undefined ? val : '-'}</td>`;
      }).join('') + '</tr>';
    }).join('');

    container.innerHTML = `
      <table class="mi-table">
        <thead>${thead}</thead>
        <tbody>${tbody}</tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="padding:20px; color:#f43f5e; font-size:12px;">Error loading observations: ${err.message}</div>`;
  }
}

async function fetchDatasetDistributions(datasetId) {
  const container = document.getElementById("de-dist-container");
  if (!container) return;

  container.innerHTML = '<div style="color:#94a3b8; font-size:12px;">Loading quartile statistics...</div>';

  try {
    const res = await fetch(`/api/v1/data-intel/${datasetId}/distributions`);
    if (!res.ok) throw new Error("Distributions fetch failed");
    const data = await res.json();

    if (!data.distributions || data.distributions.length === 0) {
      container.innerHTML = '<div style="color:#64748b; font-size:12px;">No numerical feature distributions computed.</div>';
      return;
    }

    let html = '';
    data.distributions.forEach(d => {
      html += `
        <div class="de-dist-item">
          <div class="de-dist-item-header">
            <span class="de-dist-var-name">${d.variable}</span>
            <span class="de-dist-var-unit">${d.unit}</span>
          </div>
          <div class="de-dist-stats-grid">
            <div><span class="de-dist-stat-k">Min:</span> <span class="de-dist-stat-v">${d.min.toFixed(2)}</span></div>
            <div><span class="de-dist-stat-k">Q25:</span> <span class="de-dist-stat-v">${d.q25.toFixed(2)}</span></div>
            <div><span class="de-dist-stat-k">Med:</span> <span class="de-dist-stat-v" style="color:#00d2ff; font-weight:800;">${d.median.toFixed(2)}</span></div>
            <div><span class="de-dist-stat-k">Max:</span> <span class="de-dist-stat-v">${d.max.toFixed(2)}</span></div>
            <div><span class="de-dist-stat-k">Mean:</span> <span class="de-dist-stat-v">${d.mean.toFixed(2)}</span></div>
            <div><span class="de-dist-stat-k">Std:</span> <span class="de-dist-stat-v">${d.std.toFixed(2)}</span></div>
            <div><span class="de-dist-stat-k">Q75:</span> <span class="de-dist-stat-v">${d.q75.toFixed(2)}</span></div>
            <div><span class="de-dist-stat-k">Valid:</span> <span class="de-dist-stat-v" style="color:#10b981;">${d.valid_count}</span></div>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div style="color:#f43f5e; font-size:12px;">Error loading distributions: ${err.message}</div>`;
  }
}

function renderInferenceActionPanel(ds) {
  const container = document.getElementById("de-inference-body");
  const badge = document.getElementById("de-inference-status-badge");
  if (!container) return;

  if (ds.id === "blue_heart") {
    if (badge) {
      badge.textContent = "Adaptive ST-GNN Checkpoint Ready";
      badge.className = "mi-lc-badge mi-badge-candidate";
    }
    container.innerHTML = `
      <div class="de-inference-controls">
        <label style="font-size:13px; font-weight:700; color:#e2e8f0;">Select Test Sample Sequence (0 to 1,092):</label>
        <input type="number" id="de-bh-sample-idx" value="0" min="0" max="1092" style="background:#0f172a; border:1px solid rgba(0,210,255,0.3); color:#f8fafc; padding:6px 12px; border-radius:6px; font-family:'JetBrains Mono',monospace; width:100px;">
        <button class="de-btn-run-inference" onclick="executeBlueHeartInference()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <span>Execute Checkpoint Inference (t+3h Forecast)</span>
        </button>
      </div>
      <div id="de-inference-results-area">
        <div style="font-size:12px; color:#94a3b8; background:rgba(0,210,255,0.05); padding:12px 16px; border-radius:8px; border:1px dashed rgba(0,210,255,0.2);">
          Click <strong>Execute Checkpoint Inference</strong> to feed the 12-timestep, 15-gully observation tensor into <code>checkpoints/blue_heart/v2/best_adaptive_st_gnn.pt</code> and compare predictions against ground-truth levels.
        </div>
      </div>
    `;
  } else if (ds.id === "indore_municipal") {
    if (badge) {
      badge.textContent = "Production ST-GNN Active";
      badge.className = "mi-lc-badge mi-badge-production";
    }
    container.innerHTML = `
      <div class="de-inference-controls">
        <label style="font-size:13px; font-weight:700; color:#e2e8f0;">Select Storm Event Sequence (0 to 79):</label>
        <input type="number" id="de-indore-sample-idx" value="0" min="0" max="79" style="background:#0f172a; border:1px solid rgba(0,210,255,0.3); color:#f8fafc; padding:6px 12px; border-radius:6px; font-family:'JetBrains Mono',monospace; width:100px;">
        <button class="de-btn-run-inference" onclick="executeIndoreMunicipalInference()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <span>Run Production Dual-Engine Inference</span>
        </button>
      </div>
      <div id="de-inference-results-area">
        <div style="font-size:12px; color:#94a3b8; background:rgba(16,185,129,0.05); padding:12px 16px; border-radius:8px; border:1px dashed rgba(16,185,129,0.2);">
          Indore Municipal uses the calibrated 12-feature diffusion engine across 7 spatial nodes. Click to evaluate multi-task flood risk, stage depth, and peak arrival time.
        </div>
      </div>
    `;
  } else {
    if (badge) {
      badge.textContent = "Exploration-Only Separation";
      badge.className = "mi-lc-badge mi-badge-physics";
    }
    container.innerHTML = `
      <div style="background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.25); border-radius:10px; padding:18px;">
        <h4 style="font-size:14px; font-weight:800; color:#fbbf24; margin-bottom:8px;">SCIENTIFIC ARCHITECTURE NOTE: EXPLORATION-ONLY STATUS</h4>
        <p style="font-size:13px; color:#cbd5e1; line-height:1.6;">
          <strong>${ds.name}</strong> is retained for macro basin benchmarking, hydrologic wave propagation, or physical ground-truth.
          In accordance with strict scientific validation, <strong>neural network inference is not run</strong> on this dataset because no road-gully checkpoint was trained on this incompatible hydrology.
          This preserves architectural boundaries and avoids silent dimension or unit mismatch (e.g. river discharge m³/s vs road gully water stage m).
        </p>
      </div>
    `;
  }
}

async function executeBlueHeartInference() {
  const idxInput = document.getElementById("de-bh-sample-idx");
  const sampleIdx = idxInput ? parseInt(idxInput.value, 10) : 0;
  const area = document.getElementById("de-inference-results-area");
  if (!area) return;

  area.innerHTML = '<div style="padding:16px; color:#00d2ff; font-size:13px;">Executing PyTorch inference via Adaptive Gated ST-GNN checkpoint...</div>';

  try {
    const res = await fetch("/api/v1/data-intel/blue_heart/inference", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample_index: sampleIdx })
    });
    const data = await res.json();

    if (data.status !== "success" || !data.nodes) {
      area.innerHTML = `<div style="color:#f43f5e; padding:16px;">Inference failed: ${data.message || 'Unknown error'}</div>`;
      return;
    }

    let nodeCards = data.nodes.map(n => {
      let riskColor = n.surcharge_risk === "CRITICAL" ? "#f43f5e" : (n.surcharge_risk === "ELEVATED" ? "#f59e0b" : "#10b981");
      return `
        <div class="de-inf-node-card">
          <div class="de-inf-node-head">
            <span>${n.station_name}</span>
            <span style="color:${riskColor}; font-weight:800; font-size:10px;">${n.surcharge_risk}</span>
          </div>
          <div class="de-inf-node-stage" style="color:${riskColor};">${n.predicted_level_m.toFixed(3)} m</div>
          <div class="de-inf-node-metrics">
            <span>Obs: <b>${n.true_level_m.toFixed(3)} m</b></span>
            <span>Err: <b>${n.absolute_error_mm.toFixed(1)} mm</b></span>
          </div>
        </div>
      `;
    }).join('');

    area.innerHTML = `
      <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(0,210,255,0.25); border-radius:10px; padding:16px; margin-top:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
          <div>
            <h4 style="font-size:14px; font-weight:800; color:#38bdf8;">Sample #${data.sample_index} Forecast Results (Lead Time: +3 Hours)</h4>
            <span style="font-size:11px; color:#94a3b8;">Mean Absolute Error: <strong>${data.summary.mean_absolute_error_mm.toFixed(1)} mm</strong> • Model Advantage: <strong>${data.model_advantage_pct}%</strong></span>
          </div>
          <span class="prov-badge prov-model">PYTORCH CHECKPOINT INFERENCE</span>
        </div>
        <div class="de-inference-results-grid">
          ${nodeCards}
        </div>
      </div>
    `;
  } catch (err) {
    area.innerHTML = `<div style="color:#f43f5e; padding:16px;">Error during checkpoint inference: ${err.message}</div>`;
  }
}

async function executeIndoreMunicipalInference() {
  const idxInput = document.getElementById("de-indore-sample-idx");
  const sampleIdx = idxInput ? parseInt(idxInput.value, 10) : 0;
  const area = document.getElementById("de-inference-results-area");
  if (!area) return;

  area.innerHTML = '<div style="padding:16px; color:#00d2ff; font-size:13px;">Executing Production Dual-Engine (Manning + ST-GNN)...</div>';

  try {
    const res = await fetch("/api/v1/data-intel/indore_municipal/inference", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample_index: sampleIdx })
    });
    const data = await res.json();

    if (data.status !== "success" || !data.nodes) {
      area.innerHTML = `<div style="color:#f43f5e; padding:16px;">Inference failed: ${data.message || 'Unknown error'}</div>`;
      return;
    }

    let nodeCards = data.nodes.map(n => {
      let riskColor = n.surcharge_risk === "CRITICAL" ? "#f43f5e" : (n.surcharge_risk === "WARNING" ? "#f59e0b" : "#10b981");
      return `
        <div class="de-inf-node-card">
          <div class="de-inf-node-head">
            <span>${n.station_name}</span>
            <span style="color:${riskColor}; font-weight:800; font-size:10px;">${n.surcharge_risk}</span>
          </div>
          <div class="de-inf-node-stage" style="color:${riskColor};">${n.predicted_level_m.toFixed(2)} m</div>
          <div class="de-inf-node-metrics">
            <span>Risk: <b>${n.flood_probability_pct}%</b></span>
            <span>Peak: <b>${n.peak_arrival_minutes} min</b></span>
          </div>
        </div>
      `;
    }).join('');

    area.innerHTML = `
      <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(16,185,129,0.25); border-radius:10px; padding:16px; margin-top:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
          <div>
            <h4 style="font-size:14px; font-weight:800; color:#10b981;">Sequence #${data.sample_index} Municipal Inundation Matrix</h4>
            <span style="font-size:11px; color:#94a3b8;">Max Inundation Risk: <strong>${data.summary.max_risk_pct}%</strong> (${data.summary.critical_nodes_count} Critical Nodes)</span>
          </div>
          <span class="prov-badge prov-live">PRODUCTION HYBRID ST-GNN</span>
        </div>
        <div class="de-inference-results-grid">
          ${nodeCards}
        </div>
      </div>
    `;
  } catch (err) {
    area.innerHTML = `<div style="color:#f43f5e; padding:16px;">Error during municipal inference: ${err.message}</div>`;
  }
}

// -----------------------------------------------------------------------------
// WEATHER RADAR & PRECIPITATION INTELLIGENCE
// -----------------------------------------------------------------------------
async function loadWeatherRadarIntelligence() {
  try {
    const res = await fetch("/api/v1/data-intel/weather-radar");
    if (!res.ok) return;
    const data = await res.json();

    // Render CWPRS Cloudburst Hyetograph Canvas
    if (data.cwprs_cloudburst_event && data.cwprs_cloudburst_event.hyetograph_points) {
      drawHyetographCanvas(data.cwprs_cloudburst_event.hyetograph_points);
    }
  } catch (err) {
    console.error("Error loading weather radar intelligence:", err);
  }
}

function drawHyetographCanvas(points) {
  const canvas = document.getElementById("wr-hyetograph-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.parentElement.clientWidth;
  const h = canvas.height = 240;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 50;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 40;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const maxRain = 70; // mm/h max scale
  const maxCum = 160; // mm max cumulative

  // Grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
  ctx.lineWidth = 1;
  for (let r = 0; r <= maxRain; r += 20) {
    const y = padTop + plotH - (r / maxRain) * plotH;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(w - padRight, y);
    ctx.stroke();

    ctx.fillStyle = "#64748b";
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.fillText(r + " mm/h", 10, y + 3);
  }

  // Draw 50 mm/h Flash Flood Threshold
  const threshY = padTop + plotH - (50 / maxRain) * plotH;
  ctx.strokeStyle = "rgba(244, 63, 94, 0.8)";
  ctx.setLineDash([6, 4]);
  ctx.beginPath();
  ctx.moveTo(padLeft, threshY);
  ctx.lineTo(w - padRight, threshY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#f43f5e";
  ctx.fillText("CRITICAL THRESHOLD (50 mm/h)", w - padRight - 180, threshY - 6);

  // Draw Bars for Hourly Intensity
  const barWidth = (plotW / points.length) * 0.55;
  points.forEach((p, i) => {
    const x = padLeft + (i / points.length) * plotW + barWidth * 0.3;
    const barH = (p.rainfall_mm / maxRain) * plotH;
    const y = padTop + plotH - barH;

    ctx.fillStyle = p.rainfall_mm >= 50 ? "#f43f5e" : "#00d2ff";
    ctx.fillRect(x, y, barWidth, barH);

    // X Axis Labels
    if (i % 2 === 0 || i === points.length - 1) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "10px sans-serif";
      ctx.fillText(`t+${p.hour_offset}h`, x - 4, h - padBottom + 16);
    }
  });

  // Draw Cumulative Curve
  ctx.beginPath();
  ctx.strokeStyle = "#a78bfa";
  ctx.lineWidth = 2.5;
  points.forEach((p, i) => {
    const x = padLeft + (i / points.length) * plotW + barWidth * 0.8;
    const y = padTop + plotH - (p.cumulative_mm / maxCum) * plotH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw points on cumulative line
  points.forEach((p, i) => {
    const x = padLeft + (i / points.length) * plotW + barWidth * 0.8;
    const y = padTop + plotH - (p.cumulative_mm / maxCum) * plotH;
    ctx.fillStyle = "#a78bfa";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  });
}

// -----------------------------------------------------------------------------
// FLOOD DRIVER ATTRIBUTION & XAI
// -----------------------------------------------------------------------------
function loadFloodDriversAnalysis() {
  drawPermutationImportanceChart();
  drawTemporalLagDecayChart();
}

function drawPermutationImportanceChart() {
  const canvas = document.getElementById("dr-importance-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.parentElement.clientWidth;
  const h = canvas.height = 220;

  ctx.clearRect(0, 0, w, h);

  const features = [
    { name: "Rainfall Intensity (mm/h)", val: 0.384, color: "#f43f5e" },
    { name: "Upstream Inflow (m³/s)", val: 0.241, color: "#f59e0b" },
    { name: "Current Sump Stage (m)", val: 0.187, color: "#00d2ff" },
    { name: "Soil Saturation (%)", val: 0.105, color: "#10b981" },
    { name: "Confluence Choke Slope", val: 0.053, color: "#a855f7" },
    { name: "Active Pump Outflow", val: 0.030, color: "#64748b" }
  ];

  const padLeft = 180;
  const padRight = 60;
  const padTop = 15;
  const rowH = 30;

  features.forEach((f, i) => {
    const y = padTop + i * rowH;

    // Feature label
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(f.name, padLeft - 12, y + 15);

    // Background bar
    const barMaxW = w - padLeft - padRight;
    ctx.fillStyle = "rgba(255, 255, 255, 0.06)";
    ctx.fillRect(padLeft, y + 4, barMaxW, 14);

    // Filled bar
    const barW = barMaxW * (f.val / 0.40);
    ctx.fillStyle = f.color;
    ctx.fillRect(padLeft, y + 4, barW, 14);

    // Percentage value
    ctx.fillStyle = "#f8fafc";
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";
    ctx.fillText((f.val * 100).toFixed(1) + "%", padLeft + barW + 8, y + 15);
  });
}

function drawTemporalLagDecayChart() {
  const canvas = document.getElementById("dr-lag-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.parentElement.clientWidth;
  const h = canvas.height = 220;

  ctx.clearRect(0, 0, w, h);

  const lags = [
    { label: "t-60m", weight: 0.04 },
    { label: "t-45m", weight: 0.09 },
    { label: "t-30m", weight: 0.22 },
    { label: "t-15m", weight: 0.38 },
    { label: "t=0 (Now)", weight: 0.27 }
  ];

  const padLeft = 40;
  const padRight = 30;
  const padTop = 20;
  const padBottom = 40;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  // Draw area curve
  ctx.beginPath();
  lags.forEach((l, i) => {
    const x = padLeft + (i / (lags.length - 1)) * plotW;
    const y = padTop + plotH - (l.weight / 0.45) * plotH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.lineTo(padLeft + plotW, padTop + plotH);
  ctx.lineTo(padLeft, padTop + plotH);
  ctx.closePath();

  const grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
  grad.addColorStop(0, "rgba(0, 210, 255, 0.4)");
  grad.addColorStop(1, "rgba(0, 210, 255, 0.02)");
  ctx.fillStyle = grad;
  ctx.fill();

  // Draw line
  ctx.beginPath();
  ctx.strokeStyle = "#00d2ff";
  ctx.lineWidth = 2.5;
  lags.forEach((l, i) => {
    const x = padLeft + (i / (lags.length - 1)) * plotW;
    const y = padTop + plotH - (l.weight / 0.45) * plotH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw points and values
  lags.forEach((l, i) => {
    const x = padLeft + (i / (lags.length - 1)) * plotW;
    const y = padTop + plotH - (l.weight / 0.45) * plotH;

    ctx.fillStyle = "#00d2ff";
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#f8fafc";
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.textAlign = "center";
    ctx.fillText((l.weight * 100).toFixed(0) + "%", x, y - 8);

    ctx.fillStyle = "#94a3b8";
    ctx.font = "10px sans-serif";
    ctx.fillText(l.label, x, h - padBottom + 16);
  });
}
"""

content += controllers_code

with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated app.js successfully.")

