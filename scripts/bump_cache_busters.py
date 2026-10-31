with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("style.css?v=3.8", "style.css?v=3.9")
content = content.replace("app.js?v=3.8", "app.js?v=3.9")

with open("frontend/static/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Bumped cache busters to v=3.9.")

