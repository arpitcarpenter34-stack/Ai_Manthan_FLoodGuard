with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'if "text/html" in accept and "application/json" not in accept and html_file.exists():',
    'if "text/html" in accept and html_file.exists():'
)

with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated backend/main.py line 111.")

