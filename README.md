# 🌊 HYDRO-GUARD AI : Urban Drainage, Flash Flood & Water Quality Management System
### Tailored for the City of Indore, Madhya Pradesh (Indore Municipal Corporation - IMC)
**Problem Statement 11: Production-Ready Modular Prototype**

---

## 📌 Executive Overview

**HYDRO-GUARD AI** is an end-to-end urban hydrological intelligence, edge AI, and automated drainage gate control platform specifically designed for the unique geography, river topology, and stormwater infrastructure of **Indore, Madhya Pradesh**.

Indore experiences severe monsoon waterlogging across critical low-lying choke points such as Rajwada, Rambagh, and Pardeshipura due to rapid runoff from high-elevation southern ridges down into the **Khan (Kahn) and Saraswati River** basins. Simultaneously, untreated industrial and domestic sewage discharges into the river channels degrade water quality.

HYDRO-GUARD AI resolves this dual crisis with:
1. **Topological GIS Elevation & Flow Routing Engine**: Models Indore's south-to-north elevation drop (**~560m MSL in Rau/Bhanwarkuan down to ~515m MSL at Kabithedi STP**), calculating peak flood arrival times and inundation depths.
2. **Computer Vision Water Purity & Automated Split-Pipe Diversion Gate**: Enforces the **80% Purity Rule**:
   - $\ge 80\%$ Purity: **`GATE OPEN TO KHAN RIVER`** (Harvesting and recharging clean rainwater).
   - $< 80\%$ Purity: **`DIVERTING TO STP / FILTRATION BASIN`** (Directing contaminated black/grey water to the Kabithedi 245 MLD Sewage Treatment Plant).
3. **Acoustic AI Water Level Detection**: Processes audio waveforms and spectrograms (dB SPL & FFT resonant cavity frequencies) in dark underground conduits where optical cameras fail due to zero illumination and grime.
4. **Live Meteorological & 2-Second Telemetry Streaming**: Integrates real-time Indore rainfall from the **Open-Meteo API** (Lat: 22.7196, Lon: 75.8577) and runs a 2-second background IoT stream across 7 critical drain nodes.
5. **Non-Technical Municipal Command Dashboard (Streamlit)**: Dark medical/tech UI featuring traffic-light color coding, analog speedometer gauges, interactive split-pipe schematics, bilingual plain-language action cards (English/Hindi), GenAI citizen SMS alerts, and scannable emergency QR evacuation passes.

---

## 🏛️ System Architecture

```
                                  +-----------------------------+
                                  |   Open-Meteo Weather API    |
                                  | (Indore Lat: 22.7196, Lon)  |
                                  +--------------+--------------+
                                                 | (Live Rain mm/hr)
                                                 v
+-------------------------------+ +--------------+--------------+ +-------------------------------+
|      Computer Vision AI       | |   Indore GIS Routing Engine | |      Acoustic Sewer AI        |
|  (OpenCV Turbidity & Debris)  | | (NetworkX Topo 550m->515m)  | |  (Librosa / dB SPL / FFT)     |
+---------------+---------------+ +--------------+--------------+ +---------------+---------------+
                |                                |                                |
                | (80% Purity Rule)              | (Runoff & Choke Points)        | (Dark Pipe Level %)
                v                                v                                v
+-------------------------------------------------------------------------------------------------+
|                       2-Second Background IoT Telemetry Stream Generator                         |
|                    (Bhanwarkuan -> Rambagh -> Rajwada -> Pardeshipura -> Kabithedi)             |
+------------------------------------------------+------------------------------------------------+
                                                 |
                        +------------------------+------------------------+
                        |                                                 |
                        v                                                 v
         +------------------------------+                 +-------------------------------+
         |     FastAPI Backend (8000)   |                 | Streamlit Command UI (8501)   |
         |  REST Endpoints & Simulation |                 |  Speedometers, Maps, QR Passes|
         +------------------------------+                 +-------------------------------+
```

---

## 📂 Project Directory Structure

