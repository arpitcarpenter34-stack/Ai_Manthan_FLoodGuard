import os
import sys
import json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

print("Testing comprehensive data intelligence extraction...")

# 1. BLUE HEART
bh_seq_path = "data/processed_global/urban_sequences/blue_heart_sequences_w12_h3.npz"
bh_npz = np.load(bh_seq_path, allow_pickle=True)
X_bh = bh_npz["X"] # (7282, 12, 15, 2)
mask_bh = bh_npz["mask"] # (7282, 12, 15)
Y_level = bh_npz["Y_level"] # (7282, 15)
train_idx = bh_npz["train_idx"]
val_idx = bh_npz["val_idx"]
test_idx = bh_npz["test_idx"]

# Feature 0: stage (m), Feature 1: rain (mm)
stage_all = X_bh[:, :, :, 0].flatten()
rain_all = X_bh[:, :, :, 1].flatten()
mask_all = mask_bh.flatten()

valid_stage = stage_all[mask_all > 0]
valid_rain = rain_all[mask_all > 0]

print(f"Blue Heart valid stage count: {len(valid_stage):,}")
print(f"  Stage: min={valid_stage.min():.3f}, max={valid_stage.max():.3f}, mean={valid_stage.mean():.3f}, median={np.median(valid_stage):.3f}")
print(f"  Rain: min={valid_rain.min():.3f}, max={valid_rain.max():.3f}, mean={valid_rain.mean():.3f}, median={np.median(valid_rain):.3f}")

# Histogram bins for rain (12 bins)
hist_rain, bin_edges_rain = np.histogram(valid_rain[valid_rain > 0.05], bins=12)
print("  Rain histogram bins:", hist_rain.tolist())

# Cross-correlation between rain and stage rise across time
# Sample a single sensor across sequences (e.g. sensor 0)
s0_stage = X_bh[:, -1, 0, 0]
s0_rain = X_bh[:, -1, 0, 1]
# Compute cross-correlation at lags 0 to 8 (0 to 120 min, 15 min steps)
lags = [0, 1, 2, 3, 4, 5, 6, 7, 8]
lag_minutes = [l * 15 for l in lags]
corr_lags = []
for l in lags:
    if l == 0:
        c = np.corrcoef(s0_rain, s0_stage)[0, 1]
    else:
        c = np.corrcoef(s0_rain[:-l], s0_stage[l:])[0, 1]
    corr_lags.append(float(np.nan_to_num(c, nan=0.0)))
print(f"  Lag correlation (0 to 120m): {list(zip(lag_minutes, [round(c, 3) for c in corr_lags]))}")


# 2. CWPRS
cwprs_path = "data/urban_drainage_datasets/india_cwprs/rainfall_tel_hr_cwprs_mh_2021_2025.csv"
df_cw = pd.read_csv(cwprs_path)
rain_series = df_cw["Telemetry Hourly Rainfall (mm)"].dropna()
print(f"\nCWPRS valid records: {len(rain_series):,}")
print(f"  Mean: {rain_series.mean():.2f}, Max: {rain_series.max():.2f}, Median: {rain_series.median():.2f}")


# 3. CAMELS
camels_file = "data/processed_global/camels_hourly_processed/01017000_hourly_labeled.csv"
df_cam = pd.read_csv(camels_file, nrows=10000)
print(f"\nCAMELS sample records: {len(df_cam):,}")
print("CAMELS columns:", list(df_cam.columns)[:8])
flow_series = df_cam["streamflow_m3s"].dropna()
print(f"  Streamflow mean={flow_series.mean():.2f}, max={flow_series.max():.2f}, median={flow_series.median():.2f}")

print("\nData extraction test successful!")

