with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines[115:185], 116):
    print(f"{i}: {line}", end="")

