with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines[1319:1375], 1320):
    print(f"{i}: {line}", end="")

