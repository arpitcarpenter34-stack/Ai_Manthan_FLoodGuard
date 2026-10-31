"""
Download a representative ERA5 & ERA5-Land hourly meteorological reanalysis sample
for the Potomac River (USGS 01646500: 38.9498 N, 77.1276 W) and
Aroostook River (CAMELSH 01017000: 46.7773 N, 68.1572 W).
Variables:
- precipitation (mm)
- temperature_2m (°C)
- relative_humidity_2m (%)
- wind_speed_10m (m/s)
- surface_pressure (hPa)
- soil_moisture_0_to_7cm (m3/m3) - ERA5-Land
- soil_moisture_7_to_28cm (m3/m3) - ERA5-Land
- surface_runoff (mm)
"""

import os
import json
import requests
import pandas as pd

dest_dir = r"E:\ai-manthan\hydro_guard_indore\data\global_flood_datasets\era5"
os.makedirs(dest_dir, exist_ok=True)

sites = [
    {
        "name": "potomac_usgs_01646500",
        "lat": 38.9498,
        "lon": -77.1276,
        "desc": "Potomac River Little Falls Pump Station (USGS)"
    },
    {
        "name": "aroostook_camelsh_01017000",
        "lat": 46.7773,
        "lon": -68.1572,
        "desc": "Aroostook River at Washburn, ME (CAMELSH)"
    }
]

# Fetch 1 full month of real hourly ERA5 reanalysis (e.g., 2023-07-01 to 2023-07-31)
start_date = "2023-07-01"
end_date = "2023-07-31"

hourly_vars = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "surface_pressure",
    "wind_speed_10m",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm"
]
vars_param = ",".join(hourly_vars)

all_dfs = []

for s in sites:
    url = f"https://archive-api.open-meteo.com/v1/era5?latitude={s['lat']}&longitude={s['lon']}&start_date={start_date}&end_date={end_date}&hourly={vars_param}"
    print(f"Fetching ERA5 hourly data for {s['name']} ({s['lat']}, {s['lon']})...")
    r = requests.get(url, timeout=60)
    if r.status_code == 200:
        data = r.json()
        raw_json_path = os.path.join(dest_dir, f"era5_{s['name']}_raw.json")
        with open(raw_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        hourly = data.get("hourly", {})
        df_site = pd.DataFrame(hourly)
        df_site["site_name"] = s["name"]
        df_site["latitude"] = s["lat"]
        df_site["longitude"] = s["lon"]
        df_site["description"] = s["desc"]
        all_dfs.append(df_site)
        print(f"  Successfully fetched {len(df_site)} hourly rows for {s['name']}")
    else:
        print(f"  Error fetching {s['name']}: {r.status_code} - {r.text[:200]}")

if all_dfs:
    combined_df = pd.concat(all_dfs, ignore_index=True)
    csv_path = os.path.join(dest_dir, "era5_hourly_reanalysis_sample.csv")
    combined_df.to_csv(csv_path, index=False)
    print(f"Saved combined ERA5 hourly reanalysis to {csv_path} ({len(combined_df)} rows)")

    summary = {
        "dataset_name": "ERA5 & ERA5-Land Hourly Reanalysis",
        "provider": "ECMWF Copernicus Climate Change Service (C3S) / Open-Meteo Historical Archive",
        "spatial_resolution": "0.25° (ERA5 Atmospheric) / 0.1° (ERA5-Land)",
        "temporal_resolution": "Hourly",
        "sample_period": f"{start_date} to {end_date}",
        "total_hourly_records": len(combined_df),
        "variables_acquired": hourly_vars,
        "sites_sampled": sites
    }
    with open(os.path.join(dest_dir, "era5_dataset_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Saved ERA5 summary JSON!")

