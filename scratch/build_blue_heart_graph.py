import os
import sys
import json
import glob
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

base_urban = r"E:\ai-manthan\hydro_guard_indore\data\urban_drainage_datasets"
out_graph_dir = r"E:\ai-manthan\hydro_guard_indore\data\processed_global\urban_graphs"
os.makedirs(out_graph_dir, exist_ok=True)

# 3. BLUE HEART ROAD GULLY SUBGRAPH (15 GULLIES)
print("\n--- 3. BUILDING BLUE HEART ROAD GULLY SUBGRAPH (15 SENSORS) ---")
bh_gully_files = sorted(glob.glob(os.path.join(base_urban, "blue_heart", "highway_gully_telemetry", "**", "*.csv"), recursive=True))
bh_gully_files = [f for f in bh_gully_files if "quality" not in f]
gully_names = [os.path.basename(f).replace(".csv", "") for f in bh_gully_files]
N_gully = len(gully_names)
print(f"Blue Heart Monitored Gullies found: {N_gully}")

bh_idx_csv = os.path.join(base_urban, "blue_heart", "index_telemetry_data.csv")
df_idx = pd.read_csv(bh_idx_csv)
gully_coords = {}
for _, row in df_idx.iterrows():
    loc = str(row['locationName'])
    for gn in gully_names:
        prefix = gn.split('_')[0]
        if prefix in loc or gn in loc:
            gully_coords[gn] = (float(row['locationLatitude']), float(row['locationLongitude']))

print(f"Matched Gully Coordinates: {len(gully_coords)} of {N_gully}")
for gn in gully_names:
    if gn not in gully_coords:
        # Default nearby within Eastbourne urban grid
        gully_coords[gn] = (50.77 + np.random.uniform(-0.01, 0.01), 0.28 + np.random.uniform(-0.01, 0.01))

A_gully = np.zeros((N_gully, N_gully), dtype=np.float32)
sigma = 2000.0

for i, g1 in enumerate(gully_names):
    c1 = gully_coords[g1]
    for j, g2 in enumerate(gully_names):
        if i == j:
            A_gully[i, j] = 1.0
        else:
            c2 = gully_coords[g2]
            d_lat = (c1[0] - c2[0]) * 111000.0
            d_lon = (c1[1] - c2[1]) * 111000.0 * np.cos(np.radians(c1[0]))
            dist = np.sqrt(d_lat**2 + d_lon**2)
            if dist < 5000.0:
                A_gully[i, j] = float(np.exp(-(dist**2) / (sigma**2)))

print(f"Blue Heart Gully Adjacency Shape: {A_gully.shape}, Non-zeros: {np.count_nonzero(A_gully)}")

np.save(os.path.join(out_graph_dir, "blue_heart_gully_adjacency.npy"), A_gully)
with open(os.path.join(out_graph_dir, "blue_heart_gully_node_ids.json"), "w") as f:
    json.dump({
        'sensors': gully_names,
        'total_sensors': N_gully,
        'coordinates': gully_coords
    }, f, indent=2)

print("Blue Heart gully graph artifacts saved to:", out_graph_dir)

