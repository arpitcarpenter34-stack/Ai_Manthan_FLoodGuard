with open("backend/main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines[99:125], 100):
    print(f"{i}: {line}", end="")

