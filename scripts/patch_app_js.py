from pathlib import Path

p = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\static\js\app.js")
text = p.read_text(encoding="utf-8")

old = 'loadSimulatorOptimization();\n  }'
new = 'loadSimulatorOptimization();\n  } else if (screenId === "model-intel") {\n    loadModelIntelligenceDashboard();\n  }'

if old in text:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("Patched with LF")
else:
    old_crlf = 'loadSimulatorOptimization();\r\n  }'
    new_crlf = 'loadSimulatorOptimization();\r\n  } else if (screenId === "model-intel") {\r\n    loadModelIntelligenceDashboard();\r\n  }'
    if old_crlf in text:
        text = text.replace(old_crlf, new_crlf, 1)
        p.write_text(text, encoding="utf-8")
        print("Patched with CRLF")
    else:
        print("Could not find trigger marker!")
