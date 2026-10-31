# HYDRO-GUARD AI — Multi-Domain Model Architecture Design & Candidate Evaluation
**Document ID:** `HGAI-DESIGN-MULTI-MODEL-2026-10-31`  
**Location:** `docs/MULTI_DOMAIN_MODEL_DESIGN.md`  
**Problem Statement:** PS-11 — AI-Powered Urban Drainage and Flash Flood Predictive Management System  
**Auditor:** Machine Learning Architecture & Hydroinformatics Research Group  
**Status:** APPROVED ARCHITECTURAL BLUEPRINT  

---

## 1. Executive Summary & Design Philosophy

Flash flooding and urban drainage overflow are governed by two distinct physical domains with disparate spatial and temporal scales:
1. **The Regional River Domain (Fluvial):** Natural watershed channels, drainage areas $> 100\text{ km}^2$, routing delays $6\text{--}48\text{ hours}$, baseflow recessions over weeks.
2. **The Urban Stormwater Domain (Pluvial):** Underground concrete conduits, pipe diameters $0.3\text{--}2.0\text{ m}$, catchments $0.1\text{--}10\text{ km}^2$, routing delays $15\text{--}45\text{ minutes}$, pressurized surcharge and street-level depression ponding.

**Core Scientific Directive:** Under no circumstances should these domains be treated as a single homogeneous graph. Instead, a **Multi-Domain Decoupled Architecture** is designed, integrating domain-specific spatio-temporal neural networks with a hydraulic boundary coupling layer.

---

## 2. Multi-Domain Model Components (Modules A to E)

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                               MULTI-DOMAIN PREDICTIVE ARCHITECTURE                                |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                                                                                   |
|  [FORCING ENCODER] (Component C)                                                                  |
|  ├── Inputs: Precipitation Intensity R(t), Radar Advection Grids, Surface Temperature, Pressure   |
|  └── Architecture: 1D Dilated Causal Convolution + Spatial Feature Pyramid                       |
|                                     │                                                             |
|                   ┌─────────────────┴─────────────────┐                                           |
|                   ▼                                   ▼                                           |
|  [URBAN DRAINAGE ST-GNN] (Component B)    [RIVER HYDROLOGY ST-GNN] (Component A)                  |
|  ├── Graph: Bellinge (1,020 nodes)        ├── Graph: Aroostook (4 nodes) / Potomac (5 nodes)      |
|  │          Blue Heart (15 gullies)       │                                                       |
|  ├── Time Step: Δt = 15 minutes           ├── Time Step: Δt = 1 hour                              |
|  ├── Physics: Pipe Conveyance & Head Loss ├── Physics: Muskingum-Cunge Wave Diffusion             |
|  └── Predictions: Gully/Manhole Level     └── Predictions: River Discharge Q(t+H) & Stage h(t+H)   |
|                   │                                   │                                           |
|                   │         ┌─────────────────────────┘                                           |
|                   ▼         ▼                                                                     |
|  [FORECAST FUSION & TAILWATER COUPLING] (Component E)                                             |
|  ├── Physical Interface: Outfall Boundary Head: h_backwater = max(0, h_river - z_outfall)         |
|  └── Surcharge Propagation: Reverse Diffusion Convolution P_b = D_I^(-1) A^T                      |
|                                     │                                                             |
|                                     ▼                                                             |
|  [HYDRAULIC SIMULATION & REGULARIZATION LAYER] (Component D)                                      |
|  ├── EPA-SWMM 5.2 Dynamic Wave Verification                                                       |
|  └── Physics Loss Penalty: L_phys = λ * max(0, Q_pred - Q_capacity)^2                             |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

### Component A: River ST-GNN (Fluvial Domain)
- **Data Domains:** CAMELS-Hourly ($14,624\text{ sequences}$, 4 nodes) and USGS NWIS (5 nodes).
- **Time Step:** Hourly ($\Delta t = 1\text{ hour}$). Input window $W = 12\text{ hours}$, forecast horizon $H \in \{1, 3, 6\}\text{ hours}$.
- **Objective:** Predict downstream river stage $h_{\text{river}}(t+H)$ and discharge $Q_{\text{river}}(t+H)$.

### Component B: Urban Drainage ST-GNN (Pluvial Domain)
- **Data Domains:** Bellinge ($1,020\text{ nodes}$, $1,037\text{ edges}$) and Blue Heart ($15\text{ road gullies}$, $7,282\text{ sequences}$).
- **Time Step:** Sub-hourly to hourly ($\Delta t = 15\text{ min to }1\text{ h}$).
- **Objective:** Predict underground sewer head, gully sump depth, and surface surcharge probability.

