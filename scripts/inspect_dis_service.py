with open("backend/services/dataset_intelligence_service.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines[:80], 1):
    print(f"{i}: {line}", end="")

