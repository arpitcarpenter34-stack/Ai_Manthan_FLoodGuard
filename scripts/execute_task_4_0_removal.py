import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("Starting Task 4.0 Navigation & Page Removal...")

# ==============================================================================
# 1. EDIT frontend/static/index.html
# ==============================================================================
with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# A. Remove 3 items from floating navbar (.nav-links)
old_home_nav = """        <ul class="nav-links">
          <li><a class="nav-link active" onclick="scrollToSection('hero')">Home</a></li>
          <li><a class="nav-link" onclick="navigateTo('explorer')">Dataset Explorer</a></li>
          <li><a class="nav-link" onclick="navigateTo('weather-radar')">Weather & Radar</a></li>
          <li><a class="nav-link" onclick="navigateTo('drivers')">Flood Drivers</a></li>
          <li><a class="nav-link" onclick="navigateTo('model-intel')">Model Intel</a></li>
          <li><a class="nav-link" onclick="navigateTo('prediction')">Flood Prediction</a></li>
          <li><a class="nav-link" onclick="navigateTo('map')">GIS Map</a></li>
          <li><a class="nav-link" onclick="navigateTo('simulator')">Pump Simulator</a></li>
          <li><a class="nav-link" onclick="navigateTo('history')">History & Logs</a></li>
        </ul>"""

new_home_nav = """        <ul class="nav-links">
          <li><a class="nav-link active" onclick="scrollToSection('hero')">Home</a></li>
          <li><a class="nav-link" onclick="navigateTo('explorer')">Dataset Explorer</a></li>
          <li><a class="nav-link" onclick="navigateTo('weather-radar')">Weather & Radar</a></li>
          <li><a class="nav-link" onclick="navigateTo('drivers')">Flood Drivers</a></li>
          <li><a class="nav-link" onclick="navigateTo('model-intel')">Model Intel</a></li>
          <li><a class="nav-link" onclick="navigateTo('map')">GIS Map</a></li>
          <li><a class="nav-link" onclick="navigateTo('reports')">Reports & Audit</a></li>
        </ul>"""

if old_home_nav in html:
    html = html.replace(old_home_nav, new_home_nav)
    print("1. Removed prediction, simulator, history from homepage navbar.")
else:
    print("Warning: old_home_nav not matched exactly.")

# B. Update 4 Hero Mini Cards to point to retained sections only
old_hero_cards = """          <div class="hero-feature-cards">
            <!-- Card 1: Flood Prediction -->
            <div class="hero-mini-card" onclick="navigateTo('prediction')">
              <div>
                <div class="hero-mini-icon icon-teal">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                  </svg>
                </div>
                <div class="hero-mini-title">Flood Prediction</div>
                <div class="hero-mini-desc">AI-powered inundation forecasting</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>

            <!-- Card 2: Water Purity Analysis -->
            <div class="hero-mini-card" onclick="navigateTo('purity')">
              <div>
                <div class="hero-mini-icon icon-blue">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
                  </svg>
                </div>
                <div class="hero-mini-title">Water Purity Analysis</div>
                <div class="hero-mini-desc">Check water quality from images</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>

            <!-- Card 3: Acoustic Drain Monitoring -->
            <div class="hero-mini-card" onclick="navigateTo('sound')">
              <div>
                <div class="hero-mini-icon icon-purple">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                  </svg>
                </div>
                <div class="hero-mini-title">Acoustic Drain Monitoring</div>
                <div class="hero-mini-desc">Detect abnormal sound levels</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>

            <!-- Card 4: Pump & Gate Simulation -->
            <div class="hero-mini-card" onclick="navigateTo('simulator')">
              <div>
                <div class="hero-mini-icon icon-amber">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"></path>
                  </svg>
                </div>
                <div class="hero-mini-title">Pump & Gate Simulation</div>
                <div class="hero-mini-desc">Optimize drainage operations</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>
          </div>"""

new_hero_cards = """          <div class="hero-feature-cards">
            <!-- Card 1: Dataset Explorer -->
            <div class="hero-mini-card" onclick="navigateTo('explorer')">
              <div>
                <div class="hero-mini-icon icon-teal">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                    <line x1="9" y1="21" x2="9" y2="9"></line>
                  </svg>
                </div>
                <div class="hero-mini-title">Dataset Explorer</div>
                <div class="hero-mini-desc">Multi-basin telemetry & GNN models</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>

            <!-- Card 2: Water Purity Analysis -->
            <div class="hero-mini-card" onclick="navigateTo('purity')">
              <div>
                <div class="hero-mini-icon icon-blue">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
                  </svg>
                </div>
                <div class="hero-mini-title">Water Purity Analysis</div>
                <div class="hero-mini-desc">Check water quality from images</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>

            <!-- Card 3: Acoustic Drain Monitoring -->
            <div class="hero-mini-card" onclick="navigateTo('sound')">
              <div>
                <div class="hero-mini-icon icon-purple">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                  </svg>
                </div>
                <div class="hero-mini-title">Acoustic Drain Monitoring</div>
                <div class="hero-mini-desc">Detect abnormal sound levels</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>

            <!-- Card 4: Weather & Radar -->
            <div class="hero-mini-card" onclick="navigateTo('weather-radar')">
              <div>
                <div class="hero-mini-icon icon-amber">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <circle cx="12" cy="12" r="10"></circle>
                    <circle cx="12" cy="12" r="6"></circle>
                    <circle cx="12" cy="12" r="2"></circle>
                    <line x1="12" y1="2" x2="12" y2="6"></line>
                    <line x1="12" y1="18" x2="12" y2="22"></line>
                  </svg>
                </div>
                <div class="hero-mini-title">Weather & Radar</div>
                <div class="hero-mini-desc">Cloudburst hyetograph & telemetry</div>
              </div>
              <div class="hero-mini-arrow">→</div>
            </div>
          </div>"""

