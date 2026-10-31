# AQUAGUARD AI — Drainage Blockage Monitoring, Topographical Mapping & Evidence-Based Reports Module

## 1. Executive Summary

The **Drainage Blockage Intelligence Module** is an independent, non-invasive engineering extension to the **AQUAGUARD AI** urban drainage intelligence platform. It provides municipal hydro-engineers with:
1. **Interactive Topographical Drainage Mapping:** High-resolution GIS visualization integrating Copernicus DEM GLO-30 (30m elevation datum EGM2008) and OpenStreetMap waterways.
2. **Evidence-Based Blockage Categorization:** Visual distinction between **Confirmed Blockages (RED)**, **Suspected Hotspots (ORANGE)**, **Normal Monitored Segments (GREEN)**, and **Insufficient Data (GREY)**.
3. **OpenCV Image Evidence Screening:** Ingestion and automated morphological contour and colorimetric analysis of drain outfall frames, calculating debris coverage percentage, optical turbidity index, and purity ratings.
4. **Official Downloadable Engineering Reports:** Real-time generation of downloadable **ReportLab PDFs** for individual drainage segments (with embedded inspection frames and telemetry) and **city-wide audit reports** (PDF and CSV exports).
5. **Strict Scientific Integrity (Zero Fabrication):** Cities with datasets lacking spatial drainage assets (such as the Pune CWPRS rainfall dataset) display zero synthetic blockage markers and feature explicit scientific provenance disclaimers.

---

## 2. Module Architecture

```
                  ┌─────────────────────────────────────────────────────────────┐
                  │                 AquaGuard AI Web Dashboard                  │
                  │   (#blockage: Leaflet Topo Map + Detail Panel + Audit Table)│
                  └──────────────────────────────┬──────────────────────────────┘
                                                 │ HTTP / JSON / Binary Streams
                                                 ▼
                  ┌─────────────────────────────────────────────────────────────┐
                  │          FastAPI Router: backend.api.blockage_routes        │
                  │     (/api/v1/blockage/cities, segments, summary, pdf, csv)  │
                  └───────────────┬─────────────────────────────┬───────────────┘
                                  │                             │
                                  ▼                             ▼
   ┌──────────────────────────────────────────────┐  ┌───────────────────────────┐
   │    backend.services.drainage_blockage_service│  │ backend.services.db_mgr   │
   │  - Segment GIS & DEM Coordinate Query        │  │  - drainage_segments      │
   │  - Status & Risk Classification Matrix       │  │  - blockage_observations  │
   │  - ReportLab PDF Generation Engine           │  │  - drainage_images        │
   │  - Tabular CSV Formatter                     │  │  - blockage_reports       │
   └───────────────┬──────────────────────────────┘  └───────────────────────────┘
                   │
         ┌─────────┴──────────────────────┬─────────────────────────┐
         ▼                                ▼                         ▼
┌──────────────────┐            ┌───────────────────┐     ┌───────────────────────┐
│ Copernicus DEM   │            │ OpenCV Purity AI  │     │ Real Data Repositories│
│ GLO-30 GeoTIFF   │            │ cv_purity_detector│     │ - Indore OSM & DEM    │
│ (30m, EGM2008)   │            │ (Debris & Turbid.)│     │ - Blue Heart UK Gully │
└──────────────────┘            └───────────────────┘     │ - CWPRS Pune Rainfall │
                                                          └───────────────────────┘
```

---

## 3. Database Schema (SQLite)

Four new normalized tables were added to the persistent SQLite database (`data/hydro_guard.db`) via `DatabaseManager.init_db()` using safe `CREATE TABLE IF NOT EXISTS` statements:

### 3.1 `drainage_segments`
Stores physical and hydraulic attributes of individual drainage channels:
- `id` (TEXT, PK): Unique segment identifier (e.g., `SEG_IND_05`).
- `city_id` (TEXT): Associated geographical region (`indore`, `eastbourne`, `pune`, `bellinge`).
- `segment_code` (TEXT): Municipal engineering code (e.g., `DS-05`).
- `name` (TEXT): Descriptive segment name.
- `source_node` / `target_node` (TEXT): Upstream and downstream hydraulic junctions.
- `channel_type` (TEXT): Structural form (e.g., `Box Culvert`, `Open Concrete Canal`).
- `coordinates_geojson` (TEXT): Serialized GeoJSON coordinates.
- `start_lat`, `start_lon`, `end_lat`, `end_lon`, `mid_lat`, `mid_lon` (REAL): Coordinates.
- `elevation_m` (REAL): Terrain surface elevation from Copernicus DEM GLO-30 (m MSL).
- `length_m` (REAL): Channel length in meters.
- `slope` (REAL): Longitudinal gradient.
- `manning_velocity_m_s` (REAL): Theoretical design velocity.
- `max_capacity_m3_s` (REAL): Design discharge capacity.

