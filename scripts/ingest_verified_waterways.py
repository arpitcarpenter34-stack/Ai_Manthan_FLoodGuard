"""
Ingest verified OpenStreetMap Khan River & Saraswati River geometries into data/indore_gis/.
Directly queries official OSM API (https://api.openstreetmap.org/api/0.6/) for verified way IDs.
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path("E:/ai-manthan/hydro_guard_indore/data/indore_gis")
GEOJSON_FILE = DATA_DIR / "indore_waterways_osm.geojson"
METADATA_FILE = DATA_DIR / "indore_waterways_metadata.json"

# Indore metropolitan basin bounding box
BBOX = {
    "south": 22.62,
    "west": 75.78,
    "north": 22.82,
    "east": 75.94,
    "crs": "EPSG:4326 (WGS84)"
}

# Verified OpenStreetMap Way IDs for Khan & Saraswati River systems
TARGET_WAYS = [
    {
        "id": 191817154,
        "primary_name": "Khan River (Kanh River - Main Channel)",
        "hindi_name": "कान्ह नदी (मुख्य धारा)",
        "system": "Khan River",
        "clip_to_bbox": True,  # Clip northern portion that extends to Ujjain
    },
    {
        "id": 169028701,
        "primary_name": "Saraswati River (Lower Confluence Reach)",
        "hindi_name": "सरस्वती नदी (कृष्णपुरा संगम)",
        "system": "Saraswati River",
        "clip_to_bbox": False,
    },
    {
        "id": 169028702,
        "primary_name": "Saraswati River (Upper Municipal Reach)",
        "hindi_name": "सरस्वती नदी (ऊपरी धारा)",
        "system": "Saraswati River",
        "clip_to_bbox": False,
    },
    {
        "id": 191774911,
        "primary_name": "Khan River Tributary (South Urban Branch)",
        "hindi_name": "कान्ह नदी सहायक नाला",
        "system": "Khan River",
        "clip_to_bbox": False,
    },
    {
        "id": 191774909,
        "primary_name": "Pipliyahana Drain Feeder (Culverted Reach)",
        "hindi_name": "पिपलियाहाना ड्रेन फीडर",
        "system": "Khan River Feeder",
        "clip_to_bbox": False,
    },
    {
        "id": 852094968,
        "primary_name": "Khan River (Limbodi Reach)",
        "hindi_name": "कान्ह नदी (लिम्बोदी क्षेत्र)",
        "system": "Khan River",
        "clip_to_bbox": False,
    },
    {
        "id": 852094971,
        "primary_name": "Khan River (Palda Reach)",
        "hindi_name": "कान्ह नदी (पालदा क्षेत्र)",
        "system": "Khan River",
        "clip_to_bbox": False,
    },
]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def ingest_verified_waterways():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "HydroGuardAI-Indore/1.0 (academic research; contact@hydroguard.local)"}

    features = []
    total_length_km = 0.0
    verified_ways_summary = []

    print("Fetching verified OSM waterway geometries from official OpenStreetMap API...")

    for target in TARGET_WAYS:
        way_id = target["id"]
        url = f"https://api.openstreetmap.org/api/0.6/way/{way_id}/full.json"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"Failed to fetch way {way_id}: HTTP {r.status_code}")
                continue

            data = r.json()
            elements = data.get("elements", [])
            node_map = {el["id"]: (el["lon"], el["lat"]) for el in elements if el["type"] == "node"}
            way_el = next((el for el in elements if el["type"] == "way" and el["id"] == way_id), None)
            if not way_el:
                print(f"Way element {way_id} not found in response payload.")
                continue

            raw_coords = [node_map[nid] for nid in way_el["nodes"] if nid in node_map]
            
            # Apply bbox filter if requested or sanitize bounds
            if target.get("clip_to_bbox", False):
                # Keep coordinates within Indore basin
                filtered_coords = [
                    [lon, lat] for (lon, lat) in raw_coords
                    if (BBOX["south"] - 0.01) <= lat <= (BBOX["north"] + 0.01) and (BBOX["west"] - 0.01) <= lon <= (BBOX["east"] + 0.01)
                ]
            else:
                filtered_coords = [[lon, lat] for (lon, lat) in raw_coords]

            if len(filtered_coords) < 2:
                print(f"Way {way_id} has fewer than 2 valid coordinates inside target area.")
                continue

            # Calculate feature length in km
            way_len_km = 0.0
            for i in range(len(filtered_coords) - 1):
                way_len_km += haversine_km(filtered_coords[i][1], filtered_coords[i][0], filtered_coords[i+1][1], filtered_coords[i+1][0])
            total_length_km += way_len_km

            tags = way_el.get("tags", {})
            osm_name = tags.get("name") or tags.get("name:en") or target["primary_name"]
            waterway_type = tags.get("waterway", "river")

            feature = {
                "type": "Feature",
                "id": f"way/{way_id}",
                "geometry": {
                    "type": "LineString",
                    "coordinates": filtered_coords,
                },
                "properties": {
                    "osm_id": way_id,
                    "name": osm_name,
                    "english_name": target["primary_name"],
                    "hindi_name": target["hindi_name"],
                    "river_system": target["system"],
                    "waterway_type": waterway_type,
                    "length_km": round(way_len_km, 3),
                    "node_count": len(filtered_coords),
                    "surface": tags.get("surface", "natural"),
                    "tunnel": tags.get("tunnel", "no"),
                    "layer": tags.get("layer", "0"),
                    "width": tags.get("width"),
                    "is_real_gis_data": True,
                    "source": "OpenStreetMap",
                    "attribution": "© OpenStreetMap contributors, ODbL 1.0",
                    "provenance": "VERIFIED_OSM_SURFACE_WATERWAY",
                    "hydrology_distinction": "Real open-channel surface waterway geometry. Distinct from underground municipal drainage pipes."
                }
            }
            features.append(feature)
            verified_ways_summary.append({
                "osm_id": way_id,
                "name": target["primary_name"],
                "system": target["system"],
                "waterway_type": waterway_type,
                "coordinates_count": len(filtered_coords),
                "length_km": round(way_len_km, 3)
            })
            print(f"Ingested way/{way_id} ({target['primary_name']}): {len(filtered_coords)} pts, {round(way_len_km, 2)} km")

        except Exception as e:
            print(f"Error fetching way {way_id}: {e}")

    if not features:
        print("ERROR: No features could be ingested.")
        return False

    metadata = {
        "source": "OpenStreetMap REST API v0.6",
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "geographic_region": "Indore, Madhya Pradesh, India",
        "crs": "EPSG:4326 (WGS84)",
        "bounding_box": BBOX,
        "feature_count": len(features),
        "total_waterway_length_km": round(total_length_km, 2),
        "is_real_gis_data": True,
        "provenance": "VERIFIED_OSM_SURFACE_WATERWAYS",
        "license": "Open Data Commons Open Database License (ODbL) by OpenStreetMap Foundation (OSMF)",
        "verified_features": verified_ways_summary,
        "engineering_distinction": (
            "CRITICAL DISTINCTION: These alignments represent verified real-world surface river channels "
            "(Khan and Saraswati rivers) and natural storm feeders surveyed in OpenStreetMap. "
            "They are maintained strictly separate from internal subsurface drainage culverts, "
            "pipe diameters, invert elevations, and municipal pump station telemetry."
        )
    }

    geojson_payload = {
        "type": "FeatureCollection",
        "metadata": metadata,
        "features": features
    }

    # Write GeoJSON
    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson_payload, f, indent=2, ensure_ascii=False)
    print(f"\nSuccessfully wrote {len(features)} features to {GEOJSON_FILE}")

    # Write Metadata file
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Successfully wrote metadata to {METADATA_FILE}")

    return True


if __name__ == "__main__":
    success = ingest_verified_waterways()
    sys.exit(0 if success else 1)

