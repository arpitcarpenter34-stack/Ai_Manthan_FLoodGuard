#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HYDRO-GUARD AI — TASK 3.2: ST-GNN PERFORMANCE OPTIMIZATION & ERROR ANALYSIS
Controlled Experiment Pipeline for Urban Drainage Water Level Forecasting.

Experiments:
1. Baseline 1: Persistence (lag-0 stage X_last)
2. Baseline 2: Multi-Station Ridge AR (residual formulation)
3. Experiment A: Optimized Residual Temporal GRU (Res-GRU)
4. Experiment B: Residual Spatio-Temporal GNN (Res-DCRNN)
5. Experiment C: Adaptive Gated ST-GNN (Gated Spatial Diffusion)
6. Experiment D: Graph WaveNet (Dilated Causal TCN + Adaptive Graph Diffusion)

Preservation Rules:
- Original Task 3.1 checkpoint (checkpoints/blue_heart/best_st_gnn.pt) remains UNTOUCHED.
- All v2 checkpoints saved in checkpoints/blue_heart/v2/
- All v2 logs saved in logs/blue_heart/v2/
- All v2 results saved in results/blue_heart/v2/
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
import torch.nn.functional as F
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

V2_CHECKPOINT_DIR = os.path.join(PROJECT_ROOT, r"checkpoints\blue_heart\v2")
V2_LOG_DIR = os.path.join(PROJECT_ROOT, r"logs\blue_heart\v2")
V2_RESULT_DIR = os.path.join(PROJECT_ROOT, r"results\blue_heart\v2")

