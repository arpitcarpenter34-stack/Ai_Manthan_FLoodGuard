import requests
import json

url = "https://nominatim.openstreetmap.org/search"
headers = {"User-Agent": "HydroGuardAI-Indore/1.0 (academic research; contact@hydroguard.local)"}

queries = [
    "Khan River, Indore",
    "Saraswati, Indore",
    "Khan River, Madhya Pradesh",
    "Saraswati River, Indore",
    "Kahn River, Indore"
]

results = []
seen_ids = set()

for q in queries:
    try:
        r = requests.get(url, params={"q": q, "format": "json", "polygon_geojson": 1, "extratags": 1}, headers=headers, timeout=10)
        if r.status_code == 200:
            items = r.json()
            for it in items:
                osm_type = it.get("osm_type")
                osm_id = it.get("osm_id")
                key = f"{osm_type}/{osm_id}"
                if key not in seen_ids:
                    seen_ids.add(key)
                    results.append(it)
    except Exception as e:
        print(f"Error on query {q}: {e}")

print(f"Found {len(results)} distinct OSM candidate features:")
for it in results:
    osm_type = it.get("osm_type")
    osm_id = it.get("osm_id")
    cls = it.get("class")
    typ = it.get("type")
    geo = it.get("geojson", {})
    coords = geo.get("coordinates", [])
    disp = it.get("display_name", "")
    print(f"- [{osm_type}/{osm_id}] class={cls}, type={typ}, geo={geo.get('type')} ({len(coords)} pts)")
    print(f"  Name: {disp}")
    print(f"  Bbox: {it.get('boundingbox')}")
    # print sample coordinate to verify Indore bounds [22.62-22.82, 75.78-75.94]
    if coords and isinstance(coords[0], list):
        first_coord = coords[0]
        if isinstance(first_coord[0], list):
            first_coord = first_coord[0]
        print(f"  Start Coord: lon={first_coord[0]}, lat={first_coord[1]}")

