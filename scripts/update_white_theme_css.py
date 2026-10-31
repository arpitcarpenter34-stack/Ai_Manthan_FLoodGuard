css_white_theme = """
/* ==============================================================================
   TASK 4.1-FIX: WHITE THEME SHELL FOR DATASET EXPLORER
   Exact match to design reference: media_1793427602234_3a72ebdd.jpg
   Removes dark cinematic background and styles header, sidebar & main container.
   ============================================================================== */

/* Ensure active screen container is unconditionally visible */
.screen-container.active {
  display: block !important;
}

#screen-explorer.active {
  display: block !important;
}

/* White Theme mode on #view-app */
#view-app.white-theme {
  background-image: none !important;
  background-color: #f8fafc !important;
  color: #0f172a !important;
}

#view-app.white-theme .app-header {
  background: #ffffff !important;
  border-bottom: 1px solid #e2e8f0 !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
}

#view-app.white-theme .app-brand-titles h2 {
  color: #0f172a !important;
}

#view-app.white-theme .app-brand-titles span {
  color: #0284c7 !important;
}

#view-app.white-theme .header-pill {
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  color: #334155 !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
}

#view-app.white-theme .header-pill svg {
  color: #0284c7 !important;
}

#view-app.white-theme .header-pill span {
  color: #334155 !important;
}

#view-app.white-theme .btn-home-return {
  background: #f0f9ff !important;
  border: 1px solid #bae6fd !important;
  color: #0284c7 !important;
  font-weight: 600 !important;
}

#view-app.white-theme .btn-home-return:hover {
  background: #e0f2fe !important;
}

#view-app.white-theme .app-sidebar {
  background: #ffffff !important;
  border-right: 1px solid #e2e8f0 !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  box-shadow: 1px 0 2px rgba(0, 0, 0, 0.02) !important;
}

#view-app.white-theme .sidebar-section-title {
  color: #94a3b8 !important;
}

#view-app.white-theme .sidebar-item {
  color: #475569 !important;
  font-weight: 500 !important;
}

#view-app.white-theme .sidebar-item svg {
  color: #64748b !important;
}

#view-app.white-theme .sidebar-item:hover {
  background: #f1f5f9 !important;
  color: #0284c7 !important;
}

#view-app.white-theme .sidebar-item:hover svg {
  color: #0284c7 !important;
}

#view-app.white-theme .sidebar-item.active {
  background: #0284c7 !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 6px rgba(2, 132, 199, 0.25) !important;
}

#view-app.white-theme .sidebar-item.active svg {
  color: #ffffff !important;
}

#view-app.white-theme .sidebar-footer-box {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #0f172a !important;
}

#view-app.white-theme .sidebar-footer-box h4 {
  color: #0f172a !important;
}

#view-app.white-theme .sidebar-footer-box p {
  color: #64748b !important;
}

#view-app.white-theme .app-main {
  background: #f8fafc !important;
  padding: 0 !important;
  max-width: 100% !important;
}

#view-app.white-theme .page-top-bar {
  display: none !important;
}

#view-app.white-theme #screen-explorer {
  display: block !important;
  background: #f8fafc !important;
  min-height: calc(100vh - var(--header-height)) !important;
  padding: 24px 32px !important;
}
"""

with open("frontend/static/css/style.css", "a", encoding="utf-8") as f:
    f.write("\n" + css_white_theme)

print("Successfully appended White-Theme shell styles to style.css")

