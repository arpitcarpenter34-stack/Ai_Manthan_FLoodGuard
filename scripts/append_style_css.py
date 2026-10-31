import sys
sys.stdout.reconfigure(encoding='utf-8')

css_additions = """
/* =============================================================================
   DATASET INTELLIGENCE, RADAR, DRIVERS & PROVENANCE BADGES (TASK 3.9 / MAJOR TRANSFORMATION)
   ============================================================================= */

/* Phase 11: Data Provenance Badges */
.prov-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
}

.prov-observed {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.prov-historical {
  background: rgba(14, 165, 233, 0.15);
  color: #0ea5e9;
  border: 1px solid rgba(14, 165, 233, 0.35);
}

.prov-simulated {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.prov-model {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
  border: 1px solid rgba(168, 85, 247, 0.35);
}

.prov-live {
  background: rgba(244, 63, 94, 0.15);
  color: #f43f5e;
  border: 1px solid rgba(244, 63, 94, 0.35);
}

/* Dataset Explorer Layout */
.de-header-row, .wr-header-row, .dr-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.de-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.de-selector-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(15, 23, 42, 0.85);
  padding: 6px 14px;
  border-radius: 10px;
  border: 1px solid rgba(0, 210, 255, 0.25);
}

.de-selector-box label {
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
  white-space: nowrap;
}

.de-selector-box select {
  background: #0f172a;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #f8fafc;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  outline: none;
  cursor: pointer;
}

.de-selector-box select:focus {
  border-color: #00d2ff;
}

/* Dossier Grid */
.de-dossier-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.de-dossier-card {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform 0.2s, border-color 0.2s;
}

.de-dossier-card:hover {
  border-color: rgba(0, 210, 255, 0.3);
  transform: translateY(-2px);
}

.de-dossier-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.de-dossier-title {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
}

.de-dossier-val {
  font-size: 15px;
  font-weight: 750;
  color: #f8fafc;
  word-break: break-word;
}

.de-dossier-sub {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

/* Two Column Analytics */
.de-analytics-row {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1024px) {
  .de-analytics-row {
    grid-template-columns: 1fr;
  }
}

.de-panel {
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  overflow: hidden;
}

.de-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(30, 41, 59, 0.4);
}

.de-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 750;
  color: #f8fafc;
}

.de-panel-title svg {
  color: #00d2ff;
}

.de-table-wrap {
  overflow-x: auto;
  max-height: 380px;
}

.de-dist-wrap {
  padding: 14px 18px;
  max-height: 380px;
  overflow-y: auto;
}

.de-dist-item {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.de-dist-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.de-dist-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.de-dist-var-name {
  font-size: 12px;
  font-weight: 750;
  color: #e2e8f0;
}

.de-dist-var-unit {
  font-size: 11px;
  color: #00d2ff;
  font-family: 'JetBrains Mono', monospace;
}

.de-dist-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  background: rgba(15, 23, 42, 0.5);
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
}

.de-dist-stat-k {
  color: #64748b;
}

.de-dist-stat-v {
  color: #cbd5e1;
  font-weight: 600;
  text-align: right;
}

/* Inference Action Panel */
.de-inference-panel {
  margin-bottom: 24px;
  border-color: rgba(0, 210, 255, 0.2);
}

.de-inference-content {
  padding: 20px;
}

.de-inference-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.de-btn-run-inference {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #00d2ff 0%, #0090ff 100%);
  color: #04101e;
  border: none;
  padding: 10px 22px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.de-btn-run-inference:hover {
  opacity: 0.95;
  transform: translateY(-1px);
}

.de-inference-results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.de-inf-node-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.de-inf-node-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
}

.de-inf-node-stage {
  font-size: 18px;
  font-weight: 800;
  color: #f8fafc;
  font-family: 'JetBrains Mono', monospace;
}

.de-inf-node-metrics {
  font-size: 11px;
  color: #64748b;
  display: flex;
  justify-content: space-between;
}

/* Weather & Radar Screen */
.wr-audit-banner {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: rgba(14, 165, 233, 0.08);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 24px;
}

.wr-audit-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.wr-audit-text h4 {
  font-size: 14px;
  font-weight: 800;
  color: #38bdf8;
  margin-bottom: 6px;
  letter-spacing: 0.02em;
}

.wr-audit-text p {
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.55;
}

.wr-telemetry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.wr-telem-card {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.wr-telem-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
}

.wr-telem-val {
  font-size: 28px;
  font-weight: 850;
  color: #00d2ff;
  font-family: 'JetBrains Mono', monospace;
  margin: 4px 0;
}

.wr-telem-label {
  font-size: 13px;
  font-weight: 750;
  color: #f8fafc;
}

.wr-telem-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.wr-hyetograph-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 10px 16px 14px;
  font-size: 12px;
  color: #94a3b8;
  flex-wrap: wrap;
}

.wr-hyetograph-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-swatch {
  width: 14px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}

.wr-specs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 20px;
}

.wr-specs-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wr-spec-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.wr-spec-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.wr-spec-k {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #00d2ff;
}

.wr-spec-v {
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.45;
}

/* Flood Drivers Screen */
.dr-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 1024px) {
  .dr-grid-2 {
    grid-template-columns: 1fr;
  }
}
"""

with open("frontend/static/css/style.css", "a", encoding="utf-8") as f:
    f.write(css_additions)

print("Appended styling to style.css successfully.")

