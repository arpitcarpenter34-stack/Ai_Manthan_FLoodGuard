# HYDRO-GUARD AI — TASK 3.0: TRAINING EXPERIMENT PLAN & REPRODUCIBILITY PROTOCOL

**Document ID:** `HGAI-PLN-EXPERIMENT-3.0-2026-10-31`  
**Project:** HYDRO-GUARD AI  
**Problem Statement:** PS-11 — AI-Powered Urban Drainage and Flash Flood Predictive Management System  
**Plan Date:** October 31, 2026  
**Auditor:** HYDRO-GUARD AI Technical & Scientific Audit Team  

---

## 1. Executive Overview

This document defines the strict, reproducible experiment protocol for training and benchmarking candidate machine learning architectures on the validated hydrological datasets identified in `TASK_3_0_TRAINING_READINESS.md`.

### Core Scientific Principles
- **No Data Leakage:** Strict chronological train / validation / test partitioning with enforced purge buffers.
- **Physical & Statistical Baselines:** Neural networks must be benchmarked against both non-neural statistical baselines and first-principles hydraulic physics.
- **Appropriate Hydrological Metrics:** Evaluation relies on Nash-Sutcliffe Efficiency (NSE) and Kling-Gupta Efficiency (KGE) for discharge, MAE/RMSE for continuous stages, and Critical Success Index (CSI) for verified events.
- **Strict Isolation:** All training artifacts, checkpoints, and logs are written to isolated directories (`checkpoints/`, `logs/`) without modifying the running application or overwriting existing baseline files (`data/st_gnn_model.npz`).

---

## 2. Experimental Architecture Suite

We evaluate three competitive model families across identical data splits:

