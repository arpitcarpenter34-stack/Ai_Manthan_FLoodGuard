"""
Patch frontend/static/index.html to add Task 3.8 Model Intelligence navigation and screen container.
"""

from pathlib import Path

HTML_FILE = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\static\index.html")

content = HTML_FILE.read_text(encoding="utf-8")

# 1. Add navbar link in view-home
home_nav_target = '<li><a class="nav-link" onclick="navigateTo(\'history\')">History</a></li>'
home_nav_replacement = '<li><a class="nav-link" onclick="navigateTo(\'history\')">History</a></li>\n          <li><a class="nav-link" onclick="navigateTo(\'model-intel\')">Model Intelligence</a></li>'

if 'onclick="navigateTo(\'model-intel\')"' not in content:
    content = content.replace(home_nav_target, home_nav_replacement, 1)
    print("Added Model Intelligence to view-home navbar")

# 2. Add sidebar item in view-app
sidebar_target = """          <li class="sidebar-item" id="nav-item-history" onclick="navigateTo('history')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span>History & Logs</span>
          </li>"""

sidebar_replacement = """          <li class="sidebar-item" id="nav-item-history" onclick="navigateTo('history')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span>History & Logs</span>
          </li>
          <li class="sidebar-item" id="nav-item-model-intel" onclick="navigateTo('model-intel')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
            <span>Model Intelligence & XAI</span>
          </li>"""

if 'id="nav-item-model-intel"' not in content:
    content = content.replace(sidebar_target, sidebar_replacement, 1)
    print("Added Model Intelligence to view-app sidebar")

