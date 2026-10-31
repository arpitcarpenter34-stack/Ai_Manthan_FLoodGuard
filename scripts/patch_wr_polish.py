import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path

BASE_DIR = Path(r"E:\ai-manthan\hydro_guard_indore")
JS_PATH = BASE_DIR / "frontend" / "static" / "js" / "app.js"
CSS_PATH = BASE_DIR / "frontend" / "static" / "css" / "style.css"

js_text = JS_PATH.read_text(encoding="utf-8")

# 1. Update pageTopBar hiding logic
old_hide = '(screenId === "reports" || screenId === "model-intel" || screenId === "explorer")'
new_hide = '(screenId === "reports" || screenId === "model-intel" || screenId === "explorer" || screenId === "weather-radar")'

if old_hide in js_text:
    js_text = js_text.replace(old_hide, new_hide)
    print("[OK] Updated pageTopBar hiding in app.js")
else:
    print("Notice: old_hide not found")

# 2. Update tileLayer URL
old_tile = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
new_tile = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
if old_tile in js_text:
    js_text = js_text.replace(old_tile, new_tile)
    print("[OK] Updated tileLayer URL in app.js")
else:
    print("Notice: old_tile not found")

JS_PATH.write_text(js_text, encoding="utf-8")

# 3. Add tile filter to style.css
css_text = CSS_PATH.read_text(encoding="utf-8")
tile_filter_css = """
.wr-map-container .leaflet-tile {
  filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.25);
}
"""

if ".wr-map-container .leaflet-tile" not in css_text:
    marker = "/* Nowcast & Short-term Outlook */"
    if marker in css_text:
        css_text = css_text.replace(marker, tile_filter_css + "\n" + marker)
    else:
        css_text += "\n" + tile_filter_css
    CSS_PATH.write_text(css_text, encoding="utf-8")
    print("[OK] Added .wr-map-container .leaflet-tile dark filter to style.css")
else:
    print("Notice: tile filter already present")

print("Done polish patch.")
