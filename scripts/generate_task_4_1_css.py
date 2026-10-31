import os

css_content = """
/* ==========================================================================
   TASK 4.1: WHITE-THEME DATASET EXPLORER & HYDROLOGICAL INTELLIGENCE CENTER
   Matching exact reference design: .user_uploaded/media_1793427602234_3a72ebdd.jpg
   ========================================================================== */

#screen-explorer.screen-container {
  background: #f8fafc !important;
  color: #0f172a !important;
  padding: 24px 32px !important;
  min-height: calc(100vh - 60px);
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
  background: #e0f2fe;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0284c7;
  flex-shrink: 0;
}

.wt-title {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
}

.wt-subtitle {
  font-size: 13px;
  color: #64748b;
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
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 4px;
}

.wt-info-tooltip {
  color: #94a3b8;
  cursor: help;
  font-size: 12px;
}

.wt-select-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 14px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.wt-select-box select {
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  outline: none;
  cursor: pointer;
}

/* Quick-Switch Pills */
.wt-pills-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.wt-pill-btn {
  background: #ffffff;
  color: #334155;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  line-height: 1.25;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

.wt-pill-sub {
  font-size: 10px;
  font-weight: 400;
  opacity: 0.85;
}

.wt-pill-btn:hover {
  border-color: #0284c7;
  color: #0284c7;
  background: #f0f9ff;
}

.wt-pill-btn.active {
  background: #0284c7;
  color: #ffffff;
  border-color: #0284c7;
  box-shadow: 0 2px 4px rgba(2, 132, 199, 0.25);
}

.wt-pill-btn.active .wt-pill-sub {
  color: #e0f2fe;
}

/* Summary Card */
.wt-summary-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
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
  border: 1px solid #cbd5e1;
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
  color: #0f172a;
  margin: 0 0 4px 0;
}

.wt-summary-meta {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 3px;
}

.wt-summary-meta.wt-tags {
  color: #0284c7;
  font-weight: 500;
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
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  min-width: 110px;
  text-align: center;
  box-sizing: border-box;
}

.wt-kpi-icon {
  display: inline-flex;
  margin-bottom: 4px;
}

.wt-icon-purple { color: #8b5cf6; }
.wt-icon-cyan { color: #06b6d4; }
.wt-icon-magenta { color: #ec4899; }
.wt-icon-sky { color: #0284c7; }
.wt-icon-indigo { color: #6366f1; }
.wt-icon-green { color: #16a34a; }

.wt-kpi-val {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.wt-kpi-lbl {
  font-size: 10.5px;
  color: #64748b;
  font-weight: 500;
  margin-top: 2px;
}

.wt-val-green {
  color: #16a34a !important;
}

/* Subnav Bar (6 Tabs) */
.wt-subnav-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 10px;
  overflow-x: auto;
}

.wt-subnav-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: #64748b;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.wt-subnav-tab:hover {
  color: #0284c7;
  background: #f0f9ff;
}

.wt-subnav-tab.active {
  background: #e0f2fe;
  color: #0284c7;
  border-color: #bae6fd;
  font-weight: 600;
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

/* Generic White Card */
.wt-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
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
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
}

.wt-card-action {
  font-size: 12px;
}

.wt-card-select {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 500;
  color: #334155;
  outline: none;
  cursor: pointer;
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
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
}

.wt-stat-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px solid #f1f5f9;
}

.wt-stat-row:last-child {
  border-bottom: none;
}

.wt-stat-k {
  color: #64748b;
  font-weight: 500;
}

.wt-stat-v {
  font-weight: 700;
  color: #0f172a;
  font-family: 'JetBrains Mono', monospace;
}

/* Card 2: Correlation Heatmap */
.wt-corr-layout {
  display: flex;
  gap: 10px;
  align-items: center;
  height: 150px;
  position: relative;
}

.wt-corr-grid {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.wt-corr-row {
  display: flex;
  gap: 4px;
  align-items: center;
}

.wt-corr-lbl {
  width: 70px;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  padding-right: 4px;
}

.wt-corr-cell {
  flex: 1;
  height: 22px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9.5px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: #ffffff;
}

.wt-corr-colorbar {
  width: 28px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
}

.wt-colorbar-gradient {
  width: 6px;
  flex: 1;
  border-radius: 3px;
  background: linear-gradient(to bottom, #ef4444, #ffffff, #3b82f6);
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
  color: #64748b;
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

.wt-mcell.p { background: #86efac; } /* Present: Light Green */
.wt-mcell.m { background: #fde047; } /* Missing: Yellow */
.wt-mcell.o { background: #f87171; } /* Outlier: Red */

.wt-missing-time-axis {
  display: flex;
  padding-left: 80px;
  justify-content: space-between;
  font-size: 9px;
  color: #94a3b8;
  margin-top: 4px;
}

.wt-missing-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
  font-size: 11px;
  color: #64748b;
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

/* Card 4: Time Series Analysis */
.wt-ts-controls {
  display: flex;
  gap: 14px;
  align-items: center;
  font-size: 11.5px;
  color: #475569;
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
  color: #64748b;
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
  color: #334155;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}

.wt-fi-bar-wrap {
  flex: 1;
  background: #f1f5f9;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
}

.wt-fi-bar {
  background: #0284c7;
  height: 100%;
  border-radius: 6px;
  transition: width 0.3s ease;
}

.wt-fi-pct {
  width: 40px;
  font-weight: 700;
  font-size: 10.5px;
  color: #0f172a;
  font-family: 'JetBrains Mono', monospace;
}

/* Card 6: Flood Response Curve */
.wt-fr-badge {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 11px;
  color: #0369a1;
  font-weight: 600;
}

/* Key Insights Bottom Strip */
.wt-insights-strip {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  flex-wrap: wrap;
}

.wt-insights-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.wt-insights-header svg {
  color: #0284c7;
}

.wt-insight-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 11.5px;
  color: #334155;
  font-weight: 500;
}

.wt-insight-item svg {
  color: #0284c7;
  flex-shrink: 0;
}

/* Tables in White Theme (Tabs 2 & 5) */
.wt-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.wt-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  text-align: left;
  padding: 10px 14px;
  border-bottom: 2px solid #e2e8f0;
  font-size: 11.5px;
  letter-spacing: 0.02em;
}

.wt-table td {
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
}

.wt-table tr:hover td {
  background: #f8fafc;
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

.wt-badge-blue { background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd; }
.wt-badge-green { background: #dcfce7; color: #16a34a; border: 1px solid #bbf7d0; }
.wt-badge-amber { background: #fef3c7; color: #d97706; border: 1px solid #fde68a; }
.wt-badge-purple { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }

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
  color: #334155;
  margin-bottom: 4px;
}

.wt-slider {
  width: 100%;
  accent-color: #0284c7;
}

/* Event Cards in Tab 4 */
.wt-events-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.wt-event-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

.wt-event-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.wt-event-date {
  font-size: 11.5px;
  color: #64748b;
  margin-bottom: 12px;
}

.wt-event-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  font-size: 11px;
}

.wt-event-stat-k { color: #64748b; }
.wt-event-stat-v { font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace; }

/* Inference Execution in Tab 6 */
.wt-infer-control-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.wt-btn-primary {
  background: #0284c7;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(2, 132, 199, 0.2);
  transition: all 0.15s ease;
}

.wt-btn-primary:hover {
  background: #0369a1;
}

.wt-nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.wt-node-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.wt-node-name {
  font-size: 11px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wt-node-stage {
  font-size: 16px;
  font-weight: 800;
  color: #0284c7;
  font-family: 'JetBrains Mono', monospace;
}

.wt-node-sub {
  font-size: 10px;
  color: #64748b;
  margin-top: 2px;
}
"""

with open("frontend/static/css/style.css", "a", encoding="utf-8") as f:
    f.write("\n" + css_content)

print("Successfully appended White-Theme CSS for Task 4.1 to frontend/static/css/style.css")

