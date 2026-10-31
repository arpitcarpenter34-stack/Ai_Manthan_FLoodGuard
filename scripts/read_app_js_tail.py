with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"Total lines in app.js: {len(lines)}")
for i, line in enumerate(lines[-60:], len(lines)-59):
    print(f"{i}: {line}", end="")

