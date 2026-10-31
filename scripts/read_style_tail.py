with open("frontend/static/css/style.css", "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines[-50:], len(lines)-49):
    print(f"{i}: {line}", end="")

