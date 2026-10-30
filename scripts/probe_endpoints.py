import requests
import json
import time

bbox = "22.62,75.78,22.82,75.94"
query = f"""[out:json][timeout:15];
(
  way["waterway"~"river|stream|drain|canal"]({bbox});
);
out geom;"""

endpoints = [
    ("overpass-api.de", "https://overpass-api.de/api/interpreter"),
    ("maps.mail.ru", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"),
    ("overpass.nchc.org.tw", "https://overpass.nchc.org.tw/api/interpreter"),
    ("overpass.openstreetmap.ru", "https://overpass.openstreetmap.ru/api/interpreter"),
    ("lz4.overpass-api.de", "https://lz4.overpass-api.de/api/interpreter"),
    ("kumi.systems", "https://overpass.kumi.systems/api/interpreter"),
    ("private.coffee", "https://overpass.private.coffee/api/interpreter")
]

headers = {
    "User-Agent": "HydroGuardAI/1.0 (Urban Drainage Research; contact@hydroguard.local)"
}

print("=== OVERPASS ENDPOINT PROBE RESULTS ===", flush=True)

for name, url in endpoints:
    print(f"\n[PROBING] {name} ({url})", flush=True)
    t0 = time.time()
    try:
        r = requests.post(url, data={"data": query}, headers=headers, timeout=12)
        elapsed = round(time.time() - t0, 2)
        print(f"HTTP Status: {r.status_code} ({r.reason}) | Time: {elapsed}s", flush=True)
        content_type = r.headers.get("Content-Type", "unknown")
        print(f"Content-Type: {content_type} | Content Length: {len(r.content)} bytes", flush=True)
        
        if r.status_code == 200:
            try:
                data = r.json()
                elems = data.get("elements", [])
                print(f"JSON Parsed successfully. Features retrieved: {len(elems)}", flush=True)
                if len(elems) > 0:
                    names = set(el.get("tags", {}).get("name") for el in elems if "name" in el.get("tags", {}))
                    print(f"Named waterways found: {list(names)[:5]}", flush=True)
            except Exception as e:
                print(f"JSON Parse Error: {e}. Raw text snippet: {r.text[:200]}", flush=True)
        else:
            print(f"Error Body Snippet: {r.text[:300].strip()}", flush=True)
            
    except requests.exceptions.Timeout:
        elapsed = round(time.time() - t0, 2)
        print(f"TIMEOUT: Connection timed out after {elapsed}s", flush=True)
    except requests.exceptions.SSLError as e:
        print(f"SSL ERROR: {e}", flush=True)
    except requests.exceptions.ConnectionError as e:
        print(f"CONNECTION ERROR: {e}", flush=True)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}", flush=True)

