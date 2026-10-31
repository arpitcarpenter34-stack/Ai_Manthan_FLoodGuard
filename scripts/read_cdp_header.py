with open("scripts/test_task38_cdp.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if i <= 80:
            print(f"{i}: {line}", end="")

