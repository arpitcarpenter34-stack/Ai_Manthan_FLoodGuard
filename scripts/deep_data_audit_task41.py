import os
import sys
import json
import glob
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("HYDRO-GUARD AI — TASK 4.1 COMPREHENSIVE DATASET AUDIT")
print("=" * 80)

audit_results = {}

# 1. BLUE HEART URBAN CATCHMENT
print("\n[1] AUDITING BLUE HEART URBAN CATCHMENT...")
bh_seq_path = "data/processed_global/blue_heart_sequences.npz"
bh_graph_path = "data/processed_global/blue_heart_graph.npz"
bh_raw_dir = "data/urban_drainage_datasets/blue_heart"

bh_info = {"status": "UNKNOWN"}
if os.path.exists(bh_seq_path):
    bh_npz = np.load(bh_seq_path, allow_pickle=True)
    print("  blue_heart_sequences.npz keys:", list(bh_npz.keys()))
    X_train = bh_npz.get("X_train")
    y_train = bh_npz.get("y_train")
    X_val = bh_npz.get("X_val")
    y_val = bh_npz.get("y_val")
    X_test = bh_npz.get("X_test")
    y_test = bh_npz.get("y_test")
    node_names = bh_npz.get("node_names", bh_npz.get("station_names", []))
    feature_names = bh_npz.get("feature_names", ["water_level_m", "catchment_rainfall_mm"])
    timestamps = bh_npz.get("timestamps", [])
    
    bh_info = {
        "status": "PROCESSED_AND_TRAINED",
        "seq_file": bh_seq_path,
        "X_train_shape": list(X_train.shape) if X_train is not None else None,
        "y_train_shape": list(y_train.shape) if y_train is not None else None,
        "X_val_shape": list(X_val.shape) if X_val is not None else None,
        "X_test_shape": list(X_test.shape) if X_test is not None else None,
        "node_count": len(node_names) if hasattr(node_names, '__len__') else (X_train.shape[2] if X_train is not None else 15),
        "node_names": [str(n) for n in node_names] if hasattr(node_names, '__iter__') else [],
        "feature_names": [str(f) for f in feature_names] if hasattr(feature_names, '__iter__') else [],
        "total_sequences": (X_train.shape[0] if X_train is not None else 0) + (X_val.shape[0] if X_val is not None else 0) + (X_test.shape[0] if X_test is not None else 0)
    }
    print(f"  Total sequences: {bh_info['total_sequences']}")
    print(f"  Nodes: {bh_info['node_count']}")
    print(f"  Features: {bh_info['feature_names']}")

# Check raw/cleaned CSVs for Blue Heart
raw_bh_csvs = glob.glob("data/urban_drainage_datasets/blue_heart/**/*.csv", recursive=True)
print(f"  Found {len(raw_bh_csvs)} raw/extracted Blue Heart CSV files")
if raw_bh_csvs:
    df_sample = pd.read_csv(raw_bh_csvs[0], nrows=10)
    print(f"  Sample raw CSV ({os.path.basename(raw_bh_csvs[0])}) cols:", list(df_sample.columns))
audit_results["blue_heart"] = bh_info


# 2. CAMELS-HOURLY (AROOSTOOK BASIN)
print("\n[2] AUDITING CAMELS-HOURLY (AROOSTOOK RIVER BASIN)...")
camels_dir = "data/processed_global/camels_hourly_processed"
camels_files = glob.glob(f"{camels_dir}/*hourly*.csv")
print(f"  Found {len(camels_files)} processed CAMELS files:")
camels_info = {"stations": []}
total_camels_records = 0
for cf in camels_files:
    fname = os.path.basename(cf)
    if "labeled" in fname:
        df = pd.read_csv(cf, nrows=5)
        count = sum(1 for _ in open(cf, encoding="utf-8")) - 1
        total_camels_records += count
        st_id = fname.split("_")[0]
        camels_info["stations"].append({
            "station_id": st_id,
            "file": fname,
            "records": count,
            "columns": list(df.columns)
        })
        print(f"    Station {st_id}: {count:,} records, columns: {list(df.columns)}")

camels_info["total_records"] = total_camels_records
audit_results["camels_hourly"] = camels_info


# 3. USGS NWIS (POTOMAC RIVER BASIN)
print("\n[3] AUDITING USGS NWIS (POTOMAC RIVER BASIN)...")
usgs_seq_path = "data/processed_global/usgs_potomac_sequences.npz"
usgs_raw_dir = "data/global_flood_datasets/usgs"
usgs_info = {}
if os.path.exists(usgs_seq_path):
    u_npz = np.load(usgs_seq_path, allow_pickle=True)
    print("  usgs_potomac_sequences.npz keys:", list(u_npz.keys()))
    X_u = u_npz.get("X")
    y_u = u_npz.get("y")
    stations = u_npz.get("station_ids", u_npz.get("stations", []))
    usgs_info = {
        "status": "SEQUENCES_READY",
        "X_shape": list(X_u.shape) if X_u is not None else None,
        "y_shape": list(y_u.shape) if y_u is not None else None,
        "stations": [str(s) for s in stations] if hasattr(stations, '__iter__') else [],
        "total_sequences": X_u.shape[0] if X_u is not None else 0
    }
    print(f"  USGS X shape: {usgs_info['X_shape']}, stations: {usgs_info['stations']}")