if old_hero_cards in html:
    html = html.replace(old_hero_cards, new_hero_cards)
    print("2. Updated hero mini cards to point to retained sections.")
else:
    print("Warning: old_hero_cards not matched exactly.")

# C. Remove 3 items from App Sidebar (.sidebar-menu)
pred_nav = """          <li class="sidebar-item" id="nav-item-prediction" onclick="navigateTo('prediction')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
            <span>Flood Prediction</span>
          </li>\n"""

sim_nav = """          <li class="sidebar-item" id="nav-item-simulator" onclick="navigateTo('simulator')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"></path>
            </svg>
            <span>Pump & Gate Optimizer</span>
          </li>\n"""

hist_nav = """          <li class="sidebar-item" id="nav-item-history" onclick="navigateTo('history')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
            <span>Historical Analytics</span>
          </li>\n"""

if pred_nav in html:
    html = html.replace(pred_nav, "")
    print("3a. Removed Flood Prediction from sidebar.")
if sim_nav in html:
    html = html.replace(sim_nav, "")
    print("3b. Removed Pump & Gate Optimizer from sidebar.")
if hist_nav in html:
    html = html.replace(hist_nav, "")
    print("3c. Removed Historical Analytics from sidebar.")

# D. Remove page container 1: screen-prediction
pred_pattern = re.compile(r'\s*<!-- SCREEN 4: DUAL FLOOD PREDICTION -->[\s\S]*?<section id="screen-prediction"[\s\S]*?</section>', re.MULTILINE)
if pred_pattern.search(html):
    html = pred_pattern.sub('', html)
    print("4a. Removed page container: screen-prediction.")

# E. Remove page container 2: screen-simulator
sim_pattern = re.compile(r'\s*<!-- SCREEN 5: PUMP & SLUICE SIMULATOR -->[\s\S]*?<section id="screen-simulator"[\s\S]*?</section>', re.MULTILINE)
if sim_pattern.search(html):
    html = sim_pattern.sub('', html)
    print("4b. Removed page container: screen-simulator.")

# F. Remove page container 3: screen-history
hist_pattern = re.compile(r'\s*<!-- SCREEN 6: HISTORY & LOGS \(SQLite\) -->[\s\S]*?<section id="screen-history"[\s\S]*?</section>', re.MULTILINE)
if hist_pattern.search(html):
    html = hist_pattern.sub('', html)
    print("4c. Removed page container: screen-history.")

# G. Bump cache busters to v=4.0
html = html.replace("style.css?v=3.9", "style.css?v=4.0")
html = html.replace("app.js?v=3.94", "app.js?v=4.0")

with open("frontend/static/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Updated frontend/static/index.html successfully.")


# ==============================================================================
# 2. EDIT frontend/static/js/app.js
# ==============================================================================
with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    js = f.read()

# A. Clean SCREEN_TITLES: remove prediction, simulator, history
old_screen_titles = """const SCREEN_TITLES = {
  sound: {
    title: "Sound Level Tester",
    subtitle: "Upload and analyze drain/sewer audio to estimate water level and detect abnormal conditions"
  },
  purity: {
    title: "Image Purity Tester",
    subtitle: "Computer vision colorimetric screening enforcing the 80% Khan River Purity Rule before discharge"
  },
  map: {
    title: "Indore Flood Map View",
    subtitle: "Interactive GIS topological drainage and river reaches across Indore's 45m elevation gradient"
  },
  prediction: {
    title: "Dual-Engine Flood Prediction",
    subtitle: "Simulate urban runoff using physics-based Manning routing coupled with Random Forest ML"
  },
  simulator: {
    title: "Smart Pump & Sluice Gate Simulator",
    subtitle: "Simulate urban storm surge mitigation and automated dual-gate Khan River diversion"
  },
  reports: {
    title: "Reports & Monitoring",
    subtitle: "Water Quality • Drainage • Filtration • Area Intelligence"
  },
  history: {
    title: "History & Persistent Audit Logs",
    subtitle: "Query persistent SQLite analysis history permanently stored in data/hydro_guard.db"
  },
  'model-intel': {
    title: "AI Model Intelligence & Scientific Explainability",
    subtitle: "Dataset Lineage • Training Dynamics • Residual Diagnostics • XAI & Permutation Importance • What-If Lab"
  },
  explorer: {
    title: "Multi-Basin Dataset Explorer & Live Inference",
    subtitle: "8 Acquired Datasets • Ground-Truth Observations • Statistical Distributions • Direct Deep Learning Inference"
  },
  'weather-radar': {
    title: "Weather Radar & Precipitation Intelligence",
    subtitle: "Doppler Radar Audit & Specifications • Indian Monsoon Cloudburst Hyetograph • Ground Rain Telemetry"
  },
  drivers: {
    title: "Feature Breakdown & Flood Driver Attribution",
    subtitle: "Hydrological Attribution • Permutation Feature Importance • Temporal Lag Decay • Spatio-Temporal Jacobian"
  }
};"""