### 3.2 `blockage_observations`
Stores point-in-time inspection records and telemetric diagnostic assessments:
- `id` (INTEGER, PK AUTOINCREMENT)
- `segment_id` (TEXT, FK): Linked drainage segment.
- `city_id` (TEXT)
- `status` (TEXT): `CONFIRMED_BLOCKAGE`, `SUSPECTED_BLOCKAGE`, `NORMAL_MONITORED`, `INSUFFICIENT_DATA`.
- `risk_level` (TEXT): `CRITICAL`, `WARNING`, `LOW`, `UNKNOWN`.
- `confidence_score` (REAL): Assessment confidence rating (0.0 to 1.0).
- `debris_coverage_pct` (REAL): Percentage of cross-sectional aperture obstructed by floating solid debris.
- `silt_depth_cm` (REAL): Measured or estimated sediment bed depth.
- `flow_velocity_pct` (REAL): Current flow as a percentage of nominal design velocity.
- `water_level_pct` (REAL): Sump or culvert water level as a percentage of full capacity.
- `evidence_summary` (TEXT): Detailed engineering diagnostic rationale.
- `evidence_type` (TEXT): `OPENCV_INSPECTION`, `TELEMETRIC_WATER_ANOMALY`, `TERRAIN_BOTTLENECK`, `NONE`.
- `observation_date` (TEXT): Date of inspection or sensor reading.
- `inspector_name` (TEXT): Authorized reporting entity.
- `action_recommended` (TEXT): Specific municipal intervention or maintenance order.
- `data_source` (TEXT): Originating telemetry or imaging feed.

### 3.3 `drainage_images`
Maintains photographic inspection frames linked to drainage segments:
- `id` (INTEGER, PK AUTOINCREMENT)
- `segment_id` (TEXT, FK)
- `image_path` (TEXT): Relative path to stored inspection frame.
- `caption` (TEXT)
- `capture_date` (TEXT)
- `image_source` (TEXT): `MUNICIPAL_INSPECTION_CAMERA`, `DRONE_SURVEY`, etc.
- `opencv_analyzed` (INTEGER): Flag indicating whether OpenCV screening was executed (1 or 0).
- `debris_pct` (REAL): Debris contour area percentage.
- `turbidity_score` (REAL): Optical turbidity index (NTU).
- `purity_score` (REAL): Overall water quality purity score (0 to 100%).
- `is_blockage_evidence` (INTEGER): Flag marking frame as confirmed blockage evidence.

### 3.4 `blockage_reports`
Maintains permanent audit log of generated PDF and CSV documents:
- `id` (INTEGER, PK AUTOINCREMENT)
- `report_type` (TEXT): `INDIVIDUAL_SEGMENT` or `CITY_WIDE`.
- `city_id` (TEXT)
- `segment_id` (TEXT, Nullable)
- `generated_at` (TEXT)
- `report_title` (TEXT)
- `file_path` (TEXT)
- `file_size_bytes` (INTEGER)
- `summary_json` (TEXT)

---

## 4. API Endpoints

