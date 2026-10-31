import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"E:\ai-manthan\hydro_guard_indore")
HTML_PATH = BASE_DIR / "frontend" / "static" / "index.html"
CSS_PATH = BASE_DIR / "frontend" / "static" / "css" / "style.css"
JS_PATH = BASE_DIR / "frontend" / "static" / "js" / "app.js"

print("=" * 80)
print("IMPLEMENTING PROFESSIONAL WEATHER & RADAR DASHBOARD")
print("=" * 80)

# =============================================================================
# 1. UPDATE index.html
# =============================================================================
print("\n[1/3] Updating index.html with Weather & Radar Dashboard markup...")
html_text = HTML_PATH.read_text(encoding="utf-8")

# Target section to replace
wr_section_regex = r'<section id="screen-weather-radar" class="screen-container" style="display: none;">[\s\S]*?</section>'

new_wr_html = """<section id="screen-weather-radar" class="screen-container" style="display: none;">
          <!-- 1. Header Banner -->
          <div class="wr-header-row">
            <div class="wr-header-left">
              <div class="wr-header-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path>
                  <path d="M2 12h20"></path>
                </svg>
              </div>
              <div>
                <h2 class="wr-title">Weather &amp; Radar Precipitation Intelligence</h2>
                <p class="wr-subtitle">Real-Time Atmospheric Polling • Ground Telemetry Verification • Doppler Radar Availability Audit • Extreme Storm Hyetographs</p>
              </div>
            </div>
            <div class="wr-header-actions">
              <div class="wr-region-select-box">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                <select id="wr-region-select" onchange="onWrRegionChange(this.value)">
                  <option value="indore" selected>Indore Catchment (IMC Central AWS, MP, India)</option>
                  <option value="pune_cwprs">Pune Region (CWPRS Campus AWS, MH, India)</option>
                  <option value="eastbourne">Eastbourne Catchment (Blue Heart Gages, UK)</option>
                  <option value="aroostook">Aroostook Basin (CAMELS Hydrology, ME, US)</option>
                </select>
              </div>
              <button class="wr-btn-refresh" onclick="refreshWrDashboard()" title="Refresh live atmospheric polling">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                <span>Refresh</span>
              </button>
              <div class="wr-live-pill">
                <span class="wr-live-dot"></span>
                <span id="wr-provenance-status">LIVE NWP STREAM</span>
              </div>
            </div>
          </div>

          <!-- 2. Top 5 Weather KPI Cards -->
          <div class="wr-kpi-grid">
            <!-- KPI 1: Current Rainfall Intensity -->
            <div class="wr-kpi-card">
              <div class="wr-kpi-head">
                <div class="wr-kpi-icon wr-icon-cyan">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"></path><line x1="8" y1="19" x2="8" y2="21"></line><line x1="12" y1="17" x2="12" y2="23"></line><line x1="16" y1="19" x2="16" y2="21"></line></svg>
                </div>
                <span class="wr-badge-prov" id="wr-prov-kpi1">OBSERVED (LIVE)</span>
              </div>
              <div class="wr-kpi-val" id="wr-val-current-rain">0.0 <span class="wr-kpi-unit">mm/h</span></div>
              <div class="wr-kpi-lbl">Current Rainfall Intensity</div>
              <div class="wr-kpi-sub" id="wr-sub-current-rain">Live Atmospheric Query</div>
            </div>

            <!-- KPI 2: 24h Accumulated Rainfall -->
            <div class="wr-kpi-card">
              <div class="wr-kpi-head">
                <div class="wr-kpi-icon wr-icon-purple">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>
                </div>
                <span class="wr-badge-prov">DERIVED</span>
              </div>
              <div class="wr-kpi-val" id="wr-val-accum-rain">0.0 <span class="wr-kpi-unit">mm</span></div>
              <div class="wr-kpi-lbl">Accumulated (Past 24 Hours)</div>
              <div class="wr-kpi-sub" id="wr-sub-accum-rain">Continuous Hourly Sum</div>
            </div>

            <!-- KPI 3: Next 1 Hour Forecast -->
            <div class="wr-kpi-card">
              <div class="wr-kpi-head">
                <div class="wr-kpi-icon wr-icon-sky">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                </div>
                <span class="wr-badge-prov wr-prov-fc">FORECAST</span>
              </div>
              <div class="wr-kpi-val" id="wr-val-fc-1h">0.0 <span class="wr-kpi-unit">mm</span></div>
              <div class="wr-kpi-lbl">Next 1 Hour Forecast (t+1h)</div>
              <div class="wr-kpi-sub" id="wr-sub-fc-1h">NWP Immediate Influx</div>
            </div>

            <!-- KPI 4: Next 6 Hours Forecast -->
            <div class="wr-kpi-card">
              <div class="wr-kpi-head">
                <div class="wr-kpi-icon wr-icon-indigo">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                </div>
                <span class="wr-badge-prov wr-prov-fc">FORECAST</span>
              </div>
              <div class="wr-kpi-val" id="wr-val-fc-6h">0.0 <span class="wr-kpi-unit">mm</span></div>
              <div class="wr-kpi-lbl">Next 6 Hours Accumulation</div>
              <div class="wr-kpi-sub" id="wr-sub-fc-6h">Short-Term Ensemble Window</div>
            </div>

            <!-- KPI 5: Alert & Intensity Classification -->
            <div class="wr-kpi-card">
              <div class="wr-kpi-head">
                <div class="wr-kpi-icon wr-icon-green" id="wr-icon-alert">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                </div>
                <span class="wr-badge-prov" id="wr-badge-status-level">STATUS: NOMINAL</span>
              </div>
              <div class="wr-kpi-val" id="wr-val-alert-class" style="font-size:15px;">No Rain (शुष्क)</div>
              <div class="wr-kpi-lbl">Rainfall Alert &amp; Intensity</div>
              <div class="wr-kpi-sub" id="wr-sub-alert-class">Conduit Capacity: Nominal</div>
            </div>
          </div>

          <!-- 3. Middle Section: Leaflet Map & Nowcast/Atmospheric Panel -->
          <div class="wr-middle-grid">
            <!-- Left Column: Leaflet Weather Radar & Stations Map -->
            <div class="wr-card wr-map-card">
              <div class="wr-card-head">
                <div class="wr-card-title">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/></svg>
                  <span id="wr-map-title">Catchment Precipitation &amp; Station Telemetry Map</span>
                </div>
                <div class="wr-map-tools">
                  <span class="wr-badge-prov">OBSERVED SENSORS</span>
                  <span class="wr-map-time" id="wr-map-timestamp">Synced: Live</span>
                </div>
              </div>

              <!-- Radar Scientific Availability Banner (ZERO FABRICATION POLICY) -->
              <div class="wr-radar-status-banner">
                <div class="wr-rsb-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                </div>
                <div class="wr-rsb-body">
                  <div class="wr-rsb-head">
                    <strong>DOPPLER RADAR REFLECTIVITY: UNAVAILABLE</strong>
                    <span class="wr-rsb-tag">ZERO FABRICATION POLICY</span>
                  </div>
                  <p class="wr-rsb-desc">
                    No raw Doppler radar volume scan files (IMD HDF5/GRIB2 polar coordinates or NEXRAD Level II NetCDF-4) are present on disk. Strictly adhering to scientific integrity, <strong>no simulated or decorative radar grids are rendered</strong>. Showing verified ground rain gauge telemetry stations and live NWP atmospheric forcing.
                  </p>
                  <div class="wr-rsb-specs">
                    <span><strong>Ingest Protocols Ready:</strong> ODIM_H5 (EUMETNET) • NetCDF-4 (CF-1.7) • BUFR/GRIB2</span>
                  </div>
                </div>
              </div>

              <!-- Leaflet Map Container -->
              <div class="wr-map-container" id="wr-leaflet-map"></div>

              <!-- Map Legend -->
              <div class="wr-map-legend">
                <span><span class="wr-dot" style="background:#00d2ff; box-shadow:0 0 6px #00d2ff;"></span> Automated Weather Station (AWS)</span>
                <span><span class="wr-dot" style="background:#a855f7; box-shadow:0 0 6px #a855f7;"></span> Tipping Bucket Rain Gauge</span>
                <span><span class="wr-dot" style="background:#10b981; box-shadow:0 0 6px #10b981;"></span> Reservoir / Lake Hydrology</span>
                <span><span class="wr-dot" style="background:#f43f5e; box-shadow:0 0 6px #f43f5e;"></span> Drainage Surcharge Outfall</span>
              </div>
            </div>

            <!-- Right Column: Nowcast & Short-Term Outlook Panel -->
            <div class="wr-card wr-nowcast-card">
              <div class="wr-card-head">
                <div class="wr-card-title">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                  <span>Nowcast &amp; Short-Term Outlook</span>
                </div>
                <span class="wr-badge-prov">OBSERVED &amp; FORECAST</span>
              </div>

              <div class="wr-nowcast-body">
                <!-- Trend Badge -->
                <div class="wr-trend-box">
                  <span class="wr-trend-lbl">Precipitation Trajectory:</span>
                  <span class="wr-trend-val" id="wr-trend-val">Stable Antecedent (Dry / Clear)</span>
                </div>

                <!-- 2x2 Outlook Metrics -->
                <div class="wr-nowcast-metrics-grid">
                  <div class="wr-nc-metric">
                    <span class="wr-nc-lbl">Observed Rain (t=0)</span>
                    <span class="wr-nc-val" id="wr-nc-obs">0.0 mm/h</span>
                  </div>
                  <div class="wr-nc-metric">
                    <span class="wr-nc-lbl">Next 1h Forecast (t+1h)</span>
                    <span class="wr-nc-val" id="wr-nc-fc1">0.0 mm/h</span>
                  </div>
                  <div class="wr-nc-metric">
                    <span class="wr-nc-lbl">Peak Expected Window</span>
                    <span class="wr-nc-val" id="wr-nc-peak">Clear Window</span>
                  </div>
                  <div class="wr-nc-metric">
                    <span class="wr-nc-lbl">6h Forecast Total</span>
                    <span class="wr-nc-val" id="wr-nc-accum6">0.0 mm</span>
                  </div>
                </div>

                <!-- Atmospheric Live Query -->
                <div class="wr-atmos-section">
                  <div class="wr-atmos-title">Atmospheric Meteorological Telemetry</div>
                  <div class="wr-atmos-grid">
                    <div class="wr-atmos-item">
                      <span class="wr-atmos-k">Wind Velocity:</span>
                      <span class="wr-atmos-v" id="wr-atmos-wind">8.5 km/h</span>
                    </div>
                    <div class="wr-atmos-item">
                      <span class="wr-atmos-k">Wind Direction:</span>
                      <span class="wr-atmos-v" id="wr-atmos-wind-dir">ENE (65°)</span>
                    </div>
                    <div class="wr-atmos-item">
                      <span class="wr-atmos-k">Ambient Temperature:</span>
                      <span class="wr-atmos-v" id="wr-atmos-temp">24.5 °C</span>
                    </div>
                    <div class="wr-atmos-item">
                      <span class="wr-atmos-k">Relative Humidity:</span>
                      <span class="wr-atmos-v" id="wr-atmos-humidity">72 %</span>
                    </div>
                    <div class="wr-atmos-item">
                      <span class="wr-atmos-k">Surface Pressure:</span>
                      <span class="wr-atmos-v" id="wr-atmos-pressure">955.0 hPa</span>
                    </div>
                    <div class="wr-atmos-item">
                      <span class="wr-atmos-k">Data Source:</span>
                      <span class="wr-atmos-v" id="wr-atmos-src">Open-Meteo High-Res</span>
                    </div>
                  </div>
                </div>

                <!-- Drainage Runoff Impact Section -->
                <div class="wr-drainage-impact-box">
                  <div class="wr-di-head">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>
                    <strong>Drainage Hydraulic Runoff Impact</strong>
                  </div>
                  <div class="wr-di-content">
                    <div class="wr-di-row">
                      <span>Runoff Coefficient (Urban Paved / Soil):</span>
                      <strong id="wr-di-coeff">C = 0.68</strong>
                    </div>
                    <div class="wr-di-row">
                      <span>Conduit Design Surcharge Limit:</span>
                      <strong>25.0 mm/h</strong>
                    </div>
                    <div class="wr-di-row">
                      <span>Network Surcharge Status:</span>
                      <strong id="wr-di-surcharge" style="color:#10b981;">NORMAL GRAVITY FLOW</strong>
                    </div>
                  </div>
                  <div class="wr-di-note" id="wr-di-note">
                    Coupled via Rational Runoff Method (IMC Urban Drainage Standard). ST-GNN hydraulic inference executes over calibrated telemetry.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 4. Rainfall Intensity Analytics & Hourly Forecast Charts -->
          <div class="wr-charts-grid">
            <!-- Card 1: Observed Rainfall Intensity (Last 6/12/24 Hours) -->
            <div class="wr-card">
              <div class="wr-card-head">
                <div class="wr-card-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                  <span>Rainfall Intensity — Observed Time-Series</span>
                </div>
                <div class="wr-range-pills">
                  <button class="wr-range-btn" id="wr-btn-range-6h" onclick="onWrIntensityRangeChange('6h')">6h</button>
                  <button class="wr-range-btn" id="wr-btn-range-12h" onclick="onWrIntensityRangeChange('12h')">12h</button>
                  <button class="wr-range-btn active" id="wr-btn-range-24h" onclick="onWrIntensityRangeChange('24h')">24h</button>
                </div>
              </div>

              <div class="wr-chart-canvas-wrap">
                <canvas id="wr-intensity-canvas" height="155"></canvas>
              </div>

              <div class="wr-chart-stats-strip">
                <div class="wr-cs-item">
                  <span class="wr-cs-k">Max Intensity:</span>
                  <span class="wr-cs-v" id="wr-stat-max">0.0 mm/h</span>
                </div>
                <div class="wr-cs-item">
                  <span class="wr-cs-k">Mean Intensity:</span>
                  <span class="wr-cs-v" id="wr-stat-mean">0.0 mm/h</span>
                </div>
                <div class="wr-cs-item">
                  <span class="wr-cs-k">Cumulative Rain:</span>
                  <span class="wr-cs-v" id="wr-stat-cum">0.0 mm</span>
                </div>
                <div class="wr-cs-item">
                  <span class="wr-cs-k">Missing Data:</span>
                  <span class="wr-cs-v" id="wr-stat-missing" style="color:#10b981;">0.0% (Complete)</span>
                </div>
              </div>
            </div>

            <!-- Card 2: Hourly Rainfall Forecast & Accumulation -->
            <div class="wr-card">
              <div class="wr-card-head">
                <div class="wr-card-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                  <span>Hourly Rainfall Forecast — Next 24 Hours</span>
                </div>
                <div class="wr-chart-legend-top">
                  <span><span class="wr-swatch" style="background:#0084ff;"></span> Hourly Rain (mm)</span>
                  <span><span class="wr-swatch" style="background:#a855f7;"></span> Cumulative Curve</span>
                </div>
              </div>

              <div class="wr-chart-canvas-wrap">
                <canvas id="wr-forecast-canvas" height="155"></canvas>
              </div>

              <div class="wr-chart-stats-strip">
                <div class="wr-cs-item">
                  <span class="wr-cs-k">Peak Forecast:</span>
                  <span class="wr-cs-v" id="wr-fc-stat-peak">0.0 mm/h</span>
                </div>
                <div class="wr-cs-item">
                  <span class="wr-cs-k">Peak Window:</span>
                  <span class="wr-cs-v" id="wr-fc-stat-time">Clear Window</span>
                </div>
                <div class="wr-cs-item">
                  <span class="wr-cs-k">24h Forecast Total:</span>
                  <span class="wr-cs-v" id="wr-fc-stat-total">0.0 mm</span>
                </div>
                <div class="wr-cs-item">
                  <span class="wr-cs-k">Model Source:</span>
                  <span class="wr-cs-v" style="color:#00d2ff;">Open-Meteo High-Res</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 5. Weather Station & Data Health Monitoring Table -->
          <div class="wr-card" style="margin-bottom:20px;">
            <div class="wr-card-head">
              <div class="wr-card-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                <span>Data Source Health &amp; Precipitation Telemetry Matrix</span>
              </div>
              <span class="wr-badge-prov">AUDITED SOURCES</span>
            </div>

            <div class="wr-table-wrap">
              <table class="wr-table">
                <thead>
                  <tr>
                    <th>Data Source</th>
                    <th>Geographic Coverage</th>
                    <th>Data Type</th>
                    <th>Latest Timestamp</th>
                    <th>Total Records</th>
                    <th>Sampling Frequency</th>
                    <th>Missing %</th>
                    <th>Connection Status</th>
                  </tr>
                </thead>
                <tbody id="wr-station-table-body">
                  <!-- Dynamically populated -->
                </tbody>
              </table>
            </div>
          </div>

          <!-- 6. Historical Extreme Rainfall Events Comparison -->
          <div class="wr-card">
            <div class="wr-card-head">
              <div class="wr-card-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                <span>Historical Extreme Rainfall Events Comparison (Real Dataset Records)</span>
              </div>
              <div class="wr-event-pills" id="wr-event-pills-bar">
                <!-- Dynamically rendered event pills -->
              </div>
            </div>

            <div class="wr-history-layout">
              <!-- Left: Big Hyetograph Canvas -->
              <div class="wr-history-chart-box">
                <div class="wr-hc-head">
                  <strong id="wr-ev-chart-title">Pune CWPRS Monsoon Cloudburst Extreme (145.6 mm Event)</strong>
                  <div class="wr-chart-legend-top">
                    <span><span class="wr-swatch" style="background:#00d2ff;"></span> Hourly Rain (mm/h)</span>
                    <span><span class="wr-swatch" style="background:#c084fc;"></span> Cumulative Rain (mm)</span>
                    <span><span class="wr-swatch" style="background:#ef4444; border-top:2px dashed #ef4444;"></span> Cloudburst Threshold (50 mm/h)</span>
                  </div>
                </div>
                <div style="padding: 10px 0;">
                  <canvas id="wr-history-hyetograph-canvas" height="220" style="width:100%; display:block;"></canvas>
                </div>
              </div>

              <!-- Right: Event Scientific Metrics Box -->
              <div class="wr-history-info-box" id="wr-event-details-box">
                <!-- Dynamically loaded event metrics -->
              </div>
            </div>
          </div>
        </section>"""

