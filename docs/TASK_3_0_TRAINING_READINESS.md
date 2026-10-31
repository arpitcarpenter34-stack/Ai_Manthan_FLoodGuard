# HYDRO-GUARD AI — TASK 3.0: TRAINING DATA AUDIT & DOMAIN READINESS REPORT

**Document ID:** `HGAI-AUD-DATA-READINESS-3.0-2026-10-31`  
**Project:** HYDRO-GUARD AI  
**Problem Statement:** PS-11 — AI-Powered Urban Drainage and Flash Flood Predictive Management System  
**Audit Date:** October 31, 2026  
**Auditor:** HYDRO-GUARD AI Technical & Scientific Audit Team  

---

## 1. Executive Summary

This document establishes the empirical data audit and domain-by-domain training readiness decisions for transitioning HYDRO-GUARD AI from simulation baselines to authentic machine learning model training.

### Summary Readiness Decisions

```
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                  DOMAIN READINESS DECISION SUMMARY                                    |
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
| 1. Aroostook River ST-GNN       ---> READY FOR CONTINUOUS STREAMFLOW REGRESSION (NSE/KGE)            |
|                                      NOT READY FOR OFFICIAL FLOOD CLASSIFICATION (Q99 != FEMA FLOOD)  |
| 2. Potomac River ST-GNN         ---> NOT READY FOR INDEPENDENT TRAINING (SAMPLE SIZE INSUFFICIENT: 322)|
| 3. Blue Heart Urban ST-GNN      ---> READY FOR CONTINUOUS WATER STAGE FORECASTING (MAE/RMSE/NSE)     |
| 4. Bellinge Urban Drainage      ---> NOT READY FOR NEURAL TRAINING (Sensor Zip 390MB Unextracted)    |
|                                      100% READY FOR EPA-SWMM 5.2 HYDRODYNAMIC DIGITAL TWIN           |
| 5. Urban Water Observatory (UWO)---> NOT READY FOR TRAINING (Observational Time Series Not Present)  |
| 6. Multi-Domain Fusion          ---> NOT READY (Premature prior to single-domain model verification)  |
+───────────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Comprehensive Domain-by-Domain Data Audit

---

### Domain 1: Aroostook River Basin (CAMELS-Hourly & USGS NWIS)

- **Source Files:**
  - Sequence File: `data/processed_global/temporal_sequences/aroostook_sequences_w12_h3.npz`
  - Metadata: `data/processed_global/temporal_sequences/aroostook_sequences_w12_h3_meta.json`
  - Graph Topology: `data/processed_global/graph_data/aroostook_adjacency.npy` ($4 \times 4$)
- **Usable Samples:** **$14,624\text{ continuous sequences}$** (Window = 12h, Horizon = 3h, Stride = 6h).
- **Network Dimensions:** $N = 4\text{ USGS monitoring stations}$ in Maine:
  - Station `01015800` (Aroostook River near Masardis)
  - Station `01017000` (Aroostook River at Caribou)
  - Station `01017060` (Aroostook River at Fort Fairfield)
  - Station `01017290` (Aroostook River at Washburn)
- **Tensors & Shapes:**
  - Input $X$: `(14624, 12, 4, 6)` ($14,624$ samples $\times 12$ lookback hours $\times 4$ stations $\times 6$ features)
  - Target `Y_flow`: `(14624, 4)` ($t+3\text{h}$ future streamflow in $m^3/s$)
  - Target `Y_depth`: `(14624, 4)` ($t+3\text{h}$ future depth above bankfull in $m$)
  - Target `Y_statistical_high_flow`: `(14624, 4)` (Binary $Q_{99}$ statistical high-flow threshold)
  - Target `Y_flood`: `(14624, 4)` (Alias of statistical high-flow)
- **Feature Definitions & Units:**
  1. `streamflow_m3s` ($m^3/s$): Real observed USGS streamflow. Range: $[0.0, 1177.98]$, Mean: $40.17\ m^3/s$.
  2. `water_level_m` ($m$): USGS stream stage height.
  3. `dq_dt_m3s_per_h` ($m^3/s/h$): First-order rate of discharge change.
  4. `dh_dt_m_per_h` ($m/h$): First-order rate of stage change.
  5. `streamflow_measured_mask` ($\{0, 1\}$): Gauge measurement validity mask ($1=$ observed, $0=$ interpolated).
  6. `water_level_measured_mask` ($\{0, 1\}$): Stage measurement validity mask.
- **Label Integrity & Scientific Distinction:**
  - `Y_flow`: Ground truth physical measurement from USGS discharge sensors.
  - `Y_statistical_high_flow`: Exactly $656$ positive instances ($1.12\%$ prevalence). This represents the empirical $99^{\text{th}}$ percentile ($Q_{99}$) flow rate.
  - **CRITICAL AUDIT NOTE:** Zero NOAA Storm Events were geographically matched to Aroostook coordinates. `Y_flood` is an exact duplicate of `Y_statistical_high_flow`. **It must be treated strictly as statistical high-flow anomaly detection, NOT officially verified FEMA flood stage.**
- **Missingness & Quality:**
  - $0\text{ NaNs}$ in tensor $X$.
  - Real USGS gauge gaps are preserved via binary masks (features 4 & 5).
- **Data Splitting & Leakage Controls:**
  - Chronological Partition:
    - Train ($70\%$): $10,236\text{ sequences}$ (Dec 2008 – ~July 2018)
    - Validation ($15\%$): $2,193\text{ sequences}$ (~July 2018 – ~March 2021)
    - Test ($15\%$): $2,187\text{ sequences}$ (~March 2021 – Dec 2024)
  - Leakage Protection: Strict temporal partition with $24\text{-hour}$ purge buffer between splits. Zero temporal overlap ($\text{Train} \cap \text{Val} = \emptyset$).
- **Supervised Training Verdict:** **APPROVED FOR STREAMFLOW REGRESSION ($Y_{\text{flow}}$)** using NSE, KGE, and RMSE. **UNSUITABLE for binary flood disaster classification** due to lack of verified external flood hazard labels.

---

### Domain 2: Potomac River Basin (USGS NWIS)

- **Source Files:**
  - Sequence File: `data/processed_global/temporal_sequences/potomac_sequences_w12_h3.npz`
  - Metadata: `data/processed_global/temporal_sequences/potomac_sequences_w12_h3_meta.json`
- **Usable Samples:** **Only $322\text{ sequences}$** (Window = 12h, Horizon = 3h, Stride = 1h).
- **Network Dimensions:** $N = 5\text{ USGS monitoring stations}$ in Maryland/Virginia:
  - Station `01638500` (Potomac River at Point of Rocks)
  - Station `01643000` (Potomac River near Washington DC)
  - Station `01644000` (North Branch Potomac River)
  - Station `01646500` (Potomac River at Little Falls)
  - Station `01647600` (Potomac River at Chain Bridge)
- **Tensors & Shapes:**
  - Input $X$: `(322, 12, 5, 6)`
  - Target `Y_flow`: `(322, 5)` (Range: $[0.0, 217.85]\ m^3/s$, Mean: $41.79\ m^3/s$)
  - Target `Y_statistical_high_flow`: `(322, 5)` (Only $4\text{ positive instances} = 0.25\%$)
  - Target `Y_official_flood`: `(322, 5)` (**$0\text{ positive instances} = 0.0\%$**)
  - Target `Y_flood`: `(322, 5)` ($4\text{ positive instances}$)
- **Why Are There Only 322 Sequences?**
  - Continuous sliding sequences require simultaneous, gap-free observations across ALL 5 stations. The simultaneous overlap period among all 5 USGS stations without telemetry dropouts spanned only ~337 consecutive hours.
- **Data Splitting:**
  - Train ($70\%$): $225\text{ sequences}$
  - Val ($15\%$): $48\text{ sequences}$
  - Test ($15\%$): **$25\text{ sequences}$**
- **Supervised Training Verdict:** **REJECTED / NOT READY FOR TRAINING**. 25 test samples is statistically invalid for evaluating a 5-node spatio-temporal graph neural network. Potomac cannot support independent model training without introducing serious overfitting.

---

### Domain 3: Blue Heart Urban Gully Network (Eastbourne, UK)

- **Source Files:**
  - Sequence File: `data/processed_global/urban_sequences/blue_heart_sequences_w12_h3.npz`
  - Graph Topology: `data/processed_global/urban_graphs/blue_heart_gully_adjacency.npy` ($15 \times 15$)
  - Metadata: `data/processed_global/urban_graphs/blue_heart_gully_node_ids.json`
- **Usable Samples:** **$7,282\text{ continuous sequences}$** (Window = 12h, Horizon = 3h, Stride = 1h).
- **Network Dimensions:** $N = 15\text{ road gully water-stage sensors}$ in Eastbourne, UK (`ESH5B_Star Rd`, `ESH6A_Cornfield`, `ESH7C_Sheen Rd`, etc.).
- **Tensors & Shapes:**
  - Input $X$: `(7282, 12, 15, 2)` ($7,282$ samples $\times 12$ lookback hours $\times 15$ gullies $\times 2$ features)
  - Target `Y_level`: `(7282, 15)` (Continuous water level in gully sump in meters at $t+3\text{h}$)
  - Target `Y_surcharge`: `(7282, 15)` (Binary threshold exceedance)
  - Target `mask`: `(7282, 12, 15)` (Binary valid observation mask)
- **Feature Definitions & Units:**
  1. `water_level_m` ($m$): Real measured water depth inside the gully pot. Range: $[-0.2005\ m, +1.3757\ m]$, Mean: $0.4869\ m$.
  2. `catchment_rainfall_mm_h` ($mm/h$): Real synchronized precipitation from paired rain gauge network.
- **Label Integrity & Scientific Distinction:**
  - `Y_level`: **100% Real Physical In-Situ Sensor Telemetry** across 10 continuous months (June 2025 to April 2026).
  - `Y_surcharge`: Exceeds the default sensor threshold in $68.75\%$ of instances. Note: The threshold in `index_telemetry_data.csv` is set at a low stage baseline, meaning it acts as an operational surcharge indicator rather than catastrophic flash flooding.
- **Missingness & Quality:**
  - **$97.84\%$ valid observation mask** ($2.16\%$ sensor missingness, exactly matching the audited rate).
  - Real missing timestamps are flagged in the companion mask tensor `mask`.
- **Data Splitting & Leakage Controls:**
  - Chronological Partition:
    - Train ($70\%$): $5,085\text{ sequences}$ (June 2025 – ~Jan 2026)
    - Validation ($15\%$): $1,080\text{ sequences}$ (~Jan 2026 – ~Feb 2026)
    - Test ($15\%$): $1,093\text{ sequences}$ (~Feb 2026 – April 2026)
  - Leakage Protection: Strict chronological partition with $12\text{-hour}$ purge buffers.
- **Supervised Training Verdict:** **APPROVED / HIGHEST PRIORITY FOR URBAN ST-GNN TRAINING**. This is the only dataset that captures real-world urban road-gully drainage dynamics with synchronized rainfall and in-situ water levels.

---

### Domain 4: Bellinge Urban Drainage Network (Odense, Denmark)

- **Source Files & Archives:**
  - Compressed Data Archive: `data/urban_drainage_datasets/bellinge/2_cleaned_data.zip` (**$390\text{ MB}$ compressed**, containing 29 sensor CSV files for gauges `G71F04R`, `G71F05R`, `G71F06R`, etc.)
  - Graph Artifacts:
    - Adjacency: `data/processed_global/urban_graphs/bellinge_adjacency.npy` ($1,020 \times 1,020$)
    - Node Features: `data/processed_global/urban_graphs/bellinge_node_features.npy` ($1,020 \times 4$)
    - Edge Features: `data/processed_global/urban_graphs/bellinge_edge_features.npy` ($1,037 \times 5$)
    - Node IDs: `data/processed_global/urban_graphs/bellinge_node_ids.json` (995 junctions, 16 storages, 9 outfalls)
  - Hydrodynamic Model:
    - Model INP: `data/urban_drainage_datasets/bellinge/swmm_models/7_SWMM/BellingeSWMM_v021_nopervious.inp`
    - Rainfall Record: `data/urban_drainage_datasets/bellinge/swmm_models/7_SWMM/rg_bellinge_Jun2010_Aug2021.dat` (11 years of 1-minute rainfall!)
    - Simulation Outputs: `.out` ($2.54\text{ MB}$) and `.rpt` ($469.8\text{ KB}$)
- **Observational Telemetry Status:**
  - The 29 cleaned sensor CSV files remain inside `2_cleaned_data.zip`. They have **NOT been uncompressed or parsed into sliding temporal sequence tensors ($X, Y$)**.
- **Hydrodynamic Baseline Status:**
  - Fully executed with PySWMM 2.2.0 / EPA-SWMM 5.2.4:
    - Runoff Continuity Error: $-0.969\%$
    - Flow Routing Continuity Error: $-1.625\%$
    - Numerical Quality: **CONVERGED_EXCELLENT** (Zero routing oscillations or conduit surcharge explosions).
- **Supervised Training Verdict:** **NOT READY FOR NEURAL TRAINING (PENDING TENSOR PROCESSING)**. The 390 MB zip archive must be uncompressed, synchronized with rainfall, and formatted into `.npz` sequence tensors. However, Bellinge is **100% READY as a Hydrodynamic Digital Twin Benchmark** for physics validation.

---

### Domain 5: Urban Water Observatory (Fehraltorf, Switzerland)

- **Source Files:**
  - Model Archive: `data/urban_drainage_datasets/uwo/swmm_input_files.zip` (Contains 206 calibrated SWMM `.inp` models)
  - Graph Topology: `data/processed_global/urban_graphs/uwo_adjacency.npy` ($440 \times 440$)
  - Documentation: `data_uwo_sqlite_content_overview.csv`, `uwo_field_observations_readme.md`
- **Observational Telemetry Status:**
  - The multi-gigabyte SQLite field observation databases (`data_UWO_2019-01_2020-01.sqlite`, etc.) are **NOT present** in the repository.
  - No observational streamflow or water-stage CSV/parquet files were downloaded or extracted.
- **Supervised Training Verdict:** **NOT READY FOR TRAINING**. No observational sensor time-series tensors exist. UWO can only be used for synthetic SWMM scenario comparisons, not for supervised neural learning.

---

### Domain 6: Multi-Domain Fusion Architecture

- **Concept:** Outfall tailwater boundary coupling between a river model (predicting river stage $h_{\text{river}}$) and an urban drainage model (predicting backwater surcharge $h_{\text{backwater}} = \max(0, h_{\text{river}} - z_{\text{outfall}})$).
- **Readiness Verdict:** **NOT READY FOR TRAINING**. Coupling models across domains is premature before the individual domain models (Aroostook River ST-GNN and Blue Heart Urban ST-GNN) have been independently trained, tuned, and verified.

---

## 3. Master Training Readiness Matrix

| Domain Track | Usable Samples | Graph Size ($N$) | Ground Truth Type | Missingness | Leakage Buffer | Readiness Verdict | Recommended Role |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **Aroostook River** | **14,624** | 4 Nodes | Real USGS Streamflow ($m^3/s$) | $0.0\%$ | 24h Purge | **READY (Flow Regression)** | Fluvial River ST-GNN Pretraining |
| **Potomac River** | 322 | 5 Nodes | Real USGS Streamflow ($m^3/s$) | $0.0\%$ | 12h Purge | **NOT READY** | Sample Size Inadequate |
| **Blue Heart Gully** | **7,282** | 15 Nodes | Real In-Situ Gully Level ($m$) | $2.16\%$ | 12h Purge | **READY (Stage Forecasting)** | **PRIMARY URBAN ST-GNN MODEL** |
| **Bellinge Network** | Pending Unzip | 1,020 Nodes | Real Sewer Flow (in `.zip`) | $0.0\%$ (SWMM) | Strict Time | **NOT READY (Neural)** | Hydrodynamic Twin Benchmark |
| **UWO Switzerland** | 0 (No Tensors) | 440 Nodes | None on disk | N/A | N/A | **NOT READY** | Synthetic SWMM Baseline Only |
| **Multi-Domain Fusion**| N/A | Variable | Coupled Head | N/A | N/A | **NOT READY** | Post-Training Integration Phase |

---

## 4. Final Recommendation: Which Model to Train First

### Recommendation: **Blue Heart Urban Gully ST-GNN (Track 2) MUST BE TRAINED FIRST.**

### Justification:
1. **Core Problem Statement Fidelity:** PS-11 is explicitly titled *"AI-Powered Urban Drainage and Flash Flood Predictive Management System"*. Blue Heart is the only acquired dataset that directly represents municipal urban drainage infrastructure (15 road gullies, street-level overland inundation, rainfall runoff).
2. **Direct Topographical Relevance to Indore:** Indore's urban flash flooding is pluvial and street-gully driven (roadway waterlogging and culvert surcharge at Rajwada, Bhanwarkuan, and Rambagh), which directly mirrors the Eastbourne road-gully physics, unlike large rural river basins.
3. **High Data Quality:** 7,282 clean, chronological sequences with $97.84\%$ valid observation mask and paired rain gauge inputs.
4. **Follow-Up Track:** Once the Blue Heart Urban ST-GNN is trained, **Aroostook River ST-GNN (Track 1)** should be trained as the complementary receiving-river fluvial model.