```
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    CANDIDATE ARCHITECTURE SUITE                                       |
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
| 1. Model A: ST-GNN / DCRNN (Diffusion Convolutional Recurrent Neural Network)                        |
|    - Spatial: Bi-directional Graph Diffusion Convolution over physical directed adjacency (K=2 hops)  |
|    - Temporal: Spatio-Temporal Gated Recurrent Unit (ST-GRU) with hidden dimension = 64              |
|                                                                                                       |
| 2. Model B: Graph WaveNet                                                                             |
|    - Spatial: Adaptive Adjacency Matrix (learned embeddings) + Physical Directed Adjacency            |
|    - Temporal: Stacked Dilated 1D Causal Inception Convolutions (dilation rates: 1, 2, 4, 8)          |
|                                                                                                       |
| 3. Model C: Non-Neural Baselines                                                                      |
|    - Baseline C.1: Naive Persistence Benchmark (y_{t+H} = x_t)                                        |
|    - Baseline C.2: Multi-Station Ridge Vector Autoregression (L2 Regularized AR-12)                   |
|    - Baseline C.3: 1D First-Principles Manning Hydraulic Routing Model                               |
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 3. Training Experiment Specifications

### Experiment 1: Blue Heart Urban Drainage ST-GNN (PRIMARY EXPERIMENT)
- **Target Domain:** Blue Heart 15-Gully Urban Drainage Network (Eastbourne, UK).
- **Dataset:** `data/processed_global/urban_sequences/blue_heart_sequences_w12_h3.npz`.
- **Target Variable:** Continuous gully water depth $Y_{\text{level}}$ ($m$) at horizon $H = +3\text{h}$ (180 mins).
- **Secondary Target:** Surcharge exceedance $Y_{\text{surcharge}}$ (binary indicator).
- **Sample Distribution:**
  - Total Sequences: $7,282$
  - Training Split ($70\%$): $5,085\text{ sequences}$
  - Validation Split ($15\%$): $1,080\text{ sequences}$
  - Test Split ($15\%$): $1,093\text{ sequences}$
  - Purge Buffer: $12\text{-hour window}$ between train/val and val/test boundaries.

### Experiment 2: Aroostook Fluvial River ST-GNN (COMPLEMENTARY EXPERIMENT)
- **Target Domain:** Aroostook River Basin (4 USGS stations).
- **Dataset:** `data/processed_global/temporal_sequences/aroostook_sequences_w12_h3.npz`.
- **Target Variable:** Continuous discharge $Y_{\text{flow}}$ ($m^3/s$) at horizon $H = +3\text{h}$.
- **Secondary Target:** Estimated inundation depth $Y_{\text{depth}}$ ($m$).
- **Sample Distribution:**
  - Total Sequences: $14,624$
  - Training Split ($70\%$): $10,236\text{ sequences}$
  - Validation Split ($15\%$): $2,193\text{ sequences}$
  - Test Split ($15\%$): $2,187\text{ sequences}$
  - Purge Buffer: $24\text{-hour window}$ between splits.

---

## 4. Evaluation Metrics & Hydrological Acceptance Criteria

Evaluation must use domain-appropriate metrics:

### 1. Continuous Streamflow Metrics (Aroostook River)
- **Nash-Sutcliffe Efficiency (NSE):**
  $$\text{NSE} = 1 - \frac{\sum_{t=1}^T (Q_{\text{obs}}^t - Q_{\text{sim}}^t)^2}{\sum_{t=1}^T (Q_{\text{obs}}^t - \overline{Q_{\text{obs}}})^2}$$
  - *Acceptance Target:* $\text{NSE} \ge 0.75$ (Good), $\text{NSE} \ge 0.85$ (Excellent).
- **Kling-Gupta Efficiency (KGE):**
  $$\text{KGE} = 1 - \sqrt{(r - 1)^2 + (\alpha - 1)^2 + (\beta - 1)^2}$$
  where $r$ is Pearson correlation, $\alpha = \sigma_{\text{sim}} / \sigma_{\text{obs}}$, and $\beta = \mu_{\text{sim}} / \mu_{\text{obs}}$.
  - *Acceptance Target:* $\text{KGE} \ge 0.80$.
- **Relative Peak Flow Error (rPE):**
  $$\text{rPE} = \frac{\max(Q_{\text{sim}}) - \max(Q_{\text{obs}})}{\max(Q_{\text{obs}})} \times 100\%$$
  - *Acceptance Target:* $|\text{rPE}| \le 15.0\%$.

### 2. Continuous Water Stage & Inundation Depth Metrics (Blue Heart Gullies)
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |h_{\text{obs}} - h_{\text{sim}}|$$
  - *Acceptance Target:* $\text{MAE} \le 0.05\ m$ ($5\text{ cm}$).
- **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (h_{\text{obs}} - h_{\text{sim}})^2}$$
  - *Acceptance Target:* $\text{RMSE} \le 0.08\ m$ ($8\text{ cm}$).

### 3. Event Threshold & Surcharge Metrics (Where Valid Events Exist)
- **Critical Success Index (CSI / Threat Score):**
  $$\text{CSI} = \frac{tp}{tp + fp + fn}$$
  - *Acceptance Target:* $\text{CSI} \ge 0.65$.
- **Precision-Recall AUC (PR-AUC):**
  - Preferred over ROC-AUC for imbalanced extreme event distributions.
  - *Acceptance Target:* $\text{PR-AUC} \ge 0.70$.

### 4. Peak Arrival Timing Error
- **Peak Timing Lag Error ($\Delta t_{\text{peak}}$):**
  $$\Delta t_{\text{peak}} = |t_{\text{peak, pred}} - t_{\text{peak, true}}|$$
  - *Acceptance Target:* $|\Delta t_{\text{peak}}| \le 15\text{ minutes}$ for urban gullies, $\le 1.0\text{ hour}$ for rivers.

---

## 5. Hyperparameter Configurations & Reproducibility Matrix

To ensure exact reproducibility across runs, the following standardized hyperparameter grid is locked:

| Hyperparameter | DCRNN / ST-GNN | Graph WaveNet | Multi-Station Ridge |
| :--- | :---: | :---: | :---: |
| **Random Seeds** | `[42, 123, 456]` | `[42, 123, 456]` | `[42]` |
| **Lookback Window ($T$)** | $12\text{ hours}$ | $12\text{ hours}$ | $12\text{ hours}$ |
| **Forecast Horizon ($H$)** | $+3\text{ hours}$ | $+3\text{ hours}$ | $+3\text{ hours}$ |
| **Spatial Graph Hops ($K$)** | $2\text{ hops}$ | Adaptive ($D=10$) + 1 hop | N/A (Full matrix) |
| **Hidden Dimensions** | $64$ | $32\text{ (residual)}, 64\text{ (dilation)}$ | N/A |
| **Temporal Layers** | 2 GRU Layers | 4 Dilated Conv Blocks | 1 Linear Layer |
| **Dilation Rates** | N/A | `[1, 2, 4, 8]` | N/A |
| **Dropout** | $0.20$ | $0.25$ | N/A |
| **L2 Regularization ($\lambda$)** | $1 \times 10^{-4}$ | $1 \times 10^{-4}$ | $\alpha = 1.0$ |
| **Optimizer** | AdamW | AdamW | Closed-form Cholesky |
| **Initial Learning Rate** | $1 \times 10^{-3}$ | $1 \times 10^{-3}$ | N/A |
| **LR Scheduler** | Cosine Annealing ($\eta_{\min}=10^{-5}$) | ReduceLROnPlateau (factor=0.5) | N/A |
| **Batch Size** | $64$ | $64$ | Full Batch ($5,085$) |
| **Maximum Epochs** | $50$ | $50$ | 1 Iteration |
| **Early Stopping** | Patience = 10 epochs on Val Loss | Patience = 10 epochs on Val Loss | N/A |
| **Loss Function** | Masked Huber Loss ($\delta=0.5$) | Masked Huber Loss ($\delta=0.5$) | Squared L2 Loss |

---

## 6. Checkpoint Directory & Artifact Retention Protocol

All training artifacts must be isolated from the production application:

```
E:\ai-manthan\hydro_guard_indore\
├── checkpoints\
│   ├── blue_heart_dcrnn_seed42_best_val_loss.npz
│   ├── blue_heart_graph_wavenet_seed42_best_val_loss.npz
│   ├── blue_heart_ridge_baseline.npz
│   ├── aroostook_dcrnn_seed42_best_val_nse.npz
│   └── training_run_manifest.json
├── logs\
│   ├── training_blue_heart_20261031.log
│   └── training_aroostook_20261031.log
└── results\
    ├── blue_heart_model_comparison_metrics.csv
    ├── aroostook_model_comparison_metrics.csv
    └── hydrograph_evaluations_seed42.png
