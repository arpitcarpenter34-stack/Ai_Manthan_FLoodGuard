with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    content = f.read()

old_format_block = """    let nodeCards = nodes.map(n => {
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
    }).join('');"""

new_format_block = """    let nodeCards = nodes.map(n => {
      const pred = n.predicted_stage_m !== undefined ? n.predicted_stage_m : (n.predicted_level_m || 0);
      const actual = n.actual_stage_m !== undefined ? n.actual_stage_m : n.true_level_m;
      const errCm = n.st_gnn_error_cm !== undefined ? n.st_gnn_error_cm : (n.absolute_error_mm !== undefined ? n.absolute_error_mm / 10 : null);

      const predStr = typeof pred === 'number' ? pred.toFixed(3) + ' m' : 'N/A';
      const actualStr = typeof actual === 'number' ? actual.toFixed(3) + ' m' : 'N/A (Dropout)';
      const errStr = typeof errCm === 'number' ? (errCm * 10).toFixed(1) + ' mm' : '-';

      let riskColor = (typeof errCm === 'number' && errCm > 1.0) ? "#f59e0b" : "#10b981";
      if (n.status === 'SENSOR_DROPOUT') riskColor = "#64748b";

      return `
        <div class="de-inf-node-card">
          <div class="de-inf-node-head">
            <span>${n.node_name || n.station_name || `Node ${n.node_idx}`}</span>
            <span style="color:${riskColor}; font-weight:800; font-size:10px;">${n.status || 'OK'}</span>
          </div>
          <div class="de-inf-node-stage" style="color:${riskColor};">${predStr}</div>
          <div class="de-inf-node-metrics">
            <span>Obs: <b>${actualStr}</b></span>
            <span>Err: <b>${errStr}</b></span>
          </div>
        </div>
      `;
    }).join('');"""

content = content.replace(old_format_block, new_format_block)

with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Protected number formatting in app.js successfully.")

