with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if any(k in line for k in ["prediction:", "simulator:", "history:", "nav-item-prediction", "nav-item-simulator", "nav-item-history"]):
        print(f"Line {i}: {line.strip()}")

