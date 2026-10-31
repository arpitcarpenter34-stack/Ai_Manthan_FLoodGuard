"""
Patch style.css to apply the city, river, dam, and rainfall background image
to all non-homepage pages (#view-app) in HYDRO-GUARD AI.
"""

from pathlib import Path

STYLE_PATH = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\static\css\style.css")
content = STYLE_PATH.read_text(encoding="utf-8")

# 1. Update #view-app to include the background image with fixed attachment and balanced overlay
old_view_app = """#view-app {
  background-color: var(--app-bg);
  min-height: 100vh;
  display: none;
  flex-direction: column;
}"""

new_view_app = """#view-app {
  background-color: var(--app-bg);
  min-height: 100vh;
  display: none;
  flex-direction: column;
  position: relative;
  background-image: 
    linear-gradient(180deg, rgba(7, 14, 30, 0.48) 0%, rgba(7, 14, 30, 0.68) 100%),
    url("/static/images/app_bg.jpg");
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  background-attachment: fixed;
}"""

# 2. Update .app-header for glassmorphism
old_header = """  background: rgba(7, 14, 30, 0.95);
  border-bottom: 1px solid rgba(0, 210, 255, 0.16);
  backdrop-filter: blur(16px);"""

new_header = """  background: rgba(7, 14, 30, 0.88);
  border-bottom: 1px solid rgba(0, 210, 255, 0.20);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);"""

# 3. Update .app-sidebar for glassmorphism
old_sidebar = """  background: rgba(7, 14, 30, 0.95);
  border-right: 1px solid rgba(0, 210, 255, 0.14);"""

new_sidebar = """  background: rgba(7, 14, 30, 0.88);
  border-right: 1px solid rgba(0, 210, 255, 0.16);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);"""

# 4. Update #screen-reports to use frosted glass over the fixed background
old_reports = """#screen-reports {
  background: #f1f5f9;"""

new_reports = """#screen-reports {
  background: rgba(241, 245, 249, 0.86);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);"""

# Normalize line endings for reliable replacement
c = content.replace("\r\n", "\n")
assert old_view_app in c, "old_view_app not found"
assert old_header in c, "old_header not found"
assert old_sidebar in c, "old_sidebar not found"
assert old_reports in c, "old_reports not found"

c = c.replace(old_view_app, new_view_app, 1)
c = c.replace(old_header, new_header, 1)
c = c.replace(old_sidebar, new_sidebar, 1)
c = c.replace(old_reports, new_reports, 1)

STYLE_PATH.write_text(c, encoding="utf-8")
print("style.css successfully patched with app background rules!")

