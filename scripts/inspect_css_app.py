with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

print("--- VIEW-APP IN style.css ---")
for i, l in enumerate(css.splitlines(), 1):
    if 'view-app' in l or 'app-layout' in l or 'app-main' in l or 'app-content' in l:
        print(f"Line {i}: {l.strip()}")