# 3. Add #screen-model-intel section
screen_model_intel_html = """
        <!-- SCREEN 8: MODEL INTELLIGENCE & SCIENTIFIC EXPLAINABILITY (Task 3.8) -->
        <section id="screen-model-intel" class="screen-container" style="display: none;">
          <!-- Top Page Bar / Header -->
          <div class="mi-header-row">
            <div>
              <div class="mi-badge-head">
                <span class="mi-live-dot"></span>
                <span>SCIENTIFIC AI INTELLIGENCE & TRACEABILITY</span>
              </div>
              <h2 class="mi-page-title">AI Model Intelligence & Explainability Dashboard</h2>
              <p class="mi-page-subtitle">Ground-Truth Dataset Lineage • Checkpoint Provenance • Training Dynamics • Residual Diagnostics • Permutation XAI • What-If Scenario Lab</p>
            </div>
            <div class="mi-header-badges">
              <div class="mi-model-pill mi-pill-prod">
                <span class="mi-pill-title">PRODUCTION MODEL</span>
                <span class="mi-pill-val">Hybrid ST-GNN (12 Features) • Acc 97.14%</span>
              </div>
              <div class="mi-model-pill mi-pill-cand">
                <span class="mi-pill-title">CANDIDATE DL CHECKPOINT</span>
                <span class="mi-pill-val">Adaptive Gated ST-GNN (233k weights)</span>
              </div>
            </div>
          </div>

          <!-- Section Navigation Tabs -->
          <div class="mi-subnav-bar">
            <button class="mi-tab-btn active" id="mi-btn-tab-lineage" onclick="switchModelIntelTab('lineage', this)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              <span>1. Dataset Lineage & Inventory</span>
            </button>
            <button class="mi-tab-btn" id="mi-btn-tab-training" onclick="switchModelIntelTab('training', this)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              <span>2. Training Dynamics (CSV Curves)</span>
            </button>
            <button class="mi-tab-btn" id="mi-btn-tab-evaluation" onclick="switchModelIntelTab('evaluation', this)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/></svg>
              <span>3. Model Evaluation & Residuals</span>
            </button>
            <button class="mi-tab-btn" id="mi-btn-tab-explainability" onclick="switchModelIntelTab('explainability', this)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              <span>4. Feature Importance & XAI</span>
            </button>
            <button class="mi-tab-btn" id="mi-btn-tab-whatif" onclick="switchModelIntelTab('whatif', this)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <span>5. What-If Scenario Lab</span>
            </button>
            <button class="mi-tab-btn" id="mi-btn-tab-explorer" onclick="switchModelIntelTab('explorer', this)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
              <span>6. Dataset Statistics Explorer</span>
            </button>
          </div>

          <!-- TAB 1: DATASET LINEAGE & INVENTORY -->
          <div id="mi-tab-lineage" class="mi-tab-content active" style="display: block;">
            <!-- 6 Lineage Cards in a 3x2 Grid -->
            <div class="mi-grid-3" id="mi-lineage-cards-grid">
              <!-- Dynamically rendered -->
            </div>

            <!-- Provenance & Traceability Master Matrix Table -->
            <div class="mi-card" style="margin-top: 20px;">
              <div class="mi-card-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
                <span>Dataset-to-Model Provenance & Operational Role Matrix</span>
              </div>
              <div class="mi-card-subtitle">Every dataset mapped to its input features, supervised training status, and production inference engine.</div>
              <div class="table-responsive">
                <table class="mi-table">
                  <thead>
                    <tr>
                      <th>Dataset Name</th>
                      <th>Spatial Scale & Nodes</th>
                      <th>Usable Records</th>
                      <th>Features Extracted</th>
                      <th>Target Variable</th>
                      <th>Trained Model / Checkpoint</th>
                      <th>Operational Role</th>
                    </tr>
                  </thead>
                  <tbody id="mi-provenance-table-body">
                    <!-- Populated dynamically -->
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- TAB 2: TRAINING DYNAMICS & CONVERGENCE -->
          <div id="mi-tab-training" class="mi-tab-content" style="display: none;">
            <div class="mi-grid-2">
              <div class="mi-card">
                <div class="mi-card-header-flex">
                  <div>
                    <div class="mi-card-title">Training Loss vs Validation Loss Curves</div>
                    <div class="mi-card-subtitle">Actual epoch loss history from results/blue_heart/v2/BLUE_HEART_V2_TRAINING_HISTORY.csv</div>
                  </div>
                  <div class="mi-model-selector">
                    <select id="mi-training-model-select" onchange="renderTrainingCurvesChart(this.value)">
                      <option value="Adaptive_Gated_DCRNN">Adaptive Gated ST-GNN (Selected Candidate)</option>
                      <option value="Res_Temporal_GRU">Res-Temporal GRU</option>
                      <option value="Res_DCRNN">Res-DCRNN (Physical Diffusion)</option>
                      <option value="Graph_WaveNet">Graph WaveNet (TCN + Diffusion)</option>
                      <option value="ALL">All Models Combined</option>
                    </select>
                  </div>
                </div>
                <div class="mi-canvas-container" style="height: 320px;">
                  <canvas id="mi-canvas-loss-curves"></canvas>
                </div>
                <div class="mi-chart-legend" id="mi-training-legend"></div>
              </div>

              <div class="mi-card">
                <div class="mi-card-title">Training Hyperparameters & Convergence Telemetry</div>
                <div class="mi-card-subtitle">Hyperparameter configuration and early-stopping diagnostics.</div>
                <div class="mi-telemetry-grid">
                  <div class="mi-tele-box">
                    <div class="mi-tele-val" id="mi-tele-best-epoch">Epoch 5</div>
                    <div class="mi-tele-label">Best Validation Epoch</div>
                  </div>
                  <div class="mi-tele-box">
                    <div class="mi-tele-val text-cyan" id="mi-tele-best-loss">0.20687</div>
                    <div class="mi-tele-label">Lowest Validation Loss (Huber)</div>
                  </div>
                  <div class="mi-tele-box">
                    <div class="mi-tele-val text-green">1e-3 → 5e-4</div>
                    <div class="mi-tele-label">Learning Rate Schedule</div>
                  </div>
                  <div class="mi-tele-box">
                    <div class="mi-tele-val">AdamW (wd=1e-4)</div>
                    <div class="mi-tele-label">Optimizer & Regularization</div>
                  </div>
                </div>
                <div class="mi-callout-info" style="margin-top: 16px;">
                  <b>Scientific Convergence Insight:</b> The Adaptive Gated ST-GNN achieved its minimum validation loss of <b>0.20687</b> at Epoch 5. When the validation loss plateaued and began oscillating, the patience early-stopping mechanism terminated training at Epoch 11, preventing overfitting to dry-weather baseline auto-correlation.
                </div>
              </div>
            </div>
          </div>

          <!-- TAB 3: MODEL EVALUATION & RESIDUAL DIAGNOSTICS -->
          <div id="mi-tab-evaluation" class="mi-tab-content" style="display: none;">
            <div class="mi-grid-2">
              <!-- Actual vs Predicted Scatter -->
              <div class="mi-card">
                <div class="mi-card-title">Actual vs Predicted Stage (Scatter Plot)</div>
                <div class="mi-card-subtitle">1:1 diagonal identity check on held-out test sequences (1,093 sequences, 16,396 evaluations).</div>
                <div class="mi-canvas-container" style="height: 300px;">
                  <canvas id="mi-canvas-scatter"></canvas>
                </div>
                <div class="mi-chart-footnote">Ideal forecast lies on the dashed cyan 1:1 diagonal line. Points close to the line demonstrate high prediction fidelity.</div>
              </div>

              <!-- Residual Error Histogram -->
              <div class="mi-card">
                <div class="mi-card-title">Residual Error Distribution (e = y_actual - y_pred)</div>
                <div class="mi-card-subtitle">Error histogram centered around zero error with Gaussian fit.</div>
                <div class="mi-canvas-container" style="height: 300px;">
                  <canvas id="mi-canvas-residuals"></canvas>
                </div>
                <div class="mi-chart-footnote">Over 91.4% of all test stage predictions fall within ±2.5 cm of actual road-gully observations.</div>
              </div>
            </div>

            <!-- Multi-Model Benchmark Comparison Table -->
            <div class="mi-card" style="margin-top: 20px;">
              <div class="mi-card-title">Multi-Model Benchmark Comparison (Blue Heart Held-Out Test Set)</div>
              <div class="mi-card-subtitle">Evaluated on identical 1,093 test sequences under strict zero-leakage test partitioning.</div>
              <div class="table-responsive">
                <table class="mi-table">
                  <thead>
                    <tr>
                      <th>Model Architecture</th>
                      <th>Test MAE (m)</th>
                      <th>Test RMSE (m)</th>
                      <th>Nash-Sutcliffe (NSE)</th>
                      <th>Pearson R²</th>
                      <th>Peak Δt Error</th>
                      <th>High-Water MAE</th>
                      <th>Architectural Tradeoff Verdict</th>
                    </tr>
                  </thead>
                  <tbody id="mi-benchmark-table-body">
                    <!-- Populated dynamically -->
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Indore Municipal Classification Evaluation -->
            <div class="mi-card" style="margin-top: 20px;">
              <div class="mi-card-title">Indore Municipal Hybrid ST-GNN Evaluation (400 Multi-Event Sequences)</div>
              <div class="mi-card-subtitle">Chronological 80/20 train/test split (80 unseen test storm events = 560 node evaluations).</div>
              <div class="mi-metrics-banner">
                <div class="mi-stat-card">
                  <div class="mi-stat-val text-green">97.14%</div>
                  <div class="mi-stat-lbl">Classification Accuracy</div>
                </div>
                <div class="mi-stat-card">
                  <div class="mi-stat-val text-cyan">0.9948</div>
                  <div class="mi-stat-lbl">ROC-AUC Score</div>
                </div>
                <div class="mi-stat-card">
                  <div class="mi-stat-val text-blue">98.18%</div>
                  <div class="mi-stat-lbl">F1-Score</div>
                </div>
                <div class="mi-stat-card">
                  <div class="mi-stat-val">13.12 cm</div>
                  <div class="mi-stat-lbl">Inundation Depth MAE</div>
                </div>
                <div class="mi-stat-card">
                  <div class="mi-stat-val">2.27 min</div>
                  <div class="mi-stat-lbl">Peak Arrival Time MAE</div>
                </div>
              </div>
            </div>
          </div>

          <!-- TAB 4: FEATURE IMPORTANCE & EXPLAINABLE AI (XAI) -->
          <div id="mi-tab-explainability" class="mi-tab-content" style="display: none;">
            <div class="mi-grid-2">
              <!-- Permutation Importance Bar Chart -->
              <div class="mi-card">
                <div class="mi-card-title">Permutation Feature Importance (Indore 12 Features)</div>
                <div class="mi-card-subtitle">Drop in model predictive fidelity (ΔMAE cm) when individual features are randomized.</div>
                <div class="mi-canvas-container" style="height: 380px;">
                  <canvas id="mi-canvas-importance"></canvas>
                </div>
              </div>

              <!-- Per-Node Sensitivity & Temporal Lag -->
              <div class="mi-flex-col" style="gap: 20px;">
                <div class="mi-card">
                  <div class="mi-card-title">Per-Node Hydrological Sensitivity Matrix</div>
                  <div class="mi-card-subtitle">Relative influence of rainfall vs upstream inflow vs elevation across the 7 Indore nodes.</div>
                  <div class="table-responsive">
                    <table class="mi-table" style="font-size: 12px;">
                      <thead>
                        <tr>
                          <th>Monitoring Station</th>
                          <th>Rainfall</th>
                          <th>Inflow</th>
                          <th>Elevation</th>
                          <th>Pumps</th>
                          <th>Saturation</th>
                        </tr>
                      </thead>
                      <tbody id="mi-node-sensitivity-tbody">
                        <!-- Populated dynamically -->
                      </tbody>
                    </table>
                  </div>
                </div>

                <div class="mi-card">
                  <div class="mi-card-title">Temporal Lookback Lag Attribution</div>
                  <div class="mi-card-subtitle">Influence of antecedent time steps from t-60min down to current timestep t=0.</div>
                  <div class="mi-canvas-container" style="height: 140px;">
                    <canvas id="mi-canvas-temporal-lag"></canvas>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- TAB 5: WHAT-IF SCENARIO SENSITIVITY LAB -->
          <div id="mi-tab-whatif" class="mi-tab-content" style="display: none;">
            <div class="mi-grid-2">
              <!-- Controls Column -->
              <div class="mi-card">
                <div class="mi-card-title">Controlled Single-Feature Perturbation Controls</div>
                <div class="mi-card-subtitle">Adjust individual drivers to observe non-linear hydraulic and graph neural responses.</div>
                
                <div class="mi-slider-box">
                  <div class="mi-slider-header">
                    <span>Rainfall Intensity</span>
                    <b class="text-cyan" id="mi-val-rain">45 mm/h</b>
                  </div>
                  <input type="range" class="mi-range-input" id="mi-input-rain" min="0" max="110" step="5" value="45" oninput="onWhatIfSliderChange()">
                  <div class="mi-slider-bounds"><span>0 mm/h (Dry)</span><span>110 mm/h (Cloudburst)</span></div>
                </div>

                <div class="mi-slider-box">
                  <div class="mi-slider-header">
                    <span>Soil Saturation</span>
                    <b class="text-amber" id="mi-val-sat">70%</b>
                  </div>
                  <input type="range" class="mi-range-input" id="mi-input-sat" min="20" max="100" step="5" value="70" oninput="onWhatIfSliderChange()">
                  <div class="mi-slider-bounds"><span>20% (Dry Soil)</span><span>100% (Fully Saturated)</span></div>
                </div>

                <div class="mi-slider-box">
                  <div class="mi-slider-header">
                    <span>Operational Drainage Pumps</span>
                    <b class="text-green" id="mi-val-pumps">2 Pumps</b>
                  </div>
                  <input type="range" class="mi-range-input" id="mi-input-pumps" min="0" max="6" step="1" value="2" oninput="onWhatIfSliderChange()">
                  <div class="mi-slider-bounds"><span>0 Pumps (Failure)</span><span>6 Pumps (Max Capacity)</span></div>
                </div>

                <div class="mi-slider-box">
                  <div class="mi-slider-header">
                    <span>6-Hour Antecedent Cumulative Rain</span>
                    <b class="text-blue" id="mi-val-cumul">40 mm</b>
                  </div>
                  <input type="range" class="mi-range-input" id="mi-input-cumul" min="0" max="150" step="5" value="40" oninput="onWhatIfSliderChange()">
                  <div class="mi-slider-bounds"><span>0 mm</span><span>150 mm</span></div>
                </div>
              </div>

              <!-- Dynamic Response Curves -->
              <div class="mi-card">
                <div class="mi-card-title">Dynamic Non-Linear Response Curve (Rainfall vs Inundation Depth)</div>
                <div class="mi-card-subtitle">Real-time recalculation of inundation depth and surcharge threshold.</div>
                <div class="mi-canvas-container" style="height: 250px;">
                  <canvas id="mi-canvas-whatif-response"></canvas>
                </div>
                <!-- Waterfall Attribution Breakdown -->
                <div class="mi-card-title" style="margin-top: 18px;">Prediction Waterfall Attribution Breakdown (Rajwada Confluence)</div>
                <div class="mi-waterfall-container" id="mi-waterfall-box">
                  <!-- Dynamically rendered -->
                </div>
              </div>
            </div>
          </div>

          <!-- TAB 6: DATASET STATISTICAL EXPLORER -->
          <div id="mi-tab-explorer" class="mi-tab-content" style="display: none;">
            <div class="mi-card">
              <div class="mi-card-header-flex">
                <div>
                  <div class="mi-card-title">Hydrological Feature Distribution Statistics & Missingness Telemetry</div>
                  <div class="mi-card-subtitle">Detailed statistical quartiles, mean, standard deviation, and missingness rates across all project datasets.</div>
                </div>
                <div class="mi-model-selector">
                  <select id="mi-explorer-dataset-select" onchange="renderDatasetExplorer(this.value)">
                    <option value="blue_heart">Blue Heart Urban Gully Network (Eastbourne UK)</option>
                    <option value="indore_municipal">Indore Municipal Drainage Basin (Khan & Saraswati)</option>
                    <option value="camels_hourly">CAMELS-Hourly River Benchmark (Aroostook Basin)</option>
                    <option value="india_cwprs">CWPRS Monsoon Telemetry (Pune)</option>
                  </select>
                </div>
              </div>
              <div id="mi-explorer-content">
                <!-- Dynamically populated -->
              </div>
            </div>
          </div>
        </section>
"""

modal_marker = "<!-- Modal: View Full Inspection Report -->"
if 'id="screen-model-intel"' not in content:
    content = content.replace(modal_marker, screen_model_intel_html + "\n\n        " + modal_marker, 1)
    print("Added #screen-model-intel to view-app main content")

# 4. Bump script and CSS versions
content = content.replace("style.css?v=3.5", "style.css?v=3.8")
content = content.replace("app.js?v=3.5", "app.js?v=3.8")

HTML_FILE.write_text(content, encoding="utf-8")
print(f"Successfully patched {HTML_FILE}")
