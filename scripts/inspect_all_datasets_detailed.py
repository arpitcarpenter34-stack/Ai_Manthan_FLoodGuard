"""
Detailed Inspection of all available datasets in the project.
Prints exact file paths, records, columns, and variable types.
"""

import os
import glob
import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(r"E:\ai-manthan\hydro_guard_indore")

print("=" * 80)
print(" HYDRO-GUARD AI — COMPREHENSIVE DATASET INVENTORY INSPECTION")
print("=" * 80)

# 1. Blue Heart
bh_npz_path = BASE_DIR / "data" / "processed_global" / "urban_sequences" / "blue_heart_sequences_w12_h3.npz"
if bh_npz_path.exists():
    bh_npz = np.load(bh_npz_path, allow_pickle=True)
    print(f"\n[1] Blue Heart NPZ: {bh_npz_path}")
    print(f"    Keys: {bh_npz.files}")
    print(f"    X shape: {bh_npz['X'].shape}, Y_level shape: {bh_npz['Y_level'].shape}")
    print(f"    Sensors ({len(bh_npz['sensor_names'])}): {list(bh_npz['sensor_names'])}")
    print(f"    Train: {len(bh_npz['train_idx'])}, Val: {len(bh_npz['val_idx'])}, Test: {len(bh_npz['test_idx'])}")

bh_csvs = list((BASE_DIR / "data" / "urban_drainage_datasets" / "blue_heart").rglob("*.csv"))
print(f"    Raw CSV files: {len(bh_csvs)}")
if bh_csvs:
    df0 = pd.read_csv(bh_csvs[0])
    print(f"    Sample CSV ({bh_csvs[0].name}): {len(df0)} rows, columns: {list(df0.columns)}")

# 2. CAMELS-Hourly
camels_csvs = list((BASE_DIR / "data" / "processed_global" / "camels_hourly_processed").glob("*_hourly_labeled.csv"))
print(f"\n[2] CAMELS-Hourly Processed CSVs: {len(camels_csvs)}")
total_camels_rows = 0
for f in camels_csvs:
    dfc = pd.read_csv(f, low_memory=False)
    total_camels_rows += len(dfc)
    print(f"    {f.name}: {len(dfc)} rows, cols: {list(dfc.columns[:7])}")
print(f"    Total CAMELS Records: {total_camels_rows}")

# 3. USGS NWIS Potomac
usgs_csvs = list((BASE_DIR / "data" / "processed_global" / "usgs_processed").glob("*_hourly_labeled.csv"))
print(f"\n[3] USGS NWIS Processed CSVs: {len(usgs_csvs)}")
total_usgs_rows = 0
for f in usgs_csvs:
    dfu = pd.read_csv(f, low_memory=False)
    total_usgs_rows += len(dfu)
    print(f"    {f.name}: {len(dfu)} rows, cols: {list(dfu.columns[:7])}")
print(f"    Total USGS Records: {total_usgs_rows}")

# 4. India CWPRS Telemetry
cwprs_files = list((BASE_DIR / "data" / "urban_drainage_datasets" / "india_cwprs").rglob("*.csv"))
print(f"\n[4] India CWPRS CSVs: {len(cwprs_files)}")
total_cwprs_rows = 0
for f in cwprs_files:
    dfcw = pd.read_csv(f)
    total_cwprs_rows += len(dfcw)
    print(f"    {f.name}: {len(dfcw)} rows, cols: {list(dfcw.columns)}")
print(f"    Total CWPRS Records: {total_cwprs_rows}")

# 5. Bellinge SWMM
bellinge_inp = BASE_DIR / "data" / "urban_drainage_datasets" / "bellinge" / "BellingeSWMM_v021_nopervious.inp"
bel_adj = BASE_DIR / "data" / "processed_global" / "urban_graphs" / "bellinge_adjacency.npy"
print(f"\n[5] Bellinge SWMM: {bellinge_inp.exists()}, Size: {bellinge_inp.stat().st_size if bellinge_inp.exists() else 0} bytes")
if bel_adj.exists():
    A = np.load(bel_adj)
    print(f"    Adjacency Matrix: shape {A.shape}, non-zero edges: {np.sum(A > 0)}")

# 6. UWO
uwo_adj = BASE_DIR / "data" / "processed_global" / "urban_graphs" / "uwo_adjacency.npy"
print(f"\n[6] UWO: {uwo_adj.exists()}")
if uwo_adj.exists():
    A_uwo = np.load(uwo_adj)
    print(f"    UWO Adjacency: shape {A_uwo.shape}, non-zero edges: {np.sum(A_uwo > 0)}")

# 7. ERA5 and NOAA
era5_files = list((BASE_DIR / "data" / "processed_global" / "era5_processed").glob("*.csv"))
noaa_files = list((BASE_DIR / "data" / "processed_global" / "noaa_flood_events_processed").glob("*.csv"))
print(f"\n[7] ERA5 Files: {len(era5_files)}, NOAA Flood Event Files: {len(noaa_files)}")
for f in era5_files:
    dfe = pd.read_csv(f)
    print(f"    ERA5 {f.name}: {len(dfe)} rows, cols: {list(dfe.columns)}")
for f in noaa_files:
    dfn = pd.read_csv(f)
    print(f"    NOAA {f.name}: {len(dfn)} rows, cols: {list(dfn.columns)}")

# 8. Radar Check
radar_files = list(BASE_DIR.rglob("*radar*"))
print(f"\n[8] Radar files found in repo: {len(radar_files)}")

