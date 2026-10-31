with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'if (data.status !== "success" || !data.nodes) {',
    'if ((data.status !== "SUCCESS" && data.status !== "success") || !data.nodes) {'
)

with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated status check in app.js.")

