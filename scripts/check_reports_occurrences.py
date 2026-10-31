with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if 'id="screen-reports"' in line:
            print(f"Line {i}: {line.strip()}")

