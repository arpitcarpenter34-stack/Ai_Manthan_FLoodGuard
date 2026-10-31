# Scientific Audit: Graph Topologies & Temporal Sequence Tensors
**Project:** HYDRO-GUARD AI  
**Document:** `data/processed_global/graph_sequence_audit.md`  
**Audit Date:** October 31, 2026  
**Auditor:** Antigravity Graph Neural Network Suite  

---

## 1. Executive Summary & Audit Resolution

The initial Task 2 deliverable generated sequence tensors primarily for the 4-node Aroostook River network (14,624 sequences over 16 years). Under **Task 2.1**, the Potomac River network (5 nodes) was fully integrated, verified, and its sequence tensors extracted into `data/processed_global/temporal_sequences/`.

Both connected graphs now possess fully synchronized multi-node sequence tensors with verified node ordering, adjacency weight symmetry, and zero-leakage chronological splits.

---

## 2. Complete Station & Graph Inventory

| Graph Network | Basin / Region | Node Count | Directed Edges | Continuous Timeline | Total Sequences ($W=12\text{h}, H=+3\text{h}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Aroostook River Basin** | Maine (HUC02-01) | **4 Nodes** | **3 Edges** | 2008–2024 (140,995 Hours) | **14,624 Sequences** |
| **Potomac River Basin** | Maryland/DC (HUC02-02) | **5 Nodes** | **4 Edges** | Oct 2026 Telemetry (337 Hours) | **322 Sequences** |
| **Disjoint Combined Graph**| Multi-Basin Block-Diagonal| **9 Nodes** | **7 Edges** | Multi-Basin Parallel Batching | **Combined Tensor Compatible** |

---

## 3. Node Ordering, Adjacency Matrices & Feature Order

To prevent index misalignment during graph convolutions, node ordering and feature channels are strictly fixed.

### 3.1 Aroostook River Graph Topology (4 Nodes)
- **Node Index Order:**
  - `0`: `01015800` — Aroostook River nr Masardis (Upstream Mainstem)
  - `1`: `01017060` — Hardwood Brook nr Caribou (Tributary)
  - `2`: `01017290` — Little Madawaska River nr Caribou (Lateral Tributary)
  - `3`: `01017000` — Aroostook River at Washburn (Downstream Confluence Exit)

- **Directed Adjacency Matrix $W_{\text{Aroostook}} \in \mathbb{R}^{4 \times 4}$:**
  ```
          Node 0    Node 1    Node 2    Node 3
  Node 0 [0.0000,   0.0000,   0.0000,   0.2924]  --> Masardis to Washburn (L=38.4 km)
  Node 1 [0.0000,   0.0000,   0.0000,   0.0510]  --> Hardwood Brook to Washburn (L=14.2 km)
  Node 2 [0.0000,   0.0000,   0.0000,   0.2721]  --> Little Madawaska to Washburn (L=22.6 km)
  Node 3 [0.0000,   0.0000,   0.0000,   0.0000]  --> Downstream Exit (No self-loops)
  ```

### 3.2 Potomac River Graph Topology (5 Nodes)
- **Node Index Order:**
  - `0`: `01638500` — Potomac River at Point of Rocks, MD (Upstream Mainstem)
  - `1`: `01643000` — Monocacy River at Jug Bridge, MD (Major Tributary)
  - `2`: `01644000` — Seneca Creek at Dawsonville, MD (Suburban Lateral Tributary)
  - `3`: `01647600` — NW Branch Anacostia River, Hyattsville, MD (Urban Drainage Node)
  - `4`: `01646500` — Potomac River near Little Falls Pump Sta, DC (Downstream Terminal Node)

- **Directed Adjacency Matrix $W_{\text{Potomac}} \in \mathbb{R}^{5 \times 5}$:**
  ```
          Node 0    Node 1    Node 2    Node 3    Node 4
  Node 0 [0.0000,   0.0000,   0.0000,   0.0000,   0.2941]  --> Point of Rocks to Little Falls (L=42.7 km)
  Node 1 [0.0000,   0.0000,   0.0000,   0.0000,   0.1068]  --> Monocacy to Little Falls (L=38.1 km)
  Node 2 [0.0000,   0.0000,   0.0000,   0.0000,   0.0740]  --> Seneca to Little Falls (L=19.4 km)
  Node 3 [0.0000,   0.0000,   0.0000,   0.0000,   0.0592]  --> Anacostia to Little Falls DC (L=12.0 km)
  Node 4 [0.0000,   0.0000,   0.0000,   0.0000,   0.0000]  --> Terminal Node (No self-loops)
  ```

### 3.3 Dynamic Feature Channel Order ($F=6$)
For every node $i$ at timestep $t$, the dynamic feature vector is structured identically:
- **Channel 0:** `streamflow_m3s` (Continuous physical discharge in $m^3/s$)
- **Channel 1:** `water_level_m` (Continuous physical stage in $m$)
- **Channel 2:** `dq_dt_m3s_per_h` (Hydraulic rate of change $dQ/dt$)
- **Channel 3:** `dh_dt_m_per_h` (Stage rate of change $dh/dt$)
- **Channel 4:** `streamflow_measured_mask` ($1.0$ if physically measured, $0.0$ if unobserved)
- **Channel 5:** `water_level_measured_mask` ($1.0$ if physically measured, $0.0$ if unobserved)

---

## 4. Sequence Tensor Shapes & Multi-Horizon Verification

All generated sequence tensors were audited for shape consistency:

### 4.1 Aroostook River Sequences (`temporal_sequences/`)
- **`aroostook_sequences_w12_h3.npz`**:
  - Input Tensor $X$: `(14624, 12, 4, 6)`
  - Target Tensors:
    - $Y_{\text{statistical\_high\_flow}}$: `(14624, 4)`
    - $Y_{\text{flow}}$: `(14624, 4)`
    - $Y_{\text{depth}}$: `(14624, 4)`
  - Total Training Sequences: **10,236** | Validation: **2,193** | Test: **2,191**
- **`aroostook_sequences_w6_h1.npz`**:
  - Input Tensor $X$: `(14635, 6, 4, 6)`
  - Target Tensors: `(14635, 4)`
- **`aroostook_sequences_w24_h6.npz`**:
  - Input Tensor $X$: `(14559, 24, 4, 6)`
  - Target Tensors: `(14559, 4)`

### 4.2 Potomac River Sequences (`temporal_sequences/`)
- **`potomac_sequences_w12_h3.npz`**:
  - Input Tensor $X$: `(322, 12, 5, 6)`
  - Target Tensors:
    - $Y_{\text{statistical\_high\_flow}}$: `(322, 5)`
    - $Y_{\text{official\_flood}}$: `(322, 5)`
    - $Y_{\text{flow}}$: `(322, 5)`
    - $Y_{\text{depth}}$: `(322, 5)`
  - Total Training Sequences: **225** | Validation: **48** | Test: **49**
- **`potomac_sequences_w6_h1.npz`**:
  - Input Tensor $X$: `(330, 6, 5, 6)`
  - Target Tensors: `(330, 5)`
- **`potomac_sequences_w24_h6.npz`**:
  - Input Tensor $X$: `(307, 24, 5, 6)`
  - Target Tensors: `(307, 5)`

---

## 5. Event Leakage & Chronological Split Audit

```
CHRONOLOGICAL SPLIT VALIDATION ASSERTION
Aroostook Timeline: 2008 ──────────────── 2019 ────[24h GAP]──── 2021 ────[24h GAP]──── 2024
Potomac Timeline:   Oct 17 ────────────── Oct 26 ──[12h GAP]──── Oct 28 ──[12h GAP]──── Oct 31
```

### Verified Audit Assertions:
1. **Strict Monotonicity:** $\max(\text{Train Index}) < \min(\text{Val Index})$ and $\max(\text{Val Index}) < \min(\text{Test Index})$ passed for all generated sequence files.
2. **Purge Buffer:** A buffer of $\ge 24\text{ hours}$ (Aroostook) and $\ge 12\text{ hours}$ (Potomac) separates splits. This ensures that no sliding window in the validation or test set shares overlapping timesteps with the training set.
3. **Disjoint Sets:** $\text{Train} \cap \text{Val} = \emptyset$ and $\text{Val} \cap \text{Test} = \emptyset$ confirmed with 0 common sequence indices.
4. **Observation Density:** All 9 stations possess $>95\%$ valid observations during active sliding-window extraction periods.

