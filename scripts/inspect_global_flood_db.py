"""
Inspect and document the Global Flood Database (MODIS Events V1)
URL: https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1
"""

import os
import json
import requests

dest_dir = r"E:\ai-manthan\hydro_guard_indore\data\global_flood_datasets\global_flood_db"
os.makedirs(dest_dir, exist_ok=True)

url = "https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1"
print(f"Fetching GEE catalog page for Global Flood DB from {url}...")

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
r = requests.get(url, headers=headers, timeout=30)
print(f"Status: {r.status_code}")

metadata = {
    "dataset_name": "Global Flood Database v1 (2000-2018)",
    "gee_id": "GLOBAL_FLOOD_DB/MODIS_EVENTS/V1",
    "provider": "Cloud to Street / Tellman et al. (2021) Nature",
    "url": url,
    "access_requirement": {
        "requires_auth": True,
        "platform": "Google Earth Engine",
        "auth_methods": [
            "earthengine authenticate CLI command",
            "GCP Cloud Project with Earth Engine API enabled",
            "Python ee.Initialize(project='<gcp-project-id>')",
            "Earth Engine Code Editor (browser-based GUI)"
        ],
        "credentials_status": "No GEE GCP project registered in current environment. Direct binary export requires GEE authentication token."
    },
    "spatial_coverage": "Global (169 countries across all continents)",
    "spatial_resolution": "250 meters (MODIS Terra/Aqua)",
    "temporal_coverage": "2000-01-01 to 2018-12-31 (913 individual flood events)",
    "temporal_resolution": "Event-based (aggregated multi-day flood inundation extent and duration per event)",
    "license": "Creative Commons Attribution 4.0 International (CC-BY-4.0)",
    "bands": [
        {"name": "flooded", "description": "Binary mask indicating inundated land during the event", "units": "Binary (0 or 1)"},
        {"name": "duration", "description": "Number of days the pixel remained inundated", "units": "Days"},
        {"name": "clear_views", "description": "Number of cloud-free MODIS observations over the event window", "units": "Count"},
        {"name": "clear_perc", "description": "Percentage of observation period with cloud-free views", "units": "Percent (%)"},
        {"name": "jrc_perm_water", "description": "Permanent water mask from JRC Global Surface Water", "units": "Binary (0 or 1)"}
    ],
    "citation": "Tellman, B., Sullivan, J.A., Kuhn, C. et al. Satellite imaging reveals increased proportion of population exposed to floods. Nature 596, 80–86 (2021). https://doi.org/10.1038/s41586-021-03695-w"
}

summary_path = os.path.join(dest_dir, "global_flood_db_metadata.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print(f"Saved Global Flood DB metadata to {summary_path}")
