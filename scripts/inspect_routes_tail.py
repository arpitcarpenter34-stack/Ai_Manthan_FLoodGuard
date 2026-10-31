with open("backend/api/dataset_intelligence_routes.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines[60:101], 61):
    print(f"{i}: {line}", end="")