os.makedirs(V2_CHECKPOINT_DIR, exist_ok=True)
os.makedirs(V2_LOG_DIR, exist_ok=True)
os.makedirs(V2_RESULT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. MODEL ARCHITECTURES
# ---------------------------------------------------------------------------

class GraphDiffusionConv(nn.Module):
    """Spatial Diffusion Convolution across multiple transition supports."""
    def __init__(self, supports, in_dim, out_dim):
        super().__init__()
        self.register_buffer('supports', torch.stack(supports)) # (K, N, N)
        self.num_supports = len(supports)
        self.fc = nn.Linear(self.num_supports * in_dim, out_dim)

    def forward(self, x):
        # x: (B, N, in_dim)
        outs = [torch.matmul(s, x) for s in self.supports]
        return self.fc(torch.cat(outs, dim=-1))


class DCGRUCell(nn.Module):
    """Diffusion Convolutional GRU Cell."""
    def __init__(self, supports, in_dim, hidden_dim):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.conv_gates = GraphDiffusionConv(supports, in_dim + hidden_dim, 2 * hidden_dim)
        self.conv_candidate = GraphDiffusionConv(supports, in_dim + hidden_dim, hidden_dim)

    def forward(self, x, h):
        combined = torch.cat([x, h], dim=-1)
        gates = torch.sigmoid(self.conv_gates(combined))
        reset_gate, update_gate = torch.split(gates, self.hidden_dim, dim=-1)
        c_in = torch.cat([x, reset_gate * h], dim=-1)
        candidate = torch.tanh(self.conv_candidate(c_in))
        return update_gate * h + (1.0 - update_gate) * candidate


class ResDCRNNModel(nn.Module):
    """
    Experiment B: Residual Spatio-Temporal GNN (Res-DCRNN).
    Predicts normalized stage difference Delta Y, added to persistence X_last.
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
            x_t = x_seq[:, t]
            for layer_idx, cell in enumerate(self.cells):
                h[layer_idx] = cell(x_t, h[layer_idx])
                if layer_idx < self.num_layers - 1:
                    x_t = self.dropout(h[layer_idx])
                else:
                    x_t = h[layer_idx]
        delta_norm = self.readout(h[-1]).squeeze(-1) # (B, N)
        return delta_norm


class AdaptiveGatedDCGRUCell(nn.Module):
    """
    Experiment C: Adaptive Gated DCGRU Cell.
    Dynamically balances pure local temporal recurrence vs spatial graph diffusion per node.
    """
    def __init__(self, supports, in_dim, hidden_dim, num_nodes=15):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_nodes = num_nodes
        # Local temporal linear gates
        self.local_gates = nn.Linear(in_dim + hidden_dim, 2 * hidden_dim)
        self.local_candidate = nn.Linear(in_dim + hidden_dim, hidden_dim)
        # Spatial diffusion gates
        self.spatial_gates = GraphDiffusionConv(supports, in_dim + hidden_dim, 2 * hidden_dim)
        self.spatial_candidate = GraphDiffusionConv(supports, in_dim + hidden_dim, hidden_dim)
        # Learnable node-wise spatial mixing gate logit: alpha in [-inf, inf]
        self.alpha = nn.Parameter(torch.zeros(1, num_nodes, hidden_dim))

    def forward(self, x, h):
        combined = torch.cat([x, h], dim=-1)
        gate_weight = torch.sigmoid(self.alpha) # (1, N, hidden_dim) in [0, 1]
        
        # Local vs Spatial gates blending
        g_local = self.local_gates(combined)
        g_spatial = self.spatial_gates(combined)
        g_blend = torch.sigmoid((1.0 - gate_weight.repeat(1, 1, 2)) * g_local + gate_weight.repeat(1, 1, 2) * g_spatial)
        reset_gate, update_gate = torch.split(g_blend, self.hidden_dim, dim=-1)
        
        c_in = torch.cat([x, reset_gate * h], dim=-1)
        c_local = self.local_candidate(c_in)
        c_spatial = self.spatial_candidate(c_in)
        candidate = torch.tanh((1.0 - gate_weight) * c_local + gate_weight * c_spatial)
        
        return update_gate * h + (1.0 - update_gate) * candidate


class AdaptiveGatedDCRNNModel(nn.Module):
    """Experiment C: Full Adaptive Gated ST-GNN."""
    def __init__(self, supports, in_dim=3, hidden_dim=64, num_layers=2, num_nodes=15, dropout=0.15):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.cells = nn.ModuleList([
            AdaptiveGatedDCGRUCell(supports, in_dim if i == 0 else hidden_dim, hidden_dim, num_nodes=num_nodes)
            for i in range(num_layers)
        ])
        self.dropout = nn.Dropout(dropout)
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x_seq):
        B, T, N, C = x_seq.shape
        h = [torch.zeros(B, N, self.hidden_dim, device=x_seq.device) for _ in range(self.num_layers)]
        for t in range(T):
            x_t = x_seq[:, t]
            for layer_idx, cell in enumerate(self.cells):
                h[layer_idx] = cell(x_t, h[layer_idx])
                if layer_idx < self.num_layers - 1:
                    x_t = self.dropout(h[layer_idx])
                else:
                    x_t = h[layer_idx]
        delta_norm = self.readout(h[-1]).squeeze(-1)
        return delta_norm


class ResTemporalGRUModel(nn.Module):
    """
    Experiment A: Optimized Residual Temporal GRU (Res-GRU).
    Replaces static level regression with residual delta prediction + layer normalization.
    """
    def __init__(self, in_dim=3, hidden_dim=64, num_layers=2, dropout=0.15):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.gru = nn.GRU(
            in_dim, hidden_dim, num_layers=num_layers,
            batch_first=True, dropout=dropout if num_layers > 1 else 0.0
        )
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x_seq):
        B, T, N, C = x_seq.shape
        x_flat = x_seq.permute(0, 2, 1, 3).reshape(B * N, T, C)
        out, _ = self.gru(x_flat)
        last_h = self.layer_norm(out[:, -1, :])
        delta_norm = self.readout(last_h).reshape(B, N)
        return delta_norm


class GatedTCNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=2, dilation=1):
        super().__init__()
        self.pad = (kernel_size - 1) * dilation
        self.conv_f = nn.Conv2d(in_channels, out_channels, (1, kernel_size), dilation=(1, dilation))
        self.conv_g = nn.Conv2d(in_channels, out_channels, (1, kernel_size), dilation=(1, dilation))
    def forward(self, x):
        # x: (B, C, N, T)
        x_pad = F.pad(x, (self.pad, 0, 0, 0))
        return torch.tanh(self.conv_f(x_pad)) * torch.sigmoid(self.conv_g(x_pad))


class GraphWaveNetModel(nn.Module):
    """
    Experiment D: Graph WaveNet.
    Combines dilated causal temporal convolutions with spatial diffusion over physical
    and learnable adaptive graph adjacency.
    """
    def __init__(self, supports, num_nodes=15, in_dim=3, hidden_dim=32, num_blocks=4):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        
        # Adaptive graph embeddings: A_adp = Softmax(ReLU(E1 @ E2^T))
        self.nodevec1 = nn.Parameter(torch.randn(num_nodes, 8))
        self.nodevec2 = nn.Parameter(torch.randn(num_nodes, 8))
        
        self.register_buffer('phys_supports', torch.stack(supports))
        self.total_supports = len(supports) + 1 # Physical supports + 1 adaptive support
        
        self.start_conv = nn.Conv2d(in_dim, hidden_dim, (1, 1))
        
        # Multi-scale temporal dilation blocks
        self.tcn_blocks = nn.ModuleList([
            GatedTCNBlock(hidden_dim, hidden_dim, kernel_size=2, dilation=2**i)
            for i in range(num_blocks)
        ])
        
        # Spatial graph conv after temporal blocks
        self.gconv = nn.Conv2d(hidden_dim * self.total_supports, hidden_dim, (1, 1))
        self.layer_norm = nn.LayerNorm(hidden_dim)
        
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x_seq):
        # x_seq: (B, T, N, C) -> Permute to (B, C, N, T)
        x = x_seq.permute(0, 3, 2, 1)
        h = self.start_conv(x)
        
        # Compute adaptive adjacency
        A_adp = F.softmax(F.relu(torch.matmul(self.nodevec1, self.nodevec2.T)), dim=-1)
        
        # Pass through dilated causal TCN blocks with residual connections
        for tcn in self.tcn_blocks:
            h = h + tcn(h)
            
        # Spatial diffusion over final temporal state: h[:, :, :, -1] (B, hidden_dim, N)
        h_last = h[:, :, :, -1].unsqueeze(-1) # (B, C, N, 1)
        
        outs = []
        for s in self.phys_supports:
            outs.append(torch.einsum('ij, bcjt -> bcit', s, h_last))
        outs.append(torch.einsum('ij, bcjt -> bcit', A_adp, h_last))
        
        h_diff = self.gconv(torch.cat(outs, dim=1)) # (B, hidden_dim, N, 1)
        h_diff = h_diff.squeeze(-1).permute(0, 2, 1) # (B, N, hidden_dim)
        h_diff = self.layer_norm(h_diff)
        
        delta_norm = self.readout(h_diff).squeeze(-1) # (B, N)
        return delta_norm

# ---------------------------------------------------------------------------
# 2. DATASET LOADER & METRIC UTILITIES
# ---------------------------------------------------------------------------

class ResidualSequenceDataset(Dataset):
    def __init__(self, X, Delta_Y_norm, X_last):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.Delta_Y_norm = torch.tensor(Delta_Y_norm, dtype=torch.float32)
        self.X_last = torch.tensor(X_last, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.Delta_Y_norm[idx], self.X_last[idx]


def compute_metrics(y_true, y_pred, mask=None):
    """Compute overall MAE, RMSE, R^2, and NSE with optional boolean mask."""
    if mask is not None:
        yt = y_true[mask]
        yp = y_pred[mask]
    else:
        yt = y_true
        yp = y_pred
        
    err = yp - yt
    mae = float(np.abs(err).mean())
    rmse = float(np.sqrt((err**2).mean()))
    
    # NSE
    mean_true = yt.mean()
    sst = float(((yt - mean_true)**2).sum())
    sse = float((err**2).sum())
    nse = float(1.0 - (sse / sst)) if sst > 1e-8 else 0.0
    
    # R^2
    var_true = np.var(yt)
    var_pred = np.var(yp)
    if var_true > 1e-8 and var_pred > 1e-8:
        cov = np.mean((yt - np.mean(yt)) * (yp - np.mean(yp)))
        r2 = float((cov / (np.std(yt) * np.std(yp)))**2)
    else:
        r2 = 0.0
        
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "nse": round(nse, 4), "r2": round(r2, 4)}


def compute_per_sensor_metrics(y_true, y_pred, sensor_names, mask=None):
    """Compute per-sensor breakdown."""
    results = []
    N = y_true.shape[1]
    for i in range(N):
        if mask is not None:
            m_i = mask[:, i]
            yt = y_true[m_i, i]
            yp = y_pred[m_i, i]
        else:
            yt = y_true[:, i]
            yp = y_pred[:, i]
            
        if len(yt) == 0:
            results.append({
                "sensor_idx": i, "sensor_name": str(sensor_names[i]),
                "mae_m": 0.0, "rmse_m": 0.0, "nse": 0.0, "r2": 0.0, "valid_count": 0
            })
            continue
            
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
            "r2": round(r2, 4),
            "valid_count": int(len(yt))
        })
    return results


def compute_peak_timing_error(y_true, y_pred, top_n_peaks=10, window=12):
    N_samples, N_nodes = y_true.shape
    mean_stage = y_true.mean(axis=1)
    peaks = []
    for t in range(window, N_samples - window):
        if mean_stage[t] == np.max(mean_stage[t - window : t + window + 1]):
            peaks.append((t, mean_stage[t]))
    peaks = sorted(peaks, key=lambda x: x[1], reverse=True)[:top_n_peaks]
    
    timing_errors = []
    for peak_t, _ in peaks:
        t_start = max(0, peak_t - window)
        t_end = min(N_samples, peak_t + window + 1)
        actual_peak_idx = t_start + np.argmax(mean_stage[t_start:t_end])
        pred_stage_window = y_pred[t_start:t_end].mean(axis=1)
        pred_peak_idx = t_start + np.argmax(pred_stage_window)
        timing_errors.append(abs(actual_peak_idx - pred_peak_idx))
    return float(np.mean(timing_errors)) if timing_errors else 0.0

# ---------------------------------------------------------------------------
# 3. TRAINING RUNNER
# ---------------------------------------------------------------------------

def train_residual_model(model, train_loader, val_loader, mu_delta, sigma_delta, num_epochs=25, patience=6, lr=1e-3):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3, min_lr=1e-5)
    loss_fn = nn.SmoothL1Loss(beta=0.5)
    
    best_val_loss = float('inf')
    best_state = None
    best_epoch = 0
    patience_cnt = 0
    history = []
    
    for epoch in range(1, num_epochs + 1):
        model.train()
        train_loss = 0.0
        for bx, b_dy_norm, b_xlast in train_loader:
            optimizer.zero_grad()
            pred_dy_norm = model(bx)
            loss = loss_fn(pred_dy_norm, b_dy_norm)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            train_loss += loss.item() * len(bx)
        train_loss /= len(train_loader.dataset)
        
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for bx, b_dy_norm, b_xlast in val_loader:
                pred_dy_norm = model(bx)
                loss = loss_fn(pred_dy_norm, b_dy_norm)
                val_loss += loss.item() * len(bx)
        val_loss /= len(val_loader.dataset)
        
        scheduler.step(val_loss)
        cur_lr = optimizer.param_groups[0]['lr']
        history.append({"epoch": epoch, "train_loss": round(train_loss, 6), "val_loss": round(val_loss, 6), "lr": cur_lr})
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            patience_cnt = 0
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_cnt += 1
            if patience_cnt >= patience:
                break
                
    model.load_state_dict(best_state)
    return model, best_state, best_epoch, best_val_loss, history

# ---------------------------------------------------------------------------
# 4. MAIN EXPERIMENT CONTROL LOOP
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print(" HYDRO-GUARD AI — TASK 3.2: ST-GNN PERFORMANCE OPTIMIZATION & ERROR ANALYSIS")
    print(" Controlled Benchmark: Persistence vs Ridge vs Res-GRU vs Res-DCRNN vs Adaptive-GNN vs GWNet")
    print("=" * 80)

    # 1. Load Data
    data = np.load(DATA_NPZ, allow_pickle=True)
    X_raw = data['X']               # (7282, 12, 15, 2)
    Y_level_raw = data['Y_level']   # (7282, 15)
    mask = data['mask']             # (7282, 12, 15)
    train_idx = data['train_idx']   # (5085,)
    val_idx = data['val_idx']       # (1080,)
    test_idx = data['test_idx']     # (1093,)
    sensor_names = data['sensor_names']

    N_nodes = len(sensor_names)
    print(f"Total sequences: {len(X_raw)} (Train: {len(train_idx)}, Val: {len(val_idx)}, Test: {len(test_idx)})")

    # 2. Calculate Persistence Lag-0 Base (X_last) & Residual Delta
    X_last_all = X_raw[:, -1, :, 0] # Physical water level at t=11 (meters)
    Delta_Y_all = Y_level_raw - X_last_all # Physical change in water level (meters)

    # Normalization parameters computed STRICTLY from train set
    mu_level = X_raw[train_idx, :, :, 0].mean(axis=(0, 1))
    sigma_level = X_raw[train_idx, :, :, 0].std(axis=(0, 1))
    sigma_level = np.where(sigma_level < 1e-4, 1.0, sigma_level)

    mu_rain = float(X_raw[train_idx, :, :, 1].mean())
    sigma_rain = float(X_raw[train_idx, :, :, 1].std())
    if sigma_rain < 1e-4: sigma_rain = 1.0

    mu_delta = Delta_Y_all[train_idx].mean(axis=0)
    sigma_delta = Delta_Y_all[train_idx].std(axis=0)
    sigma_delta = np.where(sigma_delta < 1e-4, 1.0, sigma_delta)

    print(f"Train Delta Mean: [{mu_delta.min():.5f}, {mu_delta.max():.5f}] m")
    print(f"Train Delta Std:  [{sigma_delta.min():.5f}, {sigma_delta.max():.5f}] m")

    # Input tensor: [norm_stage, norm_rain, mask]
    X_norm = np.zeros((X_raw.shape[0], X_raw.shape[1], X_raw.shape[2], 3), dtype=np.float32)
    X_norm[:, :, :, 0] = (X_raw[:, :, :, 0] - mu_level[None, None, :]) / sigma_level[None, None, :]
    X_norm[:, :, :, 1] = (X_raw[:, :, :, 1] - mu_rain) / sigma_rain
    X_norm[:, :, :, 2] = mask

    Delta_Y_norm = (Delta_Y_all - mu_delta[None, :]) / sigma_delta[None, :]

    # Slices
    X_train, dY_train_norm, Xlast_train = X_norm[train_idx], Delta_Y_norm[train_idx], X_last_all[train_idx]
    X_val, dY_val_norm, Xlast_val = X_norm[val_idx], Delta_Y_norm[val_idx], X_last_all[val_idx]
    X_test, dY_test_norm, Xlast_test = X_norm[test_idx], Delta_Y_norm[test_idx], X_last_all[test_idx]

    Y_test_true = Y_level_raw[test_idx]
    valid_test_mask = (mask[test_idx, -1, :] == 1.0) # True reporting observations

    train_loader = DataLoader(ResidualSequenceDataset(X_train, dY_train_norm, Xlast_train), batch_size=64, shuffle=True)
    val_loader = DataLoader(ResidualSequenceDataset(X_val, dY_val_norm, Xlast_val), batch_size=64, shuffle=False)
    test_loader = DataLoader(ResidualSequenceDataset(X_test, dY_test_norm, Xlast_test), batch_size=64, shuffle=False)

    # 3. Load Graph Supports
    adj = np.load(GRAPH_NPY)
    d_out = adj.sum(axis=1, keepdims=True); d_out[d_out == 0] = 1.0
    Pf = torch.tensor(adj / d_out, dtype=torch.float32)
    d_in = adj.sum(axis=0, keepdims=True); d_in[d_in == 0] = 1.0
    Pb = torch.tensor((adj.T) / (d_in.T), dtype=torch.float32)
    I = torch.eye(N_nodes, dtype=torch.float32)
    supports = [I, Pf, Pb, torch.matmul(Pf, Pf), torch.matmul(Pb, Pb)]

    # Dictionary to collect test predictions
    all_predictions = {}
    benchmark_results = {}
    all_histories = {}

    # -----------------------------------------------------------------------
    # BASELINE 1: PERSISTENCE
    # -----------------------------------------------------------------------
    print("\n--- Running Baseline 1: Persistence ---")
    Y_pred_persist = Xlast_test
    all_predictions["Persistence"] = Y_pred_persist
    benchmark_results["Persistence"] = {
        "all_obs": compute_metrics(Y_test_true, Y_pred_persist),
        "valid_obs": compute_metrics(Y_test_true, Y_pred_persist, mask=valid_test_mask),
        "peak_dt": compute_peak_timing_error(Y_test_true, Y_pred_persist)
    }

    # -----------------------------------------------------------------------
    # BASELINE 2: RESIDUAL MULTI-STATION RIDGE AR
    # -----------------------------------------------------------------------
    print("--- Running Baseline 2: Residual Ridge Autoregression ---")
    r_model = Ridge(alpha=100.0)
    x_tr_flat = X_norm[train_idx, :, :, :2].reshape(len(train_idx), -1)
    x_te_flat = X_norm[test_idx, :, :, :2].reshape(len(test_idx), -1)
    r_model.fit(x_tr_flat, Delta_Y_all[train_idx])
    pred_dy_ridge = r_model.predict(x_te_flat)
    Y_pred_ridge = Xlast_test + pred_dy_ridge
    all_predictions["Residual_Ridge"] = Y_pred_ridge
    benchmark_results["Residual_Ridge"] = {
        "all_obs": compute_metrics(Y_test_true, Y_pred_ridge),
        "valid_obs": compute_metrics(Y_test_true, Y_pred_ridge, mask=valid_test_mask),
        "peak_dt": compute_peak_timing_error(Y_test_true, Y_pred_ridge)
    }

    # -----------------------------------------------------------------------
    # EXPERIMENT A: RESIDUAL TEMPORAL GRU (Res-GRU)
    # -----------------------------------------------------------------------
    print("--- Running Experiment A: Residual Temporal GRU (Res-GRU) ---")
    model_gru = ResTemporalGRUModel(in_dim=3, hidden_dim=64, num_layers=2, dropout=0.15)
    model_gru, state_gru, ep_gru, val_gru, hist_gru = train_residual_model(
        model_gru, train_loader, val_loader, mu_delta, sigma_delta, num_epochs=25, patience=6, lr=1e-3
    )
    all_histories["Res_Temporal_GRU"] = hist_gru
    torch.save(state_gru, os.path.join(V2_CHECKPOINT_DIR, "best_res_temporal_gru.pt"))
    
    # Predict test
    test_dy_list = []
    with torch.no_grad():
        for bx, _, _ in test_loader:
            test_dy_list.append(model_gru(bx).numpy())
    pred_dy_norm_gru = np.concatenate(test_dy_list, axis=0)
    pred_dy_m_gru = pred_dy_norm_gru * sigma_delta[None, :] + mu_delta[None, :]
    Y_pred_gru = Xlast_test + pred_dy_m_gru
    all_predictions["Res_Temporal_GRU"] = Y_pred_gru
    benchmark_results["Res_Temporal_GRU"] = {
        "all_obs": compute_metrics(Y_test_true, Y_pred_gru),
        "valid_obs": compute_metrics(Y_test_true, Y_pred_gru, mask=valid_test_mask),
        "peak_dt": compute_peak_timing_error(Y_test_true, Y_pred_gru),
        "best_epoch": ep_gru, "best_val_loss": round(val_gru, 6)
    }

    # -----------------------------------------------------------------------
    # EXPERIMENT B: RESIDUAL SPATIO-TEMPORAL GNN (Res-DCRNN)
    # -----------------------------------------------------------------------
    print("--- Running Experiment B: Residual Spatio-Temporal GNN (Res-DCRNN) ---")
    model_dcrnn = ResDCRNNModel(supports, in_dim=3, hidden_dim=64, num_layers=2, dropout=0.15)
    model_dcrnn, state_dcrnn, ep_dcrnn, val_dcrnn, hist_dcrnn = train_residual_model(
        model_dcrnn, train_loader, val_loader, mu_delta, sigma_delta, num_epochs=25, patience=6, lr=1e-3
    )
    all_histories["Res_DCRNN"] = hist_dcrnn
    torch.save(state_dcrnn, os.path.join(V2_CHECKPOINT_DIR, "best_res_st_gnn.pt"))
    
    test_dy_list = []
    with torch.no_grad():
        for bx, _, _ in test_loader:
            test_dy_list.append(model_dcrnn(bx).numpy())
    pred_dy_norm_dcrnn = np.concatenate(test_dy_list, axis=0)
    pred_dy_m_dcrnn = pred_dy_norm_dcrnn * sigma_delta[None, :] + mu_delta[None, :]
    Y_pred_dcrnn = Xlast_test + pred_dy_m_dcrnn
    all_predictions["Res_DCRNN"] = Y_pred_dcrnn
    benchmark_results["Res_DCRNN"] = {
        "all_obs": compute_metrics(Y_test_true, Y_pred_dcrnn),
        "valid_obs": compute_metrics(Y_test_true, Y_pred_dcrnn, mask=valid_test_mask),
        "peak_dt": compute_peak_timing_error(Y_test_true, Y_pred_dcrnn),
        "best_epoch": ep_dcrnn, "best_val_loss": round(val_dcrnn, 6)
    }

    # -----------------------------------------------------------------------
    # EXPERIMENT C: ADAPTIVE GATED ST-GNN (Gated Spatial Diffusion)
    # -----------------------------------------------------------------------
    print("--- Running Experiment C: Adaptive Gated ST-GNN ---")
    model_ag_dcrnn = AdaptiveGatedDCRNNModel(supports, in_dim=3, hidden_dim=64, num_layers=2, num_nodes=N_nodes, dropout=0.15)
    model_ag_dcrnn, state_ag_dcrnn, ep_ag, val_ag, hist_ag = train_residual_model(
        model_ag_dcrnn, train_loader, val_loader, mu_delta, sigma_delta, num_epochs=25, patience=6, lr=1e-3
    )
    all_histories["Adaptive_Gated_DCRNN"] = hist_ag
    torch.save(state_ag_dcrnn, os.path.join(V2_CHECKPOINT_DIR, "best_adaptive_st_gnn.pt"))
    
    test_dy_list = []
    with torch.no_grad():
        for bx, _, _ in test_loader:
            test_dy_list.append(model_ag_dcrnn(bx).numpy())
    pred_dy_norm_ag = np.concatenate(test_dy_list, axis=0)
    pred_dy_m_ag = pred_dy_norm_ag * sigma_delta[None, :] + mu_delta[None, :]
    Y_pred_ag = Xlast_test + pred_dy_m_ag
    all_predictions["Adaptive_Gated_DCRNN"] = Y_pred_ag
    benchmark_results["Adaptive_Gated_DCRNN"] = {
        "all_obs": compute_metrics(Y_test_true, Y_pred_ag),
        "valid_obs": compute_metrics(Y_test_true, Y_pred_ag, mask=valid_test_mask),
        "peak_dt": compute_peak_timing_error(Y_test_true, Y_pred_ag),
        "best_epoch": ep_ag, "best_val_loss": round(val_ag, 6)
    }

    # -----------------------------------------------------------------------
    # EXPERIMENT D: GRAPH WAVENET (GWNet)
    # -----------------------------------------------------------------------
    print("--- Running Experiment D: Graph WaveNet (GWNet) ---")
    model_gwnet = GraphWaveNetModel(supports, num_nodes=N_nodes, in_dim=3, hidden_dim=32, num_blocks=4)
    model_gwnet, state_gwnet, ep_gw, val_gw, hist_gw = train_residual_model(
        model_gwnet, train_loader, val_loader, mu_delta, sigma_delta, num_epochs=25, patience=6, lr=1e-3
    )
    all_histories["Graph_WaveNet"] = hist_gw
    torch.save(state_gwnet, os.path.join(V2_CHECKPOINT_DIR, "best_graph_wavenet.pt"))
    
    test_dy_list = []
    with torch.no_grad():
        for bx, _, _ in test_loader:
            test_dy_list.append(model_gwnet(bx).numpy())
    pred_dy_norm_gw = np.concatenate(test_dy_list, axis=0)
    pred_dy_m_gw = pred_dy_norm_gw * sigma_delta[None, :] + mu_delta[None, :]
    Y_pred_gw = Xlast_test + pred_dy_m_gw
    all_predictions["Graph_WaveNet"] = Y_pred_gw
    benchmark_results["Graph_WaveNet"] = {
        "all_obs": compute_metrics(Y_test_true, Y_pred_gw),
        "valid_obs": compute_metrics(Y_test_true, Y_pred_gw, mask=valid_test_mask),
        "peak_dt": compute_peak_timing_error(Y_test_true, Y_pred_gw),
        "best_epoch": ep_gw, "best_val_loss": round(val_gw, 6)
    }

    # -----------------------------------------------------------------------
    # 5. COMPREHENSIVE BENCHMARK COMPARISON TABLE
    # -----------------------------------------------------------------------
    print("\n" + "=" * 105)
    print("                     TASK 3.2 CONTROLLED EXPERIMENT BENCHMARK (H = +3h)")
    print("=" * 105)
    print(f"{'Model Architecture':<26} | {'Val Loss':<10} | {'Test MAE(all)':<14} | {'Test RMSE(all)':<14} | {'Test NSE(all)':<13} | {'Valid MAE':<10} | {'Peak DT':<8}")
    print("-" * 105)
    for m_name in ["Persistence", "Residual_Ridge", "Res_Temporal_GRU", "Res_DCRNN", "Adaptive_Gated_DCRNN", "Graph_WaveNet"]:
        b = benchmark_results[m_name]
        vl = f"{b['best_val_loss']:.5f}" if 'best_val_loss' in b else "N/A"
        all_m = b["all_obs"]
        val_m = b["valid_obs"]
        print(f"{m_name:<26} | {vl:<10} | {all_m['mae']:<14.4f} | {all_m['rmse']:<14.4f} | {all_m['nse']:<13.4f} | {val_m['mae']:<10.4f} | {b['peak_dt']:<8.2f}h")
    print("=" * 105)

    # -----------------------------------------------------------------------
    # 6. HIGH-WATER PERFORMANCE (Top 10% Stages)
    # -----------------------------------------------------------------------
    thresh_90 = np.percentile(Y_test_true, 90)
    hw_mask = (Y_test_true >= thresh_90)
    hw_results = {}
    for m_name, preds in all_predictions.items():
        hw_results[m_name] = compute_metrics(Y_test_true, preds, mask=hw_mask)

    print("\n--- HIGH-WATER SUBSET EVALUATION (Top 10% Stages >= 1.10m) ---")
    for m_name, m_dict in hw_results.items():
        print(f"{m_name:<26} | HW MAE: {m_dict['mae']:.4f} m | HW RMSE: {m_dict['rmse']:.4f} m | HW NSE: {m_dict['nse']:.4f}")

    # -----------------------------------------------------------------------
    # 7. PER-SENSOR BREAKDOWN FOR BEST MODELS
    # -----------------------------------------------------------------------
    per_sensor_breakdown = {}
    for m_name, preds in all_predictions.items():
        per_sensor_breakdown[m_name] = compute_per_sensor_metrics(Y_test_true, preds, sensor_names, mask=valid_test_mask)

    # -----------------------------------------------------------------------
    # 8. EXPORT ALL DELIVERABLES
    # -----------------------------------------------------------------------
    # A. Config & Benchmark Summary
    summary_data = {
        "task": "TASK_3_2_PERFORMANCE_OPTIMIZATION",
        "dataset": "Blue Heart Urban Catchment (15 Gullies)",
        "forecast_horizon_hours": 3,
        "lookback_window_hours": 12,
        "benchmark_results": benchmark_results,
        "high_water_results": hw_results,
        "normalization_delta": {
            "mu_delta": [float(m) for m in mu_delta],
            "sigma_delta": [float(s) for s in sigma_delta]
        }
    }
    with open(os.path.join(V2_RESULT_DIR, "BLUE_HEART_V2_BENCHMARK.json"), "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    with open(os.path.join(PROJECT_ROOT, "BLUE_HEART_V2_BENCHMARK.json"), "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # B. Per-Sensor JSON
    with open(os.path.join(V2_RESULT_DIR, "BLUE_HEART_V2_PER_SENSOR.json"), "w", encoding="utf-8") as f:
        json.dump(per_sensor_breakdown, f, indent=2)
    with open(os.path.join(PROJECT_ROOT, "BLUE_HEART_V2_PER_SENSOR.json"), "w", encoding="utf-8") as f:
        json.dump(per_sensor_breakdown, f, indent=2)

    # C. History CSV
    history_rows = []
    for m_name, hist in all_histories.items():
        for row in hist:
            history_rows.append({"model": m_name, **row})
    df_hist = pd.DataFrame(history_rows)
    df_hist.to_csv(os.path.join(V2_RESULT_DIR, "BLUE_HEART_V2_TRAINING_HISTORY.csv"), index=False)
    df_hist.to_csv(os.path.join(PROJECT_ROOT, "BLUE_HEART_V2_TRAINING_HISTORY.csv"), index=False)

    # D. Test Predictions CSV
    pred_rows = []
    for t_i in range(len(test_idx)):
        orig_seq_idx = int(test_idx[t_i])
        for n_i in range(N_nodes):
            s_name = str(sensor_names[n_i])
            is_valid = bool(valid_test_mask[t_i, n_i])
            pred_rows.append({
                "test_step": t_i,
                "dataset_seq_index": orig_seq_idx,
                "sensor_idx": n_i,
                "sensor_name": s_name,
                "is_valid_reporting": is_valid,
                "true_level_m": round(float(Y_test_true[t_i, n_i]), 4),
                "persistence_pred_m": round(float(all_predictions["Persistence"][t_i, n_i]), 4),
                "res_temporal_gru_pred_m": round(float(all_predictions["Res_Temporal_GRU"][t_i, n_i]), 4),
                "res_dcrnn_pred_m": round(float(all_predictions["Res_DCRNN"][t_i, n_i]), 4),
                "adaptive_gated_dcrnn_pred_m": round(float(all_predictions["Adaptive_Gated_DCRNN"][t_i, n_i]), 4),
                "graph_wavenet_pred_m": round(float(all_predictions["Graph_WaveNet"][t_i, n_i]), 4)
            })
    df_preds = pd.DataFrame(pred_rows)
    df_preds.to_csv(os.path.join(V2_RESULT_DIR, "BLUE_HEART_V2_TEST_PREDICTIONS.csv"), index=False)
    df_preds.to_csv(os.path.join(PROJECT_ROOT, "BLUE_HEART_V2_TEST_PREDICTIONS.csv"), index=False)

    # 9. Smoke Test on V2 Checkpoints
    print("\n--- Smoke Test Verification on V2 Checkpoints ---")
    for ckpt_name in ["best_res_temporal_gru.pt", "best_res_st_gnn.pt", "best_adaptive_st_gnn.pt", "best_graph_wavenet.pt"]:
        p = os.path.join(V2_CHECKPOINT_DIR, ckpt_name)
        assert os.path.exists(p), f"Missing checkpoint {ckpt_name}"
        state = torch.load(p, map_location='cpu', weights_only=False)
        print(f"  ✓ {ckpt_name}: Verified on disk ({os.path.getsize(p)} bytes)")

    print("\n==================================================================")
    print(" TASK 3.2 CONTROLLED EXPERIMENTS COMPLETED SUCCESSFULLY")
    print("==================================================================")

if __name__ == "__main__":
    main()

