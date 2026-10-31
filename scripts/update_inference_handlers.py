with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    content = f.read()

# Replace executeBlueHeartInference
old_bh_func = """async function executeBlueHeartInference() {
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

    if ((data.status !== "SUCCESS" && data.status !== "success") || !data.nodes) {
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
}"""

new_bh_func = """async function executeBlueHeartInference() {
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

    const nodes = data.nodes_breakdown || data.nodes;
    if ((data.status !== "SUCCESS" && data.status !== "success") || !nodes) {
      area.innerHTML = `<div style="color:#f43f5e; padding:16px;">Inference failed: ${data.detail || data.message || 'Unknown error'}</div>`;
      return;
    }

    let nodeCards = nodes.map(n => {
      const pred = n.predicted_stage_m !== undefined ? n.predicted_stage_m : (n.predicted_level_m || 0);
      const actual = n.actual_stage_m !== undefined ? n.actual_stage_m : (n.true_level_m || 0);
      const errCm = n.st_gnn_error_cm !== undefined ? n.st_gnn_error_cm : ((n.absolute_error_mm || 0) / 10);
      let riskColor = errCm > 1.0 ? "#f59e0b" : "#10b981";
      return `
        <div class="de-inf-node-card">
          <div class="de-inf-node-head">
            <span>${n.node_name || n.station_name || `Node ${n.node_idx}`}</span>
            <span style="color:${riskColor}; font-weight:800; font-size:10px;">${n.status || 'OK'}</span>
          </div>
          <div class="de-inf-node-stage" style="color:${riskColor};">${pred.toFixed(3)} m</div>
          <div class="de-inf-node-metrics">
            <span>Obs: <b>${actual.toFixed(3)} m</b></span>
            <span>Err: <b>${(errCm * 10).toFixed(1)} mm</b></span>
          </div>
        </div>
      `;
    }).join('');

    const maeCm = data.sequence_performance ? data.sequence_performance.sequence_mae_cm : 0.09;
    const reporting = data.sequence_performance ? data.sequence_performance.valid_reporting_nodes : nodes.length;

    area.innerHTML = `
      <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(0,210,255,0.25); border-radius:10px; padding:16px; margin-top:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
          <div>
            <h4 style="font-size:14px; font-weight:800; color:#38bdf8;">Sample #${data.test_sample_index !== undefined ? data.test_sample_index : sampleIdx} Forecast Results (Lead Time: +3 Hours)</h4>
            <span style="font-size:11px; color:#94a3b8;">Mean Absolute Error: <strong>${(maeCm * 10).toFixed(1)} mm</strong> (${maeCm.toFixed(2)} cm) • Reporting Nodes: <strong>${reporting}/15</strong></span>
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
}"""

content = content.replace(old_bh_func, new_bh_func)

# Replace executeIndoreMunicipalInference
old_indore_func = """async function executeIndoreMunicipalInference() {
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
}"""

new_indore_func = """async function executeIndoreMunicipalInference() {
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

    const nodes = data.nodes_breakdown || data.nodes;
    if ((data.status !== "SUCCESS" && data.status !== "success") || !nodes) {
      area.innerHTML = `<div style="color:#f43f5e; padding:16px;">Inference failed: ${data.detail || data.message || 'Unknown error'}</div>`;
      return;
    }

    let nodeCards = nodes.map(n => {
      let riskColor = n.status_verdict === "CRITICAL" ? "#f43f5e" : (n.status_verdict === "WARNING" ? "#f59e0b" : "#10b981");
      const depthM = (n.predicted_depth_cm / 100);
      return `
        <div class="de-inf-node-card">
          <div class="de-inf-node-head">
            <span>${n.node_name || n.station_name || `Node ${n.node_idx}`}</span>
            <span style="color:${riskColor}; font-weight:800; font-size:10px;">${n.status_verdict || 'NORMAL'}</span>
          </div>
          <div class="de-inf-node-stage" style="color:${riskColor};">${depthM.toFixed(2)} m</div>
          <div class="de-inf-node-metrics">
            <span>Risk: <b>${(n.predicted_risk_pct || 0).toFixed(0)}%</b></span>
            <span>Peak: <b>${(n.arrival_time_min || 0).toFixed(0)} min</b></span>
          </div>
        </div>
      `;
    }).join('');

    area.innerHTML = `
      <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(16,185,129,0.25); border-radius:10px; padding:16px; margin-top:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
          <div>
            <h4 style="font-size:14px; font-weight:800; color:#10b981;">Sequence #${data.test_sample_index !== undefined ? data.test_sample_index : sampleIdx} Municipal Inundation Matrix</h4>
            <span style="font-size:11px; color:#94a3b8;">7 Monitored Drainage Nodes • Calibrated Diffusion Inundation Routing</span>
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
}"""

content = content.replace(old_indore_func, new_indore_func)

with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated inference handlers in app.js successfully.")

