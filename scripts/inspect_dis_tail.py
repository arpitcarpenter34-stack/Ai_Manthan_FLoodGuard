with open("backend/services/dataset_intelligence_service.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines[-60:], len(lines)-59):
    print(f"{i}: {line}", end="")

