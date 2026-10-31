import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- HERO MINI CARDS ---")
for i in range(120, 180):
    print(f"{i+1}: {lines[i]}", end="")

