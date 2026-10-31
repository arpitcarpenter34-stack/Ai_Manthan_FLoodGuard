import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("backend/services/dataset_intelligence_service.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if "def " in line and line.strip().startswith("def "):
        print(f"Line {i}: {line.strip()}")

