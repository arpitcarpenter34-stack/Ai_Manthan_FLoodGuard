with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if any(k in line for k in ['id="screen-prediction"', 'id="screen-simulator"', 'id="screen-history"', 'id="nav-item-prediction"', 'id="nav-item-simulator"', 'id="nav-item-history"']):
        print(f"Line {i}: {line.strip()}")

