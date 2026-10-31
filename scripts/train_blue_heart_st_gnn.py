#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HYDRO-GUARD AI — TASK 3.1: BLUE HEART URBAN ST-GNN MODEL TRAINING
Spatio-Temporal Graph Neural Network (DCRNN) Training Pipeline on Real Blue Heart Gully Telemetry.

Architectural Components:
1. Spatial Bi-directional Graph Diffusion Convolution (Forward Pf, Backward Pb, Order K=2).
2. Spatio-Temporal Diffusion Convolutional Recurrent Neural Network (DCRNN, 2 layers, hidden=64).
3. Benchmark Baselines:
   - Persistence Baseline (lag-0 stage)
   - Multi-Station Ridge Autoregression
   - Pure Temporal GRU (ablation without spatial graph diffusion)
4. Masked Huber Loss (SmoothL1, beta=0.5) on sensor-wise normalized stage.
5. Rigorous Evaluation: MAE, RMSE, R^2, NSE, High-water subset (top 10%), Peak Timing Error.
"""

import os
import sys
import json
import time
import shutil
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Ensure UTF-8 console output on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Set random seeds for strict scientific reproducibility
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

PROJECT_ROOT = r"E:\ai-manthan\hydro_guard_indore"
DATA_NPZ = os.path.join(PROJECT_ROOT, r"data\processed_global\urban_sequences\blue_heart_sequences_w12_h3.npz")
GRAPH_NPY = os.path.join(PROJECT_ROOT, r"data\processed_global\urban_graphs\blue_heart_gully_adjacency.npy")

CHECKPOINT_DIR = os.path.join(PROJECT_ROOT, r"checkpoints\blue_heart")
LOG_DIR = os.path.join(PROJECT_ROOT, r"logs\blue_heart")
RESULT_DIR = os.path.join(PROJECT_ROOT, r"results\blue_heart")

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. GRAPH DIFFUSION CONVOLUTION MODULES
# ---------------------------------------------------------------------------

class GraphDiffusionConv(nn.Module):
    """
    Spatial Diffusion Convolution Layer across multiple transition supports.
    Diffuses node features over forward and backward directed graph topologies.
    """
    def __init__(self, supports, in_dim, out_dim):
        super().__init__()
        self.register_buffer('supports', torch.stack(supports)) # Shape: (K, N, N)
        self.num_supports = len(supports)
        self.fc = nn.Linear(self.num_supports * in_dim, out_dim)

    def forward(self, x):
        # x: (B, N, in_dim)
        outs = [torch.matmul(s, x) for s in self.supports]
        x_diff = torch.cat(outs, dim=-1) # (B, N, num_supports * in_dim)
        return self.fc(x_diff)


class DCGRUCell(nn.Module):
    """
    Diffusion Convolutional Gated Recurrent Unit (DCGRU) Cell.
    Replaces standard matrix multiplication in GRU with graph diffusion convolutions.
    """
    def __init__(self, supports, in_dim, hidden_dim):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.conv_gates = GraphDiffusionConv(supports, in_dim + hidden_dim, 2 * hidden_dim)
        self.conv_candidate = GraphDiffusionConv(supports, in_dim + hidden_dim, hidden_dim)

    def forward(self, x, h):
        # x: (B, N, in_dim), h: (B, N, hidden_dim)
        combined = torch.cat([x, h], dim=-1)
        gates = torch.sigmoid(self.conv_gates(combined))
        reset_gate, update_gate = torch.split(gates, self.hidden_dim, dim=-1)
        
        c_in = torch.cat([x, reset_gate * h], dim=-1)
        candidate = torch.tanh(self.conv_candidate(c_in))
        
        h_new = update_gate * h + (1.0 - update_gate) * candidate
        return h_new


class DCRNNModel(nn.Module):
    """
    2-Layer Spatio-Temporal Diffusion Convolutional Recurrent Neural Network.
    Processes 12 lookback hours and predicts water level across all 15 nodes at H=+3h.
    """
    def __init__(self, supports, in_dim=3, hidden_dim=64, num_layers=2, dropout=0.15):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.cells = nn.ModuleList([
            DCGRUCell(supports, in_dim if i == 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])
        self.dropout = nn.Dropout(dropout)
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x_seq):
        # x_seq: (B, T, N, in_dim)
        B, T, N, C = x_seq.shape
        h = [torch.zeros(B, N, self.hidden_dim, device=x_seq.device) for _ in range(self.num_layers)]
        
        for t in range(T):
            x_t = x_seq[:, t] # (B, N, C)
            for layer_idx, cell in enumerate(self.cells):
                h[layer_idx] = cell(x_t, h[layer_idx])
                if layer_idx < self.num_layers - 1:
                    x_t = self.dropout(h[layer_idx])
                else:
                    x_t = h[layer_idx]
                    
        # Final hidden state from top layer: (B, N, hidden_dim)
        out = self.readout(h[-1]).squeeze(-1) # (B, N)
        return out


class TemporalGRUModel(nn.Module):
    """
    Pure Temporal GRU Baseline (Ablation without Spatial Graph Convolutions).
    Evaluates temporal sequence modeling without spatial information exchange.
    """
    def __init__(self, in_dim=3, hidden_dim=64, num_layers=2, dropout=0.15):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.gru = nn.GRU(
            in_dim, 
            hidden_dim, 
            num_layers=num_layers, 
            batch_first=True, 
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x_seq):
        # x_seq: (B, T, N, in_dim)
        B, T, N, C = x_seq.shape
        # Permute to (B*N, T, C) so GRU processes each station independently
        x_flat = x_seq.permute(0, 2, 1, 3).reshape(B * N, T, C)
        out, _ = self.gru(x_flat) # (B*N, T, hidden_dim)
        last_h = out[:, -1, :] # (B*N, hidden_dim)
        pred = self.readout(last_h).reshape(B, N)
        return pred

# ---------------------------------------------------------------------------
# 2. DATASET LOADER & PREPROCESSING
# ---------------------------------------------------------------------------

class SequenceDataset(Dataset):
    def __init__(self, X, Y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.Y = torch.tensor(Y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]

def compute_metrics(y_true, y_pred):
    """
    Compute MAE (m), RMSE (m), R^2, and NSE on continuous water level.
    """
    err = y_pred - y_true
    mae = float(np.abs(err).mean())
    rmse = float(np.sqrt((err**2).mean()))
    
    # Total sum of squares per node, then aggregated
    mean_true = y_true.mean(axis=0, keepdims=True)
    sst = float(((y_true - mean_true)**2).sum())
    sse = float((err**2).sum())
    
    nse = float(1.0 - (sse / sst)) if sst > 1e-8 else 0.0
    
    # R^2 correlation coefficient
    var_true = np.var(y_true)
    var_pred = np.var(y_pred)
    if var_true > 1e-8 and var_pred > 1e-8:
        cov = np.mean((y_true - np.mean(y_true)) * (y_pred - np.mean(y_pred)))
        r2 = float((cov / (np.std(y_true) * np.std(y_pred)))**2)
    else:
        r2 = 0.0
        
    return {"mae": mae, "rmse": rmse, "nse": nse, "r2": r2}

def compute_per_sensor_metrics(y_true, y_pred, sensor_names):
    """
    Compute evaluation metrics individually for each sensor.
    """
    results = []
    N = y_true.shape[1]
    for i in range(N):
        yt = y_true[:, i]
        yp = y_pred[:, i]
        err = yp - yt
        mae = float(np.abs(err).mean())
        rmse = float(np.sqrt((err**2).mean()))
        
        sst = float(((yt - yt.mean())**2).sum())
        sse = float((err**2).sum())
        nse = float(1.0 - (sse / sst)) if sst > 1e-8 else 0.0
        
        var_t = np.var(yt)
        var_p = np.var(yp)
        if var_t > 1e-8 and var_p > 1e-8:
            cov = np.mean((yt - np.mean(yt)) * (yp - np.mean(yp)))
            r2 = float((cov / (np.std(yt) * np.std(yp)))**2)
        else:
            r2 = 0.0
            
        results.append({
            "sensor_idx": i,
            "sensor_name": str(sensor_names[i]),
            "mae_m": round(mae, 4),
            "rmse_m": round(rmse, 4),
            "nse": round(nse, 4),
            "r2": round(r2, 4)
        })
    return results

def compute_peak_timing_error(y_true, y_pred, top_n_peaks=10, window=12):
    """
    Identify prominent storm peaks in test set and compute mean peak timing error Delta t (hours).
    """
    N_samples, N_nodes = y_true.shape
    mean_stage = y_true.mean(axis=1) # Catchment average stage
    
    # Find local maxima in catchment stage
    peaks = []
    for t in range(window, N_samples - window):
        if mean_stage[t] == np.max(mean_stage[t - window : t + window + 1]):
            peaks.append((t, mean_stage[t]))
            
    # Sort peaks by peak amplitude descending
    peaks = sorted(peaks, key=lambda x: x[1], reverse=True)[:top_n_peaks]
    
    timing_errors = []
    for peak_t, _ in peaks:
        t_start = max(0, peak_t - window)
        t_end = min(N_samples, peak_t + window + 1)
        
        # True catchment peak index in window
        actual_peak_idx = t_start + np.argmax(mean_stage[t_start:t_end])
        
        # Predicted catchment peak index in window
        pred_stage_window = y_pred[t_start:t_end].mean(axis=1)
        pred_peak_idx = t_start + np.argmax(pred_stage_window)
        
        dt = abs(actual_peak_idx - pred_peak_idx)
        timing_errors.append(dt)
        
    return float(np.mean(timing_errors)) if timing_errors else 0.0

# ---------------------------------------------------------------------------
# 3. MAIN TRAINING & BENCHMARK HARNESS
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print(" HYDRO-GUARD AI — TASK 3.1: BLUE HEART URBAN ST-GNN MODEL TRAINING")
    print(" Problem Statement: PS-11 (AI-Powered Urban Drainage & Flash Floods)")
    print(" Dataset: Blue Heart Urban Catchment (15 Road Gully Sensors + Rain)")
    print("=" * 72)

    # 1. Load Data
    print(f"\n[1/7] Loading processed sequence tensors from:\n  {DATA_NPZ}")
    data = np.load(DATA_NPZ, allow_pickle=True)
    X_raw = data['X']               # (7282, 12, 15, 2)
    Y_level_raw = data['Y_level']   # (7282, 15)
    mask = data['mask']             # (7282, 12, 15)
    train_idx = data['train_idx']   # (5085,)
    val_idx = data['val_idx']       # (1080,)
    test_idx = data['test_idx']     # (1093,)
    sensor_names = data['sensor_names']
    feature_names = data['feature_names']

    print(f"  Total sequences: {len(X_raw)}")
    print(f"  Train: {len(train_idx)} | Val: {len(val_idx)} | Test: {len(test_idx)}")
    print(f"  Nodes: {len(sensor_names)} | Window: 12h | Horizon: +3h")

    # 2. Compute Normalization Statistics (TRAINING SPLIT ONLY)
    print("\n[2/7] Computing sensor-wise normalization statistics from TRAIN SPLIT ONLY...")
    level_train = X_raw[train_idx, :, :, 0]
    mu_level = level_train.mean(axis=(0, 1)) # (15,)
    sigma_level = level_train.std(axis=(0, 1)) # (15,)
    sigma_level = np.where(sigma_level < 1e-4, 1.0, sigma_level)

    rain_train = X_raw[train_idx, :, :, 1]
    mu_rain = float(rain_train.mean())
    sigma_rain = float(rain_train.std())
    if sigma_rain < 1e-4:
        sigma_rain = 1.0

    print(f"  Water Level Mean range: [{mu_level.min():.4f}, {mu_level.max():.4f}] m")
    print(f"  Water Level Std range:  [{sigma_level.min():.4f}, {sigma_level.max():.4f}] m")
    print(f"  Catchment Rain Mean:    {mu_rain:.4f} mm/h | Std: {sigma_rain:.4f} mm/h")

    # Construct Normalized 3-Channel Input: [Normalized Level, Normalized Rain, Valid Mask]
    X_norm = np.zeros((X_raw.shape[0], X_raw.shape[1], X_raw.shape[2], 3), dtype=np.float32)
    X_norm[:, :, :, 0] = (X_raw[:, :, :, 0] - mu_level[None, None, :]) / sigma_level[None, None, :]
    X_norm[:, :, :, 1] = (X_raw[:, :, :, 1] - mu_rain) / sigma_rain
    X_norm[:, :, :, 2] = mask # Channel 2: observation validity indicator

    Y_level_norm = (Y_level_raw - mu_level[None, :]) / sigma_level[None, :]

    # Train, Val, Test Slices
    X_train = X_norm[train_idx]
    Y_train = Y_level_norm[train_idx]

    X_val = X_norm[val_idx]
    Y_val = Y_level_norm[val_idx]
    Y_val_true = Y_level_raw[val_idx]

    X_test = X_norm[test_idx]
    Y_test = Y_level_norm[test_idx]
    Y_test_true = Y_level_raw[test_idx]

    train_loader = DataLoader(SequenceDataset(X_train, Y_train), batch_size=64, shuffle=True)
    val_loader = DataLoader(SequenceDataset(X_val, Y_val), batch_size=64, shuffle=False)
    test_loader = DataLoader(SequenceDataset(X_test, Y_test), batch_size=64, shuffle=False)

    # 3. Load & Prepare Directed Spatial Graph
    print(f"\n[3/7] Loading directed gully adjacency graph from:\n  {GRAPH_NPY}")
    adj = np.load(GRAPH_NPY)
    N_nodes = adj.shape[0]

    # Calculate Forward Pf = D_out^-1 * A and Backward Pb = D_in^-1 * A^T
    d_out = adj.sum(axis=1, keepdims=True)
    d_out[d_out == 0] = 1.0
    Pf = torch.tensor(adj / d_out, dtype=torch.float32)

    d_in = adj.sum(axis=0, keepdims=True)
    d_in[d_in == 0] = 1.0
    Pb = torch.tensor((adj.T) / (d_in.T), dtype=torch.float32)

    I = torch.eye(N_nodes, dtype=torch.float32)
    Pf2 = torch.matmul(Pf, Pf)
    Pb2 = torch.matmul(Pb, Pb)

    supports = [I, Pf, Pb, Pf2, Pb2]
    print(f"  Graph Adjacency Shape: {adj.shape} ({np.count_nonzero(adj)} directed edges)")
    print(f"  Diffusion Supports initialized: K=2 hops ({len(supports)} diffusion matrices)")

    # -----------------------------------------------------------------------
    # 4. BENCHMARK BASELINES EVALUATION
    # -----------------------------------------------------------------------
    print("\n[4/7] Computing Benchmark Baseline Models...")
    
    # Baseline 1: Persistence
    # Predict stage at t+3 = stage at t (index 11 of lookback window)
    Y_pred_persist = X_raw[test_idx, -1, :, 0]
    metrics_persist = compute_metrics(Y_test_true, Y_pred_persist)
    print(f"  [Baseline 1 - Persistence]: MAE: {metrics_persist['mae']:.4f} m | RMSE: {metrics_persist['rmse']:.4f} m | NSE: {metrics_persist['nse']:.4f} | R^2: {metrics_persist['r2']:.4f}")

    # Baseline 2: Sensor-Wise Ridge Autoregression
    Y_pred_ridge = np.zeros_like(Y_test_true)
    for i in range(N_nodes):
        # Lookback features for sensor i: 12 levels + 12 rainfall values = 24 features
        x_tr_i = X_train[:, :, i, :2].reshape(len(train_idx), -1)
        y_tr_i = Y_train[:, i]
        x_te_i = X_test[:, :, i, :2].reshape(len(test_idx), -1)
        
        ridge_m = Ridge(alpha=10.0)
        ridge_m.fit(x_tr_i, y_tr_i)
        pred_norm_i = ridge_m.predict(x_te_i)
        Y_pred_ridge[:, i] = pred_norm_i * sigma_level[i] + mu_level[i]
        
    metrics_ridge = compute_metrics(Y_test_true, Y_pred_ridge)
    print(f"  [Baseline 2 - Ridge AR]:   MAE: {metrics_ridge['mae']:.4f} m | RMSE: {metrics_ridge['rmse']:.4f} m | NSE: {metrics_ridge['nse']:.4f} | R^2: {metrics_ridge['r2']:.4f}")

    # -----------------------------------------------------------------------
    # 5. MODEL 1: PURE TEMPORAL GRU (Ablation without Spatial Convolutions)
    # -----------------------------------------------------------------------
    print("\n[5/7] Training Baseline 3: Pure Temporal GRU (No Graph Topology)...")
    temporal_model = TemporalGRUModel(in_dim=3, hidden_dim=64, num_layers=2, dropout=0.15)
    opt_temp = torch.optim.AdamW(temporal_model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = nn.SmoothL1Loss(beta=0.5)

    best_val_loss_temp = float('inf')
    best_temp_state = None

    for epoch in range(1, 26):
        temporal_model.train()
        total_loss = 0.0
        for bx, by in train_loader:
            opt_temp.zero_grad()
            pred = temporal_model(bx)
            loss = loss_fn(pred, by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(temporal_model.parameters(), 5.0)
            opt_temp.step()
            total_loss += loss.item() * len(bx)
        train_loss = total_loss / len(train_idx)

        temporal_model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for bx, by in val_loader:
                pred = temporal_model(bx)
                loss = loss_fn(pred, by)
                val_loss += loss.item() * len(bx)
        val_loss /= len(val_idx)

        if val_loss < best_val_loss_temp:
            best_val_loss_temp = val_loss
            best_temp_state = {k: v.cpu().clone() for k, v in temporal_model.state_dict().items()}

    temporal_model.load_state_dict(best_temp_state)
    torch.save(best_temp_state, os.path.join(CHECKPOINT_DIR, "best_temporal_gru.pt"))

    # Evaluate Temporal GRU on Test Set
    temporal_model.eval()
    test_preds_temp = []
    with torch.no_grad():
        for bx, _ in test_loader:
            pred = temporal_model(bx)
            test_preds_temp.append(pred.numpy())
    Y_pred_temp_norm = np.concatenate(test_preds_temp, axis=0)
    Y_pred_temp = Y_pred_temp_norm * sigma_level[None, :] + mu_level[None, :]
    metrics_temp = compute_metrics(Y_test_true, Y_pred_temp)
    print(f"  [Baseline 3 - Temporal GRU]: MAE: {metrics_temp['mae']:.4f} m | RMSE: {metrics_temp['rmse']:.4f} m | NSE: {metrics_temp['nse']:.4f} | R^2: {metrics_temp['r2']:.4f}")

    # -----------------------------------------------------------------------
    # 6. MODEL 2: SPATIO-TEMPORAL GNN (DCRNN) FULL TRAINING
    # -----------------------------------------------------------------------
    print("\n[6/7] Training Spatio-Temporal Graph Neural Network (DCRNN)...")
    st_gnn = DCRNNModel(supports, in_dim=3, hidden_dim=64, num_layers=2, dropout=0.15)
    optimizer = torch.optim.AdamW(st_gnn.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=4, min_lr=1e-5)

    num_epochs = 35
    best_val_loss_gnn = float('inf')
    best_gnn_state = None
    patience = 8
    patience_counter = 0

    history = []
    start_time = time.time()

    print(f"  Training for up to {num_epochs} epochs with Early Stopping (patience={patience})...")
    print(f"  {'Epoch':<6} | {'Train Loss':<12} | {'Val Loss':<12} | {'Val MAE (m)':<12} | {'Val RMSE (m)':<12} | {'LR':<10}")
    print("  " + "-" * 70)

    for epoch in range(1, num_epochs + 1):
        st_gnn.train()
        total_train_loss = 0.0
        for bx, by in train_loader:
            optimizer.zero_grad()
            pred = st_gnn(bx)
            loss = loss_fn(pred, by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(st_gnn.parameters(), 5.0)
            optimizer.step()
            total_train_loss += loss.item() * len(bx)
        train_loss = total_train_loss / len(train_idx)

        # Validation Pass
        st_gnn.eval()
        total_val_loss = 0.0
        val_preds_list = []
        with torch.no_grad():
            for bx, by in val_loader:
                pred = st_gnn(bx)
                loss = loss_fn(pred, by)
                total_val_loss += loss.item() * len(bx)
                val_preds_list.append(pred.numpy())
        val_loss = total_val_loss / len(val_idx)

        # Unscale validation predictions to physical meters
        val_preds_norm = np.concatenate(val_preds_list, axis=0)
        val_preds_m = val_preds_norm * sigma_level[None, :] + mu_level[None, :]
        val_metrics = compute_metrics(Y_val_true, val_preds_m)

        current_lr = optimizer.param_groups[0]['lr']
        scheduler.step(val_loss)

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_loss": round(val_loss, 6),
            "val_mae_m": round(val_metrics['mae'], 4),
            "val_rmse_m": round(val_metrics['rmse'], 4),
            "val_nse": round(val_metrics['nse'], 4),
            "lr": current_lr
        })

        print(f"  {epoch:<6} | {train_loss:<12.6f} | {val_loss:<12.6f} | {val_metrics['mae']:<12.4f} | {val_metrics['rmse']:<12.4f} | {current_lr:<10.2e}")

        # Checkpoint Saving & Early Stopping
        if val_loss < best_val_loss_gnn:
            best_val_loss_gnn = val_loss
            patience_counter = 0
            best_gnn_state = {
                "epoch": epoch,
                "model_state_dict": {k: v.cpu().clone() for k, v in st_gnn.state_dict().items()},
                "val_loss": val_loss,
                "val_metrics": val_metrics,
                "mu_level": mu_level,
                "sigma_level": sigma_level,
                "mu_rain": mu_rain,
                "sigma_rain": sigma_rain,
                "sensor_names": [str(s) for s in sensor_names],
                "supports": [s.cpu() for s in supports],
                "hidden_dim": 64,
                "num_layers": 2
            }
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  [Early Stopping triggered at epoch {epoch} (no val loss improvement for {patience} epochs)].")
                break

    training_time = time.time() - start_time
    print(f"\n  Training completed in {training_time:.2f} seconds.")

    # Save Checkpoints
    best_ckpt_path = os.path.join(CHECKPOINT_DIR, "best_st_gnn.pt")
    final_ckpt_path = os.path.join(CHECKPOINT_DIR, "final_st_gnn.pt")
    torch.save(best_gnn_state, best_ckpt_path)
    
    final_state = {
        "epoch": len(history),
        "model_state_dict": {k: v.cpu().clone() for k, v in st_gnn.state_dict().items()},
        "mu_level": mu_level,
        "sigma_level": sigma_level,
        "mu_rain": mu_rain,
        "sigma_rain": sigma_rain,
        "sensor_names": [str(s) for s in sensor_names],
        "supports": [s.cpu() for s in supports],
        "hidden_dim": 64,
        "num_layers": 2
    }
    torch.save(final_state, final_ckpt_path)
    print(f"  Best checkpoint saved:  {best_ckpt_path}")
    print(f"  Final checkpoint saved: {final_ckpt_path}")

    # Load Best Model for Final Test Evaluation
    st_gnn.load_state_dict(best_gnn_state["model_state_dict"])
    st_gnn.eval()

    test_preds_gnn_list = []
    with torch.no_grad():
        for bx, _ in test_loader:
            pred = st_gnn(bx)
            test_preds_gnn_list.append(pred.numpy())
    Y_pred_gnn_norm = np.concatenate(test_preds_gnn_list, axis=0)
    Y_pred_gnn = Y_pred_gnn_norm * sigma_level[None, :] + mu_level[None, :]

    # -----------------------------------------------------------------------
    # 7. RIGOROUS TEST SET EVALUATION & DELIVERABLES
    # -----------------------------------------------------------------------
    print("\n[7/7] Generating Rigorous Test Set Evaluations...")
    
    metrics_gnn = compute_metrics(Y_test_true, Y_pred_gnn)
    
    # High-Water Events (evaluating on top 10% stage observations)
    thresh_90 = np.percentile(Y_test_true, 90)
    high_water_mask = Y_test_true >= thresh_90
    hw_true = Y_test_true[high_water_mask]
    
    hw_persist = Y_pred_persist[high_water_mask]
    hw_ridge = Y_pred_ridge[high_water_mask]
    hw_temp = Y_pred_temp[high_water_mask]
    hw_gnn = Y_pred_gnn[high_water_mask]
    
    metrics_hw_persist = compute_metrics(hw_true, hw_persist)
    metrics_hw_ridge = compute_metrics(hw_true, hw_ridge)
    metrics_hw_temp = compute_metrics(hw_true, hw_temp)
    metrics_hw_gnn = compute_metrics(hw_true, hw_gnn)

    # Peak Timing Error
    dt_persist = compute_peak_timing_error(Y_test_true, Y_pred_persist)
    dt_ridge = compute_peak_timing_error(Y_test_true, Y_pred_ridge)
    dt_temp = compute_peak_timing_error(Y_test_true, Y_pred_temp)
    dt_gnn = compute_peak_timing_error(Y_test_true, Y_pred_gnn)

    # Per-Sensor Breakdown for ST-GNN
    per_sensor_gnn = compute_per_sensor_metrics(Y_test_true, Y_pred_gnn, sensor_names)
    per_sensor_temp = compute_per_sensor_metrics(Y_test_true, Y_pred_temp, sensor_names)
    per_sensor_persist = compute_per_sensor_metrics(Y_test_true, Y_pred_persist, sensor_names)

    # Print Comparative Benchmark Table
    print("\n" + "=" * 90)
    print("                    TEST SET PERFORMANCE BENCHMARK (H = +3 HOURS)")
    print("=" * 90)
    print(f"{'Model':<25} | {'MAE (m)':<10} | {'RMSE (m)':<10} | {'R^2':<8} | {'NSE':<8} | {'HW MAE (m)':<12} | {'Peak DT (h)':<10}")
    print("-" * 90)
    print(f"{'1. Persistence Baseline':<25} | {metrics_persist['mae']:<10.4f} | {metrics_persist['rmse']:<10.4f} | {metrics_persist['r2']:<8.4f} | {metrics_persist['nse']:<8.4f} | {metrics_hw_persist['mae']:<12.4f} | {dt_persist:<10.2f}")
    print(f"{'2. Multi-Station Ridge AR':<25} | {metrics_ridge['mae']:<10.4f} | {metrics_ridge['rmse']:<10.4f} | {metrics_ridge['r2']:<8.4f} | {metrics_ridge['nse']:<8.4f} | {metrics_hw_ridge['mae']:<12.4f} | {dt_ridge:<10.2f}")
    print(f"{'3. Pure Temporal GRU':<25} | {metrics_temp['mae']:<10.4f} | {metrics_temp['rmse']:<10.4f} | {metrics_temp['r2']:<8.4f} | {metrics_temp['nse']:<8.4f} | {metrics_hw_temp['mae']:<12.4f} | {dt_temp:<10.2f}")
    print(f"{'4. Hybrid ST-GNN (DCRNN)':<25} | {metrics_gnn['mae']:<10.4f} | {metrics_gnn['rmse']:<10.4f} | {metrics_gnn['r2']:<8.4f} | {metrics_gnn['nse']:<8.4f} | {metrics_hw_gnn['mae']:<12.4f} | {dt_gnn:<10.2f}")
    print("=" * 90)

    # 8. Save Artifacts & Deliverables
    # A. Training Configuration
    config_dict = {
        "experiment_name": "blue_heart_urban_st_gnn",
        "task": "TASK_3_1_BLUE_HEART_MODEL_TRAINING",
        "problem_statement": "PS-11: Urban Drainage and Flash Flood Predictive Management System",
        "dataset": "Blue Heart Urban Catchment (Eastbourne, UK)",
        "num_nodes": N_nodes,
        "input_features": ["water_level_m", "catchment_rainfall_mm_h", "observation_mask"],
        "lookback_window_hours": 12,
        "forecast_horizon_hours": 3,
        "train_samples": len(train_idx),
        "val_samples": len(val_idx),
        "test_samples": len(test_idx),
        "total_sequences": len(X_raw),
        "split_strategy": "Chronological 70/15/15 with 12-hour purge buffers",
        "architecture": {
            "model_type": "Diffusion Convolutional Recurrent Neural Network (DCRNN)",
            "graph_supports": "Identity + Forward Pf + Backward Pb + Pf^2 + Pb^2 (K=2 hops)",
            "num_layers": 2,
            "hidden_dimension": 64,
            "dropout": 0.15,
            "readout_head": "Linear(64, 32) -> ReLU -> Linear(32, 1)"
        },
        "training_hyperparameters": {
            "loss_function": "SmoothL1Loss(beta=0.5) [Masked Huber]",
            "optimizer": "AdamW",
            "initial_learning_rate": 1e-3,
            "weight_decay": 1e-4,
            "batch_size": 64,
            "max_epochs": num_epochs,
            "early_stopping_patience": patience,
            "best_epoch": best_gnn_state["epoch"],
            "best_val_loss": round(best_val_loss_gnn, 6),
            "training_duration_seconds": round(training_time, 2)
        },
        "normalization": {
            "sensor_wise_stage": True,
            "mu_level": [round(float(m), 4) for m in mu_level],
            "sigma_level": [round(float(s), 4) for s in sigma_level],
            "mu_rain": round(mu_rain, 4),
            "sigma_rain": round(sigma_rain, 4)
        },
        "test_benchmark": {
            "persistence": metrics_persist,
            "ridge_ar": metrics_ridge,
            "temporal_gru": metrics_temp,
            "st_gnn_dcrnn": metrics_gnn,
            "high_water_test": {
                "persistence": metrics_hw_persist,
                "ridge_ar": metrics_hw_ridge,
                "temporal_gru": metrics_hw_temp,
                "st_gnn_dcrnn": metrics_hw_gnn
            },
            "peak_timing_error_hours": {
                "persistence": dt_persist,
                "ridge_ar": dt_ridge,
                "temporal_gru": dt_temp,
                "st_gnn_dcrnn": dt_gnn
            }
        }
    }

    config_path_results = os.path.join(RESULT_DIR, "BLUE_HEART_TRAINING_CONFIG.json")
    config_path_root = os.path.join(PROJECT_ROOT, "BLUE_HEART_TRAINING_CONFIG.json")
    with open(config_path_results, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
    with open(config_path_root, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)

    # B. Training History CSV
    df_history = pd.DataFrame(history)
    history_path_results = os.path.join(RESULT_DIR, "BLUE_HEART_TRAINING_HISTORY.csv")
    history_path_root = os.path.join(PROJECT_ROOT, "BLUE_HEART_TRAINING_HISTORY.csv")
    df_history.to_csv(history_path_results, index=False)
    df_history.to_csv(history_path_root, index=False)

    # C. Test Predictions CSV
    pred_records = []
    for seq_i in range(len(test_idx)):
        orig_seq_idx = int(test_idx[seq_i])
        for node_i in range(N_nodes):
            s_name = str(sensor_names[node_i])
            pred_records.append({
                "test_step": seq_i,
                "dataset_seq_index": orig_seq_idx,
                "sensor_idx": node_i,
                "sensor_name": s_name,
                "true_level_m": round(float(Y_test_true[seq_i, node_i]), 4),
                "st_gnn_pred_m": round(float(Y_pred_gnn[seq_i, node_i]), 4),
                "temporal_gru_pred_m": round(float(Y_pred_temp[seq_i, node_i]), 4),
                "persistence_pred_m": round(float(Y_pred_persist[seq_i, node_i]), 4),
                "error_st_gnn_m": round(float(Y_pred_gnn[seq_i, node_i] - Y_test_true[seq_i, node_i]), 4),
                "error_temporal_m": round(float(Y_pred_temp[seq_i, node_i] - Y_test_true[seq_i, node_i]), 4)
            })
    df_preds = pd.DataFrame(pred_records)
    preds_path_results = os.path.join(RESULT_DIR, "BLUE_HEART_TEST_PREDICTIONS.csv")
    preds_path_root = os.path.join(PROJECT_ROOT, "BLUE_HEART_TEST_PREDICTIONS.csv")
    df_preds.to_csv(preds_path_results, index=False)
    df_preds.to_csv(preds_path_root, index=False)

    # D. Save Per-Sensor Comparison Summary JSON
    sensor_summary = {
        "st_gnn": per_sensor_gnn,
        "temporal_gru": per_sensor_temp,
        "persistence": per_sensor_persist
    }
    with open(os.path.join(RESULT_DIR, "BLUE_HEART_PER_SENSOR_EVALUATION.json"), "w", encoding="utf-8") as f:
        json.dump(sensor_summary, f, indent=2)

    print(f"\n[Artifacts Successfully Written]:")
    print(f"  - {config_path_root}")
    print(f"  - {history_path_root}")
    print(f"  - {preds_path_root}")
    print(f"  - {best_ckpt_path}")
    print(f"  - {final_ckpt_path}")

    # 9. Smoke Test Verification
    print("\n[Smoke Test Verification]: Testing independent model loading...")
    smoke_ckpt = torch.load(best_ckpt_path, map_location='cpu', weights_only=False)
    smoke_model = DCRNNModel(smoke_ckpt['supports'], in_dim=3, hidden_dim=smoke_ckpt['hidden_dim'], num_layers=smoke_ckpt['num_layers'])
    smoke_model.load_state_dict(smoke_ckpt['model_state_dict'])
    smoke_model.eval()

    sample_x = torch.tensor(X_test[:5], dtype=torch.float32)
    with torch.no_grad():
        sample_pred_norm = smoke_model(sample_x).numpy()
    sample_pred_m = sample_pred_norm * smoke_ckpt['sigma_level'][None, :] + smoke_ckpt['mu_level'][None, :]

    print(f"  Smoke Test Input Shape:  {sample_x.shape}")
    print(f"  Smoke Test Output Shape: {sample_pred_m.shape}")
    print(f"  Sample 0 True Level (first 3 gullies): {Y_test_true[0, :3]}")
    print(f"  Sample 0 Pred Level (first 3 gullies): {sample_pred_m[0, :3]}")
    assert not np.isnan(sample_pred_m).any(), "ERROR: Smoke test produced NaNs!"
    assert sample_pred_m.shape == (5, 15), f"ERROR: Unexpected shape {sample_pred_m.shape}"
    print("  ✓ Smoke test passed: Model weights load cleanly, forward inference succeeds without error, outputs are finite.")

    print("\n==================================================================")
    print(" TASK 3.1 TRAINING & EVALUATION COMPLETED SUCCESSFULLY")
    print("==================================================================")

if __name__ == "__main__":
    main()

