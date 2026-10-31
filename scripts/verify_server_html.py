import urllib.request

req = urllib.request.urlopen("http://127.0.0.1:8000/")
html = req.read().decode('utf-8')
print(f"HTML length: {len(html)}")
print("Has 'Urban Drainage & Flood Intelligence Platform':", "Urban Drainage & Flood Intelligence Platform" in html)
print("Has 'screen-explorer':", "screen-explorer" in html)
print("Has 'screen-weather-radar':", "screen-weather-radar" in html)
print("Has 'screen-drivers':", "screen-drivers" in html)
print("Has 'screen-model-intel':", "screen-model-intel" in html)

