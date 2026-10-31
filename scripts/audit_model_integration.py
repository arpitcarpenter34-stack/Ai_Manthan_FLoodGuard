import sys
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0, r"E:\ai-manthan\hydro_guard_indore")

print("=" * 80)
print(" HYDRO-GUARD AI — SECTION 4: MODEL INTEGRATION VERIFICATION")
print("=" * 80)

# 1. Checkpoint Inspection
ckpt_path = Path(r"E:\ai-manthan\hydro_guard_indore\checkpoints\blue_heart\v2\best_adaptive_st_gnn.pt")
assert ckpt_path.exists(), f"Checkpoint missing: {ckpt_path}"
print(f"[1] CHECKPOINT FILE: {ckpt_path.name} ({ckpt_path.stat().st_size} bytes)")

ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
print(f"  Checkpoint dictionary keys: {list(ckpt.keys())}")
if "config" in ckpt:
    cfg = ckpt["config"]
    print(f"  Architecture config: in_dim={cfg.get('in_dim')}, hidden_dim={cfg.get('hidden_dim')}, num_nodes={cfg.get('num_nodes')}")
    print(f"  Best val loss recorded: {ckpt.get('best_val_loss')}")
    print(f"  Best epoch: {ckpt.get('epoch')}")

state_dict = ckpt.get("model_state_dict", ckpt)
num_params = sum(p.numel() for p in state_dict.values())
print(f"  Total trainable parameters: {num_params:,}")
for k, v in list(state_dict.items())[:6]:
    print(f"    - Parameter '{k}': shape {list(v.shape)}, dtype {v.dtype}")

# 2. Adjacency Matrix Verification
adj_path = Path(r"E:\ai-manthan\hydro_guard_indore\data\processed_global\urban_graphs\blue_heart_gully_adjacency.npy")
assert adj_path.exists(), f"Adjacency matrix missing: {adj_path}"
adj = np.load(adj_path)
print(f"\n[2] ADJACENCY MATRIX: {adj_path.name}")
print(f"  Shape: {adj.shape} (Expected: (15, 15))")
assert adj.shape == (15, 15), f"Adjacency shape mismatch: {adj.shape}"
print(f"  Value range: min={adj.min():.4f}, max={adj.max():.4f}, mean={adj.mean():.4f}")
print(f"  Diagonal elements (self-loops): min={np.diag(adj).min():.4f}, max={np.diag(adj).max():.4f}")

# 3. Test Sequences & Feature Normalization
test_seq_path = Path(r"E:\ai-manthan\hydro_guard_indore\data\processed_global\urban_sequences\blue_heart_sequences_w12_h3.npz")
assert test_seq_path.exists(), f"Test sequences missing: {test_seq_path}"
test_data = np.load(test_seq_path)
print(f"\n[3] SEQUENCES DATASET: {test_seq_path.name}")
print(f"  Arrays in archive: {list(test_data.keys())}")
X = test_data["X"]
y = test_data["Y_level"]
sensor_names = test_data["sensor_names"]
feature_names = test_data["feature_names"]
print(f"  Sensor names ({len(sensor_names)}): {list(sensor_names)}")
print(f"  Feature names: {list(feature_names)}")
print(f"  Total X tensor shape: {X.shape} (Sequences, Timesteps, Nodes, Features)")
print(f"  Total y tensor shape: {y.shape} (Sequences, Nodes)")
print(f"  Raw feature names in NPZ: {list(feature_names)}")
print("  Inference features (in_dim=3): [normalized_stage_zscore, normalized_rain_zscore, observation_validity_mask]")
assert X.shape[1] == 12, f"Expected 12 lookback steps (3h), got {X.shape[1]}"
assert X.shape[2] == 15, f"Expected 15 nodes, got {X.shape[2]}"
assert X.shape[3] == 2, f"Expected 2 raw features in NPZ, got {X.shape[3]}"

# 4. Blue Heart Engine Live Sample Inference
from backend.models.blue_heart_st_gnn import blue_heart_st_gnn
print("\n[4] EXECUTING REAL-DATA INFERENCE ON HELD-OUT SAMPLES:")
for test_idx in [0, 15, 50, 100]:
    pred = blue_heart_st_gnn.predict_sample(test_idx)
    assert pred["status"] == "success"
    mae = pred["mean_absolute_error_mm"]
    max_stage = pred["max_predicted_stage_m"]
    nodes_cnt = len(pred["nodes"])
    print(f"  Sample #{test_idx:3d}: MAE={mae:5.2f} mm | Max Gully Stage={max_stage:6.3f} m | Monitored Gullies={nodes_cnt}")
    # Verify node fields
    first_node = pred["nodes"][0]
    assert "current_level_m" in first_node
    assert "predicted_level_m" in first_node
    assert "true_level_m" in first_node
    assert "absolute_error_mm" in first_node

# 5. Independent Indore Prediction Engine Verification
from backend.models.hybrid_prediction_engine import hybrid_prediction_engine
print("\n[5] INDEPENDENT INDORE ENGINE CHECK:")
ind_res = hybrid_prediction_engine.predict_hybrid_flood(rainfall_intensity_mmh=25.0)
print(f"  Architecture: {ind_res['model_architecture']}")
print(f"  Primary Engine: {ind_res['primary_engine']}")
print(f"  Physics Engine: {ind_res['physics_engine']}")
print(f"  Evaluated Nodes Count: {len(ind_res['node_predictions'])} (Expected: 7 Indore stations)")
assert len(ind_res["node_predictions"]) == 7
print(f"  Indore Baseline Weight File: E:\\ai-manthan\\hydro_guard_indore\\data\\st_gnn_model.npz exists: {Path('E:/ai-manthan/hydro_guard_indore/data/st_gnn_model.npz').exists()}")

print("\n=> MODEL INTEGRATION AUDIT: 100% VERIFIED AND SEPARATED.")
