import os
import sys
import json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# Blue Heart inspect
bh_npz_path = "data/processed_global/urban_sequences/blue_heart_sequences_w12_h3.npz"
if os.path.exists(bh_npz_path):
    bh = np.load(bh_npz_path, allow_pickle=True)
    print("Blue Heart w12_h3 keys:", list(bh.keys()))
    for k in bh.keys():
        v = bh[k]
        if hasattr(v, 'shape'):
            print(f"  {k}: shape {v.shape}, dtype {v.dtype}")
        elif isinstance(v, list) or isinstance(v, dict):
            print(f"  {k}: len {len(v)}")
        else:
            print(f"  {k}: {type(v)}")

# Blue Heart node ids
bh_nodes_path = "data/processed_global/urban_graphs/blue_heart_gully_node_ids.json"
if os.path.exists(bh_nodes_path):
    with open(bh_nodes_path) as f:
        node_ids = json.load(f)
    print(f"Blue Heart Gully Nodes ({len(node_ids)}):", node_ids)

# CWPRS inspect
cwprs_path = "data/urban_drainage_datasets/india_cwprs/rainfall_tel_hr_cwprs_mh_2021_2025.csv"
if os.path.exists(cwprs_path):
    df_cw = pd.read_csv(cwprs_path)
    print("\nCWPRS shape:", df_cw.shape)
    print("CWPRS columns:", list(df_cw.columns))
    print("CWPRS head:\n", df_cw.head(3))
    print("CWPRS date range:", df_cw.iloc[0, 0], "to", df_cw.iloc[-1, 0])
    rain_col = df_cw.columns[1]
    print(f"Rainfall stats ({rain_col}):")
    print(df_cw[rain_col].describe())

# USGS Potomac inspect
usgs_csv = "data/global_flood_datasets/usgs/usgs_hourly_potomac_sample.csv"
if os.path.exists(usgs_csv):
    df_u = pd.read_csv(usgs_csv)
    print("\nUSGS Potomac shape:", df_u.shape)
    print("USGS Potomac columns:", list(df_u.columns))
    print("USGS Potomac stations:", df_u['site_code'].unique() if 'site_code' in df_u.columns else 'N/A')