usgs_csvs = glob.glob("data/global_flood_datasets/usgs/**/*.csv", recursive=True)
if usgs_csvs:
    print(f"  Found {len(usgs_csvs)} raw USGS CSV files")
    df_u = pd.read_csv(usgs_csvs[0], nrows=5)
    print(f"  Sample USGS cols: {list(df_u.columns)}")
audit_results["usgs_potomac"] = usgs_info


# 4. BELLINGE URBAN DRAINAGE BENCHMARK (DENMARK)
print("\n[4] AUDITING BELLINGE URBAN DRAINAGE (DTU DENMARK)...")
bellinge_dir = "data/urban_drainage_datasets/bellinge"
bellinge_files = glob.glob(f"{bellinge_dir}/**/*.*", recursive=True)
print(f"  Found {len(bellinge_files)} Bellinge files.")
swmm_models = glob.glob(f"{bellinge_dir}/**/*.inp", recursive=True)
print(f"  SWMM INP models: {[os.path.basename(m) for m in swmm_models]}")
bellinge_csvs = glob.glob(f"{bellinge_dir}/**/*.csv", recursive=True)
if bellinge_csvs:
    print(f"  Bellinge CSV files: {[os.path.basename(c) for c in bellinge_csvs]}")
bellinge_dat = glob.glob(f"{bellinge_dir}/**/*.dat", recursive=True)
if bellinge_dat:
    print(f"  Rain gauge / data files: {[os.path.basename(d) for d in bellinge_dat]}")
    # Inspect size
    for d in bellinge_dat:
        sz = os.path.getsize(d) / (1024 * 1024)
        print(f"    {os.path.basename(d)}: {sz:.2f} MB")
audit_results["bellinge_swmm"] = {
    "status": "SWMM_BENCHMARK_GROUND_TRUTH",
    "inp_models": [os.path.basename(m) for m in swmm_models],
    "file_count": len(bellinge_files)
}


# 5. URBAN WATER OBSERVATORY (UWO)
print("\n[5] AUDITING URBAN WATER OBSERVATORY (UWO)...")
uwo_dir = "data/urban_drainage_datasets/uwo"
uwo_files = glob.glob(f"{uwo_dir}/**/*.*", recursive=True)
print(f"  Found {len(uwo_files)} UWO files:")
for uf in uwo_files[:10]:
    print(f"    {os.path.basename(uf)} ({os.path.getsize(uf):,} bytes)")
uwo_graph_path = "data/processed_global/uwo_kearney_graph.npz"
if os.path.exists(uwo_graph_path):
    ug = np.load(uwo_graph_path, allow_pickle=True)
    print(f"  uwo_kearney_graph.npz keys: {list(ug.keys())}")
    adj = ug.get("adjacency")
    print(f"  Adjacency shape: {adj.shape if adj is not None else None}")


# 6. INDIA CWPRS RAINFALL TELEMETRY
print("\n[6] AUDITING INDIA CWPRS RAINFALL TELEMETRY...")
cwprs_path = "data/global_flood_datasets/cwprs/pune_rainfall_hourly.csv"
if os.path.exists(cwprs_path):
    df_cw = pd.read_csv(cwprs_path)
    print(f"  CWPRS records: {len(df_cw):,}")
    print(f"  CWPRS columns: {list(df_cw.columns)}")
    rain_col = [c for c in df_cw.columns if "rain" in c.lower()][0]
    max_rain = df_cw[rain_col].max()
    print(f"  Max hourly rainfall: {max_rain:.2f} mm")
    print(f"  Start: {df_cw.iloc[0][0]}, End: {df_cw.iloc[-1][0]}")
    audit_results["india_cwprs"] = {
        "status": "TELEMETRY_READY",
        "records": len(df_cw),
        "max_rain_mm": float(max_rain),
        "columns": list(df_cw.columns)
    }

# 7. INDORE MUNICIPAL (KHAN & SARASWATI BASINS)
print("\n[7] AUDITING INDORE MUNICIPAL BASIN...")
indore_model_path = "data/st_gnn_model.npz"
if os.path.exists(indore_model_path):
    im = np.load(indore_model_path, allow_pickle=True)
    print(f"  st_gnn_model.npz keys: {list(im.keys())}")
    for k in im.keys():
        arr = im[k]
        if hasattr(arr, 'shape'):
            print(f"    {k}: shape {arr.shape}, dtype {arr.dtype}")

with open("data/task_41_data_audit.json", "w", encoding="utf-8") as f:
    json.dump(audit_results, f, indent=2)

print("\nAudit completed and saved to data/task_41_data_audit.json.")

