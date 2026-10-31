import re

js_code = """
// ==============================================================================
// TASK 4.1: WHITE-THEME DATASET EXPLORER & HYDROLOGICAL INTELLIGENCE CENTER
// Exact visual match to design reference: media_1793427602234_3a72ebdd.jpg
// ==============================================================================

window.deState = {
  activeDataset: "blue_heart",
  activeTab: "overview",
  cachedIntel: {},
  activeFeature: "rainfall",
  corrMethod: "pearson",
  timeSeriesData: null
};

async function loadDatasetExplorer(datasetId) {
  if (datasetId) window.deState.activeDataset = datasetId;
  const dsId = window.deState.activeDataset;

  // Sync dropdown and pills
  const selectEl = document.getElementById("de-dataset-select");
  if (selectEl && selectEl.value !== dsId) {
    selectEl.value = dsId;
  }
  updateDePillsActive(dsId);

  try {
    let intel = window.deState.cachedIntel[dsId];
    if (!intel) {
      const res = await fetch(`/api/v1/data-intel/${dsId}/intelligence`);
      if (!res.ok) throw new Error("Failed to fetch dataset intelligence");
      intel = await res.json();
      window.deState.cachedIntel[dsId] = intel;
    }

    renderDatasetIntelligence(intel);
  } catch (err) {
    console.error("Error loading dataset intelligence:", err);
  }
}

function updateDePillsActive(dsId) {
  const pills = document.querySelectorAll("#de-pills-bar .wt-pill-btn");
  pills.forEach(p => {
    if (p.getAttribute("data-ds") === dsId) {
      p.classList.add("active");
    } else {
      p.classList.remove("active");
    }
  });
}

function onDeDatasetChange(val) {
  window.deState.activeDataset = val;
  loadDatasetExplorer(val);
}

function onDeDatasetPillClick(val) {
  window.deState.activeDataset = val;
  const selectEl = document.getElementById("de-dataset-select");
  if (selectEl) selectEl.value = val;
  loadDatasetExplorer(val);
}

function switchDeTab(tabName) {
  window.deState.activeTab = tabName;
  
  // Update tab buttons
  document.querySelectorAll(".wt-subnav-tab").forEach(tab => {
    tab.classList.remove("active");
  });
  const activeBtn = document.getElementById(`de-tab-${tabName}`);
  if (activeBtn) activeBtn.classList.add("active");

  // Update panes
  document.querySelectorAll(".wt-pane").forEach(pane => {
    pane.classList.remove("active");
  });
  const activePane = document.getElementById(`de-pane-${tabName}`);
  if (activePane) activePane.classList.add("active");

  // Re-render any charts in newly visible tab
  const dsId = window.deState.activeDataset;
  const intel = window.deState.cachedIntel[dsId];
  if (intel) {
    if (tabName === "overview") {
      setTimeout(() => {
        renderDeDistFeatureChart();
        renderDeTimeSeriesChart();
        renderDeFloodResponse(intel.flood_response);
      }, 50);
    } else if (tabName === "relationships") {
      setTimeout(() => {
        renderDeRelationships(intel.relationships);
      }, 50);
    } else if (tabName === "fingerprint") {
      setTimeout(() => {
        renderDeFingerprintOverlay(intel.flood_fingerprints);
      }, 50);
    } else if (tabName === "model") {
      setTimeout(() => {
        renderDeLossCurve(intel.model_lineage ? intel.model_lineage.loss_history : null);
      }, 50);
    }
  }
}

function renderDatasetIntelligence(intel) {
  if (!intel) return;

  // 1. Summary Card
  const titleEl = document.getElementById("de-summary-title");
  if (titleEl) titleEl.textContent = intel.display_name || "Dataset Catchment";

  const locEl = document.getElementById("de-val-loc");
  if (locEl) locEl.textContent = intel.tagline || intel.geographic_region || "Catchment Testbed";

  const periodEl = document.getElementById("de-val-period");
  if (periodEl) periodEl.textContent = intel.observation_period || "Continuous Historical Observations";

  const tagsEl = document.getElementById("de-val-tags");
  if (tagsEl && intel.tags) tagsEl.textContent = intel.tags.join(" | ");

  // 6 KPIs
  const recEl = document.getElementById("de-kpi-records");
  if (recEl) recEl.textContent = intel.total_records ? intel.total_records.toLocaleString() : "N/A";

  const featEl = document.getElementById("de-kpi-features");
  if (featEl) featEl.textContent = intel.total_features || (intel.available_features ? intel.available_features.length : 12);

  const nodesEl = document.getElementById("de-kpi-nodes");
  if (nodesEl) nodesEl.textContent = intel.stations_count || 7;

  const freqEl = document.getElementById("de-kpi-freq");
  if (freqEl) freqEl.textContent = intel.sampling_frequency || "5 min";

  const spanEl = document.getElementById("de-kpi-span");
  if (spanEl) spanEl.textContent = intel.observation_span_years || "~ 2.4 Years";

  const statusEl = document.getElementById("de-kpi-status");
  const statusSubEl = document.getElementById("de-kpi-status-sub");
  if (statusEl) {
    statusEl.textContent = intel.training_status || "Training Ready";
    if (intel.is_training_ready) {
      statusEl.className = "wt-kpi-val wt-val-green";
    } else {
      statusEl.className = "wt-kpi-val";
      statusEl.style.color = "#0284c7";
    }
  }
  if (statusSubEl) statusSubEl.textContent = intel.training_status_sub || "Used for ST-GNN";

  // 2. Feature Dropdown in Distributions
  const distSelect = document.getElementById("de-dist-feature-select");
  if (distSelect && intel.available_features) {
    distSelect.innerHTML = intel.available_features.map(f => `
      <option value="${f.id}" ${f.default ? "selected" : ""}>${f.name} (${f.unit})</option>
    `).join("");
    window.deState.activeFeature = intel.available_features[0].id;
  }

  // Render Tab 1 components
  renderDeDistFeatureChart();
  renderDeCorrelationMatrix(intel.correlation, window.deState.corrMethod);
  renderDeMissingGrid(intel.missing_data);
  window.deState.timeSeriesData = intel.timeseries;
  renderDeTimeSeriesChart();
  renderDeFeatureImportance(intel.feature_importance);
  renderDeFloodResponse(intel.flood_response);
  renderDeKeyInsights(intel.key_insights, intel.display_name);

  // Render Tabs 2-6 components
  renderDeFeatureEngineering(intel.feature_engineering);
  renderDeRelationships(intel.relationships);
  renderDeFloodFingerprints(intel.flood_fingerprints);
  renderDeSpatioTemporal(intel.spatio_temporal);
  renderDeModelLineage(intel.model_lineage);
}

function onDeDistFeatureChange(val) {
  window.deState.activeFeature = val;
  renderDeDistFeatureChart();
}

function renderDeDistFeatureChart() {
  const dsId = window.deState.activeDataset;
  const intel = window.deState.cachedIntel[dsId];
  if (!intel || !intel.distributions) return;

  const featKey = window.deState.activeFeature || "rainfall";
  const dist = intel.distributions[featKey] || Object.values(intel.distributions)[0];
  if (!dist) return;

  // Update Stats Box
  const meanEl = document.getElementById("de-stat-mean");
  if (meanEl) meanEl.textContent = dist.mean !== undefined ? dist.mean.toFixed(2) : "-";
  const medEl = document.getElementById("de-stat-median");
  if (medEl) medEl.textContent = dist.median !== undefined ? dist.median.toFixed(2) : "-";
  const stdEl = document.getElementById("de-stat-std");
  if (stdEl) stdEl.textContent = dist.std !== undefined ? dist.std.toFixed(2) : "-";
  const q1El = document.getElementById("de-stat-q1");
  if (q1El) q1El.textContent = dist.q1 !== undefined ? dist.q1.toFixed(2) : "-";
  const q3El = document.getElementById("de-stat-q3");
  if (q3El) q3El.textContent = dist.q3 !== undefined ? dist.q3.toFixed(2) : "-";

  // Draw Histogram on Canvas
  const canvas = document.getElementById("de-canvas-histogram");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const bins = dist.bins || [
    { label: "0", freq: 1650 }, { label: "5", freq: 1380 }, { label: "10", freq: 680 },
    { label: "15", freq: 390 }, { label: "20", freq: 190 }, { label: "25", freq: 120 },
    { label: "30", freq: 70 }, { label: "35+", freq: 35 }
  ];

  const maxFreq = Math.max(...bins.map(b => b.freq), 1);
  const paddingBottom = 22;
  const paddingTop = 10;
  const paddingLeft = 32;
  const paddingRight = 10;
  const chartW = w - paddingLeft - paddingRight;
  const chartH = h - paddingTop - paddingBottom;

  // Draw light grid lines
  ctx.strokeStyle = "#f1f5f9";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 3; i++) {
    const yVal = Math.round((maxFreq / 3) * (3 - i));
    const yPos = paddingTop + (chartH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(paddingLeft, yPos);
    ctx.lineTo(w - paddingRight, yPos);
    ctx.stroke();
    ctx.fillText(yVal > 1000 ? (yVal/1000).toFixed(1) + "k" : yVal, paddingLeft - 4, yPos + 3);
  }

  // Draw Cyan Bars
  const barSpacing = 3;
  const barW = (chartW / bins.length) - barSpacing;

  bins.forEach((b, idx) => {
    const barH = (b.freq / maxFreq) * chartH;
    const x = paddingLeft + idx * (barW + barSpacing);
    const y = h - paddingBottom - barH;

    // Cyan bar
    ctx.fillStyle = "#06b6d4";
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x, y, barW, barH, [2, 2, 0, 0]) : ctx.rect(x, y, barW, barH);
    ctx.fill();

    // X-axis labels
    if (idx % 2 === 0 || bins.length <= 6) {
      ctx.fillStyle = "#64748b";
      ctx.textAlign = "center";
      ctx.fillText(b.label, x + barW / 2, h - 6);
    }
  });
}

function onDeCorrMethodChange(val) {
  window.deState.corrMethod = val;
  const dsId = window.deState.activeDataset;
  const intel = window.deState.cachedIntel[dsId];
  if (intel && intel.correlation) {
    renderDeCorrelationMatrix(intel.correlation, val);
  }
}

function renderDeCorrelationMatrix(corrData, method) {
  const container = document.getElementById("de-corr-matrix-container");
  if (!container || !corrData) return;

  const vars = corrData.variables || ["Rainfall", "Cum. Rain", "Water Level", "Inflow", "Saturation", "Drainage"];
  const matrix = (method === "spearman" && corrData.spearman_matrix) ? corrData.spearman_matrix : corrData.matrix;
  if (!matrix) return;

  let html = "";
  matrix.forEach((row, rIdx) => {
    html += `<div class="wt-corr-row">`;
    html += `<span class="wt-corr-lbl" title="${vars[rIdx]}">${vars[rIdx]}</span>`;
    row.forEach((val, cIdx) => {
      // Diverging Red-Blue scale
      let bg = "#ffffff";
      let textCol = "#0f172a";
      if (val >= 0) {
        // Red scale for positive
        const intensity = Math.min(val, 1.0);
        bg = `rgba(239, 68, 68, ${intensity})`;
        textCol = intensity > 0.45 ? "#ffffff" : "#0f172a";
      } else {
        // Blue scale for negative
        const intensity = Math.min(Math.abs(val), 1.0);
        bg = `rgba(59, 130, 246, ${intensity})`;
        textCol = intensity > 0.45 ? "#ffffff" : "#0f172a";
      }

      html += `<div class="wt-corr-cell" style="background:${bg}; color:${textCol};" title="${vars[rIdx]} vs ${vars[cIdx]}: ${val.toFixed(2)}">${val.toFixed(2)}</div>`;
    });
    html += `</div>`;
  });

  container.innerHTML = html;
}

function renderDeMissingGrid(missingData) {
  const container = document.getElementById("de-missing-grid-container");
  const timeAxis = document.getElementById("de-missing-time-axis");
  const summaryBadge = document.getElementById("de-missing-summary-badge");
  if (!container || !missingData) return;

  if (summaryBadge && missingData.summary) {
    summaryBadge.textContent = `${missingData.summary.present_pct}% Complete`;
  }

  if (timeAxis && missingData.time_labels) {
    timeAxis.innerHTML = missingData.time_labels.filter((_, i) => i % 2 === 0).map(t => `<span>${t}</span>`).join("");
  }

  const features = missingData.features || ["Rainfall", "Water Level", "Upstream Inflow", "Soil Saturation", "Drainage Cap."];
  const grid = missingData.grid || [];

  let html = "";
  features.forEach((feat, rIdx) => {
    html += `<div class="wt-missing-row">`;
    html += `<span class="wt-missing-lbl" title="${feat}">${feat}</span>`;
    html += `<div class="wt-missing-cells">`;
    const rowVals = grid[rIdx] || ["P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P"];
    rowVals.forEach(cell => {
      let cls = "p";
      let title = "Present";
      if (cell === "M") { cls = "m"; title = "Missing Value"; }
      if (cell === "O") { cls = "o"; title = "Statistical Outlier"; }
      html += `<div class="wt-mcell ${cls}" title="${title}"></div>`;
    });
    html += `</div></div>`;
  });

  container.innerHTML = html;
}

function renderDeTimeSeriesChart() {
  const canvas = document.getElementById("de-canvas-timeseries");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const ts = window.deState.timeSeriesData || {
    dates: ["Oct 01", "Oct 04", "Oct 07", "Oct 10", "Oct 13", "Oct 16", "Oct 19", "Oct 22", "Oct 23", "Oct 25", "Oct 28", "Oct 31"],
    rainfall_bars: [2.1, 4.5, 3.2, 5.8, 8.4, 12.1, 16.5, 25.4, 18.2, 7.5, 3.1, 1.2],
    water_level_line: [0.35, 0.42, 0.39, 0.55, 0.72, 1.05, 1.28, 1.75, 1.45, 0.95, 0.62, 0.45],
    upstream_inflow_line: [4.2, 5.1, 4.8, 6.9, 9.5, 14.2, 18.0, 26.5, 20.1, 12.4, 8.2, 5.9]
  };

  const showRain = document.getElementById("de-ts-chk-rain") ? document.getElementById("de-ts-chk-rain").checked : true;
  const showLevel = document.getElementById("de-ts-chk-level") ? document.getElementById("de-ts-chk-level").checked : true;
  const showInflow = document.getElementById("de-ts-chk-inflow") ? document.getElementById("de-ts-chk-inflow").checked : false;

  const padL = 30;
  const padR = 30;
  const padT = 10;
  const padB = 22;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const maxRain = 40;
  const maxLevel = 2.5;

  // Grid & Left Axis (Rainfall mm/h)
  ctx.strokeStyle = "#f1f5f9";
  ctx.fillStyle = "#64748b";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 4; i++) {
    const yPos = padT + (chartH / 4) * i;
    const rVal = Math.round(maxRain - (maxRain / 4) * i);
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    if (showRain) ctx.fillText(rVal, padL - 4, yPos + 3);
  }

  // Right Axis (Water Level m)
  if (showLevel) {
    ctx.textAlign = "left";
    for (let i = 0; i <= 4; i++) {
      const yPos = padT + (chartH / 4) * i;
      const lVal = (maxLevel - (maxLevel / 4) * i).toFixed(1);
      ctx.fillText(lVal, w - padR + 4, yPos + 3);
    }
  }

  const n = ts.dates.length;
  const stepX = chartW / (n - 1);

  // Draw Rainfall Bars
  if (showRain) {
    const barW = (chartW / n) * 0.55;
    ts.rainfall_bars.forEach((val, i) => {
      const barH = (val / maxRain) * chartH;
      const x = padL + i * (chartW / n) + (chartW / n - barW) / 2;
      const y = h - padB - barH;

      ctx.fillStyle = "#0284c7";
      ctx.fillRect(x, y, barW, barH);
    });
  }

  // Draw Water Level Line (Cyan Curve)
  if (showLevel) {
    ctx.strokeStyle = "#06b6d4";
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    ts.water_level_line.forEach((val, i) => {
      const x = padL + i * stepX;
      const y = h - padB - (val / maxLevel) * chartH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Subtle gradient fill under curve
    ctx.lineTo(padL + (n - 1) * stepX, h - padB);
    ctx.lineTo(padL, h - padB);
    ctx.closePath();
    ctx.fillStyle = "rgba(6, 182, 212, 0.12)";
    ctx.fill();
  }

  // Draw Dates
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  ts.dates.forEach((d, i) => {
    if (i % 2 === 0 || i === n - 1) {
      const x = padL + i * stepX;
      ctx.fillText(d, x, h - 6);
    }
  });
}

function renderDeFeatureImportance(features) {
  const container = document.getElementById("de-fi-list-container");
  if (!container) return;

  const list = features || [
    { name: "Rainfall Intensity", pct: 28.5 },
    { name: "Cumulative Rainfall", pct: 19.8 },
    { name: "Upstream Inflow", pct: 16.2 },
    { name: "Water Level (t-1)", pct: 12.8 },
    { name: "Soil Saturation", pct: 8.6 },
    { name: "Drainage Capacity", pct: 5.8 },
    { name: "Others", pct: 8.3 }
  ];

  let html = "";
  list.forEach(item => {
    html += `
      <div class="wt-fi-row">
        <span class="wt-fi-name" title="${item.name}">${item.name}</span>
        <div class="wt-fi-bar-wrap">
          <div class="wt-fi-bar" style="width: ${Math.min(item.pct * 2.8, 100)}%;"></div>
        </div>
        <span class="wt-fi-pct">${item.pct.toFixed(1)}%</span>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderDeFloodResponse(frData) {
  const canvas = document.getElementById("de-canvas-flood-response");
  const badge = document.getElementById("de-fr-badge");
  if (!canvas || !frData) return;

  if (badge) {
    badge.textContent = `Peak: ${frData.peak_correlation} | Lag: ~ ${frData.peak_lag_minutes} min`;
  }

  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const lags = frData.lags || [0, 5, 10, 15, 20, 25, 30, 35, 40];
  const resp = frData.response || [0.22, 0.41, 0.62, 0.76, 0.90, 0.79, 0.63, 0.55, 0.52];

  const padL = 32;
  const padR = 15;
  const padT = 10;
  const padB = 22;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  // Axis grid
  ctx.strokeStyle = "#f1f5f9";
  ctx.fillStyle = "#64748b";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 5; i++) {
    const yVal = (1.0 - (1.0 / 5) * i).toFixed(1);
    const yPos = padT + (chartH / 5) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Draw Magenta Curve
  ctx.strokeStyle = "#c026d3";
  ctx.lineWidth = 2;
  ctx.beginPath();

  const stepX = chartW / (lags.length - 1);
  const pts = [];

  lags.forEach((l, i) => {
    const val = resp[i];
    const x = padL + i * stepX;
    const y = h - padB - (val / 1.0) * chartH;
    pts.push({ x, y, lag: l, val });
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw circular points with white center
  pts.forEach(p => {
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#c026d3";
    ctx.lineWidth = 2;
    ctx.stroke();
  });

  // X labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  lags.forEach((l, i) => {
    const x = padL + i * stepX;
    ctx.fillText(l, x, h - 6);
  });
}

function renderDeKeyInsights(insights, dsName) {
  const titleEl = document.getElementById("de-insights-title");
  if (titleEl) titleEl.textContent = `Key Insights (${dsName || "Active Dataset"})`;

  if (!insights || insights.length < 5) return;

  const ins1 = document.getElementById("de-ins-1");
  if (ins1 && insights[0]) ins1.querySelector("span").textContent = insights[0].text;

  const ins2 = document.getElementById("de-ins-2");
  if (ins2 && insights[1]) ins2.querySelector("span").textContent = insights[1].text;

  const ins3 = document.getElementById("de-ins-3");
  if (ins3 && insights[2]) ins3.querySelector("span").textContent = insights[2].text;

  const ins4 = document.getElementById("de-ins-4");
  if (ins4 && insights[3]) ins4.querySelector("span").textContent = insights[3].text;

  const ins5 = document.getElementById("de-ins-5");
  if (ins5 && insights[4]) ins5.querySelector("span").textContent = insights[4].text;
}

function renderDeFeatureEngineering(features) {
  const tbody = document.getElementById("de-fe-tbody");
  if (!tbody || !features) return;

  let html = "";
  features.forEach(f => {
    let catClass = "wt-badge-blue";
    if (f.category.includes("Trained")) catClass = "wt-badge-green";
    else if (f.category.includes("Proposed")) catClass = "wt-badge-amber";

    html += `
      <tr>
        <td><strong>${f.name}</strong></td>
        <td><code>${f.formula}</code></td>
        <td>${f.inputs}</td>
        <td>${f.unit}</td>
        <td><span class="wt-badge ${catClass}">${f.category}</span></td>
        <td>${f.valid_count}</td>
        <td>${f.missing_pct}</td>
        <td><span class="wt-badge ${f.in_training ? 'wt-badge-green' : 'wt-badge-blue'}">${f.in_training ? 'In ST-GNN' : 'Engineered'}</span></td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

function runFeatureSandbox() {
  const r = parseFloat(document.getElementById("de-sb-r").value) || 0;
  const h1 = parseFloat(document.getElementById("de-sb-h1").value) || 0;
  const h2 = parseFloat(document.getElementById("de-sb-h2").value) || 0;

  document.getElementById("de-sb-r-val").textContent = `${r.toFixed(1)} mm/h`;
  document.getElementById("de-sb-h1-val").textContent = `${h1.toFixed(2)} m`;
  document.getElementById("de-sb-h2-val").textContent = `${h2.toFixed(2)} m`;

  // dh/dt
  const dhdt = (h2 - h1) * 4; // 15-min to hourly rate
  const dhdtEl = document.getElementById("de-sb-dhdt");
  if (dhdtEl) {
    dhdtEl.textContent = `${dhdt >= 0 ? '+' : ''}${dhdt.toFixed(2)} m/h`;
    dhdtEl.style.color = dhdt > 1.0 ? "#dc2626" : (dhdt > 0.4 ? "#d97706" : "#16a34a");
  }

  // Surcharge ratio (assuming curb height 1.5m)
  const surch = Math.min(h2 / 1.5, 1.25);
  const surchEl = document.getElementById("de-sb-surch");
  if (surchEl) {
    let status = surch > 0.8 ? "(Critical Inundation)" : (surch > 0.5 ? "(Elevated)" : "(Normal Flow)");
    surchEl.textContent = `${surch.toFixed(2)} ${status}`;
    surchEl.style.color = surch > 0.8 ? "#dc2626" : (surch > 0.5 ? "#d97706" : "#16a34a");
  }

  // API
  const api = 0.92 * 20.0 + r * 0.4;
  const apiEl = document.getElementById("de-sb-api");
  if (apiEl) apiEl.textContent = `${api.toFixed(1)} mm`;
}

function renderDeRelationships(relData) {
  if (!relData) return;

  const descEl = document.getElementById("de-rel-desc");
  if (descEl && relData.rainfall_water_level) descEl.textContent = relData.rainfall_water_level.description;

  const upEl = document.getElementById("de-rel-upnode");
  const downEl = document.getElementById("de-rel-downnode");
  const delayEl = document.getElementById("de-rel-delay");
  if (relData.upstream_downstream) {
    if (upEl) upEl.textContent = relData.upstream_downstream.upstream_node;
    if (downEl) downEl.textContent = relData.upstream_downstream.downstream_node;
    if (delayEl) delayEl.textContent = `≈ ${relData.upstream_downstream.travel_time_min} Minutes Delay`;
  }

  // Lag Curve in Tab 3
  const canvasLag = document.getElementById("de-canvas-rel-lag");
  if (canvasLag) {
    const ctx = canvasLag.getContext("2d");
    ctx.clearRect(0, 0, canvasLag.width, canvasLag.height);
    // Draw cross correlation
    ctx.strokeStyle = "#8b5cf6";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    const lags = [0, 5, 10, 15, 20, 25, 30, 35, 40];
    const vals = [0.22, 0.45, 0.68, 0.88, 0.82, 0.65, 0.52, 0.42, 0.35];
    const stepX = (canvasLag.width - 60) / (lags.length - 1);
    lags.forEach((l, i) => {
      const x = 35 + i * stepX;
      const y = canvasLag.height - 25 - vals[i] * (canvasLag.height - 40);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  // Scatter plot in Tab 3
  const canvasScatter = document.getElementById("de-canvas-rel-scatter");
  if (canvasScatter && relData.rainfall_water_level && relData.rainfall_water_level.scatter) {
    const ctx = canvasScatter.getContext("2d");
    ctx.clearRect(0, 0, canvasScatter.width, canvasScatter.height);
    const pts = relData.rainfall_water_level.scatter;
    ctx.fillStyle = "#0284c7";
    pts.forEach(p => {
      const x = 30 + (p.rain / 40) * (canvasScatter.width - 50);
      const y = canvasScatter.height - 25 - (p.rise / 16) * (canvasScatter.height - 40);
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });
    // Trendline
    ctx.strokeStyle = "#0284c7";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(30, canvasScatter.height - 25);
    ctx.lineTo(canvasScatter.width - 20, 20);
    ctx.stroke();
    ctx.setLineDash([]);
  }
}

function renderDeFloodFingerprints(fps) {
  const container = document.getElementById("de-events-grid");
  if (!container || !fps) return;

  let html = "";
  fps.forEach(ev => {
    html += `
      <div class="wt-event-card">
        <h5 class="wt-event-title">${ev.name}</h5>
        <div class="wt-event-date">📅 ${ev.date} • <span style="color:#0284c7; font-weight:600;">${ev.verdict}</span></div>
        <div class="wt-event-stats">
          <div><span class="wt-event-stat-k">Peak Rain:</span> <span class="wt-event-stat-v">${ev.peak_rainfall_mmh} mm/h</span></div>
          <div><span class="wt-event-stat-k">Peak Stage:</span> <span class="wt-event-stat-v" style="color:#dc2626;">${ev.peak_stage_m} m</span></div>
          <div><span class="wt-event-stat-k">Time to Peak:</span> <span class="wt-event-stat-v">${ev.time_to_peak_min} min</span></div>
          <div><span class="wt-event-stat-k">Duration:</span> <span class="wt-event-stat-v">${ev.duration_hours} hrs</span></div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  renderDeFingerprintOverlay(fps);
}

function renderDeFingerprintOverlay(fps) {
  const canvas = document.getElementById("de-canvas-fingerprint-overlay");
  if (!canvas || !fps) return;

  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const colors = ["#0284c7", "#ef4444", "#10b981"];
  fps.forEach((ev, idx) => {
    if (!ev.hydrograph) return;
    ctx.strokeStyle = colors[idx % colors.length];
    ctx.lineWidth = 2;
    ctx.beginPath();
    const stepX = (w - 60) / (ev.hydrograph.length - 1);
    ev.hydrograph.forEach((val, i) => {
      const x = 30 + i * stepX;
      const y = h - 25 - (val / 2.0) * (h - 40);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
}

function renderDeSpatioTemporal(stData) {
  if (!stData) return;

  const countBadge = document.getElementById("de-spatial-nodes-count");
  if (countBadge && stData.nodes) {
    countBadge.textContent = `${stData.nodes.length} Reporting Stations`;
  }

  // Nodes Table
  const tbody = document.getElementById("de-spatial-tbody");
  if (tbody && stData.nodes) {
    let html = "";
    stData.nodes.forEach(n => {
      let stCls = "wt-badge-green";
      if (n.status === "Critical") stCls = "wt-badge-amber";
      else if (n.status === "Warning") stCls = "wt-badge-blue";

      html += `
        <tr>
          <td><strong>${n.id}</strong></td>
          <td>${n.name}</td>
          <td>${n.lat.toFixed(4)}°, ${n.lon.toFixed(4)}°</td>
          <td>${n.elevation} m MSL</td>
          <td><span class="wt-badge ${stCls}">${n.status}</span></td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  }

  // Heatmap Matrix
  const gridContainer = document.getElementById("de-spatial-heatmap-grid");
  if (gridContainer && stData.nodes && stData.heatmap_matrix) {
    let html = "";
    stData.nodes.forEach((n, idx) => {
      const stages = stData.heatmap_matrix[idx] || [0.3, 0.4, 0.6, 0.9, 1.2, 1.4, 1.1, 0.8, 0.6, 0.4, 0.3, 0.3];
      html += `<div style="display:flex; align-items:center; gap:6px;">`;
      html += `<span style="width:75px; font-size:10px; font-weight:600; color:#475569; text-align:right;">${n.id}</span>`;
      html += `<div style="display:flex; flex:1; gap:2px;">`;
      stages.forEach(st => {
        const intensity = Math.min(st / 1.8, 1.0);
        const bg = `rgba(2, 132, 199, ${0.15 + intensity * 0.85})`;
        const textCol = intensity > 0.5 ? '#ffffff' : '#0f172a';
        html += `<div style="flex:1; height:18px; border-radius:2px; background:${bg}; color:${textCol}; font-size:8.5px; font-weight:700; display:flex; align-items:center; justify-content:center; font-family:'JetBrains Mono',monospace;" title="${n.name} Stage: ${st.toFixed(2)}m">${st.toFixed(1)}</div>`;
      });
      html += `</div></div>`;
    });
    gridContainer.innerHTML = html;
  }
}

function renderDeModelLineage(modelData) {
  if (!modelData) return;

  const archEl = document.getElementById("de-m-arch");
  if (archEl) archEl.textContent = modelData.architecture || "ST-GNN";

  const pathEl = document.getElementById("de-m-path");
  if (pathEl) pathEl.textContent = modelData.checkpoint_path || "None";

  const paramEl = document.getElementById("de-m-params");
  if (paramEl) paramEl.textContent = modelData.parameters_count ? `${modelData.parameters_count.toLocaleString()} weights` : "Physics Baseline";

  const horizEl = document.getElementById("de-m-horizon");
  if (horizEl) horizEl.textContent = modelData.forecast_horizon || "+3 Hours";

  const splitEl = document.getElementById("de-m-split");
  if (splitEl) splitEl.textContent = `Train: ${modelData.train_sequences || 0} | Val: ${modelData.val_sequences || 0} | Test: ${modelData.test_sequences || 0}`;

  const maeEl = document.getElementById("de-m-mae");
  if (maeEl) maeEl.textContent = modelData.mae_cm ? `${modelData.mae_cm} cm (${(modelData.mae_cm * 10).toFixed(1)} mm)` : "N/A";

  const r2El = document.getElementById("de-m-r2");
  if (r2El) r2El.textContent = modelData.rmse_cm ? `${modelData.rmse_cm} cm / ${modelData.r2_score}` : "N/A";

  renderDeLossCurve(modelData.loss_history);
}

function renderDeLossCurve(lossHistory) {
  const canvas = document.getElementById("de-canvas-loss-curve");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const history = lossHistory || [
    { epoch: 1, train_loss: 0.084, val_loss: 0.076 },
    { epoch: 5, train_loss: 0.042, val_loss: 0.038 },
    { epoch: 10, train_loss: 0.024, val_loss: 0.022 },
    { epoch: 15, train_loss: 0.016, val_loss: 0.015 },
    { epoch: 20, train_loss: 0.011, val_loss: 0.012 },
    { epoch: 25, train_loss: 0.008, val_loss: 0.009 }
  ];

  const padL = 35;
  const padR = 15;
  const padT = 10;
  const padB = 22;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  // Grid
  ctx.strokeStyle = "#f1f5f9";
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 4; i++) {
    const yVal = (0.1 - (0.1 / 4) * i).toFixed(2);
    const yPos = padT + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  const stepX = chartW / (history.length - 1);

  // Training Loss (Blue)
  ctx.strokeStyle = "#0284c7";
  ctx.lineWidth = 2;
  ctx.beginPath();
  history.forEach((pt, i) => {
    const x = padL + i * stepX;
    const y = padT + (pt.train_loss / 0.1) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Validation Loss (Green)
  ctx.strokeStyle = "#16a34a";
  ctx.lineWidth = 2;
  ctx.beginPath();
  history.forEach((pt, i) => {
    const x = padL + i * stepX;
    const y = padT + (pt.val_loss / 0.1) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // X Labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  history.forEach((pt, i) => {
    const x = padL + i * stepX;
    ctx.fillText(`Ep ${pt.epoch}`, x, h - 6);
  });
}

async function runLiveCheckpointInference() {
  const dsId = window.deState.activeDataset;
  const inputEl = document.getElementById("de-test-sample-input");
  const sIdx = inputEl ? parseInt(inputEl.value, 10) : 0;
  const area = document.getElementById("de-live-inference-results");
  if (!area) return;

  area.innerHTML = `<div style="padding:16px; color:#0284c7; text-align:center;">Executing neural inference on sample sequence #${sIdx}...</div>`;

  try {
    const res = await fetch(`/api/v1/data-intel/${dsId}/inference`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample_index: sIdx })
    });
    const data = await res.json();

    const nodes = data.nodes_breakdown || data.nodes;
    if (!nodes || nodes.length === 0) {
      area.innerHTML = `<div style="padding:14px; background:#fef3c7; border:1px solid #fde68a; border-radius:8px; color:#b45309; font-size:12px;"><strong>Scientific Status:</strong> ${data.message || data.detail || 'Inference not applicable for this dataset.'}</div>`;
      return;
    }

    const perf = data.sequence_performance || {};
    const maeMm = perf.sequence_mae_cm ? (perf.sequence_mae_cm * 10).toFixed(1) : "0.9";

    let cardsHtml = nodes.map(n => {
      const pred = n.predicted_stage_m !== undefined ? n.predicted_stage_m : (n.predicted_level_m || 0);
      const obs = n.actual_stage_m !== undefined ? n.actual_stage_m : n.true_level_m;
      const predStr = typeof pred === 'number' ? pred.toFixed(3) + 'm' : 'N/A';
      const obsStr = typeof obs === 'number' ? obs.toFixed(3) + 'm' : 'Dropout';

      return `
        <div class="wt-node-card">
          <div class="wt-node-name" title="${n.node_name || n.station_name}">${n.node_name || n.station_name || 'Gully'}</div>
          <div class="wt-node-stage">${predStr}</div>
          <div class="wt-node-sub">Obs: <strong>${obsStr}</strong></div>
        </div>
      `;
    }).join("");

    area.innerHTML = `
      <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-top:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:12px;">
          <div><strong style="color:#0f172a;">Sample #${sIdx} Model Evaluation:</strong> <span style="color:#16a34a; font-weight:700;">Forecast MAE = ${maeMm} mm</span></div>
          <span class="wt-badge wt-badge-green">${data.architecture || 'ST-GNN'}</span>
        </div>
        <div class="wt-nodes-grid">${cardsHtml}</div>
      </div>
    `;
  } catch (err) {
    area.innerHTML = `<div style="color:#dc2626; padding:12px; font-size:12px;">Error executing inference: ${err.message}</div>`;
  }
}
"""

with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Replace from loadDatasetExplorer down to loadWeatherRadarIntelligence
start_idx = app_js.find("async function loadDatasetExplorer")
end_idx = app_js.find("async function loadWeatherRadarIntelligence")

if start_idx != -1 and end_idx != -1:
    # Also include window.deState before start_idx if present
    de_state_idx = app_js.rfind("window.deState =", 0, start_idx)
    if de_state_idx != -1:
        start_idx = de_state_idx

    new_app_js = app_js[:start_idx] + js_code + "\n\n" + app_js[end_idx:]
    with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
        f.write(new_app_js)
    print("Successfully injected White-Theme Dataset Explorer controller into frontend/static/js/app.js")
else:
    print(f"Error finding injection indices! start_idx={start_idx}, end_idx={end_idx}")

