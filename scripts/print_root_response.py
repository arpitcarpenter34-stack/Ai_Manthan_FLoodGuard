import urllib.request

req = urllib.request.urlopen("http://127.0.0.1:8000/")
html = req.read().decode('utf-8')
print("--- RESPONSE FROM http://127.0.0.1:8000/ ---")
print(html)

