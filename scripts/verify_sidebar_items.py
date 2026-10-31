import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

in_sidebar = False
for i, line in enumerate(lines, 1):
    if '<ul class="sidebar-menu">' in line:
        in_sidebar = True
    if in_sidebar:
        if '<span>' in line:
            print(f"Line {i}: {line.strip()}")
        if '</ul>' in line:
            break