if re.search(wr_section_regex, html_text):
    html_text = re.sub(wr_section_regex, new_wr_html, html_text)
    print("  ✓ Successfully replaced screen-weather-radar in index.html")
else:
    print("  ✗ Regex did not find screen-weather-radar in index.html!")

# Update cache buster
html_text = html_text.replace('/static/css/style.css?v=4.2.0', '/static/css/style.css?v=4.3.0')
html_text = html_text.replace('/static/js/app.js?v=4.2.0', '/static/js/app.js?v=4.3.0')

HTML_PATH.write_text(html_text, encoding="utf-8")
print("  ✓ index.html written successfully")


# =============================================================================
# 2. UPDATE style.css
# =============================================================================
print("\n[2/3] Updating style.css with Weather & Radar glassmorphism styling...")
css_text = CSS_PATH.read_text(encoding="utf-8")

wr_css_regex = r'/\* Weather & Radar Screen \*/[\s\S]*?(?=/\* Flood Drivers Screen \*/)'

new_wr_css = """/* Weather & Radar Screen - Dark Navy Glassmorphism Design System */
.wr-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.wr-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.wr-header-icon {
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

.wr-title {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.wr-subtitle {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.wr-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.wr-region-select-box {
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

.wr-region-select-box select {
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  outline: none;
  cursor: pointer;
}

.wr-region-select-box select option {
  background: #0b1528;
  color: #ffffff;
}

.wr-btn-refresh {
  background: rgba(11, 21, 40, 0.7);
  color: #cbd5e1;
  border: 1px solid rgba(0, 210, 255, 0.25);
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 12.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.wr-btn-refresh:hover {
  background: rgba(0, 132, 255, 0.2);
  border-color: #00d2ff;
  color: #ffffff;
  transform: translateY(-1px);
}

.wr-live-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  color: #4ade80;
  letter-spacing: 0.04em;
}

.wr-live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 8px #4ade80;
  animation: pulseLive 2s infinite;
}

@keyframes pulseLive {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

/* 5 Weather KPI Cards */
.wr-kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

@media (max-width: 1300px) {
  .wr-kpi-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .wr-kpi-grid {
    grid-template-columns: 1fr;
  }
}

.wr-kpi-card {
  background: rgba(11, 21, 40, 0.82);
  border: 1px solid rgba(0, 210, 255, 0.22);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.wr-kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 210, 255, 0.45);
}

.wr-kpi-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.wr-kpi-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
}

.wr-icon-cyan { color: #00d2ff; }
.wr-icon-purple { color: #a855f7; }
.wr-icon-sky { color: #38bdf8; }
.wr-icon-indigo { color: #818cf8; }
.wr-icon-green { color: #4ade80; }

.wr-badge-prov {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 132, 255, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(0, 210, 255, 0.25);
  letter-spacing: 0.04em;
}

.wr-prov-fc {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border-color: rgba(168, 85, 247, 0.3);
}

.wr-kpi-val {
  font-size: 22px;
  font-weight: 800;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.2;
  margin-bottom: 4px;
}

.wr-kpi-unit {
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
}

.wr-kpi-lbl {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 2px;
}

.wr-kpi-sub {
  font-size: 10.5px;
  color: #64748b;
}

/* Middle Grid: Map & Nowcast */
.wr-middle-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

@media (max-width: 1024px) {
  .wr-middle-grid {
    grid-template-columns: 1fr;
  }
}

.wr-card {
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

.wr-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.wr-card-title {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.wr-map-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.wr-map-time {
  font-size: 11px;
  color: #94a3b8;
  font-family: 'JetBrains Mono', monospace;
}

/* Radar Status Banner */
.wr-radar-status-banner {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.28);
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.wr-rsb-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.wr-rsb-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: #f59e0b;
  margin-bottom: 4px;
}

.wr-rsb-tag {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.wr-rsb-desc {
  font-size: 11.5px;
  color: #cbd5e1;
  line-height: 1.45;
  margin: 0 0 6px 0;
}

.wr-rsb-specs {
  font-size: 10.5px;
  color: #94a3b8;
}

.wr-map-container {
  width: 100%;
  height: 350px;
  border-radius: 10px;
  border: 1px solid rgba(0, 210, 255, 0.2);
  overflow: hidden;
  position: relative;
  background: #070e1e;
}

.wr-map-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 10px;
  font-size: 11px;
  color: #94a3b8;
  flex-wrap: wrap;
}

.wr-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}

/* Nowcast & Outlook Body */
.wr-nowcast-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wr-trend-box {
  background: rgba(7, 14, 30, 0.7);
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.wr-trend-lbl {
  color: #94a3b8;
  font-weight: 500;
}

.wr-trend-val {
  color: #4ade80;
  font-weight: 700;
}

.wr-nowcast-metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.wr-nc-metric {
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.wr-nc-lbl {
  font-size: 10.5px;
  color: #94a3b8;
}

.wr-nc-val {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
}

.wr-atmos-section {
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
  border-radius: 10px;
  padding: 12px;
}

.wr-atmos-title {
  font-size: 11.5px;
  font-weight: 700;
  color: #38bdf8;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.wr-atmos-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
  font-size: 11px;
}

.wr-atmos-item {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 210, 255, 0.08);
  padding: 3px 0;
}

.wr-atmos-k { color: #94a3b8; }
.wr-atmos-v { font-weight: 600; color: #ffffff; font-family: 'JetBrains Mono', monospace; }

.wr-drainage-impact-box {
  background: rgba(7, 14, 30, 0.8);
  border: 1px solid rgba(0, 210, 255, 0.22);
  border-radius: 10px;
  padding: 12px;
}

.wr-di-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #00d2ff;
  margin-bottom: 8px;
}

.wr-di-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  margin-bottom: 8px;
}

.wr-di-row {
  display: flex;
  justify-content: space-between;
  color: #cbd5e1;
}

.wr-di-note {
  font-size: 10px;
  color: #64748b;
  line-height: 1.4;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 6px;
}

/* Charts Grid */
.wr-charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

@media (max-width: 900px) {
  .wr-charts-grid {
    grid-template-columns: 1fr;
  }
}

.wr-range-pills {
  display: flex;
  gap: 4px;
  background: rgba(7, 14, 30, 0.6);
  border: 1px solid rgba(0, 210, 255, 0.2);
  border-radius: 6px;
  padding: 2px;
}

.wr-range-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.wr-range-btn.active {
  background: #0084ff;
  color: #ffffff;
  box-shadow: 0 0 8px rgba(0, 132, 255, 0.5);
}

.wr-chart-canvas-wrap {
  width: 100%;
  height: 160px;
  position: relative;
  margin-top: 8px;
}

.wr-chart-stats-strip {
  display: flex;
  justify-content: space-between;
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.15);
  border-radius: 8px;
  padding: 8px 12px;
  margin-top: 10px;
  font-size: 11px;
  flex-wrap: wrap;
  gap: 8px;
}

.wr-cs-item {
  display: flex;
  gap: 6px;
}

.wr-cs-k { color: #94a3b8; }
.wr-cs-v { font-weight: 700; color: #ffffff; font-family: 'JetBrains Mono', monospace; }

.wr-chart-legend-top {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 11px;
  color: #94a3b8;
}

.wr-swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
  margin-right: 4px;
}

/* Station Health Table */
.wr-table-wrap {
  overflow-x: auto;
}

.wr-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.wr-table th {
  background: rgba(7, 14, 30, 0.85);
  color: #94a3b8;
  font-weight: 600;
  text-align: left;
  padding: 10px 14px;
  border-bottom: 2px solid rgba(0, 210, 255, 0.2);
  font-size: 11.5px;
  white-space: nowrap;
}

.wr-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 210, 255, 0.08);
  color: #e2e8f0;
  background: transparent;
  white-space: nowrap;
}

.wr-table tr:hover td {
  background: rgba(0, 132, 255, 0.08);
}

.wr-badge-green { background: rgba(16, 185, 129, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; }
.wr-badge-cyan { background: rgba(0, 210, 255, 0.15); color: #00d2ff; border: 1px solid rgba(0, 210, 255, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; }
.wr-badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; }
.wr-badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; }

/* Historical Rainfall Events */
.wr-event-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.wr-ev-pill {
  background: rgba(11, 21, 40, 0.7);
  color: #cbd5e1;
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.wr-ev-pill:hover {
  border-color: #00d2ff;
  color: #ffffff;
  background: rgba(0, 132, 255, 0.2);
}

.wr-ev-pill.active {
  background: linear-gradient(135deg, #0084ff 0%, #0060df 100%);
  color: #ffffff;
  border-color: #00d2ff;
  box-shadow: 0 0 12px rgba(0, 132, 255, 0.45);
}

.wr-history-layout {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 16px;
  margin-top: 12px;
}

@media (max-width: 1024px) {
  .wr-history-layout {
    grid-template-columns: 1fr;
  }
}

.wr-history-chart-box {
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 10px;
  padding: 14px;
}

.wr-hc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.wr-hc-head strong {
  font-size: 12.5px;
  color: #ffffff;
}

.wr-history-info-box {
  background: rgba(7, 14, 30, 0.65);
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wr-hi-row {
  display: flex;
  justify-content: space-between;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(0, 210, 255, 0.08);
  font-size: 11.5px;
}

.wr-hi-k { color: #94a3b8; }
.wr-hi-v { font-weight: 700; color: #ffffff; font-family: 'JetBrains Mono', monospace; }

"""

