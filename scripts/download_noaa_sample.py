import os
import gzip
import shutil
import requests
import pandas as pd

dest_dir = r"E:\ai-manthan\hydro_guard_indore\data\global_flood_datasets\noaa"
os.makedirs(dest_dir, exist_ok=True)

# 2023 details file
filename = "StormEvents_details-ftp_v1.0_d2023_c20260323.csv.gz"
url = f"https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/{filename}"
gz_path = os.path.join(dest_dir, filename)
csv_name = filename.replace(".gz", "")
csv_path = os.path.join(dest_dir, csv_name)

if not os.path.exists(csv_path):
    print(f"Downloading {filename} from NCEI NOAA...")
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    with open(gz_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    print(f"Downloaded {filename} ({round(os.path.getsize(gz_path)/(1024*1024), 2)} MB). Extracting...")
    
    with gzip.open(gz_path, 'rb') as f_in:
        with open(csv_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Extracted to {csv_path} ({round(os.path.getsize(csv_path)/(1024*1024), 2)} MB)!")

# Analyze flood events
print(f"Analyzing {csv_path}...")
df = pd.read_csv(csv_path, low_memory=False)
print(f"Total storm events in 2023: {len(df)}")
print(f"Columns: {list(df.columns)}")

# Filter flood events
flood_events = df[df['EVENT_TYPE'].str.contains('Flood|Flash', case=False, na=False)]
print(f"Total flood/flash flood events in 2023: {len(flood_events)}")
print("Event type distribution:")
print(flood_events['EVENT_TYPE'].value_counts())

# Save flood-specific subset
flood_subset_path = os.path.join(dest_dir, "noaa_storm_events_2023_floods.csv")
flood_events.to_csv(flood_subset_path, index=False)
print(f"Saved flood subset ({len(flood_events)} rows) to {flood_subset_path}")

# Check missingness on flood events
summary = {
    "total_records": len(df),
    "flood_records": len(flood_events),
    "event_types": flood_events['EVENT_TYPE'].value_counts().to_dict(),
    "sample_record": flood_events.iloc[0].dropna().to_dict()
}
import json
with open(os.path.join(dest_dir, "noaa_dataset_summary.json"), "w") as f:
    json.dump(summary, f, indent=2, default=str)
print("Saved summary to noaa_dataset_summary.json")

