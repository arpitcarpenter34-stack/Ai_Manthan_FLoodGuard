import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- FEATURE LAUNCH CARDS ---")
for i in range(250, 385):
    if "feature-launch-card" in lines[i] or "flc-title" in lines[i]:
        print(f"{i+1}: {lines[i]}", end="")

