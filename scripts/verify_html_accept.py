import urllib.request

req = urllib.request.Request("http://127.0.0.1:8000/", headers={"Accept": "text/html,application/xhtml+xml"})
with urllib.request.urlopen(req) as response:
    html = response.read().decode('utf-8')

print(f"HTML length with text/html: {len(html)}")
print("Has 'Urban Drainage & Flood Intelligence Platform':", "Urban Drainage & Flood Intelligence Platform" in html)
print("Has 'screen-explorer':", "screen-explorer" in html)
print("Has 'screen-weather-radar':", "screen-weather-radar" in html)
print("Has 'screen-drivers':", "screen-drivers" in html)
print("Has 'screen-model-intel':", "screen-model-intel" in html)

