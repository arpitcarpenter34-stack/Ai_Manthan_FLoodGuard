"""
Fetch connected USGS stream gauges along the Potomac River basin.
Nodes:
1. 01638500 - POTOMAC RIVER AT POINT OF ROCKS, MD (Upstream node 1)
2. 01643000 - MONOCACY RIVER AT JUG BRIDGE NEAR FREDERICK, MD (Tributary node)
3. 01644000 - SENECA CREEK AT DAWSONVILLE, MD (Tributary node)
4. 01646500 - POTOMAC RIVER NEAR WASH, DC LITTLE FALLS PUMP STA (Downstream mainstem node)
5. 01647600 - NORTHWEST BRANCH ANACOSTIA RIVER NEAR HYATTSVILLE, MD (Urban drainage tributary)

Parameters:
- 00060: Discharge (Streamflow in ft3/s -> converted to m3/s)
- 00065: Gage height (Water level in ft -> converted to m)
Period: Past 30 days continuous observations (15-minute to hourly)
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime

sites = ["01638500", "01643000", "01644000", "01646500", "01647600"]
sites_str = ",".join(sites)
url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={sites_str}&period=P14D&parameterCd=00060,00065"

out_dir = r"E:\ai-manthan\hydro_guard_indore\data\global_flood_datasets\usgs"
os.makedirs(out_dir, exist_ok=True)

print(f"Fetching USGS data for sites: {sites_str}...")
r = requests.get(url, timeout=60)
if r.status_code == 200:
    data = r.json()
    raw_path = os.path.join(out_dir, "usgs_potomac_raw_14d.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"Saved raw USGS json to {raw_path}")

    # Parse into structured tabular records
    time_series = data.get("value", {}).get("timeSeries", [])
    stations_meta = {}
    records = []

    for ts in time_series:
        source_info = ts.get("sourceInfo", {})
        site_code = source_info.get("siteCode", [{}])[0].get("value")
        site_name = source_info.get("siteName")
        lat = source_info.get("geoLocation", {}).get("geogLocation", {}).get("latitude")
        lon = source_info.get("geoLocation", {}).get("geogLocation", {}).get("longitude")
        var_info = ts.get("variable", {})
        var_code = var_info.get("variableCode", [{}])[0].get("value")
        var_desc = var_info.get("variableDescription")
        unit = var_info.get("unit", {}).get("unitCode")

        if site_code not in stations_meta:
            stations_meta[site_code] = {
                "site_code": site_code,
                "site_name": site_name,
                "latitude": lat,
                "longitude": lon,
                "variables": []
            }
        stations_meta[site_code]["variables"].append({"code": var_code, "desc": var_desc, "unit": unit})

        values = ts.get("values", [{}])[0].get("value", [])
        for v in values:
            dt_str = v.get("dateTime")
            val = v.get("value")
            qualifiers = ",".join(v.get("qualifiers", []))
            try:
                num_val = float(val)
            except (ValueError, TypeError):
                num_val = None
            
            records.append({
                "site_code": site_code,
                "site_name": site_name,
                "latitude": lat,
                "longitude": lon,
                "variable_code": var_code,
                "variable_name": var_desc,
                "unit": unit,
                "timestamp": dt_str,
                "value": num_val,
                "qualifiers": qualifiers
            })

    df = pd.DataFrame(records)
    csv_path = os.path.join(out_dir, "usgs_potomac_observations.csv")
    df.to_csv(csv_path, index=False)
    print(f"Parsed {len(df)} observations across {len(stations_meta)} stations to {csv_path}")

    meta_path = os.path.join(out_dir, "usgs_potomac_stations.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(stations_meta, f, indent=2)
    print(f"Saved stations metadata to {meta_path}")

    # Also build a pivot table with hourly resampled values for graph alignment
    # Convert discharge to m3/s (1 cfs = 0.0283168 m3/s) and gage height to m (1 ft = 0.3048 m)
    pivot_records = []
    df['dt'] = pd.to_datetime(df['timestamp'])
    
    summary = {
        "station_count": len(stations_meta),
        "total_records": len(df),
        "date_min": str(df['dt'].min()),
        "date_max": str(df['dt'].max()),
        "stations": stations_meta
    }
    with open(os.path.join(out_dir, "usgs_dataset_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
else:
    print(f"Error fetching USGS data: {r.status_code} - {r.text[:300]}")

