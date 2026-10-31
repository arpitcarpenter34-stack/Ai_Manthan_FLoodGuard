import re

with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Check sidebar items to remove
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

print("pred_nav in content:", pred_nav in content)
print("sim_nav in content:", sim_nav in content)
print("hist_nav in content:", hist_nav in content)

# 2. Check page containers
pred_sec = re.search(r'<!-- SCREEN 4: DUAL FLOOD PREDICTION -->[\s\S]*?<section id="screen-prediction"[\s\S]*?</section>', content)
print("Found screen-prediction container:", bool(pred_sec))

sim_sec = re.search(r'<!-- SCREEN 5: PUMP & SLUICE SIMULATOR -->[\s\S]*?<section id="screen-simulator"[\s\S]*?</section>', content)
print("Found screen-simulator container:", bool(sim_sec))

hist_sec = re.search(r'<!-- SCREEN 6: HISTORY & LOGS \(SQLite\) -->[\s\S]*?<section id="screen-history"[\s\S]*?</section>', content)
print("Found screen-history container:", bool(hist_sec))

