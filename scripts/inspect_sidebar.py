with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

print("--- APP-HEADER, APP-SIDEBAR, APP-LAYOUT ---")
lines = css.splitlines()
for i, l in enumerate(lines, 1):
    if any(k in l for k in ['.app-header', '.app-sidebar', '.sidebar-item', '.app-main']):
        print(f"Line {i}: {l.strip()[:80]}")

