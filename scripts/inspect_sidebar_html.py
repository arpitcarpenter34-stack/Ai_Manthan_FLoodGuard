import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines[480:560], 481):
    print(f"{i}: {line}", end="")