```
hydro_guard_indore/
├── backend/
│   ├── main.py                     # Primary FastAPI server with CORS & lifecycle simulator
│   ├── api/
│   │   ├── __init__.py             # API package exports
│   │   ├── flood_routes.py         # Endpoints for water levels, rainfall & prediction
│   │   └── sensor_routes.py        # Endpoints for CV Purity & Acoustic Sensors
│   ├── models/
│   │   ├── __init__.py             # Model package exports
│   │   ├── cv_purity_detector.py   # OpenCV Logic for 80% Water Purity Check
│   │   ├── acoustic_level_ai.py    # Librosa spectrogram/dB-to-Water-Level AI model
│   │   └── indore_routing_engine.py# NetworkX/GIS topological flow & gate control engine
│   ├── services/
│   │   ├── open_meteo_client.py    # Live rain forecast fetcher for Indore (Lat: 22.7196, Lon: 75.8577)
│   │   └── osmnx_gis_loader.py     # Indore elevation & drainage graph loader using OSMnx
│   └── simulators/
│       └── sensor_stream_sim.py    # Background simulator generating 2-sec JSON telemetry stream
├── frontend/
│   ├── app.py                      # Main Streamlit Dashboard with Dark Medical/Tech Theme
│   └── components/
│       ├── map_visualizer.py       # Indore GIS Topology & Heatmap Render (Folium/Matplotlib)
│       └── gauge_widgets.py        # Speedometer Gauge, Split-Pipe Diversion & Action Cards
├── data/
│   ├── indore_gis/                 # Cached GIS network topologies & GeoJSON
│   ├── sample_audio/               # Sewer hydrophone test recordings (WAV)
│   └── sample_images/              # Outfall camera test frames (JPG)
├── config.py                       # Project Coordinates (Indore MSL: 550m to 515m), Thresholds
├── requirements.txt                # Python dependencies
└── README.md                       # Architecture & setup instructions
```

---

## ⚡ Core Feature Implementations

### 1. Indore Topographical Elevation Drop & River Routing
- **Hydrological Profile**: Indore slopes continuously downwards from South to North:
  - **Rau Headwaters**: $560.0\text{ m MSL}$
  - **Bhanwarkuan Drain**: $552.0\text{ m MSL}$
  - **Rajwada (Krishnapura Chhatri Confluence)**: $540.0\text{ m MSL}$
  - **Rambagh Drain**: $536.0\text{ m MSL}$
  - **Pardeshipura Industrial Drain**: $526.0\text{ m MSL}$
  - **Kabithedi 245 MLD STP (Northern Discharge)**: $515.0\text{ m MSL}$
- **Calculations**: Computes Manning's velocity $v = \frac{1}{n} R^{2/3} S^{1/2}$, sub-catchment runoff via Rational Formula $Q = \frac{C \cdot I \cdot A}{3.6}$, and NetworkX directed topological propagation to forecast peak flood arrival time ($T_p$) and surface inundation depths ($\text{cm}$).

### 2. The 80% Purity Rule & Automated Split-Pipe Gate
- Evaluates outfall turbidity, HSV chromatic clarity, and morphological floating solid waste patches.
- **Rule Enforcement**:
  - $\ge 80.0\%$ Purity: **`GATE OPEN TO KHAN RIVER`** (Recharges natural river ecosystem with unpolluted rainwater).
  - $< 80.0\%$ Purity: **`DIVERTING TO STP / FILTRATION BASIN`** (Prevents raw sewage from reaching the river by routing into Kabithedi biological treatment basins).

### 3. Acoustic AI Sewer Water Level Model
- Overcomes dark, steamy, condensation-heavy underground sewers where optical cameras blind.
- Computes Sound Pressure Level (dB SPL) and spectral centroids via FFT / spectrogram analysis.
- Correlates resonant acoustic vibrations and turbulence to hydraulic depth (0% to 100%).

### 4. Live 2-Second IoT Telemetry Stream & Open-Meteo
- Fetches real-time precipitation, humidity, and wind from Open-Meteo for Indore.
- Thread-safe background generator broadcasts 2-second JSON telemetry across all Indore sumps.

