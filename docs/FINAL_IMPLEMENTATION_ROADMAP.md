# HYDRO-GUARD AI — Final Implementation & Engineering Roadmap
**Document ID:** `HGAI-ROADMAP-2026-10-31`  
**Location:** `docs/FINAL_IMPLEMENTATION_ROADMAP.md`  
**Problem Statement:** PS-11 — AI-Powered Urban Drainage and Flash Flood Predictive Management System  
**Status:** COMPLETE / OFFICIAL ENGINEERING ROADMAP  

---

## 1. Executive Summary & Current Project Phase

With the completion of **Task 1** (Global River Data Acquisition), **Task 2 & 2.1** (Preprocessing, Validation & Label Disambiguation), **Task 2.2** (Final River Training Readiness Gate), and **Task 2.3** (Urban Drainage Data Acquisition & PS-11 Audit), HYDRO-GUARD AI has successfully established a scientifically rigorous data and architectural foundation.

This roadmap details the sequential execution phases required to transition the candidate models, physics engines, and dashboards into an integrated, production-ready flood predictive management system.

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    PROJECT ROADMAP & PHASING                                      |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                                                                                   |
|  [PHASE 1: DATA FOUNDATION & AUDIT] ───> COMPLETED (Tasks 1, 2, 2.1, 2.2, 2.3)                    |
|  ├── Global Hydrological Acquisition (CAMELS-Hourly, USGS, NOAA, ERA5)                            |
|  ├── Zero-Leakage Sequence Tensors Generated (14,946 clean sequences)                             |
|  ├── Urban Drainage Benchmarks Acquired (Bellinge, Blue Heart, UWO, CWPRS)                         |
|  └── Full PS-11 Requirements Matrix & Architecture Authored                                       |
|                                                                                                   |
|  [PHASE 2: MODEL TRAINING & VALIDATION] ───> TASK 3 (AWAITING USER COMMAND)                       |
|  ├── Step 3.1: DCRNN Pretraining on Decadal Hydrology (Aroostook 14,624 sequences)                |
|  ├── Step 3.2: DCRNN Urban Drainage Training (Bellinge 1,021-node network)                        |
|  ├── Step 3.3: Few-Shot Adaptation & Zero-Shot Testing on Potomac & CWPRS                         |
|  └── Step 3.4: Ablation Studies (Physics Loss vs Standard MSE; Focal Loss vs BCE)                 |
|                                                                                                   |
|  [PHASE 3: HYDRAULIC DIGITAL TWIN & REAL-TIME INTEGRATION] ───> TASK 4                            |
|  ├── Step 4.1: Live Sensor Telemetry Integration (FastAPI background ingestion)                   |
|  ├── Step 4.2: Acoustic Blockage Factor (β) Calibration from Real Sewer Telemetry                 |
|  └── Step 4.3: Coupling Fluvial Outfall Boundary Conditions to Sewer Surcharge                    |
|                                                                                                   |
|  [PHASE 4: STREET-LEVEL 2D INUNDATION & OPTIMIZATION] ───> TASK 5 & 6                             |
|  ├── Step 5.1: High-Resolution (15m) DEM Overland Inundation Polygon Generation                   |
|  ├── Step 6.1: Model Predictive Control (MPC) Solver for Pump & Sluice Gate Dispatch              |
|  └── Step 6.2: Automated Multi-Tier Emergency Alert Engine Dispatches                             |
|                                                                                                   |
|  [PHASE 5: PRODUCTION HARDENING & FINAL EVALUATION] ───> TASK 7                                   |
|  ├── Step 7.1: Containerization (Docker Compose for FastAPI, Streamlit, Celery)                   |
|  └── Step 7.2: Final End-to-End Stress Testing & Demonstration Sign-Off                           |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Phase-by-Phase Execution Details

### Phase 2: ST-GNN Model Training & Benchmark Evaluation (Task 3)
> **GATE REQUIREMENT:** Strictly halted until explicit user command is provided.

- **Step 3.1: Hydrological Foundation Pretraining (Aroostook):**
  - Input: `aroostook_sequences_w12_h3.npz` ($10,236$ train, $2,193$ val, $2,187$ test).
  - Train 2-layer bidirectional DCRNN with masked Huber loss and physical mass conservation loss.
  - Metrics target: Nash-Sutcliffe Efficiency $\text{NSE} \ge 0.75$, Kling-Gupta Efficiency $\text{KGE} \ge 0.80$.
- **Step 3.2: Urban Drainage Network Training (Bellinge):**
  - Extract $1,021 \times 1,021$ sparse adjacency from `BellingeSWMM_v021_nopervious.inp`.
  - Train candidate ST-GNN on 15-minute sewer level and flow telemetry.
  - Metrics target: Surcharge Classification $\text{PR-AUC} \ge 0.70$, $\text{CSI} \ge 0.60$.
