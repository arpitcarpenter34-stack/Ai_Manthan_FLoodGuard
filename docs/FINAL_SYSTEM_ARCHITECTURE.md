# HYDRO-GUARD AI — Unified System Architecture Specification
**Document ID:** `HGAI-ARCH-UNIFIED-2026-10-31`  
**Location:** `docs/FINAL_SYSTEM_ARCHITECTURE.md`  
**Problem Statement:** PS-11 — AI-Powered Urban Drainage and Flash Flood Predictive Management System  
**Status:** COMPLETE ARCHITECTURE DESIGN SPECIFICATION  

---

## 1. Architectural Vision & Core Principles

HYDRO-GUARD AI is an enterprise-grade cyber-physical system designed to predict, mitigate, and manage urban flash floods and drainage surcharges.

The architecture strictly adheres to three foundational design laws:
1. **Physical & Temporal Decoupling:** Fast-response urban stormwater pipe networks ($5\text{--}15\text{ minute}$ concentration times) are separated from slow-response natural river basins ($6\text{--}72\text{ hour}$ routing times), communicating exclusively via outfall hydraulic boundary conditions.
2. **Hybrid Intelligence (Physics + AI):** Data-driven graph neural networks provide fast forward-looking state predictions ($T + 1\text{h}, 3\text{h}, 6\text{h}$), while 1D/2D hydraulic physics engines enforce strict mass and momentum conservation ($\frac{\partial Q}{\partial x} + \frac{\partial A}{\partial t} = 0$).
3. **Candidate Model Pragmatism:** The Diffusion Convolutional Recurrent Neural Network (DCRNN / ST-GNN) is treated as a **candidate model** evaluated against statistical and physical baselines, rather than an unverified assumption.

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    HYDRO-GUARD AI DATA PIPELINE                                   |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                                                                                   |
|  [EXTERNAL SENSING & FORCING]                                                                     |
|  ┌─────────────────────┐    ┌─────────────────────┐    ┌───────────────────────────────────────┐  |
|  │ A. METEOROLOGICAL   │    │ B. RADAR NOWCASTING │    │ I. IoT IN-SITU TELEMETRY              │  |
|  │ - Open-Meteo REST   │    │ - X/C-Band Radar    │    │ - Road Gullies (Ultrasonic)           │  |
|  │ - ERA5 Reanalysis   │    │ - Rain Gauges       │    │ - Sewer Depth & Acoustic Blockage     │  |
|  │ - IMD NWP Forecast  │    │ - Optical Tracking  │    │ - Fluvial River Gauges                │  |
|  └──────────┬──────────┘    └──────────┬──────────┘    └───────────────────┬───────────────────┘  |
|             │                          │                                   │                      |
|             ▼                          ▼                                   ▼                      |
|  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │                             CENTRAL DATA INGESTION & QUALITY BUS                            │  |
|  │ - Unit Normalization (SI: m³/s, m, mm/h)                                                    │  |
|  │ - Chronological Sliding Window Buffering (W=12h, s=1h)                                      │  |
|  │ - Outlier & Missing Value Masking (Zero-Imputation Prohibited)                              │  |
|  └──────────────────────────────────────┬──────────────────────────────────────────────────────┘  |
|                                         │                                                         |
|         ┌───────────────────────────────┴───────────────────────────────┐                         |
|         ▼                                                               ▼                         |
|  ┌─────────────────────────────────────┐             ┌─────────────────────────────────────────┐  |
|  │ C. RIVER HYDROLOGY ENGINE           │             │ D. URBAN DRAINAGE DIGITAL TWIN          │  |
|  │ - Large Basin Muskingum-Cunge 1D    │             │ - EPA-SWMM Hydrodynamic Model           │  |
|  │ - Fluvial Outfall Head Elevations   │             │ - 1,021 Nodes (Manholes, Gullies)       │  |
|  │ - Daily / Hourly Baseflow Routing   │             │ - 1,046 Conduits, Pumps & Sluice Gates  │  |
|  └──────────────────┬──────────────────┘             └────────────────────┬────────────────────┘  |
|                     │                                                     │                       |
|                     │       ┌─────────────────────────────────────────────┘                       |
|                     ▼       ▼                                                                     |
|  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │ E. SPATIO-TEMPORAL PREDICTION ENGINE (CANDIDATE ST-GNN / DCRNN)                             │  |
|  │ - Bidirectional Graph Random Walk Convolution (Forward: Gravity; Backward: Backwater)       │  |
|  │ - Multi-Step Recurrent Gating (H=1h, 3h, 6h Water Level & Discharge Forecasts)              │  |
|  │ - Physics Loss Regularization (Hydraulic Capacity Constraint Penalty)                       │  |
|  └──────────────────────────────────────┬──────────────────────────────────────────────────────┘  |
|                                         │                                                         |
|                                         ▼                                                         |
|  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │ F. HYDRAULIC VALIDATION & SIMULATION                                                        │  |
|  │ - Manning's Full-Pipe / Surcharge Formula: Q = (1-β)·(1/n)·A·R^(2/3)·S^(1/2)                │  |
|  │ - Dynamic Backwater Head Tracking & Surcharge Detection                                     │  |
|  └──────────────────┬──────────────────────────────────────────────────────┬───────────────────┘  |
|                     │                                                      │                      |
|                     ▼                                                      ▼                      |
|  ┌─────────────────────────────────────┐             ┌─────────────────────────────────────────┐  |
|  │ G. STREET INUNDATION MAPPING        │             │ H. PUMP & GATE OPTIMIZATION             │  |
|  │ - 1D-to-2D Overland DEM Spill       │             │ - Model Predictive Control (MPC)        │  |
|  │ - Height-Above-Nearest-Drainage     │             │ - Dynamic Sluice Gate Throttling        │  |
|  │ - Street Ponding Depth (15m Grid)   │             │ - Peak-Shaving Wet Well Dispatch        │  |
|  └──────────────────┬──────────────────┘             └────────────────────┬────────────────────┘  |
|                     │                                                     │                       |
|                     └───────────────────────────┬─────────────────────────┘                       |
|                                                 ▼                                                 |
|  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │ J. ALERT & EMERGENCY MANAGEMENT SERVICE                                                     │  |
|  │ - NWS/CWC Standard Risk Tiers: Normal (0), Action (1), Minor (2), Major (3)                 │  |
|  │ - Automated Push, SMS, Webhook, and Civil Defense Evacuation Routing                        │  |
|  └──────────────────────────────────────┬──────────────────────────────────────────────────────┘  |
|                                         │                                                         |
|                                         ▼                                                         |
|  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │ K. COMMAND CENTER DASHBOARD & VISUALIZATION                                                 │  |
|  │ - FastAPI High-Throughput REST Gateway (Port 8000)                                          │  |
|  │ - Interactive Leaflet GIS Inundation Map & Sensor Gauges (Port 8501)                        │  |
|  │ - Cinematic ZIP-Based Operational Scroll Animation Interface                                │  |
|  └─────────────────────────────────────────────────────────────────────────────────────────────┘  |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Detailed Module Specifications (Components A to K)

