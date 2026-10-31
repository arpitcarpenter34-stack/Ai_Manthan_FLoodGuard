import re

html_template = """        <!-- =========================================================================
             TASK 4.1: WHITE-THEME DATASET EXPLORER & HYDROLOGICAL INTELLIGENCE CENTER
             Strict adherence to reference design: media_1793427602234_3a72ebdd.jpg
             ========================================================================= -->
        <section id="screen-explorer" class="screen-container" style="display: none;">
          <!-- 1. Header Banner -->
          <div class="wt-header-row">
            <div class="wt-header-left">
              <div class="wt-header-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2">
                  <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                  <polyline points="2 17 12 22 22 17"></polyline>
                  <polyline points="2 12 12 17 22 12"></polyline>
                </svg>
              </div>
              <div>
                <h2 class="wt-title">Dataset Explorer &amp; Flood Intelligence</h2>
                <p class="wt-subtitle">Explore datasets, engineer features, analyze hydrological drivers and build flood insights</p>
              </div>
            </div>
          </div>

          <!-- 2. Dataset Selector Bar -->
          <div class="wt-selector-row">
            <div class="wt-select-group">
              <label class="wt-select-label">Select Dataset <span class="wt-info-tooltip" title="Switch active dataset for analysis">ⓘ</span></label>
              <div class="wt-select-box">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2">
                  <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                  <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                </svg>
                <select id="de-dataset-select" onchange="onDeDatasetChange(this.value)">
                  <option value="blue_heart" selected>Blue Heart – Urban Catchment</option>
                  <option value="camels_hourly">CAMELS (Aroostook, US)</option>
                  <option value="usgs_potomac">USGS (Potomac, US)</option>
                  <option value="bellinge_swmm">Bellinge (Denmark)</option>
                  <option value="uwo_kearney">UWO (Canada)</option>
                  <option value="india_cwprs">CWPRS (India)</option>
                </select>
              </div>
            </div>
            
            <div class="wt-pills-group" id="de-pills-bar">
              <button class="wt-pill-btn active" data-ds="blue_heart" onclick="onDeDatasetPillClick('blue_heart')">Blue Heart<br><span class="wt-pill-sub">(UK)</span></button>
              <button class="wt-pill-btn" data-ds="camels_hourly" onclick="onDeDatasetPillClick('camels_hourly')">CAMELS<br><span class="wt-pill-sub">(Aroostook, US)</span></button>
              <button class="wt-pill-btn" data-ds="usgs_potomac" onclick="onDeDatasetPillClick('usgs_potomac')">USGS<br><span class="wt-pill-sub">(Potomac, US)</span></button>
              <button class="wt-pill-btn" data-ds="bellinge_swmm" onclick="onDeDatasetPillClick('bellinge_swmm')">Bellinge<br><span class="wt-pill-sub">(Denmark)</span></button>
              <button class="wt-pill-btn" data-ds="uwo_kearney" onclick="onDeDatasetPillClick('uwo_kearney')">UWO<br><span class="wt-pill-sub">(Canada)</span></button>
              <button class="wt-pill-btn" data-ds="india_cwprs" onclick="onDeDatasetPillClick('india_cwprs')">CWPRS<br><span class="wt-pill-sub">(India)</span></button>
            </div>
          </div>

          <!-- 3. Summary Card & 6 KPIs -->
          <div class="wt-summary-card">
            <div class="wt-summary-left">
              <div class="wt-thumb-container">
                <div class="wt-catchment-thumb" id="de-catchment-thumb">
                  <svg class="wt-thumb-art" viewBox="0 0 200 120" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#bae6fd"/><stop offset="100%" stop-color="#e0f2fe"/></linearGradient>
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
                    <path d="M40,85 L160,85 M50,85 L50,110 M150,85 L150,110" stroke="#f8fafc" stroke-width="3"/>
                  </svg>
                </div>
              </div>
              <div class="wt-summary-info">
                <h3 id="de-summary-title" class="wt-summary-title">Blue Heart Urban Catchment</h3>
                <div class="wt-summary-meta" id="de-summary-loc"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> <span id="de-val-loc">Rotterdam, Netherlands (UK Testbed)</span></div>
                <div class="wt-summary-meta" id="de-summary-period"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> <span id="de-val-period">Jun 2016 – Nov 2018</span></div>
                <div class="wt-summary-meta wt-tags" id="de-summary-tags"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> <span id="de-val-tags">Urban Drainage | Water Level | Rainfall</span></div>
              </div>
            </div>

            <!-- 6 KPI Cards -->
            <div class="wt-summary-kpis">
              <div class="wt-kpi-card">
                <div class="wt-kpi-icon wt-icon-purple">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                </div>
                <div class="wt-kpi-val" id="de-kpi-records">16,396</div>
                <div class="wt-kpi-lbl">Total Records</div>
              </div>
              <div class="wt-kpi-card">
                <div class="wt-kpi-icon wt-icon-cyan">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
                </div>
                <div class="wt-kpi-val" id="de-kpi-features">12</div>
                <div class="wt-kpi-lbl">Features</div>
              </div>
              <div class="wt-kpi-card">
                <div class="wt-kpi-icon wt-icon-magenta">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                </div>
                <div class="wt-kpi-val" id="de-kpi-nodes">7</div>
                <div class="wt-kpi-lbl">Sensors / Nodes</div>
              </div>
              <div class="wt-kpi-card">
                <div class="wt-kpi-icon wt-icon-sky">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                </div>
                <div class="wt-kpi-val" id="de-kpi-freq">5 min</div>
                <div class="wt-kpi-lbl">Sampling Frequency</div>
              </div>
              <div class="wt-kpi-card">
                <div class="wt-kpi-icon wt-icon-indigo">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                </div>
                <div class="wt-kpi-val" id="de-kpi-span">~ 2.4 Years</div>
                <div class="wt-kpi-lbl">Observation Period</div>
              </div>
              <div class="wt-kpi-card">
                <div class="wt-kpi-icon wt-icon-green">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                <div class="wt-kpi-val wt-val-green" id="de-kpi-status">Training Ready</div>
                <div class="wt-kpi-lbl" id="de-kpi-status-sub">Used for ST-GNN</div>
              </div>
            </div>
          </div>

          <!-- 4. Subnav Bar (6 Tabs) -->
          <div class="wt-subnav-bar">
            <button class="wt-subnav-tab active" id="de-tab-overview" onclick="switchDeTab('overview')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="12" width="4" height="8"/><rect x="10" y="8" width="4" height="12"/><rect x="17" y="4" width="4" height="16"/></svg>
              <span>Data Overview</span>
            </button>
            <button class="wt-subnav-tab" id="de-tab-features" onclick="switchDeTab('features')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <span>Feature Engineering Lab</span>
            </button>
            <button class="wt-subnav-tab" id="de-tab-relationships" onclick="switchDeTab('relationships')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12c.6 0 1.2-.4 1.4-1C4.3 8.2 6.1 6 8.5 6c3 0 4 4 6 4 2.5 0 4-3 6.5-3 1.4 0 2 1 2 1"/><path d="M2 18c.6 0 1.2-.4 1.4-1 1-2.8 2.8-5 5.1-5 3 0 4 4 6 4 2.5 0 4-3 6.5-3 1.4 0 2 1 2 1"/></svg>
              <span>Hydrological Relationships</span>
            </button>
            <button class="wt-subnav-tab" id="de-tab-fingerprint" onclick="switchDeTab('fingerprint')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12C2 6.5 6.5 2 12 2a10 10 0 0 1 8 4"/><path d="M5 19.5C5.5 18 6 15 6 12c0-.7.1-1.4.3-2"/><path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/><path d="M10 20c.5-1 1-2.5 1-4 0-.8.1-1.5.3-2.1"/><path d="M14 13.5a1.5 1.5 0 0 1 3 0c0 1.5-.5 3.5-1 5"/><path d="M17 10c0-1.7-.8-3.2-2-4.1"/><path d="M21.5 17c-.5-2-1.5-4-3-5.5"/></svg>
              <span>Flood Fingerprint</span>
            </button>
            <button class="wt-subnav-tab" id="de-tab-spatial" onclick="switchDeTab('spatial')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><line x1="9" y1="6" x2="15" y2="6"/><line x1="6" y1="9" x2="6" y2="15"/><line x1="18" y1="9" x2="18" y2="15"/><line x1="9" y1="18" x2="15" y2="18"/></svg>
              <span>Spatio-Temporal Analysis</span>
            </button>
            <button class="wt-subnav-tab" id="de-tab-model" onclick="switchDeTab('model')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>
              <span>Model &amp; Prediction Insights</span>
            </button>
          </div>

          <!-- =========================================================================
               TAB 1: DATA OVERVIEW (EXACT REPLICA OF REFERENCE DESIGN)
               ========================================================================= -->
          <div class="wt-pane active" id="de-pane-overview">
            <div class="wt-overview-grid">
              <!-- Card 1: Feature Distributions -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Feature Distributions</h4>
                  <div class="wt-card-action">
                    <select id="de-dist-feature-select" class="wt-card-select" onchange="onDeDistFeatureChange(this.value)">
                      <option value="rainfall">Rainfall Intensity (mm/h)</option>
                      <option value="water_level">Water Level Stage (m)</option>
                      <option value="upstream_inflow">Upstream Inflow (m³/s)</option>
                    </select>
                  </div>
                </div>
                <div class="wt-dist-layout">
                  <div class="wt-dist-chart">
                    <canvas id="de-canvas-histogram" width="220" height="145"></canvas>
                  </div>
                  <div class="wt-dist-stats" id="de-dist-stats-box">
                    <div class="wt-stat-row"><span class="wt-stat-k">Mean</span><span class="wt-stat-v" id="de-stat-mean">4.37</span></div>
                    <div class="wt-stat-row"><span class="wt-stat-k">Median</span><span class="wt-stat-v" id="de-stat-median">1.20</span></div>
                    <div class="wt-stat-row"><span class="wt-stat-k">Std Dev</span><span class="wt-stat-v" id="de-stat-std">6.92</span></div>
                    <div class="wt-stat-row"><span class="wt-stat-k">Q1 (25%)</span><span class="wt-stat-v" id="de-stat-q1">0.40</span></div>
                    <div class="wt-stat-row"><span class="wt-stat-k">Q3 (75%)</span><span class="wt-stat-v" id="de-stat-q3">5.10</span></div>
                  </div>
                </div>
              </div>

              <!-- Card 2: Feature Correlation Heatmap -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Feature Correlation Heatmap <span class="wt-info-tooltip" title="Pairwise Pearson / Spearman correlation matrix">ⓘ</span></h4>
                  <div class="wt-card-action">
                    <select id="de-corr-method-select" class="wt-card-select" onchange="onDeCorrMethodChange(this.value)">
                      <option value="pearson">Pearson</option>
                      <option value="spearman">Spearman</option>
                    </select>
                  </div>
                </div>
                <div class="wt-corr-layout">
                  <div class="wt-corr-grid" id="de-corr-matrix-container">
                    <!-- Dynamic Matrix Rows Injected -->
                  </div>
                  <div class="wt-corr-colorbar">
                    <span>1.0</span>
                    <div class="wt-colorbar-gradient"></div>
                    <span>0</span>
                    <div class="wt-colorbar-gradient" style="background: linear-gradient(to bottom, #ffffff, #3b82f6);"></div>
                    <span>-1.0</span>
                  </div>
                </div>
              </div>

              <!-- Card 3: Missing Data Analysis -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Missing Data Analysis</h4>
                  <span style="font-size:11px; color:#16a34a; font-weight:600;" id="de-missing-summary-badge">95.8% Complete</span>
                </div>
                <div class="wt-missing-grid-wrap" id="de-missing-grid-container">
                  <!-- Injected rows of temporal status -->
                </div>
                <div class="wt-missing-time-axis" id="de-missing-time-axis">
                  <span>Jun'16</span>
                  <span>Dec'16</span>
                  <span>Jun'17</span>
                  <span>Dec'17</span>
                  <span>Jun'18</span>
                  <span>Nov'18</span>
                </div>
                <div class="wt-missing-legend">
                  <div class="wt-mlegend-item"><div class="wt-mlegend-box" style="background:#86efac;"></div><span>Present (95.8%)</span></div>
                  <div class="wt-mlegend-item"><div class="wt-mlegend-box" style="background:#fde047;"></div><span>Missing (3.1%)</span></div>
                  <div class="wt-mlegend-item"><div class="wt-mlegend-box" style="background:#f87171;"></div><span>Outlier (1.1%)</span></div>
                </div>
              </div>

              <!-- Card 4: Time Series Analysis -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Time Series Analysis</h4>
                  <div class="wt-ts-controls">
                    <label><input type="checkbox" id="de-ts-chk-rain" checked onchange="renderDeTimeSeriesChart()"> Rainfall</label>
                    <label><input type="checkbox" id="de-ts-chk-level" checked onchange="renderDeTimeSeriesChart()"> Water Level</label>
                    <label><input type="checkbox" id="de-ts-chk-inflow" onchange="renderDeTimeSeriesChart()"> Inflow</label>
                    <select id="de-ts-range-select" class="wt-card-select" onchange="renderDeTimeSeriesChart()">
                      <option value="30d">Last 30 Days</option>
                      <option value="all">Full Series</option>
                    </select>
                  </div>
                </div>
                <div class="wt-chart-canvas-wrap">
                  <canvas id="de-canvas-timeseries" width="360" height="120"></canvas>
                </div>
                <div class="wt-chart-legend">
                  <div class="wt-clegend-item"><div class="wt-clegend-bar" style="background:#0284c7;"></div><span>Rainfall (mm/h)</span></div>
                  <div class="wt-clegend-item"><div class="wt-clegend-line" style="background:#06b6d4;"></div><span>Water Level (m)</span></div>
                </div>
              </div>

              <!-- Card 5: Feature Importance (ST-GNN) -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Feature Importance (ST-GNN)</h4>
                  <span class="wt-badge wt-badge-blue" id="de-fi-badge">Global XAI</span>
                </div>
                <div class="wt-fi-list" id="de-fi-list-container">
                  <!-- Injected horizontal bar items -->
                </div>
              </div>

              <!-- Card 6: Flood Response (Rainfall -> Water Level) -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Flood Response (Rainfall → Water Level) <span class="wt-info-tooltip" title="Impulse response lag cross-correlation">ⓘ</span></h4>
                  <div class="wt-fr-badge" id="de-fr-badge">Peak: 0.76 | Lag: ~ 15 min</div>
                </div>
                <div class="wt-chart-canvas-wrap">
                  <canvas id="de-canvas-flood-response" width="360" height="120"></canvas>
                </div>
                <div class="wt-chart-legend">
                  <div class="wt-clegend-item"><div class="wt-clegend-line" style="background:#c026d3;"></div><span>Cross-Correlation Lag Function (Rainfall → Water Level)</span></div>
                </div>
              </div>
            </div>

            <!-- Key Insights Strip (Matching Reference) -->
            <div class="wt-insights-strip" id="de-insights-strip">
              <div class="wt-insights-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>
                <span id="de-insights-title">Key Insights (Blue Heart)</span>
              </div>
              <div class="wt-insight-item" id="de-ins-1">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/></svg>
                <span>Rainfall strongly correlates with water level (r = 0.76)</span>
              </div>
              <div class="wt-insight-item" id="de-ins-2">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                <span>Response lag time ≈ 15 minutes</span>
              </div>
              <div class="wt-insight-item" id="de-ins-3">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12C2 6.5 6.5 2 12 2a10 10 0 0 1 8 4"/><path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/><path d="M14 13.5a1.5 1.5 0 0 1 3 0c0 1.5-.5 3.5-1 5"/></svg>
                <span>Current event matches historical flood pattern #3 (Similarity: 0.87)</span>
              </div>
              <div class="wt-insight-item" id="de-ins-4">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/></svg>
                <span>Node N4 &amp; N5 show highest flood influence (Propagation Risk: High)</span>
              </div>
              <div class="wt-insight-item" id="de-ins-5">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
                <span>Data quality: 95.8% (Training: 70% | Validation: 15% | Test: 15%)</span>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               TAB 2: FEATURE ENGINEERING LAB
               ========================================================================= -->
          <div class="wt-pane" id="de-pane-features">
            <div class="wt-card" style="margin-bottom:16px;">
              <div class="wt-card-head">
                <h4 class="wt-card-title">Feature Recipe Catalog &amp; Provenance Matrix</h4>
                <div style="font-size:12px; color:#64748b;">10 Certified Hydrological Features • Mathematical Formulation</div>
              </div>
              <div style="overflow-x:auto;">
                <table class="wt-table" id="de-fe-table">
                  <thead>
                    <tr>
                      <th>Feature Name</th>
                      <th>Mathematical Formula</th>
                      <th>Inputs &amp; Sensors</th>
                      <th>Unit</th>
                      <th>Category</th>
                      <th>Valid Records</th>
                      <th>Missing %</th>
                      <th>Training Status</th>
                    </tr>
                  </thead>
                  <tbody id="de-fe-tbody">
                    <!-- Populated dynamically -->
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Interactive Feature Generator Sandbox -->
            <div class="wt-card">
              <div class="wt-card-head">
                <h4 class="wt-card-title">Interactive Feature Synthesis Sandbox</h4>
                <span class="wt-badge wt-badge-green">Live Math Execution</span>
              </div>
              <div class="wt-sandbox-grid">
                <div>
                  <div class="wt-slider-row">
                    <div class="wt-slider-head"><span>Antecedent Rainfall R(t) [mm/h]:</span> <span id="de-sb-r-val">35.0 mm/h</span></div>
                    <input type="range" class="wt-slider" id="de-sb-r" min="0" max="100" value="35" oninput="runFeatureSandbox()">
                  </div>
                  <div class="wt-slider-row">
                    <div class="wt-slider-head"><span>Water Level Stage H(t-1) [m]:</span> <span id="de-sb-h1-val">0.45 m</span></div>
                    <input type="range" class="wt-slider" id="de-sb-h1" min="0" max="2" step="0.05" value="0.45" oninput="runFeatureSandbox()">
                  </div>
                  <div class="wt-slider-row">
                    <div class="wt-slider-head"><span>Current Stage H(t) [m]:</span> <span id="de-sb-h2-val">0.85 m</span></div>
                    <input type="range" class="wt-slider" id="de-sb-h2" min="0" max="2" step="0.05" value="0.85" oninput="runFeatureSandbox()">
                  </div>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:16px;">
                  <h5 style="margin:0 0 10px 0; font-size:13px; color:#0f172a;">Computed Derived Variables:</h5>
                  <div class="wt-stat-row"><span class="wt-stat-k">Rate of Rise (dh/dt):</span> <span class="wt-stat-v" id="de-sb-dhdt">+1.60 m/h</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Gully Surcharge Ratio (S):</span> <span class="wt-stat-v" id="de-sb-surch">0.57 (Elevated)</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Synthesized Antecedent Index (API):</span> <span class="wt-stat-v" id="de-sb-api">32.2 mm</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">GNN Readiness Classification:</span> <span class="wt-stat-v" style="color:#16a34a;">Valid Tensor Input</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               TAB 3: HYDROLOGICAL RELATIONSHIPS
               ========================================================================= -->
          <div class="wt-pane" id="de-pane-relationships">
            <div class="wt-overview-grid" style="grid-template-columns: 1fr 1fr;">
              <!-- Lead-Lag Cross Correlation -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Catchment Lead-Lag Impulse Response</h4>
                  <span class="wt-badge wt-badge-purple">Peak Lag: 15 min</span>
                </div>
                <div class="wt-chart-canvas-wrap" style="height:180px;">
                  <canvas id="de-canvas-rel-lag" width="400" height="180"></canvas>
                </div>
                <p style="font-size:12px; color:#64748b; margin-top:8px;" id="de-rel-desc">
                  Rapid impervious urban response: road-gully water levels reach peak stage 15 to 20 minutes following convective burst.
                </p>
              </div>

              <!-- Rainfall vs Water Rise Regression -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Precipitation vs Stage Rise Regression</h4>
                  <span class="wt-badge wt-badge-blue">R² = 0.912</span>
                </div>
                <div class="wt-chart-canvas-wrap" style="height:180px;">
                  <canvas id="de-canvas-rel-scatter" width="400" height="180"></canvas>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11.5px; color:#64748b; margin-top:8px;">
                  <span>Equation: <strong>ΔH = 0.41·R - 0.12</strong></span>
                  <span>Pearson Correlation: <strong>r = 0.76</strong></span>
                </div>
              </div>
            </div>

            <!-- Upstream to Downstream Propagation Card -->
            <div class="wt-card">
              <div class="wt-card-head">
                <h4 class="wt-card-title">Hydrodynamic Channel Flow Propagation</h4>
                <span class="wt-badge wt-badge-green">Kinematic Wave Translation</span>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap; padding:10px 0;">
                <div style="flex:1; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; text-align:center;">
                  <div style="font-size:11px; color:#64748b;">UPSTREAM GULLY</div>
                  <div style="font-size:15px; font-weight:700; color:#0f172a; margin:4px 0;" id="de-rel-upnode">ESH5B Star Rd (Node N1)</div>
                  <div style="font-size:11px; color:#0284c7;">Peak Inflow: 18.2 m³/s</div>
                </div>
                <div style="text-align:center;">
                  <div style="font-size:11px; color:#64748b; margin-bottom:4px;">TRAVEL TIME DELAY</div>
                  <div style="background:#e0f2fe; color:#0284c7; font-weight:700; padding:6px 14px; border-radius:20px; font-size:13px;" id="de-rel-delay">≈ 12 Minutes Delay</div>
                  <div style="font-size:10px; color:#94a3b8; margin-top:4px;">Attenuation: -14.5%</div>
                </div>
                <div style="flex:1; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; text-align:center;">
                  <div style="font-size:11px; color:#64748b;">DOWNSTREAM BOTTLENECK</div>
                  <div style="font-size:15px; font-weight:700; color:#0f172a; margin:4px 0;" id="de-rel-downnode">ESH8D Terminus Rd (Node N4)</div>
                  <div style="font-size:11px; color:#dc2626;">Surcharge Risk: Critical</div>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               TAB 4: FLOOD FINGERPRINT
               ========================================================================= -->
          <div class="wt-pane" id="de-pane-fingerprint">
            <div class="wt-card-head" style="margin-bottom:12px;">
              <h4 class="wt-card-title">Historical Extreme Storm Profiles &amp; Hydrograph Signatures</h4>
              <span class="wt-badge wt-badge-blue">Event Library</span>
            </div>
            <div class="wt-events-grid" id="de-events-grid">
              <!-- Dynamically populated event cards -->
            </div>

            <!-- Dynamic Hydrograph Comparison Canvas -->
            <div class="wt-card">
              <div class="wt-card-head">
                <h4 class="wt-card-title">Comparative Storm Hydrograph Overlay</h4>
                <div style="font-size:12px; color:#64748b;">Ground-Truth Historical Water Level Stage Traces</div>
              </div>
              <div class="wt-chart-canvas-wrap" style="height:160px;">
                <canvas id="de-canvas-fingerprint-overlay" width="800" height="160"></canvas>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               TAB 5: SPATIO-TEMPORAL ANALYSIS
               ========================================================================= -->
          <div class="wt-pane" id="de-pane-spatial">
            <div class="wt-overview-grid" style="grid-template-columns: 1.1fr 0.9fr;">
              <!-- Sensor Nodes Table -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Catchment Sensor Network Inventory</h4>
                  <span class="wt-badge wt-badge-green" id="de-spatial-nodes-count">7 Reporting Stations</span>
                </div>
                <div style="overflow-x:auto;">
                  <table class="wt-table">
                    <thead>
                      <tr>
                        <th>Node ID</th>
                        <th>Location</th>
                        <th>Coordinates</th>
                        <th>Elevation</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody id="de-spatial-tbody">
                      <!-- Dynamically populated -->
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Node-wise Stage Heatmap Grid -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Spatio-Temporal Water Stage Matrix</h4>
                  <span style="font-size:11px; color:#64748b;">Stage Height [m] across time</span>
                </div>
                <div id="de-spatial-heatmap-grid" style="display:flex; flex-direction:column; gap:6px; margin-top:8px;">
                  <!-- Dynamic spatio-temporal rows -->
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               TAB 6: MODEL & PREDICTION INSIGHTS
               ========================================================================= -->
          <div class="wt-pane" id="de-pane-model">
            <div class="wt-overview-grid" style="grid-template-columns: 1fr 1fr;">
              <!-- Architecture & Lineage -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">ST-GNN Checkpoint Provenance</h4>
                  <span class="wt-badge wt-badge-green" id="de-model-badge">PyTorch Trained</span>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px; font-size:12px;">
                  <div class="wt-stat-row"><span class="wt-stat-k">Architecture:</span> <span class="wt-stat-v" id="de-m-arch">Adaptive Gated ST-GNN</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Checkpoint Path:</span> <span class="wt-stat-v" style="font-size:10.5px;" id="de-m-path">checkpoints/blue_heart/v2/best_adaptive_st_gnn.pt</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Parameter Count:</span> <span class="wt-stat-v" id="de-m-params">233,941 weights</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Forecast Horizon:</span> <span class="wt-stat-v" id="de-m-horizon">+3 Hours (12 timesteps)</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Sequence Split:</span> <span class="wt-stat-v" id="de-m-split">Train: 5,085 | Val: 1,080 | Test: 1,093</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Test Set MAE:</span> <span class="wt-stat-v" style="color:#0284c7;" id="de-m-mae">0.09 cm (0.9 mm)</span></div>
                  <div class="wt-stat-row"><span class="wt-stat-k">Test Set RMSE / R²:</span> <span class="wt-stat-v" style="color:#16a34a;" id="de-m-r2">0.18 cm / 0.942</span></div>
                </div>
              </div>

              <!-- Loss Convergence Curve -->
              <div class="wt-card">
                <div class="wt-card-head">
                  <h4 class="wt-card-title">Training &amp; Validation Loss Dynamics</h4>
                  <span style="font-size:11px; color:#64748b;">Epochs 1 - 25</span>
                </div>
                <div class="wt-chart-canvas-wrap" style="height:170px;">
                  <canvas id="de-canvas-loss-curve" width="400" height="170"></canvas>
                </div>
                <div class="wt-chart-legend">
                  <div class="wt-clegend-item"><div class="wt-clegend-line" style="background:#0284c7;"></div><span>Training Loss</span></div>
                  <div class="wt-clegend-item"><div class="wt-clegend-line" style="background:#16a34a;"></div><span>Validation Loss</span></div>
                </div>
              </div>
            </div>

            <!-- Live Test Sequence Predictor -->
            <div class="wt-card" id="de-model-inference-card">
              <div class="wt-card-head">
                <h4 class="wt-card-title">Live Test Sequence Execution: Feed Tensor to Trained Model</h4>
                <span class="wt-badge wt-badge-blue">Direct Checkpoint Evaluator</span>
              </div>
              <div class="wt-infer-control-box">
                <label style="font-size:12.5px; font-weight:600; color:#1e293b;">Test Sample Index (0 – 1,092):</label>
                <input type="number" id="de-test-sample-input" value="0" min="0" max="1092" style="background:#ffffff; border:1px solid #cbd5e1; border-radius:6px; padding:6px 12px; font-family:'JetBrains Mono',monospace; width:90px;">
                <button class="wt-btn-primary" onclick="runLiveCheckpointInference()">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                  <span>Execute Checkpoint Inference (+3h Lead Time)</span>
                </button>
              </div>

              <!-- Live Execution Output Area -->
              <div id="de-live-inference-results">
                <div style="background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; padding:16px; color:#64748b; font-size:12px; text-align:center;">
                  Click <strong>Execute Checkpoint Inference</strong> to feed sample sequence tensor into the trained model and compare predicted vs observed stage heights.
                </div>
              </div>
            </div>
          </div>
        </section>
"""

with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Replace existing #screen-explorer
pattern = r'<!-- =+\s+SCREEN: DATASET EXPLORER.*?</section>'
match = re.search(pattern, content, re.DOTALL)
if match:
    new_content = content[:match.start()] + html_template + content[match.end():]
    with open("frontend/static/index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully replaced #screen-explorer in frontend/static/index.html")
else:
    print("Could not find regex match! Falling back to line-based replacement.")
    start_pos = content.find('<section id="screen-explorer"')
    end_pos = content.find('</section>', start_pos)
    if start_pos != -1 and end_pos != -1:
        # include comment before if any
        com_start = content.rfind('<!--', 0, start_pos)
        if com_start != -1 and 'DATASET EXPLORER' in content[com_start:start_pos]:
            start_pos = com_start
        new_content = content[:start_pos] + html_template + content[end_pos + len('</section>'):]
        with open("frontend/static/index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully replaced #screen-explorer via string pos in frontend/static/index.html")