- **Step 3.3: Out-of-Domain Generalization & Zero-Shot Testing:**
  - Evaluate pretrained weights on Potomac River ($322$ sequences) and CWPRS rainfall forcing.
  - Measure domain shift degradation and lead-time decay ($1\text{h}$ vs $3\text{h}$ vs $6\text{h}$).
- **Step 3.4: Scientific Candidate Model Ablation:**
  - Compare DCRNN against ConvLSTM, Vanilla GRU, and pure hydrodynamic SWMM simulation.
  - If DCRNN does not demonstrate statistically significant improvement over SWMM, transparently log findings.

---

### Phase 3: Hydraulic Digital Twin & Telemetry Integration (Task 4)
- **Step 4.1: Dynamic Ingestion Pipeline:**
  - Build asynchronous Celery / Redis background worker polling Open-Meteo REST API every 15 minutes.
  - Standardize in-memory sliding window buffer $(12 \times V \times 6)$ for inference.
- **Step 4.2: Real Acoustic Blockage Sensor Telemetry:**
  - Ingest signal-to-noise ratio (SNR) decibel drops and ultrasonic reflections from Blue Heart road gullies.
  - Formulate empirical mapping: $\beta(t) = f(\text{SNR}_{\text{drop}}, \Delta h_{\text{recession}})$.
- **Step 4.3: Outfall Boundary Coupling:**
  - Connect river water level $h_{\text{river}}(t)$ at Kahn/Saraswati confluence to stormwater outfall inverts, calculating backwater head $h_{\text{backwater}} = \max(0, h_{\text{river}} - z_{\text{outfall}})$.

---

### Phase 4: Street Inundation & Infrastructure Optimization (Tasks 5 & 6)
- **Step 5.1: 2D Street Inundation Mapping:**
  - Ingest SRTM 30m / CartoDEM for Indore urban core.
  - Generate vectorized GeoJSON flood polygons representing flood depth thresholds ($0.1\text{ m}, 0.3\text{ m}, 0.5\text{ m}, 1.0\text{+ m}$).
  - Render dynamically in Streamlit Leaflet map component (`frontend/components/flood_map.py`).
- **Step 6.1: Active Pump and Sluice Gate MPC Solver:**
  - Formulate real-time quadratic programming solver using `scipy.optimize` or `cvxpy`.
  - Compute optimal pump start/stop schedules and gate openings to minimize surcharge risk while penalizing electrical power consumption.
- **Step 6.2: Automated Emergency Warning Service:**
  - Connect `backend/services/reporting_service.py` to simulated SMS/Webhook dispatchers.
  - Trigger civic warnings 2 to 4 hours in advance of predicted street-level ponding.

---

### Phase 5: Production Hardening & Full-Stack Demonstration (Task 7)
- **Step 7.1: Architecture Containerization:**
  - Create multi-stage `Dockerfile` and `docker-compose.yml` orchestrating:
    1. `backend`: FastAPI Python 3.13 service (port 8000).
    2. `frontend`: Streamlit interactive portal (port 8501).
    3. `web-gateway`: Nginx serving static homepage animations and proxying REST APIs.
- **Step 7.2: Final Verification & Sign-Off:**
  - Run end-to-end integration test suite verifying 100% of PS-11 deliverables.
  - Confirm all user safeguards, homepage visual animations, and background images remain 100% intact.

---

## 3. Dependency Graph & Milestone Gate Criteria

```
[Task 1: Global Data Acquisition] (DONE)
               │
               ▼
[Task 2 & 2.1: Preprocessing & Label Audit] (DONE)
               │
               ▼
[Task 2.2: River Training Readiness Gate] (DONE)
               │
               ▼
[Task 2.3: Urban Data Acquisition & PS-11 Audit] (DONE)
               │
               ▼  <─── GATE: User Explicit Authorization Required
[Task 3: ST-GNN Model Training & Benchmark]
               │
               ▼
[Task 4: Real-Time Telemetry & Blockage Integration]
               │
               ▼
[Tasks 5 & 6: 2D Inundation & Pump/Gate Optimization]
               │
               ▼
[Task 7: Containerization & Final Production Launch]
```

---

## 4. Engineering Safeguards & Protocols

1. **No Premature Training:** Training scripts in Task 3 will not be executed until the user explicitly issues the command to begin.
2. **Preserve Existing Code & UI:** The existing frontend, canvas animations, and non-homepage background photos remain untouched.
3. **Local Version Control:** Zero remote git pushes or external repository syncs. All work is kept strictly local.
4. **Data Separation:** Raw archives in `data/urban_drainage_datasets/` and `data/global_flood_datasets/` remain read-only; processed tensors reside in `data/processed_global/`.

