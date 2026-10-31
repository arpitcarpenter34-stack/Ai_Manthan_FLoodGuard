with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines[38:65], 39):
    print(f"{i}: {line}", end="")