### Component A: Meteorological Forecasting
- **Primary Function:** Ingest real-time weather observations, numerical weather prediction (NWP) forecasts, and atmospheric variables.
- **Data Feeds:** Open-Meteo REST API (hourly temperature, precipitation, barometric surface pressure, humidity); ERA5 atmospheric reanalysis archive.
- **Output:** Standardized meteorological tensor slice $\mathbf{M}_t \in \mathbb{R}^{W \times 3}$ (precipitation rate $mm/h$, temperature $^\circ C$, pressure $hPa$).

### Component B: Radar and Rainfall Nowcasting
- **Primary Function:** High-resolution spatial tracking of convective storm cells with short-range nowcasting ($0\text{--}2\text{ hours}$).
- **Data Feeds:** High-frequency tipping bucket rain gauges ($1\text{--}15\text{ min}$); local X-band radar and regional C-band radar (benchmarked from Bellinge; satellite proxy for Indore).
- **Processing:** Marshall-Palmer $Z\text{--}R$ relationship ($Z = 200 R^{1.6}$) and optical flow advection tracking to produce grid rainfall intensities $R(x, y, t)$.

### Component C: River Hydrology Engine
- **Primary Function:** Simulate natural river reaches, regional floodplains, and tributary routing.
- **Model:** 1D Muskingum-Cunge diffusive wave routing:
  $$Q_{j+1}^{n+1} = C_1 Q_j^{n+1} + C_2 Q_j^n + C_3 Q_{j+1}^n$$
