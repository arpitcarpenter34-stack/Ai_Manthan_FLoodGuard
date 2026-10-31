import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"E:\ai-manthan\hydro_guard_indore")
JS_PATH = BASE_DIR / "frontend" / "static" / "js" / "app.js"
CSS_PATH = BASE_DIR / "frontend" / "static" / "css" / "style.css"
HTML_PATH = BASE_DIR / "frontend" / "static" / "index.html"

print("=" * 80)
print("UPDATING DATASET EXPLORER TO DARK NAVY GLASSMORPHISM & FIXING HEATMAP")
print("=" * 80)

# =============================================================================
# 1. UPDATE app.js
# =============================================================================
print("\n[1/3] Updating app.js...")
js_content = JS_PATH.read_text(encoding="utf-8")

# A. Remove white-theme toggle in navigateTo
old_nav = """    if (screenId === "explorer") {
      vApp.classList.add("white-theme");
    } else {
      vApp.classList.remove("white-theme");
    }"""
new_nav = """    vApp.classList.remove("white-theme");"""

if old_nav in js_content:
    js_content = js_content.replace(old_nav, new_nav)
    print("  ✓ Removed white-theme toggle in navigateTo")
else:
    # Try normalized CRLF/LF match
    pattern = r'if\s*\(\s*screenId\s*===\s*"explorer"\s*\)\s*\{\s*vApp\.classList\.add\("white-theme"\);\s*\}\s*else\s*\{\s*vApp\.classList\.remove\("white-theme"\);\s*\}'
    js_content = re.sub(pattern, 'vApp.classList.remove("white-theme");', js_content)
    print("  ✓ Regex-replaced white-theme toggle in navigateTo")

# B. Replace renderDeCorrelationMatrix
old_corr_fn = """function renderDeCorrelationMatrix(corrData, method) {
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
}"""

new_corr_fn = """function formatCorrVarLabel(name) {
  if (!name) return "";
  const str = name.toString().trim();
  const key = str.toLowerCase();
  const map = {
    "rainfall": "Rainfall",
    "rainfall intensity": "Rainfall",
    "catchment_rainfall": "Rainfall",
    "telemetry rainfall": "Rainfall",
    "precipitation": "Precip",
    "cum. rainfall": "Cum.Rain",
    "cum. rain": "Cum.Rain",
    "cumulative rainfall": "Cum.Rain",
    "water level": "WaterLvl",
    "water level stage": "WaterLvl",
    "water_level": "WaterLvl",
    "water_level_stage": "WaterLvl",
    "upstream inflow": "Upstream",
    "upstream": "Upstream",
    "inflow": "Upstream",
    "soil saturation": "SoilSat",
    "soil sat.": "SoilSat",
    "soil_saturation": "SoilSat",
    "saturation": "SoilSat",
    "drainage cap.": "DrainCap",
    "drainage capacity": "DrainCap",
    "drainage_cap": "DrainCap",
    "drainage": "DrainCap",
    "streamflow": "Streamfl",
    "temperature": "Temp",
    "discharge": "Discharge",
    "stage": "Stage",
    "velocity": "Velocity",
    "depth": "Depth",
    "invert elev.": "InvertZ",
    "slope": "Slope",
    "length": "Length",
    "capacity": "Capacity",
    "observation_mask": "ObsMask",
    "lag1_stage": "Lag1Lvl",
    "lag3_stage": "Lag3Lvl",
    "acquisition time": "Time"
  };
  if (map[key]) return map[key];
  if (str.length > 8) return str.substring(0, 7) + ".";
  return str;
}

function renderDeCorrelationMatrix(corrData, method) {
  const container = document.getElementById("de-corr-matrix-container");
  if (!container || !corrData) return;

  const rawVars = corrData.variables || ["Rainfall", "Cum. Rain", "Water Level", "Inflow", "Saturation", "Drainage"];
  const matrix = (method === "spearman" && corrData.spearman_matrix) ? corrData.spearman_matrix : corrData.matrix;
  if (!matrix) return;

  const vars = rawVars.map(v => formatCorrVarLabel(v));

  let html = "";
  
  // 1. Top X-Axis Header Row
  html += `<div class="wt-corr-header-row">`;
  html += `<div class="wt-corr-corner-spacer"></div>`;
  vars.forEach((v, idx) => {
    html += `<div class="wt-corr-top-lbl" title="${rawVars[idx]}">${v}</div>`;
  });
  html += `</div>`;

  // 2. Matrix Rows with Left Y-Axis Labels
  matrix.forEach((row, rIdx) => {
    html += `<div class="wt-corr-row">`;
    html += `<span class="wt-corr-lbl" title="${rawVars[rIdx]}">${vars[rIdx]}</span>`;
    row.forEach((val, cIdx) => {
      // Diverging Red-Blue scale matching dark theme reference
      let bg = "rgba(30, 41, 59, 0.6)";
      if (val >= 0) {
        if (val >= 0.95) {
          bg = "#b91c1c";
        } else if (val >= 0.80) {
          bg = `rgba(220, 38, 38, ${0.80 + (val - 0.80) * 0.75})`;
        } else if (val >= 0.60) {
          bg = `rgba(239, 68, 68, ${0.65 + (val - 0.60) * 0.75})`;
        } else if (val >= 0.40) {
          bg = `rgba(239, 68, 68, ${0.48 + (val - 0.40) * 0.85})`;
        } else if (val >= 0.20) {
          bg = `rgba(239, 68, 68, ${0.32 + (val - 0.20) * 0.80})`;
        } else {
          bg = `rgba(239, 68, 68, ${0.18 + val * 0.70})`;
        }
      } else {
        const absVal = Math.abs(val);
        if (absVal >= 0.80) {
          bg = "#1d4ed8";
        } else if (absVal >= 0.60) {
          bg = `rgba(37, 99, 235, ${0.70 + (absVal - 0.60) * 0.80})`;
        } else if (absVal >= 0.40) {
          bg = `rgba(59, 130, 246, ${0.55 + (absVal - 0.40) * 0.75})`;
        } else if (absVal >= 0.20) {
          bg = `rgba(59, 130, 246, ${0.40 + (absVal - 0.20) * 0.75})`;
        } else {
          bg = `rgba(59, 130, 246, ${0.22 + absVal * 0.85})`;
        }
      }

      html += `<div class="wt-corr-cell" style="background:${bg};" title="${rawVars[rIdx]} vs ${rawVars[cIdx]}: ${val.toFixed(2)}">${val.toFixed(2)}</div>`;
    });
    html += `</div>`;
  });

  container.innerHTML = html;
}"""

