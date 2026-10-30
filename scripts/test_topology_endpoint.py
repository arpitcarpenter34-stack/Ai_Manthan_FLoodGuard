import sys
import requests
sys.stdout.reconfigure(encoding="utf-8")

r = requests.get("http://127.0.0.1:8000/api/v1/flood/topology", timeout=5)
print("Status Code:", r.status_code)
data = r.json()
print("API Status:", data.get("status"))
print("Keys in Response:", list(data.keys()))

if "real_waterways" in data:
    rw = data["real_waterways"]
    features = rw.get("features", [])
    print(f"\nReal Waterways features returned: {len(features)}")
    for f in features:
        p = f.get("properties", {})
        print(f"  * [{f.get('id')}] {p.get('english_name')} ({p.get('river_system')}): {p.get('length_km')} km, {p.get('node_count')} nodes, is_real_gis_data={p.get('is_real_gis_data')}")

if "metadata" in data:
    md = data["metadata"]
    print(f"\nMetadata Summary:")
    print(f"  * Source: {md.get('source')}")
    print(f"  * Retrieval: {md.get('retrieval_timestamp')}")
    print(f"  * Region: {md.get('geographic_region')}")
    print(f"  * CRS: {md.get('crs')}")
    print(f"  * Total Length: {md.get('total_waterway_length_km')} km")
    print(f"  * Provenance: {md.get('provenance')}")
    print(f"  * License: {md.get('license')}")

if "geojson" in data:
    gj = data["geojson"]
    print(f"\nUnified GeoJSON features count: {len(gj.get('features', []))}")