### 5. Municipal Operator & Citizen Alert Dashboard
- **Speedometer Fuel-Style Gauge**: Visual indication of hydraulic capacity (Green $\le 50\%$, Yellow $51-75\%$, Red $>75\%$).
- **Interactive Split-Pipe SVG**: Shows real-time motorized valve diversion.
- **Plain-Language Action Cards**: e.g., *"कबीटखेड़ी मुख्य पंप चालू कर दिया गया है (Kabithedi Main Pump Activated)"*.
- **Citizen Safety**: Generates bilingual emergency SMS broadcasts and dynamic QR passes for high-ground evacuation shelters (Holkar Stadium / Brilliant Convention Centre).

---

## 🚀 Installation & Rapid Start

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### 1. Clone & Setup Environment
```bash
cd hydro_guard_indore
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Launch the FastAPI Backend & Reference-Matched Web UI
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- **Reference-Matched Web Application**: Open `http://localhost:8000` in any web browser to experience the exact reference UI featuring glassmorphism navbar, live floating environmental cards, video modal, interactive Leaflet map, dual prediction, and real upload tools!
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### 3. Launch the Streamlit Operations Command Dashboard
In a separate terminal:
```bash
python -m streamlit run frontend/app.py --server.port 8501
```
- Open browser at: `http://localhost:8501`
- Features a clean, professional 7-page navigation structure (Overview, Indore Flood Map, Flood Prediction, Water Image Analysis, Drain Sound Analysis, Pump & Gate Simulation, Reports) with zero API key watermarks and real file upload workflows.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Reference-matched Web Application (HTML) or System Metadata (JSON) |
| `GET` | `/health` | System health and 2-second background IoT simulator status |
| `GET` | `/api/v1/flood/environmental-summary` | Real-time metrics specifically powering the 3 floating hero cards |
| `GET` | `/api/v1/flood/ml-model/info` | Random Forest ML evaluation metrics (92.7% accuracy, 93.8% ROC-AUC) |
| `POST` | `/api/v1/flood/ml-predict` | Machine learning flash flood risk inference and advisory |
| `GET` | `/api/v1/flood/current-levels` | Real-time water levels and alert status for all 7 Indore nodes |
| `GET` | `/api/v1/flood/rainfall` | Live Open-Meteo weather and precipitation for Indore |
| `POST` | `/api/v1/flood/predict` | Predict peak flood arrival time and inundation depths (Physics routing) |
| `GET` | `/api/v1/flood/topology` | Full GeoJSON drainage network and elevation bounds |
| `GET` | `/api/v1/flood/elevation-profile` | South-to-North elevation drop data (560m to 515m MSL) |
| `POST` | `/api/v1/sensors/cv-purity/analyze` | Upload or test drain outfall image for 80% Purity Rule |
| `POST` | `/api/v1/sensors/acoustic-level/analyze` | Upload or synthesize sewer audio for level estimation |
| `GET` | `/api/v1/sensors/telemetry/live` | Latest 2-second IoT telemetry stream snapshot |
| `POST` | `/api/v1/sensors/simulation/control` | Interactively inject storm surges or sewer contamination |

---

## 🧪 Verification & Operational Walkthrough

1. **Verify Backend Health**:
   ```bash
   curl http://localhost:8000/health
   ```
2. **Test 80% Purity Rule with Sample Outfall**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/sensors/cv-purity/analyze" -F "sample_type=clean_rainwater"
   curl -X POST "http://localhost:8000/api/v1/sensors/cv-purity/analyze" -F "sample_type=polluted_sludge"
   ```
3. **Test Acoustic AI Model**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/sensors/acoustic-level/analyze" -F "test_level_pct=88.0"
   ```
4. **Trigger Monsoonal Surge Simulation**:
   Adjust the **Storm Surge Multiplier** in the Streamlit sidebar (Tab 1) or toggle **Inject Heavy Sewer Effluent** to watch the automated split-pipe gate divert instantly from the Khan River into Kabithedi STP!

---

## 🏛️ Built For
**Indore Smart City Development Limited (ISCDL)** & **Indore Municipal Corporation (IMC)**  
*Swachh Indore, Surakshit Indore (स्वच्छ इंदौर, सुरक्षित इंदौर)*