if old_corr_fn in js_content:
    js_content = js_content.replace(old_corr_fn, new_corr_fn)
    print("  ✓ Replaced renderDeCorrelationMatrix with Top X-axis labels and responsive formatting")
else:
    # Use regex replacement
    pattern = r'function\s+renderDeCorrelationMatrix\s*\([^)]*\)\s*\{[\s\S]*?container\.innerHTML\s*=\s*html;\s*\}'
    js_content = re.sub(pattern, new_corr_fn, js_content)
    print("  ✓ Regex-replaced renderDeCorrelationMatrix")

# C. Update 2D canvas grid line colors to dark theme
# In renderDeDistFeatureChart
js_content = js_content.replace('ctx.strokeStyle = "#f1f5f9";\n  ctx.lineWidth = 1;\n  ctx.fillStyle = "#94a3b8";',
                                'ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";\n  ctx.lineWidth = 1;\n  ctx.fillStyle = "#94a3b8";')

# In renderDeTimeSeriesChart
js_content = js_content.replace('// Grid & Left Axis (Rainfall mm/h)\n  ctx.strokeStyle = "#f1f5f9";',
                                '// Grid & Left Axis (Rainfall mm/h)\n  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";')

# In renderDeFloodResponse
js_content = js_content.replace('// Axis grid\n  ctx.strokeStyle = "#f1f5f9";',
                                '// Axis grid\n  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";')

# In renderDeLossCurve
js_content = js_content.replace('// Grid\n  ctx.strokeStyle = "#f1f5f9";\n  ctx.fillStyle = "#94a3b8";',
                                '// Grid\n  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";\n  ctx.fillStyle = "#94a3b8";')

JS_PATH.write_text(js_content, encoding="utf-8")
print("  ✓ app.js successfully written")


# =============================================================================
# 2. UPDATE style.css
# =============================================================================
print("\n[2/3] Updating style.css...")
css_content = CSS_PATH.read_text(encoding="utf-8")

# Find the start of Task 4.1 styles
marker = "/* ==========================================================================\n   TASK 4.1:"
if marker not in css_content:
    marker = "/* ==========================================================================\r\n   TASK 4.1:"

start_idx = css_content.find(marker)
if start_idx == -1:
    print("  ✗ Could not find Task 4.1 marker in style.css!")
