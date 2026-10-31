with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    js = f.read()

# 1. Update initRoutingFromHash
old_routing = """function initRoutingFromHash() {
  const hash = window.location.hash.replace("#", "").toLowerCase();
  if (!hash || hash === "home") {
    navigateToHome(false);
  } else if (SCREEN_TITLES[hash]) {
    navigateTo(hash, false);
  } else {
    navigateToHome(false);
  }
}"""

new_routing = """function initRoutingFromHash() {
  const hash = window.location.hash.replace("#", "").toLowerCase();
  if (!hash || hash === "home") {
    navigateToHome(false);
  } else if (SCREEN_TITLES[hash] || hash === "explorer") {
    navigateTo(hash, false);
  } else {
    navigateToHome(false);
  }
}"""

if old_routing in js:
    js = js.replace(old_routing, new_routing)
    print("Updated initRoutingFromHash")
else:
    print("old_routing not matched exactly, checking regex...")
    import re
    js = re.sub(r'else\s+if\s*\(\s*SCREEN_TITLES\[hash\]\s*\)', 'else if (SCREEN_TITLES[hash] || hash === "explorer")', js)

# 2. Update navigateTo
old_toggle_start = js.find("// Toggle View Containers")
if old_toggle_start != -1:
    old_toggle_end = js.find("// Screen-Specific Triggers", old_toggle_start)
    if old_toggle_end != -1:
        new_toggle_block = """// Toggle View Containers
  const vHome = document.getElementById("view-home");
  const vApp = document.getElementById("view-app");
  if (vHome) {
    vHome.classList.remove("active");
    vHome.style.display = "none";
  }
  if (vApp) {
    vApp.classList.add("active");
    vApp.style.display = "block";
    if (screenId === "explorer") {
      vApp.classList.add("white-theme");
    } else {
      vApp.classList.remove("white-theme");
    }
  }

  // Toggle Active Screen
  document.querySelectorAll(".screen-container").forEach(el => {
    el.classList.remove("active");
    el.style.display = "none";
  });
  const targetScreen = document.getElementById(`screen-${screenId}`);
  if (targetScreen) {
    targetScreen.classList.add("active");
    targetScreen.style.display = "block";
  }

  // Update Sidebar Active Pill
  document.querySelectorAll(".sidebar-item").forEach(item => item.classList.remove("active"));
  const activeNavItem = document.getElementById(`nav-item-${screenId}`);
  if (activeNavItem) activeNavItem.classList.add("active");

  // Update Screen Title & Subtitle
  const meta = SCREEN_TITLES[screenId];
  if (meta) {
    const curTitle = document.getElementById("current-screen-title");
    const curSub = document.getElementById("current-screen-subtitle");
    if (curTitle) curTitle.textContent = meta.title;
    if (curSub) curSub.textContent = meta.subtitle;
  }

  // Hide general page-top-bar on dedicated dashboard screens
  const pageTopBar = document.querySelector(".page-top-bar");
  if (pageTopBar) {
    pageTopBar.style.display = (screenId === "reports" || screenId === "model-intel" || screenId === "explorer") ? "none" : "flex";
  }

  """
        js = js[:old_toggle_start] + new_toggle_block + js[old_toggle_end:]
        print("Updated navigateTo toggle block successfully")

with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(js)

print("Saved frontend/static/js/app.js")

