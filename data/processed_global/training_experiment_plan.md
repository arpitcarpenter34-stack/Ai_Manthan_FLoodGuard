# HYDRO-GUARD AI — ST-GNN Training Experiment Plan & Protocol
**Document ID:** `HGAI-EXP-PLAN-2026-10-31`  
**Location:** `data/processed_global/training_experiment_plan.md`  
**Auditor:** HYDRO-GUARD AI Machine Learning Research Team  
**Status:** READY FOR AUTHORIZATION (Task 3 Execution Blueprint)  

---

## 1. Experimental Overview & Objectives

This document establishes the rigorous, reproducible training protocol for the upgraded **Hybrid Spatio-Temporal Graph Neural Network (ST-GNN / DCRNN) + Hydraulic Physics Engine** of HYDRO-GUARD AI.

The experiments are designed to transition the model from initial synthetic baseline demonstrations to scientifically validated real-world performance using the curated, quality-audited CAMELS-Hourly, USGS NWIS, NOAA Storm Events, and ERA5 datasets.

```
+---------------------------------------------------------------------------------------------------+
|                                 FOUR-TIER EXPERIMENT PROTOCOL                                     |
+---------------------------------------------------------------------------------------------------+
|  [EXP 1: Synthetic Baseline]       ---> Control benchmark (Indore 14-node synthetic series)       |
|  [EXP 2: Aroostook Decadal]        ---> Long-term hydrological foundation (14,624 real sequences) |
|  [EXP 3: Potomac Operational]      ---> Urban storm & flash-flood adaptation (322 real sequences) |
|  [EXP 4: Joint / Transfer GNN]     ---> Domain-balanced multi-graph foundation + transfer model    |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Dataset & Tensor Specifications

All input and target tensors have been generated, audited, and stored in `data/processed_global/temporal_sequences/`:

| Experiment | Input Tensor File | Train Shape $(N, W, V, F)$ | Val Shape $(N, W, V, F)$ | Test Shape $(N, W, V, F)$ | Target Tensors |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP 1: Baseline** | Synthetic Indore Cache | $(280, 12, 14, 5)$ | $(60, 12, 14, 5)$ | $(60, 12, 14, 5)$ | Flood risk $[0, 1]$ |
| **EXP 2: Aroostook** | `aroostook_sequences_w12_h3.npz` | $(10236, 12, 4, 6)$ | $(2193, 12, 4, 6)$ | $(2187, 12, 4, 6)$ | $Y_{\text{high\_flow}}$, $Y_{\text{discharge}}$, $Y_{\text{depth}}$ |
| **EXP 3: Potomac** | `potomac_sequences_w12_h3.npz` | $(225, 12, 5, 6)$ | $(48, 12, 5, 6)$ | $(25, 12, 5, 6)$ | $Y_{\text{high\_flow}}$, $Y_{\text{discharge}}$, $Y_{\text{depth}}$ |
| **EXP 4: Multi-Graph** | Disjoint Block-Diagonal | $(10461, 12, 9, 6)$ | $(2241, 12, 9, 6)$ | $(2212, 12, 9, 6)$ | Disjoint node targets ($9\text{ nodes}$) |

### 2.1 Feature Channels ($F=6$)
1. `precipitation_mm_per_h`: Hourly precipitation ($mm/h$, ERA5 reanalysis).
2. `discharge_m3_per_s`: River discharge ($m^3/s$, CAMELS / USGS continuous gauge).
3. `water_level_stage_m`: Water level / stage height ($m$, USGS gauge / rating curve).
4. `temperature_celsius`: Surface air temperature ($^\circ C$, ERA5 reanalysis).
5. `surface_pressure_hpa`: Atmospheric surface pressure ($hPa$, ERA5 reanalysis).
6. `drainage_capacity_utilization`: Dimensionless ratio $\min(1.5, Q_{\text{observed}} / Q_{\text{bankfull}}})$.

---

## 3. Model Architecture Specifications

- **Backbone:** Diffusion Convolutional Recurrent Neural Network (DCRNN)
- **Diffusion Steps ($K$):** $K = 2$ (captures upstream inflow and downstream backwater influence within 2 hops).
- **Hidden Dimensions:** $64$ units per DCGRU cell.
- **Recurrent Layers:** $2$ stacked bidirectional DCGRU layers.
- **Dropout:** $0.20$ applied between recurrent layers to prevent co-adaptation.
- **Output Heads:**
  1. **Continuous Regression Head:** 2-layer MLP with LayerNorm predicting future discharge ($m^3/s$) and water stage ($m$) at horizon $T+H$.
  2. **Flood Risk Classification Head:** 2-layer MLP with Sigmoid/Softmax predicting:
     - Binary Statistical High-Flow ($Q \ge Q_{99}$)
     - Multi-Class Stage Exceedance (Normal, Action, Minor Flood, Major Flood)

---

## 4. Loss Functions & Optimization Strategy

### 4.1 Hybrid Objective Function
The loss function combines empirical prediction accuracy with hydraulic physical consistency:
$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{reg}} + \lambda_{\text{cls}} \mathcal{L}_{\text{cls}} + \lambda_{\text{phys}} \mathcal{L}_{\text{phys}}$$

1. **Regression Loss ($\mathcal{L}_{\text{reg}}$):** Smooth L1 (Huber) Loss on normalized water levels and streamflow to protect against extreme storm outliers:
   $$\mathcal{L}_{\text{reg}} = \frac{1}{|V|} \sum_{v \in V} \text{SmoothL1}(y_{v, T+H}, \hat{y}_{v, T+H})$$

2. **Classification Loss ($\mathcal{L}_{\text{cls}}$) — Severe Class Imbalance Handling:**
   Because flood and statistical high-flow events represent only $1.0\%\text{--}3.5\%$ of observed hours, standard Cross-Entropy collapses to predicting all zeros.
   - **Method A: Focal Loss:**
     $$\mathcal{L}_{\text{focal}} = -\alpha_t (1 - p_t)^\gamma \log(p_t), \quad \gamma = 2.0, \quad \alpha = 0.75$$
   - **Method B: Weighted BCE (`pos_weight`):**
     $$\text{pos\_weight} = \frac{N_{\text{negatives}}}{N_{\text{positives}}} \approx \frac{98}{2} = 49.0$$

3. **Physics Conservation Loss ($\mathcal{L}_{\text{phys}}$):**
   Penalizes downstream predictions that violate mass conservation or exceed pipe/channel hydraulic capacity without surcharge:
   $$\mathcal{L}_{\text{phys}} = \sum_{(u, v) \in E} \max\left(0, \hat{Q}_v - (\hat{Q}_u + Q_{\text{lateral, max}})\right)^2$$

### 4.2 Training Hyperparameters
- **Optimizer:** `AdamW` ($\beta_1 = 0.9, \beta_2 = 0.999, \epsilon = 10^{-8}$)
- **Weight Decay:** $1 \times 10^{-4}$
- **Initial Learning Rate:** $1 \times 10^{-3}$
- **LR Scheduler:** CosineAnnealingLR ($T_{\text{max}} = 50$, $\eta_{\text{min}} = 1 \times 10^{-5}$)
- **Batch Size:**
  - Aroostook (EXP 2): $64$ sequences/batch
  - Potomac (EXP 3): $16$ sequences/batch
  - Joint Multi-Graph (EXP 4): Balanced $32$ Aroostook $+ 32$ Potomac
- **Max Epochs:** $100$ epochs
- **Early Stopping:** Patience $= 15$ epochs monitored on Validation PR-AUC.

---

## 5. Evaluation Metrics & Success Criteria

### 5.1 Hydrological Regression Metrics
1. **Nash-Sutcliffe Efficiency (NSE):**
   $$\text{NSE} = 1 - \frac{\sum_{t} (Q_{\text{obs}}^t - Q_{\text{sim}}^t)^2}{\sum_t (Q_{\text{obs}}^t - \overline{Q_{\text{obs}}})^2} \quad (\text{Target: } \text{NSE} \ge 0.75)$$
2. **Kling-Gupta Efficiency (KGE):** Evaluates correlation, bias, and variability simultaneously ($\text{Target: } \text{KGE} \ge 0.80$).
3. **Peak Flow Timing Error ($\Delta T_{\text{peak}}$):** Difference between observed and predicted hydrograph peak ($\text{Target: } |\Delta T| \le 1.0\text{ hour}$).

### 5.2 Flood Event Classification Metrics
Because accuracy is misleading on $98\%$ majority negative data, performance must be judged on:
1. **Precision-Recall AUC (PR-AUC):** Minimum target $\ge 0.70$.
2. **Critical Success Index (CSI / Threat Score):**
   $$\text{CSI} = \frac{\text{Hits}}{\text{Hits} + \text{Misses} + \text{False Alarms}} \quad (\text{Target: } \ge 0.60)$$
3. **False Alarm Ratio (FAR):**
   $$\text{FAR} = \frac{\text{False Alarms}}{\text{Hits} + \text{False Alarms}} \quad (\text{Target: } \le 0.25)$$

---

## 6. Reproducibility & Seed Protocols

To ensure strict scientific reproducibility across operating systems and GPU hardware:
1. **Deterministic Seeds:**
   - Primary Seed: `42`
   - Multi-run Variance Seeds: `101`, `2024`
2. **Environment Pinning:**
   - PyTorch: `2.x`
   - Python: `3.13.x`
   - `torch.use_deterministic_algorithms(True)`
   - `torch.backends.cudnn.deterministic = True`
3. **Artifact Logging:**
   - Model weights saved to `data/models/st_gnn_real_aroostook.pt`
   - Training curves and loss histories saved to `data/processed_global/training_logs_exp*.json`

---

## 7. Execution Gate Requirement
> **CRITICAL DIRECTIVE:** Model training and weight modification remain **HALTED** until the user explicitly issues the execution command for Task 3.

