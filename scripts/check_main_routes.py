with open("backend/main.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "html" in line.lower() or "static" in line.lower() or "@app.get" in line.lower():
            print(f"Line {i}: {line.strip()}")