### Component C: Meteorological / Radar Encoder
- **Architecture:** 1D Dilated Causal Convolutional Network (TCN).
- **Function:** Encodes raw precipitation time series and spatial radar grids into dense temporal embeddings $\mathbf{e}_{\text{rain}} \in \mathbb{R}^{d}$, capturing antecedent moisture, peak storm pulses, and hyetograph shape.

### Component D: Hydraulic Physics Component
- **Tooling:** EPA-SWMM 5.2 engine via PySWMM.
- **Role:** Evaluates full dynamic wave equations on extreme return periods. During ST-GNN inference, computes Manning's capacity constraint:
  $$Q_{\text{capacity}} = (1 - \beta) \cdot \frac{1}{n} A R^{2/3} S^{1/2}$$
  Penalizes unphysical neural predictions via regularized loss $\mathcal{L}_{\text{phys}}$.

### Component E: Forecast Fusion & Boundary Coupling Layer
- **Physical Boundary Law:** When river water level $h_{\text{river}}(t)$ rises above the sewer outfall crown $z_{\text{outfall}}$, gravity outflow is choked, creating upstream backwater surcharge:
  $$Q_{\text{outfall}} = C_d A \sqrt{2 g \max(0, h_{\text{sewer}} - h_{\text{river}})}$$
- The fusion layer connects Component A's river stage prediction to Component B's outfall node boundary, activating backward graph diffusion ($P_b = D_I^{-1} A^T$) to forecast upstream manhole popping hours in advance.

---

## 3. Comparison of Candidate Spatio-Temporal Architectures

To ensure scientific rigor, three advanced graph neural architectures are evaluated as candidate solutions:

| Dimension / Criteria | Candidate 1: DCRNN (Baseline) | Candidate 2: Graph WaveNet | Candidate 3: Temporal GAT (TGAT) | Physics Baseline: EPA-SWMM |
| :--- | :--- | :--- | :--- | :--- |
| **Spatial Operation** | Bidirectional Random Walk Graph Convolution ($P_f, P_b$) | Diffusion Conv + Self-Adaptive Adjacency Matrix | Multi-Head Graph Attention over spatial neighbors | Full 1D Saint-Venant Momentum & Continuity Equations |
| **Temporal Operation** | Gated Recurrent Unit (DCGRU) | Dilated Causal Temporal Convolutions (TCN) | Self-Attention across temporal history | Finite-difference numerical integration |
| **Directed DAG Handling** | **Superior** (Forward routing vs backward surcharge explicit) | **Good** (Combines fixed DAG with learned adaptive matrix) | Moderate (Attention weights may learn unphysical reverse flow) | **Exact Physical Truth** |
| **Computational Speed** | Fast ($\approx 4\text{ ms / batch}$) | **Ultra-Fast** ($\approx 1.2\text{ ms / batch}$, non-recurrent) | Slower ($\approx 8\text{ ms / batch}$) | Moderate ($\approx 1\text{--}5\text{ sec / run}$) |
| **Memory Footprint** | Moderate (BPTT through 12 steps) | **Low** (Parallel feedforward convolutions) | High (Quadratic attention memory) | Low (CPU RAM only) |
| **Suitability for PS-11** | **Strong Primary Candidate** | **Strong Alternative Candidate** | Exploratory Candidate | **Mandatory Ground-Truth Baseline** |

### Evaluation Protocol
In Task 3, **Candidate 1 (DCRNN)** and **Candidate 2 (Graph WaveNet)** will be trained under identical seeds, datasets, and loss functions. The model demonstrating superior Precision-Recall AUC (PR-AUC) and Nash-Sutcliffe Efficiency (NSE) on the held-out test sets will be selected as the production model.

---

## 4. Multi-Domain Loss Formulation

The joint training objective combines multi-horizon accuracy, class imbalance mitigation, and physical mass conservation:
$$\mathcal{L} = \mathcal{L}_{\text{Huber}}(y_{\text{stage}}, \hat{y}_{\text{stage}}) + \lambda_{\text{cls}} \mathcal{L}_{\text{Focal}}(y_{\text{surcharge}}, \hat{y}_{\text{surcharge}}) + \lambda_{\text{phys}} \mathcal{L}_{\text{physics}}$$

- **Focal Loss ($\gamma = 2.0, \alpha = 0.75$):** Prevents the model from degenerating to majority non-flood predictions on severely imbalanced urban surcharge events ($< 3\%$ positive rate).
- **Physics Loss ($\lambda_{\text{phys}} = 0.10$):**
  $$\mathcal{L}_{\text{physics}} = \frac{1}{|E|} \sum_{(u, v) \in E} \max\left(0, \hat{Q}_{uv} - Q_{\text{capacity}, uv}\right)^2$$

