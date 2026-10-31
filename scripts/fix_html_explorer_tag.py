with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    c = f.read()

old_tag = '<section id="screen-explorer" class="screen-container" style="display: none;">'
new_tag = '<section id="screen-explorer" class="screen-container">'

if old_tag in c:
    c = c.replace(old_tag, new_tag)
    with open("frontend/static/index.html", "w", encoding="utf-8") as f:
        f.write(c)
    print("Fixed #screen-explorer tag in index.html (removed style='display: none;')")
else:
    print("Old tag not found verbatim; checking regex...")
    import re
    c, count = re.subn(r'<section\s+id=["\']screen-explorer["\']\s+class=["\']screen-container["\']\s+style=["\'][^"\']*["\']>', '<section id="screen-explorer" class="screen-container">', c)
    if count > 0:
        with open("frontend/static/index.html", "w", encoding="utf-8") as f:
            f.write(c)
        print(f"Fixed {count} occurrence(s) via regex")
    else:
        print("No replacement made.")