- **Role in System:** Computes the receiving water surface elevation $h_{\text{river}}(t)$ at urban stormwater outfall locations.

### Component D: Urban Drainage Digital Twin
- **Primary Function:** Provide high-fidelity physical representation of the underground sewer network.
- **Model:** Hydrodynamic EPA-SWMM 5.2 engine.
- **Network Specification:** 
  - Subcatchments ($713$ in Bellinge; $246$ in UWO; $14$ in Indore prototype).
  - Manholes and Junctions ($996$ in Bellinge; $427$ in UWO).
  - Conduits, Weirs, Orifices, Pumps, and Storage Units.
- **Output:** Hydraulic conveyance matrix $\mathbf{K}$, node invert elevations, full-pipe capacities $Q_{\text{cap}}$.

### Component E: Spatio-Temporal Prediction Engine (Candidate ST-GNN / DCRNN)
- **Primary Function:** Ultra-fast multi-node forecasting of future water levels and discharge ($H = 1\text{h}, 3\text{h}, 6\text{h}$).
- **Architecture:** Diffusion Convolutional Recurrent Neural Network (DCRNN):
  $$\mathbf{H}^{(t)} = \text{DCGRU}(\mathbf{X}^{(t)}, \mathbf{H}^{(t-1)}; \mathbf{P}_f, \mathbf{P}_b)$$
  where $\mathbf{P}_f = \mathbf{D}_O^{-1}\mathbf{A}$ represents gravity forward routing and $\mathbf{P}_b = \mathbf{D}_I^{-1}\mathbf{A}^T$ represents backwater wave surcharge propagation.
- **Pragmatic Assessment:** Benchmarked continuously against standard LSTM, GRU, and 1D hydrodynamic routing. If DCRNN fails to outperform simpler physics baselines in PR-AUC or NSE, the physics engine takes precedence.