```

### Safety Rules:
1. `data/st_gnn_model.npz` must **NOT be overwritten** during training experiments.
2. The running FastAPI service (`127.0.0.1:8000`) and Streamlit dashboard (`localhost:8501`) will continue referencing `data/st_gnn_model.npz` until a trained checkpoint has passed all acceptance gates and received user sign-off.
3. Every training run will record git-equivalent hashes, environment specs, random seeds, wall-clock training times, and training loss curves.

---

## 7. Execution Readiness & Authorization Check

```
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                  EXPERIMENT EXECUTION READINESS GATE                                  |
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
|  [CRITERION 1] Data Tensors Audited & Verified?        ---> YES (Blue Heart 7,282, Aroostook 14,624)  |
|  [CRITERION 2] Chronological Leakage Purge Verified?   ---> YES (Zero Temporal Overlap)              |
|  [CRITERION 3] Evaluation Metrics Strictly Matched?    ---> YES (NSE, KGE, MAE, RMSE, CSI)           |
|  [CRITERION 4] Non-Neural Baselines Prepared?          ---> YES (Persistence, Ridge, Manning)        |
|  [CRITERION 5] Isolated Checkpoint Paths Designated?   ---> YES (checkpoints/, logs/, results/)      |
|  [CRITERION 6] Explicit User Training Authorization?   ---> PENDING AUTHORIZATION (HALTED)           |
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
```

**Status:** The experimental plan is complete, reproducible, and ready for immediate launch.  
**Standing Order:** Execution is **HALTED**. We are waiting for explicit user authorization before launching model training.