new_screen_titles = """const SCREEN_TITLES = {
  sound: {
    title: "Sound Level Tester",
    subtitle: "Upload and analyze drain/sewer audio to estimate water level and detect abnormal conditions"
  },
  purity: {
    title: "Image Purity Tester",
    subtitle: "Computer vision colorimetric screening enforcing the 80% Khan River Purity Rule before discharge"
  },
  map: {
    title: "Spatial Drainage GIS View",
    subtitle: "Interactive GIS topological drainage and river reaches across the elevation gradient"
  },
  reports: {
    title: "Reports & Monitoring",
    subtitle: "Water Quality • Drainage • Filtration • Area Intelligence"
  },
  'model-intel': {
    title: "AI Model Intelligence & Scientific Explainability",
    subtitle: "Dataset Lineage • Training Dynamics • Residual Diagnostics • XAI & Permutation Importance • What-If Lab"
  },
  explorer: {
    title: "Multi-Basin Dataset Explorer & Live Inference",
    subtitle: "8 Acquired Datasets • Ground-Truth Observations • Statistical Distributions • Direct Deep Learning Inference"
  },
  'weather-radar': {
    title: "Weather Radar & Precipitation Intelligence",
    subtitle: "Doppler Radar Audit & Specifications • Indian Monsoon Cloudburst Hyetograph • Ground Rain Telemetry"
  },
  drivers: {
    title: "Feature Breakdown & Flood Driver Attribution",
    subtitle: "Hydrological Attribution • Permutation Feature Importance • Temporal Lag Decay • Spatio-Temporal Jacobian"
  }
};"""

if old_screen_titles in js:
    js = js.replace(old_screen_titles, new_screen_titles)
    print("5. Removed prediction, simulator, history from SCREEN_TITLES.")
else:
    print("Warning: old_screen_titles not matched exactly.")

# B. Clean navigateTo screen-specific triggers: remove history, prediction, simulator
old_triggers = """  // Screen-Specific Triggers
  if (screenId === "map") {
    setTimeout(initLeafletMap, 150);
    setTimeout(loadStreetInundationPanel, 200);
  } else if (screenId === "reports") {
    loadReportsAndMonitoring();
  } else if (screenId === "history") {
    fetchHistoryLogs();
    fetchDbStats();
  } else if (screenId === "prediction") {
    runDualPrediction();
  } else if (screenId === "simulator") {
    loadSimulatorOptimization();
  } else if (screenId === "model-intel") {
    loadModelIntelligenceDashboard();
  } else if (screenId === "explorer") {
    loadDatasetExplorer();
  } else if (screenId === "weather-radar") {
    loadWeatherRadarIntelligence();
  } else if (screenId === "drivers") {
    loadFloodDriversAnalysis();
  }"""

new_triggers = """  // Screen-Specific Triggers
  if (screenId === "map") {
    setTimeout(initLeafletMap, 150);
    setTimeout(loadStreetInundationPanel, 200);
  } else if (screenId === "reports") {
    loadReportsAndMonitoring();
  } else if (screenId === "model-intel") {
    loadModelIntelligenceDashboard();
  } else if (screenId === "explorer") {
    loadDatasetExplorer();
  } else if (screenId === "weather-radar") {
    loadWeatherRadarIntelligence();
  } else if (screenId === "drivers") {
    loadFloodDriversAnalysis();
  }"""

if old_triggers in js:
    js = js.replace(old_triggers, new_triggers)
    print("6. Cleaned navigateTo triggers in app.js.")
else:
    print("Warning: old_triggers not matched exactly.")

# C. Safe default in navigateTo if unknown screenId is requested
js = js.replace('if (!SCREEN_TITLES[screenId]) screenId = "sound";', 'if (!SCREEN_TITLES[screenId]) screenId = "explorer";')

with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(js)

print("Updated frontend/static/js/app.js successfully.")

