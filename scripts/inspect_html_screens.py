from pathlib import Path
content = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\static\index.html").read_text(encoding="utf-8")
for i, line in enumerate(content.splitlines(), 1):
    if 'id="screen-' in line:
        print(f"{i}: {line.strip()}")