### Component F: Hydraulic Simulation & Physics Validator
- **Primary Function:** Enforce hydraulic laws and physical consistency checks on neural network predictions.
- **Core Formula (Manning's Pipe Capacity with Acoustic Blockage):**
  $$Q_{\text{capacity}} = (1 - \beta) \cdot \frac{1}{n} A R^{2/3} S^{1/2}$$
  where $\beta \in [0.0, 1.0]$ is the measured acoustic/visual blockage factor.
- **Surcharge Sentry:** When predicted flow $\hat{Q}_v > Q_{\text{capacity}}$, the simulator flags pipe pressurized surcharge, raises water levels into the manhole chimney, and triggers surface flooding when $h > h_{\text{road}}$.

### Component G: Street-Level Inundation Mapping
- **Primary Function:** Translate pipe and manhole overflows into street-level flood depth polygons.
- **Algorithm:** Height-Above-Nearest-Drainage (HAND) coupled with 30m SRTM / CartoDEM depression filling:
  $$\text{Depth}(x, y) = \max\left(0, h_{\text{overflow}} - \text{DEM}(x, y)\right)$$
- **Output:** GeoJSON vector polygons and raster GeoTIFF layers depicting inundation depths ($0.1\text{ m}, 0.3\text{ m}, 0.5\text{ m}, 1.0\text{+ m}$).

### Component H: Pump and Sluice-Gate Optimization
- **Primary Function:** Control mechanical drainage infrastructure to maximize storage and prevent downstream overtopping.
- **Optimization Formulation (Model Predictive Control - MPC):**
  $$\min_{\{u_t\}} \sum_{t=1}^{T_p} \left( \sum_{v \in V_{\text{flood}}} (h_v(t) - h_{\text{safe}})_+^2 + w_E \sum_{p \in \text{pumps}} P_p(t) + w_G \sum_{g} (\Delta u_{g, t})^2 \right)$$
  subject to pump start/stop latency, maximum motor power, and storage freeboard.

### Component I: IoT In-Situ Telemetry
- **Primary Function:** Ingest real-time field observations from physical sensors.
- **Sensor Types:** Ultrasonic non-contact water level sensors; Doppler radar pipe velocity meters; road gully depth monitors; tipping bucket rain gauges; acoustic pipe blockage monitors.
- **Quality Assurance:** Automatic outlier removal, spike clipping, rate-of-change screening, and signal-to-noise ratio (SNR) flagging.

### Component J: Alert and Emergency Management Service
- **Primary Function:** Generate, audit, and dispatch emergency alerts.
- **Threshold Tiers:**
  - `Tier 0 (Green)`: Normal baseflow ($h < 0.60 h_{\text{bankfull}}$).
  - `Tier 1 (Yellow)`: Action stage ($0.60 \le h / h_{\text{bankfull}} < 0.85$).
  - `Tier 2 (Orange)`: Minor flood / pipe surcharge ($0.85 \le h / h_{\text{bankfull}} < 1.00$).
  - `Tier 3 (Red)`: Major flood / surface inundation ($h \ge h_{\text{bankfull}}$ or road water $> 15\text{ cm}$).
- **Delivery Mechanisms:** Automated SMS, Telegram bot, REST webhook to municipal disaster response teams, and automated audit logging.

### Component K: Command Center Dashboard
- **Primary Function:** Provide role-based situational awareness for city administrators, engineers, and citizens.
- **Frontend Stack:**
  - Homepage: High-performance canvas-rendered cinematic animation.
  - Interactive GIS Portal: Streamlit + Folium/Leaflet rendering live node status, water stage graphs, blockage levels, and flood depth contours.
- **Backend Stack:** FastAPI async REST engine serving OpenAPI 3.0 endpoints with sub-100ms response times.

---

## 3. Inter-Module Data Flow & API Contracts

| Source Module | Target Module | Data Payload & Format | Protocol | Frequency |
| :--- | :--- | :--- | :--- | :--- |
| **A (Meteo) & B (Radar)** | Central Bus | Hourly / 15-min rainfall time series (JSON / NetCDF) | REST / Webhook | $15\text{ min}$ |
| **I (IoT Telemetry)** | Central Bus | Level, velocity, battery, SNR flags (JSON) | MQTT / REST | $5\text{ min}$ |
| **Central Bus** | **E (ST-GNN)** | Standardized tensor $(B, 12, V, 6)$ (NumPy float32) | In-Memory / Torch | $15\text{ min}$ |
| **E (ST-GNN)** | **F (Hydraulics)** | Predicted stage $\hat{h}(t+H)$ and flow $\hat{Q}(t+H)$ | In-Memory / JSON | $15\text{ min}$ |
| **C (River)** | **D & F (Sewer Twin)** | River outfall tailwater stage boundary $h_{\text{outfall}}$ | Internal API | $1\text{ hour}$ |
| **F (Hydraulics)** | **G (Inundation)** | Manhole overflow volume $V_{\text{overflow}}$ ($m^3$) | Internal Function | On Exceedance |
| **F (Hydraulics)** | **H (Optimization)** | Storage tank water depths & surcharge forecasts | Solver Input | $15\text{ min}$ |
| **G & F** | **J (Alerting)** | High-risk node IDs and estimated inundation depths | REST POST | Instantaneous |
| **J, G, E, I** | **K (Dashboard)** | Real-time map layers, sensor telemetry, alert feeds | WebSocket / REST | $5\text{ sec}$ polling |

---

## 4. Architectural Sign-Off
- **Status:** **APPROVED FOR IMPLEMENTATION PLANNING**
- **Next Step:** Detail phasing and sprint boundaries in `docs/FINAL_IMPLEMENTATION_ROADMAP.md`.

