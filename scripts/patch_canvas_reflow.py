with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    content = f.read()

# Update loadFloodDriversAnalysis to use setTimeout
old_drivers_func = """function loadFloodDriversAnalysis() {
  drawPermutationImportanceChart();
  drawTemporalLagDecayChart();
}"""

new_drivers_func = """function loadFloodDriversAnalysis() {
  setTimeout(() => {
    drawPermutationImportanceChart();
    drawTemporalLagDecayChart();
  }, 100);
}"""
content = content.replace(old_drivers_func, new_drivers_func)

# Update drawPermutationImportanceChart
old_imp_w = "const w = canvas.width = canvas.parentElement.clientWidth;"
new_imp_w = "const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 600;\n  const w = canvas.width = parentW > 50 ? parentW : 600;"
content = content.replace(old_imp_w, new_imp_w)

# Update drawTemporalLagDecayChart
old_lag_w = "const w = canvas.width = canvas.parentElement.clientWidth;"
# Notice if there's a second occurrence
content = content.replace(old_imp_w, new_imp_w)

with open("frontend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated canvas width calculation in app.js.")

