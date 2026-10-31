with open("scripts/verify_task_38_model_intel.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if i <= 80:
            print(f"{i}: {line}", end="")