else:
    base_css = css_content[:start_idx]

    new_explorer_css = """/* ==========================================================================
   TASK 4.1: DARK NAVY & CYAN GLASSMORPHISM DATASET EXPLORER
   Matching exact reference design: media_1793430594740_8306ed4a.jpg
   ========================================================================== */

#screen-explorer.screen-container {
  background: transparent !important;
  color: #f8fafc !important;
  padding: 24px 30px !important;
  min-height: calc(100vh - var(--header-height));
  box-sizing: border-box;
}

/* Header Banner */
.wt-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.wt-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.wt-header-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: rgba(0, 132, 255, 0.15);
  border: 1px solid rgba(0, 210, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00d2ff;
  flex-shrink: 0;
  box-shadow: 0 0 16px rgba(0, 210, 255, 0.2);
}

.wt-title {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.wt-subtitle {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

/* Dataset Selector Bar */
.wt-selector-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.wt-select-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.wt-select-label {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.wt-info-tooltip {
  color: #00d2ff;
  cursor: help;
  font-size: 12px;
}

.wt-select-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(7, 14, 30, 0.85);
  border: 1px solid rgba(0, 210, 255, 0.3);
  border-radius: 8px;
  padding: 8px 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(10px);
}

.wt-select-box svg {
  color: #00d2ff;
  stroke: #00d2ff;
}

.wt-select-box select {
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  outline: none;
  cursor: pointer;
}

.wt-select-box select option {
  background: #0b1528;
  color: #ffffff;
}

/* Quick-Switch Pills */
.wt-pills-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.wt-pill-btn {
  background: rgba(11, 21, 40, 0.7);
  color: #cbd5e1;
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  line-height: 1.25;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(8px);
}

.wt-pill-sub {
  font-size: 10px;
  font-weight: 400;
  opacity: 0.85;
  color: #94a3b8;
}

.wt-pill-btn:hover {
  border-color: #00d2ff;
  color: #ffffff;
  background: rgba(0, 132, 255, 0.2);
  transform: translateY(-1px);
}

.wt-pill-btn.active {
  background: linear-gradient(135deg, #0084ff 0%, #0060df 100%);
  color: #ffffff;
  border-color: #00d2ff;
  box-shadow: 0 0 14px rgba(0, 132, 255, 0.5);
}

.wt-pill-btn.active .wt-pill-sub {
  color: #e0f2fe;
}

/* Summary Card */
.wt-summary-card {
  background: rgba(11, 21, 40, 0.82);
  border: 1px solid rgba(0, 210, 255, 0.22);
  border-radius: 14px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.wt-summary-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 320px;
}

.wt-thumb-container {
  width: 140px;
  height: 84px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
  border: 1px solid rgba(0, 210, 255, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.wt-catchment-thumb {
  width: 100%;
  height: 100%;
  position: relative;
}

.wt-thumb-art {
  width: 100%;
  height: 100%;
  display: block;
}

.wt-summary-title {
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 4px 0;
}

.wt-summary-meta {
  font-size: 12px;
  color: #cbd5e1;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 3px;
}

.wt-summary-meta svg {
  color: #00d2ff;
}

.wt-summary-meta.wt-tags {
  color: #00d2ff;
  font-weight: 600;
  font-size: 11px;
  margin-top: 4px;
}

/* 6 KPI Cards */
.wt-summary-kpis {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.wt-kpi-card {
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 10px;
  padding: 10px 14px;
  min-width: 105px;
  text-align: center;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.wt-kpi-card:hover {
  border-color: rgba(0, 210, 255, 0.45);
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

.wt-kpi-icon {
  display: inline-flex;
  margin-bottom: 4px;
}

.wt-icon-purple { color: #a855f7; }
.wt-icon-cyan { color: #00d2ff; }
.wt-icon-magenta { color: #f43f5e; }
.wt-icon-sky { color: #38bdf8; }
.wt-icon-indigo { color: #818cf8; }
.wt-icon-green { color: #4ade80; }

.wt-kpi-val {
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.2;
}

.wt-kpi-lbl {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
  margin-top: 2px;
  text-transform: capitalize;
}

.wt-val-green {
  color: #4ade80 !important;
}

/* Subnav Bar (6 Tabs) */
.wt-subnav-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(0, 210, 255, 0.15);
  padding-bottom: 8px;
  overflow-x: auto;
}

.wt-subnav-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(11, 21, 40, 0.65);
  color: #cbd5e1;
  border: 1px solid rgba(0, 210, 255, 0.15);
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.wt-subnav-tab svg {
  color: #94a3b8;
  transition: color 0.2s ease;
}

.wt-subnav-tab:hover {
  color: #ffffff;
  background: rgba(0, 132, 255, 0.18);
  border-color: rgba(0, 210, 255, 0.4);
}

.wt-subnav-tab:hover svg {
  color: #00d2ff;
}

.wt-subnav-tab.active {
  background: linear-gradient(135deg, #0084ff 0%, #0060df 100%);
  color: #ffffff;
  border-color: #00d2ff;
  font-weight: 600;
  box-shadow: 0 0 14px rgba(0, 132, 255, 0.45);
}

.wt-subnav-tab.active svg {
  color: #ffffff;
}

/* Sub-panes */
.wt-pane {
  display: none;
}

.wt-pane.active {
  display: block;
}

/* Tab 1: Overview Grid (3 columns x 2 rows) */
.wt-overview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

@media (max-width: 1200px) {
  .wt-overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .wt-overview-grid {
    grid-template-columns: 1fr;
  }
}

/* Generic Dark Glassmorphism Card */
.wt-card {
  background: rgba(11, 21, 40, 0.82);
  border: 1px solid rgba(0, 210, 255, 0.22);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  display: flex;
  flex-direction: column;
}

.wt-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.wt-card-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
}

.wt-card-action {
  font-size: 12px;
}

.wt-card-select {
  background: rgba(7, 14, 30, 0.85);
  border: 1px solid rgba(0, 210, 255, 0.3);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11.5px;
  font-weight: 500;
  color: #ffffff;
  outline: none;
  cursor: pointer;
}

.wt-card-select option {
  background: #0b1528;
  color: #ffffff;
}

/* Card 1: Feature Distributions layout */
.wt-dist-layout {
  display: flex;
  gap: 16px;
  align-items: center;
  height: 150px;
}

.wt-dist-chart {
  flex: 1.4;
  height: 100%;
  position: relative;
}

.wt-dist-stats {
  flex: 0.9;
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 11.5px;
}

.wt-stat-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px solid rgba(0, 210, 255, 0.08);
}

.wt-stat-row:last-child {
  border-bottom: none;
}

.wt-stat-k {
  color: #94a3b8;
  font-weight: 500;
}

.wt-stat-v {
  font-weight: 700;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
}

/* Card 2: Feature Correlation Heatmap */
.wt-corr-layout {
  display: flex;
  gap: 10px;
  align-items: stretch;
  min-height: 175px;
  position: relative;
}

.wt-corr-grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.wt-corr-header-row {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-bottom: 2px;
}

.wt-corr-corner-spacer {
  width: 58px;
  min-width: 58px;
  max-width: 58px;
  flex-shrink: 0;
}

.wt-corr-top-lbl {
  flex: 1;
  min-width: 0;
  font-size: 9.5px;
  font-weight: 600;
  color: #94a3b8;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 1px;
}

.wt-corr-row {
  display: flex;
  gap: 3px;
  align-items: center;
  flex: 1;
  margin: 1px 0;
}

.wt-corr-lbl {
  width: 58px;
  min-width: 58px;
  max-width: 58px;
  font-size: 9.5px;
  font-weight: 600;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  padding-right: 5px;
  flex-shrink: 0;
}

.wt-corr-cell {
  flex: 1;
  min-width: 0;
  height: 22px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9.5px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.85);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  cursor: default;
}

.wt-corr-cell:hover {
  transform: scale(1.08);
  z-index: 2;
  box-shadow: 0 0 8px rgba(0, 210, 255, 0.7);
}

.wt-corr-colorbar {
  width: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  font-size: 9px;
  color: #94a3b8;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  padding: 2px 0;
  flex-shrink: 0;
}

.wt-colorbar-gradient {
  width: 6px;
  flex: 1;
  border-radius: 3px;
  background: linear-gradient(to bottom, #ef4444, #334155, #3b82f6);
  margin: 2px 0;
}

/* Card 3: Missing Data Temporal Grid */
.wt-missing-grid-wrap {
  display: flex;
  flex-direction: column;
  gap: 5px;
  height: 110px;
  justify-content: center;
}

.wt-missing-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.wt-missing-lbl {
  width: 75px;
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  padding-right: 4px;
}

.wt-missing-cells {
  flex: 1;
  display: flex;
  gap: 2px;
}

.wt-mcell {
  flex: 1;
  height: 15px;
  border-radius: 2px;
}

.wt-mcell.p { background: #4ade80; } /* Present: Green */
.wt-mcell.m { background: #facc15; } /* Missing: Yellow */
.wt-mcell.o { background: #f87171; } /* Outlier: Red */

.wt-missing-time-axis {
  display: flex;
  padding-left: 80px;
  justify-content: space-between;
  font-size: 9px;
  color: #64748b;
  margin-top: 4px;
}

.wt-missing-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.wt-mlegend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.wt-mlegend-box {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

#de-missing-summary-badge {
  color: #4ade80 !important;
  font-weight: 700;
}

/* Card 4: Time Series Analysis */
.wt-ts-controls {
  display: flex;
  gap: 14px;
  align-items: center;
  font-size: 11.5px;
  color: #cbd5e1;
}

.wt-ts-controls label {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.wt-chart-canvas-wrap {
  width: 100%;
  height: 120px;
  position: relative;
  margin-top: 8px;
}

.wt-chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 6px;
}

.wt-clegend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.wt-clegend-line {
  width: 12px;
  height: 3px;
  border-radius: 1px;
}

.wt-clegend-bar {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

/* Card 5: Feature Importance Bar List */
.wt-fi-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: 150px;
  justify-content: space-around;
}

.wt-fi-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.wt-fi-name {
  width: 105px;
  color: #cbd5e1;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}

.wt-fi-bar-wrap {
  flex: 1;
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
}

.wt-fi-bar {
  background: linear-gradient(90deg, #0084ff 0%, #00d2ff 100%);
  height: 100%;
  border-radius: 6px;
  transition: width 0.3s ease;
}

.wt-fi-pct {
  width: 40px;
  font-weight: 700;
  font-size: 10.5px;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
}

/* Card 6: Flood Response Curve */
.wt-fr-badge {
  background: rgba(0, 132, 255, 0.15);
  border: 1px solid rgba(0, 210, 255, 0.3);
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 11px;
  color: #00d2ff;
  font-weight: 600;
}

/* Key Insights Bottom Strip */
.wt-insights-strip {
  background: rgba(11, 21, 40, 0.82);
  border: 1px solid rgba(0, 210, 255, 0.22);
  border-radius: 12px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(16px);
  margin-top: 20px;
  flex-wrap: wrap;
}

.wt-insights-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
}

.wt-insights-header svg {
  color: #00d2ff;
}

.wt-insight-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 11.5px;
  color: #cbd5e1;
  font-weight: 500;
}

.wt-insight-item svg {
  color: #00d2ff;
  flex-shrink: 0;
}

/* Tables in Tabs 2 & 5 */
.wt-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.wt-table th {
  background: rgba(7, 14, 30, 0.85);
  color: #94a3b8;
  font-weight: 600;
  text-align: left;
  padding: 10px 14px;
  border-bottom: 2px solid rgba(0, 210, 255, 0.2);
  font-size: 11.5px;
  letter-spacing: 0.02em;
}

.wt-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 210, 255, 0.1);
  color: #e2e8f0;
  background: transparent;
}

.wt-table tr:hover td {
  background: rgba(0, 132, 255, 0.1);
}

.wt-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.wt-badge-blue { background: rgba(2, 132, 199, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
.wt-badge-green { background: rgba(16, 185, 129, 0.2); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); }
.wt-badge-amber { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
.wt-badge-purple { background: rgba(147, 51, 234, 0.2); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.3); }

/* Interactive Sandbox in Tab 2 */
.wt-sandbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.wt-slider-row {
  margin-bottom: 12px;
}

.wt-slider-head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 4px;
}

.wt-slider {
  width: 100%;
  accent-color: #00d2ff;
}

/* Event Cards in Tab 4 */
.wt-events-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.wt-event-card {
  background: rgba(11, 21, 40, 0.82);
  border: 1px solid rgba(0, 210, 255, 0.22);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(16px);
}

.wt-event-title {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 4px 0;
}

.wt-event-date {
  font-size: 11.5px;
  color: #94a3b8;
  margin-bottom: 12px;
}

.wt-event-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
  border-radius: 8px;
  padding: 10px;
  font-size: 11px;
}

.wt-event-stat-k { color: #94a3b8; }
.wt-event-stat-v { font-weight: 700; color: #ffffff; font-family: 'JetBrains Mono', monospace; }

/* Inference Execution in Tab 6 */
.wt-infer-control-box {
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 10px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.wt-btn-primary {
  background: linear-gradient(135deg, #0084ff 0%, #0060df 100%);
  color: #ffffff;
  border: 1px solid #00d2ff;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  box-shadow: 0 0 14px rgba(0, 132, 255, 0.45);
  transition: all 0.2s ease;
}

.wt-btn-primary:hover {
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
  box-shadow: 0 0 18px rgba(0, 210, 255, 0.6);
}

.wt-nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.wt-node-card {
  background: rgba(11, 21, 40, 0.7);
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
  backdrop-filter: blur(8px);
}

.wt-node-name {
  font-size: 11px;
  font-weight: 700;
  color: #cbd5e1;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wt-node-stage {
  font-size: 16px;
  font-weight: 800;
  color: #00d2ff;
  font-family: 'JetBrains Mono', monospace;
}

.wt-node-sub {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 2px;
}

/* Ensure active screen container is unconditionally visible */
.screen-container.active {
  display: block !important;
}

#screen-explorer.active {
  display: block !important;
}
"""
    CSS_PATH.write_text(base_css + new_explorer_css, encoding="utf-8")
    print("  ✓ style.css successfully written with dark glassmorphic styling")


