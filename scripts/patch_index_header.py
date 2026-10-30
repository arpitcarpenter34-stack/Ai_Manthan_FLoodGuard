with open('frontend/static/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

old = '''          <div class="rm-header-row">
            <div>
              <h2 class="rm-page-title">Reports & Monitoring</h2>'''

new = '''          <div class="rm-header-row">
            <div style="display: flex; align-items: center; gap: 14px;">
              <button class="btn-page-back" onclick="navigateToHome()" title="Back to Homepage" style="margin: 0; background: #ffffff; border: 1px solid #cbd5e1; color: #0284c7; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-radius: 8px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="19" y1="12" x2="5" y2="12"></line>
                  <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
              </button>
              <div>
                <h2 class="rm-page-title">Reports & Monitoring</h2>'''

# Normalize newlines if needed
if old.replace('\r\n', '\n') in text.replace('\r\n', '\n'):
    text = text.replace('\r\n', '\n')
    old_clean = old.replace('\r\n', '\n')
    new_clean = new.replace('\r\n', '\n')
    text = text.replace(old_clean, new_clean, 1)
    with open('frontend/static/index.html', 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print("SUCCESS: index.html updated")
else:
    print("FAILED: old string not found")