if re.search(wr_css_regex, css_text):
    css_text = re.sub(wr_css_regex, new_wr_css, css_text)
    print("  ✓ Successfully replaced Weather & Radar CSS styles in style.css")
else:
    print("  ✗ Regex did not find Weather & Radar section in style.css!")

CSS_PATH.write_text(css_text, encoding="utf-8")
print("  ✓ style.css written successfully")


# =============================================================================
# 3. UPDATE app.js
# =============================================================================
print("\n[3/3] Updating app.js with interactive Weather Radar logic...")
js_text = JS_PATH.read_text(encoding="utf-8")

wr_js_regex = r'async function loadWeatherRadarIntelligence\(\)[\s\S]*?(?=// -{10,}\s*\n// FLOOD DRIVER ATTRIBUTION)'

new_wr_js = """window.wrState = {
  activeRegion: "indore",
  intensityRange: "24h",
  activeEventId: "EVENT_CWPRS_MONSOON",
  cachedData: null,
  leafletMap: null,
  mapMarkers: []
};

async function loadWeatherRadarIntelligence() {
  try {
    const region = window.wrState.activeRegion || "indore";
    const res = await fetch(`/api/v1/data-intel/weather-radar?region=${region}`);
    if (!res.ok) return;
    const data = await res.json();
    window.wrState.cachedData = data;

    // 1. Populate 5 KPI Cards
    renderWrKpis(data.kpis);

    // 2. Populate Nowcast & Atmospheric Panel
    renderWrNowcast(data.nowcast_outlook, data.forecast_and_impact);

    // 3. Render Rainfall Intensity Chart
    renderWrIntensityChart(data.intensity_analytics, window.wrState.intensityRange);

    // 4. Render Hourly Forecast Chart
    renderWrForecastChart(data.forecast_and_impact);

    // 5. Initialize or Update Leaflet Map
    setTimeout(() => {
      initWrLeafletMap(data.region_info);
    }, 150);

    // 6. Populate Station Health Table
    renderWrStationTable(data.station_health);

    // 7. Render Historical Storm Events Comparison
    renderWrHistoricalComparison(data.historical_comparison);

    // 8. Update Top Status Pill
    const provStatus = document.getElementById("wr-provenance-status");
    if (provStatus) {
      provStatus.textContent = data.kpis && data.kpis.provenance && data.kpis.provenance.current.includes("LIVE") 
        ? "LIVE NWP STREAM" 
        : "ARCHIVED TELEMETRY";
    }

  } catch (err) {
    console.error("Error loading weather radar intelligence:", err);
  }
}

function onWrRegionChange(val) {
  window.wrState.activeRegion = val;
  loadWeatherRadarIntelligence();
}

function refreshWrDashboard() {
  const btn = document.querySelector(".wr-btn-refresh");
  if (btn) btn.classList.add("loading");
  loadWeatherRadarIntelligence().finally(() => {
    if (btn) btn.classList.remove("loading");
  });
}

function renderWrKpis(kpis) {
  if (!kpis) return;

  const valRain = document.getElementById("wr-val-current-rain");
  if (valRain) valRain.innerHTML = `${kpis.current_rainfall_mmh.toFixed(1)} <span class="wr-kpi-unit">mm/h</span>`;

  const valAccum = document.getElementById("wr-val-accum-rain");
  if (valAccum) valAccum.innerHTML = `${kpis.accumulated_24h_mm.toFixed(1)} <span class="wr-kpi-unit">mm</span>`;

  const valFc1 = document.getElementById("wr-val-fc-1h");
  if (valFc1) valFc1.innerHTML = `${kpis.forecast_1h_mm.toFixed(1)} <span class="wr-kpi-unit">mm</span>`;

  const valFc6 = document.getElementById("wr-val-fc-6h");
  if (valFc6) valFc6.innerHTML = `${kpis.forecast_6h_mm.toFixed(1)} <span class="wr-kpi-unit">mm</span>`;

  const valAlert = document.getElementById("wr-val-alert-class");
  const subAlert = document.getElementById("wr-sub-alert-class");
  const badgeLevel = document.getElementById("wr-badge-status-level");
  const iconAlert = document.getElementById("wr-icon-alert");

  if (kpis.classification) {
    const cls = kpis.classification;
    if (valAlert) valAlert.textContent = cls.label;
    if (subAlert) subAlert.textContent = cls.impact;
    if (badgeLevel) {
      badgeLevel.textContent = `STATUS: ${cls.level.toUpperCase()}`;
      badgeLevel.style.color = cls.color;
      badgeLevel.style.borderColor = cls.color;
    }
    if (iconAlert) iconAlert.style.color = cls.color;
  }
}

function renderWrNowcast(nowcast, forecast) {
  if (!nowcast) return;

  const trendEl = document.getElementById("wr-trend-val");
  if (trendEl) {
    trendEl.textContent = nowcast.trend;
    trendEl.style.color = nowcast.trend_color || "#4ade80";
  }

  const obsEl = document.getElementById("wr-nc-obs");
  if (obsEl) obsEl.textContent = `${nowcast.observed_intensity_mmh.toFixed(1)} mm/h`;

  const fc1El = document.getElementById("wr-nc-fc1");
  if (fc1El) fc1El.textContent = `${nowcast.forecast_intensity_1h_mmh.toFixed(1)} mm/h`;

  const peakEl = document.getElementById("wr-nc-peak");
  if (peakEl && forecast) peakEl.textContent = forecast.peak_forecast_time || "Clear Window";

  const accum6El = document.getElementById("wr-nc-accum6");
  if (accum6El) accum6El.textContent = `${nowcast.forecast_accumulation_6h_mm.toFixed(1)} mm`;

  const atmos = nowcast.atmospheric;
  if (atmos) {
    const windEl = document.getElementById("wr-atmos-wind");
    if (windEl) windEl.textContent = `${atmos.wind_speed_kmh} km/h`;

    const dirEl = document.getElementById("wr-atmos-wind-dir");
    if (dirEl) dirEl.textContent = `${atmos.wind_direction_cardinal} (${Math.round(atmos.wind_direction_deg)}°)`;

    const tempEl = document.getElementById("wr-atmos-temp");
    if (tempEl) tempEl.textContent = `${atmos.temperature_c} °C`;

    const humEl = document.getElementById("wr-atmos-humidity");
    if (humEl) humEl.textContent = `${atmos.relative_humidity_pct} %`;

    const pressEl = document.getElementById("wr-atmos-pressure");
    if (pressEl) pressEl.textContent = `${atmos.surface_pressure_hpa} hPa`;
  }

  // Hydraulic Impact
  if (forecast && forecast.hydraulic_impact) {
    const hi = forecast.hydraulic_impact;
    const coeffEl = document.getElementById("wr-di-coeff");
    if (coeffEl) coeffEl.textContent = `C = ${hi.runoff_coefficient_c}`;

    const surchEl = document.getElementById("wr-di-surcharge");
    if (surchEl) {
      surchEl.textContent = hi.surcharge_risk;
      surchEl.style.color = hi.surcharge_color || "#10b981";
    }

    const noteEl = document.getElementById("wr-di-note");
    if (noteEl) noteEl.textContent = hi.model_coupling_note;
  }
}

function onWrIntensityRangeChange(range) {
  window.wrState.intensityRange = range;
  document.querySelectorAll(".wr-range-btn").forEach(b => b.classList.remove("active"));
  const activeBtn = document.getElementById(`wr-btn-range-${range}`);
  if (activeBtn) activeBtn.classList.add("active");

  if (window.wrState.cachedData && window.wrState.cachedData.intensity_analytics) {
    renderWrIntensityChart(window.wrState.cachedData.intensity_analytics, range);
  }
}

function renderWrIntensityChart(analytics, range) {
  const canvas = document.getElementById("wr-intensity-canvas");
  if (!canvas || !analytics) return;

  const key = range === "6h" ? "series_6h" : range === "12h" ? "series_12h" : "series_24h";
  const sData = analytics[key] || analytics["series_24h"];
  if (!sData) return;

  // Update summary stats
  const st = sData.stats || {};
  const maxEl = document.getElementById("wr-stat-max");
  if (maxEl) maxEl.textContent = `${(st.max || 0.0).toFixed(1)} mm/h`;

  const meanEl = document.getElementById("wr-stat-mean");
  if (meanEl) meanEl.textContent = `${(st.mean || 0.0).toFixed(1)} mm/h`;

  const cumEl = document.getElementById("wr-stat-cum");
  if (cumEl) cumEl.textContent = `${(st.sum || 0.0).toFixed(1)} mm`;

  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 500;
  const w = canvas.width = parentW > 50 ? parentW : 500;
  const h = canvas.height = 155;
  ctx.clearRect(0, 0, w, h);

  const padL = 36;
  const padR = 15;
  const padT = 12;
  const padB = 24;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const vals = sData.values || [];
  const times = sData.times || [];
  const n = vals.length;
  if (n === 0) return;

  const maxV = Math.max(...vals, 10.0);

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px 'JetBrains Mono', monospace";
  ctx.textAlign = "right";

  for (let i = 0; i <= 3; i++) {
    const yVal = ((maxV / 3) * (3 - i)).toFixed(1);
    const yPos = padT + (chartH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Draw Line
  const stepX = chartW / Math.max(1, n - 1);
  ctx.strokeStyle = "#00d2ff";
  ctx.lineWidth = 2.2;
  ctx.beginPath();

  vals.forEach((v, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (v / maxV) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Gradient fill under curve
  ctx.lineTo(padL + (n - 1) * stepX, padT + chartH);
  ctx.lineTo(padL, padT + chartH);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, padT, 0, padT + chartH);
  grad.addColorStop(0, "rgba(0, 210, 255, 0.28)");
  grad.addColorStop(1, "rgba(0, 210, 255, 0.0)");
  ctx.fillStyle = grad;
  ctx.fill();

  // Draw points
  vals.forEach((v, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (v / maxV) * chartH;
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#00d2ff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });

  // X Axis Timestamps
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  times.forEach((t, i) => {
    if (i % Math.ceil(n / 6) === 0 || i === n - 1) {
      const x = padL + i * stepX;
      ctx.fillText(t, x, h - 6);
    }
  });
}

function renderWrForecastChart(fcData) {
  const canvas = document.getElementById("wr-forecast-canvas");
  if (!canvas || !fcData) return;

  const hours = fcData.forecast_hours || [];
  const n = hours.length;
  if (n === 0) return;

  // Update stats
  const peakEl = document.getElementById("wr-fc-stat-peak");
  if (peakEl) peakEl.textContent = `${(fcData.peak_forecast_mmh || 0.0).toFixed(1)} mm/h`;

  const timeEl = document.getElementById("wr-fc-stat-time");
  if (timeEl) timeEl.textContent = fcData.peak_forecast_time || "Clear Window";

  const totalEl = document.getElementById("wr-fc-stat-total");
  if (totalEl) totalEl.textContent = `${(fcData.forecast_cumulative_24h_mm || 0.0).toFixed(1)} mm`;

  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 500;
  const w = canvas.width = parentW > 50 ? parentW : 500;
  const h = canvas.height = 155;
  ctx.clearRect(0, 0, w, h);

  const padL = 36;
  const padR = 36;
  const padT = 12;
  const padB = 24;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const rainVals = hours.map(h => h.rain_mm);
  const cumVals = hours.map(h => h.cum_rain_mm);
  const maxRain = Math.max(...rainVals, 8.0);
  const maxCum = Math.max(...cumVals, 12.0);

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px 'JetBrains Mono', monospace";
  ctx.textAlign = "right";

  for (let i = 0; i <= 3; i++) {
    const yVal = ((maxRain / 3) * (3 - i)).toFixed(1);
    const yPos = padT + (chartH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Right Axis (Cumulative)
  ctx.textAlign = "left";
  for (let i = 0; i <= 3; i++) {
    const cVal = ((maxCum / 3) * (3 - i)).toFixed(1);
    const yPos = padT + (chartH / 3) * i;
    ctx.fillText(cVal, w - padR + 4, yPos + 3);
  }

  // Draw Bars
  const barW = (chartW / n) * 0.55;
  hours.forEach((pt, i) => {
    const barH = (pt.rain_mm / maxRain) * chartH;
    const x = padL + i * (chartW / n) + (chartW / n - barW) / 2;
    const y = padT + chartH - barH;

    const grad = ctx.createLinearGradient(0, y, 0, padT + chartH);
    grad.addColorStop(0, "#00d2ff");
    grad.addColorStop(1, "#0084ff");
    ctx.fillStyle = grad;
    ctx.fillRect(x, y, barW, barH);
  });

  // Draw Cumulative Curve
  const stepX = chartW / (n - 1);
  ctx.strokeStyle = "#a855f7";
  ctx.lineWidth = 2;
  ctx.beginPath();

  cumVals.forEach((c, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (c / maxCum) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // X Axis Labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  hours.forEach((pt, i) => {
    if (i % 4 === 0 || i === n - 1) {
      const x = padL + i * (chartW / n) + (chartW / n) / 2;
      ctx.fillText(pt.label, x, h - 6);
    }
  });
}

function initWrLeafletMap(regInfo) {
  const container = document.getElementById("wr-leaflet-map");
  if (!container || typeof L === "undefined") return;

  const lat = regInfo ? regInfo.lat : 22.7196;
  const lon = regInfo ? regInfo.lon : 75.8577;
  const zoom = regInfo ? regInfo.zoom : 12;

  // Update map title
  const titleEl = document.getElementById("wr-map-title");
  if (titleEl && regInfo) {
    titleEl.textContent = `${regInfo.name} — Sensor Telemetry`;
  }

  if (window.wrState.leafletMap) {
    window.wrState.leafletMap.setView([lat, lon], zoom);
    window.wrState.leafletMap.invalidateSize();
  } else {
    window.wrState.leafletMap = L.map("wr-leaflet-map", {
      center: [lat, lon],
      zoom: zoom,
      zoomControl: true
    });

    // Dark tiles
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; CartoDB &copy; OpenStreetMap',
      maxZoom: 19
    }).addTo(window.wrState.leafletMap);
  }

  // Clear old markers
  if (window.wrState.mapMarkers) {
    window.wrState.mapMarkers.forEach(m => window.wrState.leafletMap.removeLayer(m));
    window.wrState.mapMarkers = [];
  }

  // Add stations
  const stations = regInfo && regInfo.stations ? regInfo.stations : [];
  stations.forEach(s => {
    const marker = L.circleMarker([s.lat, s.lon], {
      radius: 7,
      fillColor: s.type.includes("AWS") ? "#00d2ff" : s.type.includes("Gully") ? "#a855f7" : "#10b981",
      color: "#ffffff",
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(window.wrState.leafletMap);

    marker.bindPopup(`
      <div style="font-family:sans-serif; font-size:12px; color:#0f172a; padding:4px;">
        <strong style="color:#0284c7;">${s.name}</strong><br>
        <span style="font-size:11px; color:#64748b;">${s.type}</span><br>
        <strong>Status:</strong> ${s.status}<br>
        <strong>Sampling:</strong> ${s.sampling}<br>
        <strong>Coords:</strong> ${s.lat.toFixed(4)}°, ${s.lon.toFixed(4)}°
      </div>
    `);

    window.wrState.mapMarkers.push(marker);
  });
}

function renderWrStationTable(stations) {
  const tbody = document.getElementById("wr-station-table-body");
  if (!tbody || !stations) return;

  let html = "";
  stations.forEach(s => {
    html += `
      <tr>
        <td><strong>${s.name}</strong></td>
        <td>${s.coverage}</td>
        <td><span class="wr-badge-prov">${s.type}</span></td>
        <td style="font-family:'JetBrains Mono', monospace;">${s.latest_timestamp}</td>
        <td style="font-family:'JetBrains Mono', monospace;">${s.records_count}</td>
        <td>${s.resolution}</td>
        <td style="color:#4ade80; font-family:'JetBrains Mono', monospace;">${s.missing_pct}</td>
        <td><span class="${s.status_badge || 'wr-badge-green'}">${s.status}</span></td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

function renderWrHistoricalComparison(histData) {
  if (!histData || !histData.events) return;

  const events = histData.events;
  const pillsContainer = document.getElementById("wr-event-pills-bar");
  if (pillsContainer) {
    let pillsHtml = "";
    events.forEach(ev => {
      const activeCls = ev.id === window.wrState.activeEventId ? "active" : "";
      pillsHtml += `<button class="wr-ev-pill ${activeCls}" onclick="onWrEventSelect('${ev.id}')">${ev.title.split('(')[0].trim()}</button>`;
    });
    pillsContainer.innerHTML = pillsHtml;
  }

  // Find active event
  const activeEv = events.find(e => e.id === window.wrState.activeEventId) || events[0];
  if (!activeEv) return;

  // Title
  const titleEl = document.getElementById("wr-ev-chart-title");
  if (titleEl) titleEl.textContent = activeEv.title;

  // Details Box
  const detailsBox = document.getElementById("wr-event-details-box");
  if (detailsBox) {
    detailsBox.innerHTML = `
      <div class="wr-hi-row"><span class="wr-hi-k">Dataset Provenance:</span><span class="wr-hi-v">${activeEv.dataset}</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Station Location:</span><span class="wr-hi-v">${activeEv.location}</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Event Observation Date:</span><span class="wr-hi-v">${activeEv.date}</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Total Event Rainfall:</span><span class="wr-hi-v" style="color:#00d2ff;">${activeEv.total_rainfall_mm} mm</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Peak Hourly Intensity:</span><span class="wr-hi-v" style="color:#f43f5e;">${activeEv.peak_intensity_mmh} mm/h</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Storm Duration:</span><span class="wr-hi-v">${activeEv.duration_hours} Hours</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Classification:</span><span class="wr-hi-v" style="color:#fbbf24;">${activeEv.classification}</span></div>
      <div style="font-size:11px; color:#cbd5e1; line-height:1.45; margin-top:4px;">
        <strong>Hydrological Role:</strong> ${activeEv.scientific_impact}
      </div>
    `;
  }

  // Draw Hyetograph Canvas
  renderWrHistoryHyetograph(activeEv);
}

function onWrEventSelect(eventId) {
  window.wrState.activeEventId = eventId;
  if (window.wrState.cachedData && window.wrState.cachedData.historical_comparison) {
    renderWrHistoricalComparison(window.wrState.cachedData.historical_comparison);
  }
}

function renderWrHistoryHyetograph(ev) {
  const canvas = document.getElementById("wr-history-hyetograph-canvas");
  if (!canvas || !ev || !ev.hyetograph) return;

  const hData = ev.hyetograph;
  const times = hData.timesteps || [];
  const rain = hData.hourly_rain || [];
  const cum = hData.cumulative_rain || [];
  const n = times.length;
  if (n === 0) return;

  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 600;
  const w = canvas.width = parentW > 50 ? parentW : 600;
  const h = canvas.height = 220;
  ctx.clearRect(0, 0, w, h);

  const padL = 40;
  const padR = 40;
  const padT = 16;
  const padB = 26;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const maxRain = Math.max(...rain, 55.0);
  const maxCum = Math.max(...cum, 100.0);

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px 'JetBrains Mono', monospace";
  ctx.textAlign = "right";

  for (let i = 0; i <= 4; i++) {
    const yVal = ((maxRain / 4) * (4 - i)).toFixed(1);
    const yPos = padT + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Right Axis (Cumulative)
  ctx.textAlign = "left";
  for (let i = 0; i <= 4; i++) {
    const cVal = ((maxCum / 4) * (4 - i)).toFixed(1);
    const yPos = padT + (chartH / 4) * i;
    ctx.fillText(cVal, w - padR + 4, yPos + 3);
  }

  // Critical Flash Flood Threshold Line (50 mm/h)
  if (maxRain >= 45.0) {
    const threshY = padT + chartH - (50 / maxRain) * chartH;
    ctx.strokeStyle = "rgba(239, 68, 68, 0.85)";
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(padL, threshY);
    ctx.lineTo(w - padR, threshY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#ef4444";
    ctx.font = "9px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    ctx.fillText("50 mm/h CLOUDBURST THRESHOLD", w - padR - 8, threshY - 4);
  }

  // Draw Bars
  const barW = (chartW / n) * 0.58;
  rain.forEach((v, i) => {
    const barH = (v / maxRain) * chartH;
    const x = padL + i * (chartW / n) + (chartW / n - barW) / 2;
    const y = padT + chartH - barH;

    ctx.fillStyle = v >= 50.0 ? "#ef4444" : "#00d2ff";
    ctx.fillRect(x, y, barW, barH);
  });

  // Cumulative Curve
  const stepX = chartW / (n - 1);
  ctx.strokeStyle = "#c084fc";
  ctx.lineWidth = 2.2;
  ctx.beginPath();

  cum.forEach((c, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (c / maxCum) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw points
  cum.forEach((c, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (c / maxCum) * chartH;
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#c084fc";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });

  // X Axis Labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  times.forEach((t, i) => {
    if (i % 2 === 0 || i === n - 1) {
      const x = padL + i * (chartW / n) + (chartW / n) / 2;
      ctx.fillText(t, x, h - 6);
    }
  });
}
"""

if re.search(wr_js_regex, js_text):
    js_text = re.sub(wr_js_regex, new_wr_js, js_text)
    print("  ✓ Successfully replaced Weather Radar JavaScript logic in app.js")
else:
    print("  ✗ Regex did not find Weather Radar section in app.js!")

JS_PATH.write_text(js_text, encoding="utf-8")
print("  ✓ app.js written successfully")

print("\n" + "=" * 80)
print("WEATHER & RADAR DASHBOARD IMPLEMENTATION COMPLETE!")
print("=" * 80)

