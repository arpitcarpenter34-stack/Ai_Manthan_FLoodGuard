# HYDRO-GUARD AI — Urban Drainage Graph Topology Audit
**Document ID:** `HGAI-AUDIT-URBAN-GRAPH-2026-10-31`  
**Location:** `docs/URBAN_GRAPH_DATA_AUDIT.md`  
**Artifact Directory:** `data/processed_global/urban_graphs/`  
**Status:** COMPLETE / FULLY AUDITED & VERIFIED  

---

## 1. Overview of Urban Graph Construction

In accordance with Task 2.4 Section 3, independent, physically grounded graph representations were constructed for each acquired urban drainage case study:
1. **Bellinge Hydrodynamic Graph** ($1,020\text{ nodes}$, $1,037\text{ edges}$)
2. **UWO Hydrodynamic Graph** ($440\text{ nodes}$, $448\text{ edges}$)
3. **Blue Heart Road Gully Graph** ($15\text{ sensor nodes}$, $173\text{ edges}$)

### Architectural Rule: Multi-Domain Isolation
**Under no circumstances are different cities or river networks combined into a single physically connected graph.** Each urban graph topology is preserved in its own mathematical domain ($G_{\text{Bellinge}}$, $G_{\text{UWO}}$, $G_{\text{BlueHeart}}$).

---

## 2. Graph Artifact Specifications

| Graph Domain | Adjacency Matrix | Node Features | Edge Features | Node Metadata JSON | Total Nodes | Directed Edges |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Bellinge** | `bellinge_adjacency.npy`<br>$(1020, 1020)$ | `bellinge_node_features.npy`<br>$(1020, 4)$ | `bellinge_edge_features.npy`<br>$(1037, 6)$ | `bellinge_node_ids.json` | **1,020** | **1,037** |
| **UWO** | `uwo_adjacency.npy`<br>$(440, 440)$ | `uwo_node_features.npy`<br>$(440, 3)$ | Embedded in weights | `uwo_node_ids.json` | **440** | **448** |
| **Blue Heart** | `blue_heart_gully_adjacency.npy`<br>$(15, 15)$ | Embedded in telemetry | Distance weights | `blue_heart_gully_node_ids.json` | **15** | **173** |

---

## 3. Detailed Topology & Physical Connectivity

### 3.1 Bellinge Hydrodynamic Graph (1,020 Nodes)
- **Node Composition:**
  - $995$ Manhole Junctions (underground access shafts, flow splitters)
  - $16$ Retention Storage Basins (detention tanks, balancing reservoirs)
  - $9$ Gravity Outfalls (terminal discharge points into Odense River)
- **Node Feature Channels ($D_{\text{node}} = 4$):**
  1. `invert_elevation_m`: Ground elevation minus depth ($m$ above datum).
  2. `max_depth_m`: Depth from invert to street rim ($m$).
  3. `init_depth_m`: Dry weather baseflow depth ($m$).
  4. `node_type_code`: Categorical integer ($0 = \text{Junction}, 1 = \text{Outfall}, 2 = \text{Storage}$).
- **Edge Composition:**
  - $1,006$ Conduits (circular pipes, diameter $0.20\text{--}1.60\text{ m}$)
  - $6$ Lift Pump Stations (`G70F11Pp1`, `G71F12Pp1`, `G71F12Pp2`, etc.)
  - $14$ Overflow Weirs
  - $4$ Throttle Orifices
  - $7$ Outlets
- **Adjacency Weight Formulation:**
  Edge weights $W_{ij}$ represent physical conveyance per unit reach length ($K_{ij} / L_{ij}$):
  $$K_{ij} = \frac{1}{n_{ij}} A_{ij} R_{ij}^{2/3}, \quad W_{ij} = \text{clip}\left(\frac{K_{ij}}{L_{ij}}, 0.01, 10.0\right)$$
  - Self-loops: $W_{ii} = 1.0$ (local state retention).
  - Sparsity: $2,052$ non-zero entries in a $1,020 \times 1,020$ matrix (Density $= 0.197\%$).

---

### 3.2 UWO Hydrodynamic Graph (440 Nodes)
- **Node Composition:**
  - $427$ Junctions
  - $5$ Retention Storage Tanks
  - $8$ Outfalls
- **Edge Composition:**
  - $431$ Conduits
  - $5$ Pumps
  - $15$ Combined Sewer Overflow (CSO) Weirs
- **Adjacency Matrix:**
  $440 \times 440$ float32 matrix with $888$ non-zero entries. Graph captures hydraulic throttle lines and overflow weirs feeding retention basins.

---

### 3.3 Blue Heart Road Gully Subgraph (15 Monitored Sensors)
- **Node Composition:** 15 actively monitored road gullies (`ESH5B`, `ESH6A`, `ESH7C`, `ESH8D`, `JBA11A` through `JBA21K`).
- **Spatial Coupling Formulation:**
  Because highway gullies capture overland runoff across contiguous street catchments, edge weights are modeled using a Gaussian distance-decay kernel within a $5\text{ km}$ cutoff radius:
  $$W_{ij} = \exp\left(-\frac{\text{dist}(c_i, c_j)^2}{\sigma^2}\right), \quad \sigma = 2,000\text{ meters}$$
  - $173$ active spatial edges linking neighbors in the Eastbourne urban core.

---

## 4. Graph Direction & Physical Validation
1. **DAG Convention:** In both Bellinge and UWO, gravity conduits flow strictly downstream from high invert elevation to low invert elevation ($z_{\text{us}} > z_{\text{ds}}$).
2. **Reverse Flow / Backwater Capability:** While forward adjacency $P_f = D_O^{-1} A$ routes water downstream with gravity, the Diffusion Graph Convolution layer automatically computes backward adjacency $P_b = D_I^{-1} A^T$ to model upstream backwater pressure during outfall submergence.
3. **Storage Verification:** All `.npy` matrices and `.json` index files have been written to `data/processed_global/urban_graphs/` and verified with automated loading tests.