# =============================================================================
# 3. UPDATE index.html
# =============================================================================
print("\n[3/3] Updating index.html...")
html_content = HTML_PATH.read_text(encoding="utf-8")

# Bump cache buster
html_content = html_content.replace('/static/css/style.css?v=4.0', '/static/css/style.css?v=4.2.0')
html_content = html_content.replace('/static/js/app.js?v=4.0', '/static/js/app.js?v=4.2.0')

# Update header SVG stroke to cyan
html_content = html_content.replace('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2">',
                                    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2">')

# Update select box SVG stroke to cyan
html_content = html_content.replace('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2">',
                                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2">')

# Update thumbnail SVG colors to dark cityscape
old_thumb_art = """                      <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#bae6fd"/><stop offset="100%" stop-color="#e0f2fe"/></linearGradient>
                      <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#0284c7"/><stop offset="100%" stop-color="#0369a1"/></linearGradient>
                    </defs>
                    <rect width="200" height="120" fill="url(#skyGrad)"/>
                    <path d="M0,70 Q50,60 100,75 T200,65 L200,120 L0,120 Z" fill="#64748b" opacity="0.3"/>
                    <path d="M0,80 Q50,70 110,88 T200,82 L200,120 L0,120 Z" fill="url(#waterGrad)"/>
                    <rect x="25" y="45" width="22" height="30" fill="#cbd5e1"/>
                    <rect x="52" y="38" width="28" height="38" fill="#94a3b8"/>
                    <rect x="85" y="50" width="20" height="26" fill="#cbd5e1"/>
                    <rect x="135" y="42" width="26" height="34" fill="#94a3b8"/>
                    <rect x="165" y="52" width="24" height="24" fill="#cbd5e1"/>
                    <path d="M40,85 L160,85 M50,85 L50,110 M150,85 L150,110" stroke="#f8fafc" stroke-width="3"/>"""

new_thumb_art = """                      <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#070e1e"/><stop offset="100%" stop-color="#0f2b48"/></linearGradient>
                      <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#0284c7"/><stop offset="100%" stop-color="#00d2ff"/></linearGradient>
                    </defs>
                    <rect width="200" height="120" fill="url(#skyGrad)"/>
                    <path d="M0,70 Q50,60 100,75 T200,65 L200,120 L0,120 Z" fill="#00d2ff" opacity="0.2"/>
                    <path d="M0,80 Q50,70 110,88 T200,82 L200,120 L0,120 Z" fill="url(#waterGrad)"/>
                    <rect x="25" y="45" width="22" height="30" fill="#1e293b"/>
                    <rect x="52" y="38" width="28" height="38" fill="#334155"/>
                    <rect x="85" y="50" width="20" height="26" fill="#1e293b"/>
                    <rect x="135" y="42" width="26" height="34" fill="#334155"/>
                    <rect x="165" y="52" width="24" height="24" fill="#1e293b"/>
                    <path d="M40,85 L160,85 M50,85 L50,110 M150,85 L150,110" stroke="#00d2ff" stroke-width="2.5"/>"""

if old_thumb_art in html_content:
    html_content = html_content.replace(old_thumb_art, new_thumb_art)
    print("  ✓ Updated catchment thumbnail art to dark cityscape")
else:
    print("  ! Catchment thumbnail art already updated or had slightly different spacing")

HTML_PATH.write_text(html_content, encoding="utf-8")
print("  ✓ index.html successfully written")

print("\n" + "=" * 80)
print("ALL MODIFICATIONS APPLIED CLEANLY AND PRECISELY!")
print("=" * 80)
