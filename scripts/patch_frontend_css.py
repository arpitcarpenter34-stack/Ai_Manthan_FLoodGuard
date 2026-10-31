"""
CSS styles for Task 3.8: AI Model Intelligence & Scientific Explainability.
Appends scoped .mi-* classes to frontend/static/css/style.css.
"""

from pathlib import Path

CSS_FILE = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\static\css\style.css")

MI_CSS = """

/* ==========================================================================
   TASK 3.8: AI MODEL INTELLIGENCE & SCIENTIFIC EXPLAINABILITY STYLES (.mi-*)
   ========================================================================== */
.mi-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 22px;
  flex-wrap: wrap;
  gap: 16px;
}

.mi-badge-head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 210, 255, 0.12);
  border: 1px solid rgba(0, 210, 255, 0.35);
  color: var(--cyan-accent);
  padding: 4px 12px;
  border-radius: 50px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.mi-live-dot {
  width: 7px;
  height: 7px;
  background: var(--cyan-accent);
  border-radius: 50%;
  box-shadow: 0 0 8px var(--cyan-accent);
  animation: pulse-live 1.8s infinite;
}

.mi-page-title {
  font-size: 24px;
  font-weight: 850;
  color: #f8fafc;
  margin-bottom: 4px;
  letter-spacing: -0.4px;
}

.mi-page-subtitle {
  font-size: 13px;
  color: var(--muted-text);
  max-width: 820px;
  line-height: 1.5;
}

.mi-header-badges {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.mi-model-pill {
  display: flex;
  flex-direction: column;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.mi-pill-prod {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.08);
}

.mi-pill-cand {
  border-color: rgba(0, 210, 255, 0.4);
  background: rgba(0, 210, 255, 0.08);
}

.mi-pill-title {
  font-size: 10px;
  font-weight: 750;
  color: var(--muted-text);
  letter-spacing: 0.6px;
  text-transform: uppercase;
}

.mi-pill-val {
  font-size: 12px;
  font-weight: 700;
  color: #f1f5f9;
  margin-top: 2px;
}

/* Subnav Tabs */
.mi-subnav-bar {
  display: flex;
  gap: 8px;
  background: rgba(11, 21, 40, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 6px;
  margin-bottom: 22px;
  overflow-x: auto;
}

.mi-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.mi-tab-btn:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.05);
}

.mi-tab-btn.active {
  background: rgba(0, 210, 255, 0.15);
  border: 1px solid rgba(0, 210, 255, 0.4);
  color: #00d2ff;
  font-weight: 700;
}

/* Layout Grids */
.mi-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.mi-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.mi-flex-col {
  display: flex;
  flex-direction: column;
}

/* Card Panels */
.mi-card {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  position: relative;
  transition: border-color 0.2s ease;
}

.mi-card:hover {
  border-color: rgba(0, 210, 255, 0.35);
}

.mi-card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 10px;
}

.mi-card-title {
  font-size: 15px;
  font-weight: 750;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mi-card-subtitle {
  font-size: 12px;
  color: var(--muted-text);
  margin-top: 3px;
  margin-bottom: 14px;
  line-height: 1.4;
}

/* Lineage Cards */
.mi-lineage-card {
  background: rgba(11, 21, 40, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.2s ease;
}

.mi-lineage-card:hover {
  border-color: rgba(0, 210, 255, 0.4);
  transform: translateY(-2px);
}

.mi-lc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.mi-lc-badge {
  font-size: 10px;
  font-weight: 750;
  padding: 3px 8px;
  border-radius: 6px;
  text-transform: uppercase;
}

.mi-badge-supervised {
  background: rgba(0, 210, 255, 0.15);
  color: #00d2ff;
  border: 1px solid rgba(0, 210, 255, 0.3);
}

.mi-badge-production {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.mi-badge-physics {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.mi-badge-baseline {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.mi-lc-title {
  font-size: 15px;
  font-weight: 750;
  color: #f8fafc;
  margin-bottom: 4px;
}

.mi-lc-source {
  font-size: 11px;
  color: var(--cyan-accent);
  margin-bottom: 10px;
}

.mi-lc-stat-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 12px;
}

.mi-lc-stat-row:last-child {
  border-bottom: none;
}

.mi-lc-label {
  color: var(--muted-text);
}

.mi-lc-val {
  color: #e2e8f0;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

/* Tables */
.mi-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  color: #cbd5e1;
}

.mi-table th {
  background: rgba(15, 23, 42, 0.8);
  color: #00d2ff;
  font-weight: 700;
  text-align: left;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 210, 255, 0.2);
  white-space: nowrap;
}

.mi-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.mi-table tr:hover td {
  background: rgba(255, 255, 255, 0.03);
}

/* Canvas Boxes */
.mi-canvas-container {
  width: 100%;
  position: relative;
  background: rgba(7, 14, 30, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  overflow: hidden;
}

.mi-canvas-container canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.mi-chart-footnote {
  font-size: 11px;
  color: var(--muted-text);
  margin-top: 8px;
  font-style: italic;
}

.mi-chart-legend {
  display: flex;
  gap: 16px;
  margin-top: 10px;
  font-size: 12px;
  color: #cbd5e1;
}

.mi-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.mi-legend-color {
  width: 12px;
  height: 3px;
  border-radius: 2px;
}

/* Telemetry Grid */
.mi-telemetry-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.mi-tele-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  padding: 14px;
}

.mi-tele-val {
  font-size: 18px;
  font-weight: 800;
  color: #f8fafc;
  font-family: 'JetBrains Mono', monospace;
}

.mi-tele-label {
  font-size: 11px;
  color: var(--muted-text);
  margin-top: 4px;
}

.mi-callout-info {
  background: rgba(2, 132, 199, 0.1);
  border-left: 3px solid var(--sky-blue);
  border-radius: 6px;
  padding: 12px 14px;
  font-size: 12px;
  color: #bae6fd;
  line-height: 1.5;
}

/* Metrics Banner */
.mi-metrics-banner {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.mi-stat-card {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}

.mi-stat-val {
  font-size: 22px;
  font-weight: 850;
  color: #f8fafc;
  font-family: 'JetBrains Mono', monospace;
}

.mi-stat-lbl {
  font-size: 11px;
  color: var(--muted-text);
  margin-top: 4px;
}

/* Sliders */
.mi-slider-box {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
}

.mi-slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #e2e8f0;
  font-weight: 600;
  margin-bottom: 8px;
}

.mi-range-input {
  width: 100%;
  -webkit-appearance: none;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.15);
  outline: none;
}

.mi-range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--cyan-accent);
  cursor: pointer;
  box-shadow: 0 0 10px var(--cyan-accent);
}

.mi-slider-bounds {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--muted-text);
  margin-top: 6px;
}

/* Waterfall */
.mi-waterfall-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.mi-wf-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.mi-wf-label {
  width: 180px;
  color: #cbd5e1;
  white-space: nowrap;
}

.mi-wf-bar-wrap {
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  height: 14px;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.mi-wf-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.mi-wf-val {
  width: 60px;
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
}

.mi-wf-positive .mi-wf-bar { background: var(--warn-amber); }
.mi-wf-positive .mi-wf-val { color: var(--warn-amber); }

.mi-wf-negative .mi-wf-bar { background: var(--safe-green); }
.mi-wf-negative .mi-wf-val { color: var(--safe-green); }

.mi-wf-total .mi-wf-bar { background: var(--danger-red); }
.mi-wf-total .mi-wf-val { color: var(--danger-red); }

.mi-wf-base .mi-wf-bar { background: var(--sky-blue); }
.mi-wf-base .mi-wf-val { color: var(--sky-blue); }

.mi-model-selector select {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(0, 210, 255, 0.3);
  color: #f1f5f9;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  outline: none;
}

@media (max-width: 1024px) {
  .mi-grid-2, .mi-grid-3, .mi-metrics-banner {
    grid-template-columns: 1fr;
  }
}
"""

content = CSS_FILE.read_text(encoding="utf-8")
if "TASK 3.8: AI MODEL INTELLIGENCE" not in content:
    content += MI_CSS
    CSS_FILE.write_text(content, encoding="utf-8")
    print(f"Appended .mi-* styles to {CSS_FILE}")
else:
    print("Styles already present.")
