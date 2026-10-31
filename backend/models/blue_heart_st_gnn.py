"""
HYDRO-GUARD AI — Task 3.3 Blue Heart Urban ST-GNN Integration Engine.
Loads Task 3.2 Adaptive Gated Spatio-Temporal Graph Neural Network candidate
(checkpoints/blue_heart/v2/best_adaptive_st_gnn.pt) for real-data road-gully water level forecasting.

Scientific Separation:
- Clearly distinguished from the Indore Municipal Corporation demonstration digital twin.
- Evaluated on real historical Blue Heart highway telemetry (Eastbourne, UK; Zenodo 20699635).
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger("hydroguard.blue_heart_gnn")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CKPT_PATH = PROJECT_ROOT / "checkpoints" / "blue_heart" / "v2" / "best_adaptive_st_gnn.pt"
GRAPH_PATH = PROJECT_ROOT / "data" / "processed_global" / "urban_graphs" / "blue_heart_gully_adjacency.npy"
DATA_NPZ = PROJECT_ROOT / "data" / "processed_global" / "urban_sequences" / "blue_heart_sequences_w12_h3.npz"
BENCHMARK_PATH = PROJECT_ROOT / "BLUE_HEART_V2_BENCHMARK.json"


# ---------------------------------------------------------------------------
# ARCHITECTURE DEFINITION (Matches Training Script in Task 3.2)
# ---------------------------------------------------------------------------

class GraphDiffusionConv(nn.Module):
    def __init__(self, supports: List[torch.Tensor], in_dim: int, out_dim: int):
        super().__init__()
        self.register_buffer('supports', torch.stack(supports))
        self.num_supports = len(supports)
        self.fc = nn.Linear(self.num_supports * in_dim, out_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        outs = [torch.matmul(s, x) for s in self.supports]
        return self.fc(torch.cat(outs, dim=-1))


class AdaptiveGatedDCGRUCell(nn.Module):
    def __init__(self, supports: List[torch.Tensor], in_dim: int, hidden_dim: int, num_nodes: int = 15):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_nodes = num_nodes
        self.local_gates = nn.Linear(in_dim + hidden_dim, 2 * hidden_dim)
        self.local_candidate = nn.Linear(in_dim + hidden_dim, hidden_dim)
        self.spatial_gates = GraphDiffusionConv(supports, in_dim + hidden_dim, 2 * hidden_dim)
        self.spatial_candidate = GraphDiffusionConv(supports, in_dim + hidden_dim, hidden_dim)
        self.alpha = nn.Parameter(torch.zeros(1, num_nodes, hidden_dim))

    def forward(self, x: torch.Tensor, h: torch.Tensor) -> torch.Tensor:
        combined = torch.cat([x, h], dim=-1)
        gate_weight = torch.sigmoid(self.alpha)
        
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
    def __init__(self, supports: List[torch.Tensor], in_dim: int = 3, hidden_dim: int = 64, num_layers: int = 2, num_nodes: int = 15, dropout: float = 0.0):
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

    def forward(self, x_seq: torch.Tensor) -> torch.Tensor:
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


# ---------------------------------------------------------------------------
# INFERENCE SERVICE WRAPPER
# ---------------------------------------------------------------------------

class BlueHeartSTGNNService:
    """Production Inference Service for Blue Heart Adaptive Gated ST-GNN."""

    def __init__(self):
        self.model: Optional[AdaptiveGatedDCRNNModel] = None
        self.is_loaded: bool = False
        self.sensor_names: List[str] = []
        self.num_nodes: int = 15
        self.mu_delta: np.ndarray = np.zeros(15, dtype=np.float32)
        self.sigma_delta: np.ndarray = np.ones(15, dtype=np.float32)
        self.mu_level: np.ndarray = np.zeros(15, dtype=np.float32)
        self.sigma_level: np.ndarray = np.ones(15, dtype=np.float32)
        self.mu_rain: float = 0.1281
        self.sigma_rain: float = 0.6621
        self._load_engine()

    def _load_engine(self):
        try:
            if not CKPT_PATH.exists() or not GRAPH_PATH.exists():
                logger.warning("Blue Heart checkpoint or graph adjacency missing.")
                return

            # 1. Load Graph and Diffusion Supports
            adj = np.load(str(GRAPH_PATH))
            self.num_nodes = adj.shape[0]
            d_out = adj.sum(axis=1, keepdims=True)
            d_out[d_out == 0] = 1.0
            Pf = torch.tensor(adj / d_out, dtype=torch.float32)

            d_in = adj.sum(axis=0, keepdims=True)
            d_in[d_in == 0] = 1.0
            Pb = torch.tensor((adj.T) / (d_in.T), dtype=torch.float32)

            I = torch.eye(self.num_nodes, dtype=torch.float32)
            supports = [I, Pf, Pb, torch.matmul(Pf, Pf), torch.matmul(Pb, Pb)]

            # 2. Build Model & Load Checkpoint
            self.model = AdaptiveGatedDCRNNModel(supports, in_dim=3, hidden_dim=64, num_layers=2, num_nodes=self.num_nodes, dropout=0.0)
            state_dict = torch.load(str(CKPT_PATH), map_location='cpu', weights_only=False)
            self.model.load_state_dict(state_dict)
            self.model.eval()

            # 3. Load Normalization Parameters
            if BENCHMARK_PATH.exists():
                with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
                    bench = json.load(f)
                self.mu_delta = np.array(bench.get("normalization_delta", {}).get("mu_delta", np.zeros(15)), dtype=np.float32)
                self.sigma_delta = np.array(bench.get("normalization_delta", {}).get("sigma_delta", np.ones(15)), dtype=np.float32)

            # 4. Sensor Names
            if DATA_NPZ.exists():
                npz_data = np.load(str(DATA_NPZ), allow_pickle=True)
                self.sensor_names = [str(s) for s in npz_data['sensor_names']]
                tr_idx = npz_data['train_idx']
                self.mu_level = npz_data['X'][tr_idx, :, :, 0].mean(axis=(0, 1))
                self.sigma_level = npz_data['X'][tr_idx, :, :, 0].std(axis=(0, 1))
                self.sigma_level[self.sigma_level < 1e-4] = 1.0

            self.is_loaded = True
            logger.info("Adaptive Gated ST-GNN loaded successfully from %s", CKPT_PATH)
        except Exception as e:
            logger.error("Failed to load Adaptive Gated ST-GNN: %s", e)
            self.is_loaded = False

    def predict_sample(self, test_index: int = 0) -> Dict[str, Any]:
        """Runs forward inference on a real held-out test sequence."""
        if not self.is_loaded or not DATA_NPZ.exists():
            return {"status": "error", "message": "Engine not loaded or data tensor missing."}

        npz_data = np.load(str(DATA_NPZ), allow_pickle=True)
        te_idx = npz_data['test_idx']
        if test_index >= len(te_idx):
            test_index = 0
            
        seq_idx = int(te_idx[test_index])
        x_raw = npz_data['X'][seq_idx:seq_idx + 1] # (1, 12, 15, 2)
        mask_raw = npz_data['mask'][seq_idx:seq_idx + 1] # (1, 12, 15)
        y_true = npz_data['Y_level'][seq_idx] # (15,)
        x_last = x_raw[0, -1, :, 0] # (15,)

        # Normalize Input
        x_norm = np.zeros((1, 12, self.num_nodes, 3), dtype=np.float32)
        x_norm[:, :, :, 0] = (x_raw[:, :, :, 0] - self.mu_level[None, None, :]) / self.sigma_level[None, None, :]
        x_norm[:, :, :, 1] = (x_raw[:, :, :, 1] - self.mu_rain) / self.sigma_rain
        x_norm[:, :, :, 2] = mask_raw

        with torch.no_grad():
            x_tensor = torch.tensor(x_norm, dtype=torch.float32)
            pred_dy_norm = self.model(x_tensor).numpy()[0] # (15,)

        pred_dy = pred_dy_norm * self.sigma_delta + self.mu_delta
        pred_y = x_last + pred_dy

        node_results = []
        for i in range(self.num_nodes):
            s_name = self.sensor_names[i] if i < len(self.sensor_names) else f"Gully_{i}"
            cur_stage = float(x_last[i])
            pred_stage = float(pred_y[i])
            true_stage = float(y_true[i])
            delta_cm = float(pred_dy[i] * 100.0)
            err_mm = float(abs(pred_stage - true_stage) * 1000.0)
            surcharge = pred_stage > 0.30

            node_results.append({
                "sensor_idx": i,
                "sensor_name": s_name,
                "current_level_m": round(cur_stage, 4),
                "predicted_level_m": round(pred_stage, 4),
                "true_level_m": round(true_stage, 4),
                "predicted_change_cm": round(delta_cm, 2),
                "absolute_error_mm": round(err_mm, 2),
                "surcharge_risk": bool(surcharge),
                "status": "SURCHARGE WARNING" if surcharge else "NORMAL"
            })

        mean_err_mm = float(np.mean([n["absolute_error_mm"] for n in node_results]))
        return {
            "status": "success",
            "model": "Adaptive Gated ST-GNN (v2)",
            "domain": "Blue Heart Urban Catchment (Eastbourne, UK)",
            "test_sample_index": test_index,
            "dataset_sequence_index": seq_idx,
            "forecast_horizon_hours": 3,
            "lookback_window_hours": 12,
            "mean_absolute_error_mm": round(mean_err_mm, 2),
            "max_predicted_stage_m": round(float(np.max(pred_y)), 4),
            "nodes": node_results
        }

    def get_benchmark_metadata(self) -> Dict[str, Any]:
        """Returns official Task 3.2 benchmark scores."""
        if BENCHMARK_PATH.exists():
            with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "status": "warning",
            "message": "Benchmark summary file not found."
        }


# Singleton Instance
blue_heart_st_gnn = BlueHeartSTGNNService()

