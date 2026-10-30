"""
Fetch real Indore waterways from OpenStreetMap Overpass API and save GeoJSON and metadata.
Audited Bounding Box: [22.62, 75.78, 22.82, 75.94]
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests

DATA_DIR = Path("E:/ai-manthan/hydro_guard_indore/data/indore_gis")
GEOJSON_FILE = DATA_DIR / "indore_waterways_osm.geojson"
METADATA_FILE = DATA_DIR / "indore_waterways_metadata.json"

BBOX = [22.62, 75.78, 22.82, 75.94]  # south, west, north, east
OVERPASS_QUERY = f"""[out:json][timeout:50][bbox:{BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]}];
(
  way["waterway"~"^(river|stream|drain|canal)$"];
);
out geom;
"""

ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def fetch_osm_waterways():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    response_data = None
    successful_endpoint = None

    headers = {
        "User-Agent": "HydroGuardAI/1.0 (Indore Urban Drainage and Flash Flood Predictive Management System; research/educational)"
    }

    for ep in ENDPOINTS:
        try:
            print(f"Querying Overpass API: {ep}...")
            r = requests.post(ep, data={"data": OVERPASS_QUERY}, headers=headers, timeout=40)
            if r.status_code == 200:
                response_data = r.json()
                successful_endpoint = ep
                print(f"Success from {ep}!")
                break
            else:
                print(f"Endpoint {ep} returned status {r.status_code}")
        except Exception as e:
            print(f"Failed querying {ep}: {e}")

    if not response_data or "elements" not in response_data:
        print("ERROR: Could not fetch from Overpass API.")
        return False

    elements = response_data["elements"]
    print(f"Retrieved {len(elements)} raw waterway elements from OpenStreetMap.")

    features = []
    total_length_km = 0.0
    named_waterways = set()
    waterway_types = {}

    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        
        geom = el["geometry"]
        if len(geom) < 2:
            continue

        coordinates = [[pt["lon"], pt["lat"]] for pt in geom]
        
        # Calculate length of this way
        way_len = 0.0
        for i in range(len(coordinates) - 1):
            way_len += haversine_km(coordinates[i][1], coordinates[i][0], coordinates[i+1][1], coordinates[i+1][0])
        total_length_km += way_len

        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or tags.get("name:hi") or "Unnamed Drain/Channel"
        wtype = tags.get("waterway", "drain")
        
        waterway_types[wtype] = waterway_types.get(wtype, 0) + 1
        if tags.get("name"):
            named_waterways.add(tags["name"])

        feature = {
            "type": "Feature",
            "id": f"way/{el['id']}",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates,
            },
            "properties": {
                "osm_id": el["id"],
                "name": name,
                "waterway": wtype,
                "length_km": round(way_len, 3),
                "is_real_gis_data": True,
                "source": "OpenStreetMap",
                "tunnel": tags.get("tunnel"),
                "covered": tags.get("covered"),
                "layer": tags.get("layer"),
                "surface": tags.get("surface"),
            }
        }
        features.append(feature)

    geojson_collection = {
        "type": "FeatureCollection",
        "metadata": {
            "source": "OpenStreetMap Overpass API",
            "endpoint": successful_endpoint,
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
            "bounding_box": {
                "south": BBOX[0],
                "west": BBOX[1],
                "north": BBOX[2],
                "east": BBOX[3],
                "crs": "EPSG:4326 (WGS84)"
            },
            "tags_queried": ["river", "stream", "drain", "canal"],
            "feature_count": len(features),
            "total_waterway_length_km": round(total_length_km, 2),
            "waterway_breakdown": waterway_types,
            "named_waterways": sorted(list(named_waterways)),
            "provenance": "REAL_GIS_DATA",
            "is_real_gis_data": True,
            "hydrological_notes": (
                "Waterway alignments represent real surface open-channel and river geometries from OpenStreetMap contributors. "
                "Subsurface conduit dimensions, pipe inverts, and localized flow friction factors are NOT present in OSM and are simulated."
            )
        },
        "features": features
    }

    # Save GeoJSON
    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson_collection, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(features)} GeoJSON features to {GEOJSON_FILE}")

    # Save Metadata summary
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson_collection["metadata"], f, indent=2, ensure_ascii=False)
    print(f"Saved metadata summary to {METADATA_FILE}")

    print("\nSummary:")
    print(f"- Total Features: {len(features)}")
    print(f"- Total Waterway Length: {round(total_length_km, 2)} km")
    print(f"- Breakdown by Type: {waterway_types}")
    print(f"- Named Waterways: {sorted(list(named_waterways))}")
    return True


if __name__ == "__main__":
    success = fetch_osm_waterways()
    sys.exit(0 if success else 1)

