import os
import sys
import glob
import json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

base_urban = r"E:\ai-manthan\hydro_guard_indore\data\urban_drainage_datasets"
out_seq_dir = r"E:\ai-manthan\hydro_guard_indore\data\processed_global\urban_sequences"
os.makedirs(out_seq_dir, exist_ok=True)

print("==================================================================")
print("             TASK 2.4 - STEP 4: PREPARE URBAN TEMPORAL SEQUENCES  ")
print("==================================================================")

# 1. Load Blue Heart 15 Gully Sensors
gully_files = sorted(glob.glob(os.path.join(base_urban, "blue_heart", "highway_gully_telemetry", "**", "*.csv"), recursive=True))
gully_files = [f for f in gully_files if "quality" not in f]
gully_names = [os.path.basename(f).replace(".csv", "") for f in gully_files]
print(f"Loading {len(gully_names)} road gully sensors...")

gully_dfs = {}
for gf, gn in zip(gully_files, gully_names):
    df = pd.read_csv(gf)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('timestamp').drop_duplicates('timestamp')
    df = df.set_index('timestamp')
    # Resample to 1-hour means (preserving real values, NaNs for missing)
    df_h = df[['Water Level [mm]']].resample('1h').mean()
    df_h['Water Level [mm]'] = df_h['Water Level [mm]'] / 1000.0 # to meters
    df_h.rename(columns={'Water Level [mm]': f'{gn}_level_m'}, inplace=True)
    gully_dfs[gn] = df_h

# 2. Load Blue Heart Rain Gauges
rain_files = sorted(glob.glob(os.path.join(base_urban, "blue_heart", "rain_gauge_telemetry", "**", "*.csv"), recursive=True))
rain_files = [f for f in rain_files if "quality" not in f]
print(f"Loading {len(rain_files)} rain gauges...")

rain_dfs = []
for rf in rain_files[:5]: # use 5 primary catchment rain gauges
    df_r = pd.read_csv(rf)
    df_r['timestamp'] = pd.to_datetime(df_r['timestamp'], utc=True)
    df_r = df_r.sort_values('timestamp').drop_duplicates('timestamp').set_index('timestamp')
    df_rh = df_r[['Rainfall Depth [mm]']].resample('1h').sum()
    rain_dfs.append(df_rh)

# Catchment mean rainfall
df_rain_all = pd.concat(rain_dfs, axis=1)
df_rain_mean = df_rain_all.mean(axis=1).to_frame(name='catchment_rainfall_mm_h')

# 3. Synchronize / Align
df_all_gullies = pd.concat(list(gully_dfs.values()), axis=1)
df_aligned = pd.concat([df_all_gullies, df_rain_mean], axis=1).dropna(subset=['catchment_rainfall_mm_h'])

# Find common continuous observation window
# Restrict to 2025-07-01 to 2026-04-30
df_aligned = df_aligned.loc['2025-07-01':'2026-04-30']
print(f"Synchronized hourly timestamps: {len(df_aligned)} hours (from {df_aligned.index.min()} to {df_aligned.index.max()})")

level_cols = [c for c in df_aligned.columns if c.endswith('_level_m')]
V = len(level_cols)
T = len(df_aligned)
print(f"Nodes V={V}, Time steps T={T}")

# Build Feature Matrices
# Features per node: [water_level_m, rainfall_intensity_mmh]
# Create missingness mask: 1 if observed, 0 if NaN
levels = df_aligned[level_cols].values # (T, V)
rainfall = np.repeat(df_aligned[['catchment_rainfall_mm_h']].values, V, axis=1) # (T, V)

mask = (~np.isnan(levels)).astype(np.float32) # (T, V)
# Fill NaNs with 0 in feature matrix ONLY accompanied by mask=0
levels_clean = np.nan_to_num(levels, nan=0.0)

# Build (T, V, F) where F=2
node_temporal = np.stack([levels_clean, rainfall], axis=-1).astype(np.float32)
print(f"Full Temporal Node Tensor: {node_temporal.shape}, Missingness rate: {(1.0 - mask.mean())*100:.2f}%")

# 4. Generate Sliding Window Sequences
configs = [
    ('w12_h3', 12, 3),
    ('w6_h1', 6, 1),
    ('w24_h6', 24, 6)
]

for cfg_name, W, H in configs:
    X_list = []
    Y_level_list = []
    Y_surch_list = []
    mask_list = []
    
    for t in range(T - (W + H - 1)):
        # Input window: t to t+W
        X_w = node_temporal[t : t + W] # (W, V, F)
        M_w = mask[t : t + W]          # (W, V)
        # Target at t+W+H-1
        target_t = t + W + H - 1
        Y_l = levels_clean[target_t]   # (V,)
        # Surcharge threshold: level > 0.30 m
        Y_s = (levels_clean[target_t] > 0.30).astype(np.float32)
        
        # Only keep sequence if at least 70% of gully nodes are actively reporting in window
        if M_w.mean() >= 0.70:
            X_list.append(X_w)
            Y_level_list.append(Y_l)
            Y_surch_list.append(Y_s)
            mask_list.append(M_w)
            
    X_arr = np.array(X_list, dtype=np.float32)
    Y_level_arr = np.array(Y_level_list, dtype=np.float32)
    Y_surch_arr = np.array(Y_surch_list, dtype=np.float32)
    mask_arr = np.array(mask_list, dtype=np.float32)
    
    N_seq = len(X_arr)
    # Chronological split 70 / 15 / 15 with 12h purge buffer
    n_train = int(N_seq * 0.70)
    n_val = int(N_seq * 0.15)
    
    train_idx = np.arange(0, n_train - 12)
    val_idx = np.arange(n_train, n_train + n_val - 12)
    test_idx = np.arange(n_train + n_val, N_seq)
    
    out_file = os.path.join(out_seq_dir, f"blue_heart_sequences_{cfg_name}.npz")
    np.savez_compressed(
        out_file,
        X=X_arr,
        Y_level=Y_level_arr,
        Y_surcharge=Y_surch_arr,
        mask=mask_arr,
        train_idx=train_idx,
        val_idx=val_idx,
        test_idx=test_idx,
        window_hours=W,
        horizon_hours=H,
        sensor_names=level_cols,
        feature_names=["water_level_m", "catchment_rainfall_mm_h"]
    )
    print(f"Saved {cfg_name}: {N_seq} sequences (Train: {len(train_idx)}, Val: {len(val_idx)}, Test: {len(test_idx)}) -> {out_file}")

print("\nUrban temporal sequence generation complete.")

