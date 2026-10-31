with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("app.js?v=3.92", "app.js?v=3.93")

with open("frontend/static/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Bumped app.js to v=3.93.")

