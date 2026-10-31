with open("backend/api/dataset_intelligence_routes.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines[:60], 1):
    print(f"{i}: {line}", end="")

