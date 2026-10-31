import os

with open('frontend/static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

with open('frontend/static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

print("--- 1. SCREEN-CONTAINER TAGS IN index.html ---")
lines = html.splitlines()
for i, l in enumerate(lines, 1):
    if 'screen-container' in l and '<' in l:
        print(f"Line {i}: {l.strip()}")

print("\n--- 2. CHECK .screen-container.active in CSS ---")
for i, l in enumerate(css.splitlines(), 1):
    if 'screen-container' in l:
        print(f"Line {i}: {l.strip()}")

print("\n--- 3. CHECK #screen-explorer.active in CSS ---")
if '#screen-explorer.active' in css or '#screen-explorer.screen-container.active' in css:
    print("Found active rule for #screen-explorer")
else:
    print("WARNING: No specific #screen-explorer.active rule in style.css!")

print("\n--- 4. CHECK app.js navigateTo function ---")
nav_idx = js.find("function navigateTo(")
if nav_idx != -1:
    print(js[nav_idx:nav_idx+500])

