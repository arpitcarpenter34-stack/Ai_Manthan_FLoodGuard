with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines[119:220], 120):
    print(f"{i}: {line}", end="")