All endpoints are mounted under the `/api/v1/blockage` prefix:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/blockage/cities` | Returns list of supported cities, coverage metadata, and scientific limitation declarations. |
| `GET` | `/api/v1/blockage/segments` | Returns drainage segments with coordinates, elevations, and latest observations (`city_id`, `status`, `risk` query filters). |
| `GET` | `/api/v1/blockage/segments/{segment_id}` | Detailed geometry, Copernicus DEM elevation, observation history, and image evidence for a single segment. |
| `GET` | `/api/v1/blockage/segments/{segment_id}/images` | Photographic inspection frames, OpenCV debris percentages, turbidity, and purity metrics. |
| `GET` | `/api/v1/blockage/summary` | City-wide scorecard: counts of Confirmed (RED), Suspected (ORANGE), Monitored (GREEN), and Insufficient Data (GREY). |
| `GET` | `/api/v1/blockage/reports/individual/{segment_id}/pdf` | Downloads official ReportLab PDF certificate for an individual drainage segment. |
| `GET` | `/api/v1/blockage/reports/city/{city_id}/pdf` | Downloads comprehensive city-wide drainage blockage & topographical audit ReportLab PDF. |
| `GET` | `/api/v1/blockage/reports/city/{city_id}/csv` | Streams tabular drainage dataset with all coordinates, elevations, and blockage diagnostics as CSV. |

---

## 5. Dataset Coverage & Scientific Limitations

### 5.1 Indore (Madhya Pradesh, India)
- **Topographical Context:** Real Copernicus DEM GLO-30 30m raster (`copernicus_glo30_n22_e075.tif`).
- **Drainage Network:** 9 monitored segments across Khan and Saraswati river basins.
- **Blockage Evidence:**
  - **Confirmed Blockages (RED):** `DS-05` (Pardeshipura Industrial Drain, 74.5% debris, 78cm silt) and `DS-08` (Mhow Naka Culvert, 68.2% debris, 72cm silt). Verified by outfall camera frames and OpenCV screening.
  - **Suspected Hotspots (ORANGE):** `DS-03` (Rambagh Urban Collector, adverse slope backwater) and `DS-06` (Vijay Nagar Sump, trash rack blinding).
  - **Normal Monitored (GREEN):** `DS-01` (Rau), `DS-02` (Bhanwarkuan), `DS-04` (Rajwada), `DS-07` (Kabithedi).
  - **Insufficient Data (GREY):** `DS-09` (Scheme 54 Lateral, pending CCTV camera installation).

### 5.2 Eastbourne & Pevensey Levels (East Sussex, UK)
- **Data Source:** Blue Heart UK Highway Gully & Rain Gauge Telemetry (`data/urban_drainage_datasets/blue_heart/`).
- **Drainage Network:** 4 monitored road gully links.
- **Blockage Evidence:** Derived from ultrasonic gully pot water and silt depth telemetry (sustained post-rain retention).
- **Limitations:** No street CCTV inspection photographs in repository; honest "No drainage inspection image available" notice displayed.

### 5.3 Pune & Khadakwasla Region (Maharashtra, India)
- **Data Source:** CWPRS Hourly Rainfall Telemetry (2021–2025).
- **Drainage Network:** None in repository.
- **Scientific Integrity Protocol:** **Zero synthetic or fake blockage markers are created.** When selected in the UI, the dashboard shows 0 segments and displays the explicit scientific notice:
  > *"Strict Scientific Integrity: This dataset provides meteorological rainfall telemetry only. No municipal drainage network coordinates or physical blockage observations exist in the repository. As per protocol, no simulated or fake blockage markers are created."*

### 5.4 Bellinge (Odense, Denmark)
- **Data Source:** SWMM Hydraulic Sewer Network (`data/urban_drainage_datasets/bellinge/`).
- **Drainage Network:** 2 SWMM sewer links with sensor coordinates.
- **Blockage Evidence:** Hydraulic velocity anomalies only; no direct visual camera photographs.

---

## 6. Files Created & Modified

### New Files Created:
1. `backend/services/drainage_blockage_service.py` — Core service coordinating GIS, DEM elevations, OpenCV analysis, and ReportLab PDF/CSV generation.
2. `backend/api/blockage_routes.py` — FastAPI router with 8 endpoints and Pydantic validation models.
3. `tests/test_drainage_blockage.py` — Comprehensive 13-test automated test suite.
4. `docs/DRAINAGE_BLOCKAGE_MODULE.md` — This detailed technical documentation document.

### Existing Files Modified (Preserving All Legacy Code):
1. `backend/services/db_manager.py` — Added table creation statements (`drainage_segments`, `blockage_observations`, `drainage_images`, `blockage_reports`) and helper query methods to `DatabaseManager`.
2. `backend/api/__init__.py` — Exported `blockage_router`.
3. `backend/main.py` — Mounted `blockage_router`.
4. `frontend/static/css/style.css` — Appended styling for `.blockage-container`, `.blockage-layout-grid`, `.blockage-pill`, and pulsing Leaflet markers (`.leaflet-blockage-marker`).
5. `frontend/static/index.html` — Added navigation link in header, sidebar entry, homepage launch card, and complete `#screen-blockage` DOM container.
6. `frontend/static/js/app.js` — Registered `blockage` in `SCREEN_TITLES`, wired `navigateTo('blockage')`, and added full asynchronous client controller.

---

## 7. Testing Results

The complete project test suite passes with **40/40 tests passing (100% pass rate)**:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.4.2, pluggy-1.6.0
rootdir: E:\ai-manthan\hydro_guard_indore
plugins: anyio-4.15.1, platformdirs-4.14.0
collected 40 items

tests\test_drainage_blockage.py .............                            [ 32%]
tests\test_hybrid_st_gnn.py ......                                       [ 47%]
tests\test_real_gis_topology.py .......                                  [ 65%]
tests\test_reports_monitoring.py .......                                 [ 82%]
tests\test_spatial_river_network.py .......                              [100%]

======================== 40 passed, 1 warning in 8.21s ========================
```

---

## 8. How to Use the Module

### 8.1 Starting the Application
```powershell
cd E:\ai-manthan\hydro_guard_indore
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 8.2 Accessing the Dashboard
- Open your browser to: **`http://127.0.0.1:8000/#blockage`**
- Or click **"Blockage Intel"** in the top navigation bar or left sidebar.

### 8.3 Interacting with the Features
1. **Switch Cities:** Use the top-left dropdown to switch between Indore, Eastbourne, Pune, or Bellinge.
2. **Filter by Status:** Click filter pills to display only Confirmed (RED), Suspected (ORANGE), Normal (GREEN), or Insufficient (GREY).
3. **Inspect a Segment:** Click any colored drainage line or pulsing marker on the Leaflet map, or click a row in the bottom inventory table.
4. **View Evidence:** The right panel immediately updates with the Copernicus DEM elevation, coordinates, debris %, silt depth, and inspection camera photograph.
5. **Download Reports:**
   - Click **"📥 Download Drainage Blockage Report (PDF)"** in the right panel to download a segment certificate.
   - Click **"📥 Download City Report (PDF)"** in the header to download a city-wide audit.
   - Click **"📊 Export CSV"** to export the raw data.

