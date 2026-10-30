"""
Comprehensive 11-Stage Verification and Smoke Test Suite for HYDRO-GUARD AI (Indore).
Validates GIS elevation drop, hydrological routing, CV 80% purity rule,
acoustic AI sewer sensing, Open-Meteo API with offline fallback,
2-second IoT simulator, frontend widgets, and FastAPI endpoints.
"""

import sys
import py_compile
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

passed_count = 0
failed_count = 0


def record_test(name: str, passed: bool, detail: str = ""):
    global passed_count, failed_count
    if passed:
        passed_count += 1
        print(f"  [PASS] {name} {f'({detail})' if detail else ''}")
    else:
        failed_count += 1
        print(f"  [FAIL] {name} {f'({detail})' if detail else ''}")


print("=" * 70)
print("  HYDRO-GUARD AI : SYSTEM VERIFICATION & COMPLIANCE SUITE")
print("=" * 70)

# ------------------------------------------------------------------------------
# STAGE 1: PYTHON ENVIRONMENT & IMPORTS
# ------------------------------------------------------------------------------
print("\n[STAGE 1] Validating Python Runtime & Core Imports...")
core_packages = [
    "fastapi", "uvicorn", "pydantic", "requests", "networkx", "folium",
    "numpy", "scipy", "pandas", "matplotlib", "cv2", "qrcode", "PIL",
    "librosa", "soundfile", "osmnx", "geopandas", "shapely", "streamlit_folium", "streamlit"
]
for pkg in core_packages:
    try:
        mod = __import__(pkg)
        record_test(f"Import {pkg:<16}", True, getattr(mod, "__version__", "ready"))
    except Exception as e:
        record_test(f"Import {pkg:<16}", False, str(e))

# ------------------------------------------------------------------------------
# STAGE 2: PYTHON SYNTAX COMPILATION (ALL FILES)
# ------------------------------------------------------------------------------
print("\n[STAGE 2] Compiling Python Source Code for Syntax Integrity...")
py_files = list(PROJECT_ROOT.glob("**/*.py"))
for pf in py_files:
    if ".venv" in str(pf) or "__pycache__" in str(pf):
        continue
    rel = pf.relative_to(PROJECT_ROOT)
    try:
        py_compile.compile(str(pf), doraise=True)
        record_test(f"Syntax compile {str(rel):<38}", True)
    except Exception as e:
        record_test(f"Syntax compile {str(rel):<38}", False, str(e))

# ------------------------------------------------------------------------------
# STAGE 3: CONFIGURATION & GIS TOPOLOGY LOADER
# ------------------------------------------------------------------------------
print("\n[STAGE 3] Validating Indore Topography & GIS Loader...")
import config
from backend.services.osmnx_gis_loader import indore_gis_loader

graph = indore_gis_loader.get_indore_drainage_graph()
record_test("Drainage Network Nodes", graph.number_of_nodes() == 7, f"Count: {graph.number_of_nodes()}")
record_test("Hydraulic Flow Edges", graph.number_of_edges() == 6, f"Count: {graph.number_of_edges()}")

profile = indore_gis_loader.get_elevation_profile()
drop_m = profile[0]["elevation_m"] - profile[-1]["elevation_m"]
record_test("South-to-North Elevation Drop", drop_m == 45.0, f"Rau 560m -> Kabithedi 515m ({drop_m}m drop)")

geojson = indore_gis_loader.to_geojson()
record_test("GeoJSON Export Generation", len(geojson.get("features", [])) >= 13, f"{len(geojson.get('features', []))} features")

# ------------------------------------------------------------------------------
# STAGE 4: HYDROLOGICAL ROUTING & FLOOD PREDICTION ENGINE
# ------------------------------------------------------------------------------
print("\n[STAGE 4] Validating Indore Hydrological Routing & Flood Prediction Engine...")
from backend.models.indore_routing_engine import routing_engine

# Cloudburst downpour (24 mm/hr)
res_storm = routing_engine.simulate_routing(rainfall_mm_hr=24.0, runoff_coeff=0.72)
record_test("Storm Surge Detection", res_storm["overall_basin_status"] == "CRITICAL", f"Status: {res_storm['overall_basin_status']}")
record_test("Choke Points Identified", len(res_storm["choke_points"]) > 0, f"{len(res_storm['choke_points'])} choke points")
record_test("Simulation Mode Flag", res_storm.get("simulation_mode") is True)

# Zero rain dry weather
res_dry = routing_engine.simulate_routing(rainfall_mm_hr=0.0, runoff_coeff=0.72)
record_test("Dry Weather Base Flow", res_dry["overall_basin_status"] == "SAFE", f"Status: {res_dry['overall_basin_status']}")

# Regression Test: predict_downstream_inundation (Used by Streamlit Flood Prediction Page)
pred_res = routing_engine.predict_downstream_inundation(rainfall_mm_hr=35.0, surge_multiplier=1.2, active_pumps=2)
has_expected_fields = all(k in pred_res for k in ["peak_flood_arrival_mins", "peak_choke_point", "node_predictions"])
record_test("Routing Engine predict_downstream_inundation Method", has_expected_fields and pred_res["peak_flood_arrival_mins"] > 0)

# Verify DataFrame schema required by frontend/app.py line 339
node_preds = pred_res.get("node_predictions", [])
has_all_df_cols = (len(node_preds) == 7 and all(
    all(col in np for col in ["node_name", "elevation_msl", "water_level_pct", "status", "gate_action"])
    for np in node_preds
))
record_test("Inundation Node Predictions DataFrame Contract", has_all_df_cols, f"{len(node_preds)} nodes formatted")

# Verify Pump Drawdown Mitigation
pred_no_pumps = routing_engine.predict_downstream_inundation(rainfall_mm_hr=35.0, surge_multiplier=1.2, active_pumps=0)
pump_relief_observed = pred_res["node_predictions"][0]["water_level_pct"] < pred_no_pumps["node_predictions"][0]["water_level_pct"]
record_test("Active Pumps Hydraulic Relief", pump_relief_observed, f"0 pumps: {pred_no_pumps['node_predictions'][0]['water_level_pct']}% -> 2 pumps: {pred_res['node_predictions'][0]['water_level_pct']}%")

# ------------------------------------------------------------------------------
# STAGE 5: COMPUTER VISION WATER PURITY & 80% DIVERSION RULE
# ------------------------------------------------------------------------------
print("\n[STAGE 5] Validating Computer Vision Water Purity (80% Rule)...")
from backend.models.cv_purity_detector import cv_detector

clean_frame = cv_detector.generate_synthetic_drain_frame("clean_rainwater")
clean_res = cv_detector.analyze_image(clean_frame)
record_test("Clean Rainwater Purity >= 80%", clean_res["is_clean"] is True, f"Purity: {clean_res['purity_score']}%")
record_test("Clean Water Gate Action", clean_res["gate_status"] == config.GATE_CLEAN_ACTION, clean_res["gate_status"])

polluted_frame = cv_detector.generate_synthetic_drain_frame("polluted_sludge")
polluted_res = cv_detector.analyze_image(polluted_frame)
record_test("Polluted Sewage Purity < 80%", polluted_res["is_clean"] is False, f"Purity: {polluted_res['purity_score']}%")
record_test("Polluted Water Gate Action", polluted_res["gate_status"] == config.GATE_DIRTY_ACTION, polluted_res["gate_status"])

# Corrupted / empty image handling
corrupt_res = cv_detector.analyze_image(b"not_an_image_random_bytes")
record_test("Corrupted Image Graceful Error", "error" in corrupt_res and corrupt_res["is_clean"] is False)

# ------------------------------------------------------------------------------
# STAGE 6: UNDERGROUND SEWER ACOUSTIC WATER LEVEL AI
# ------------------------------------------------------------------------------
print("\n[STAGE 6] Validating Acoustic AI Sewer Level Sensing...")
from backend.models.acoustic_level_ai import acoustic_ai

audio_bytes = acoustic_ai.generate_synthetic_sewer_audio(target_level_pct=88.0, duration_sec=2.5, filename="test_surge_88pct.wav")
ac_res = acoustic_ai.analyze_audio(audio_bytes)
record_test("Acoustic Inferred Level Bounded", 0.0 <= ac_res["estimated_water_level_pct"] <= 100.0, f"{ac_res['estimated_water_level_pct']}%")
record_test("Decibel SPL Computation", 30.0 <= ac_res["decibel_spl"] <= 100.0, f"{ac_res['decibel_spl']} dB SPL")
record_test("Spectrogram Visual Generation", len(ac_res.get("spectrogram_image_b64", "")) > 100)

# Silent audio input (zeros)
import numpy as np
silent_signal = np.zeros(22050 * 2, dtype=np.float32)
silent_res = acoustic_ai.analyze_audio(silent_signal)
record_test("Silent Audio Handling (Graceful baseline)", silent_res["estimated_water_level_pct"] <= 10.0, f"Level: {silent_res['estimated_water_level_pct']}%")

# ------------------------------------------------------------------------------
# STAGE 7: OPEN-METEO WEATHER CLIENT & OFFLINE FALLBACK
# ------------------------------------------------------------------------------
print("\n[STAGE 7] Validating Open-Meteo Precipitation & Offline Fallback...")
from backend.services.open_meteo_client import weather_client

weather = weather_client.fetch_live_weather()
record_test("Weather Client Indore Coordinates", weather.get("city") == "Indore" and weather.get("latitude") == 22.7196)
record_test("Rainfall Rate & Category", "rainfall_intensity_mm_hr" in weather and "rainfall_category" in weather)

# Verify offline fallback model
fallback_weather = weather_client._generate_fallback_weather()
record_test("Offline Meteorological Fallback", fallback_weather.get("is_live_api") is False and "forecast_6h" in fallback_weather)

# ------------------------------------------------------------------------------
# STAGE 8: 2-SECOND TELEMETRY STREAM SIMULATOR
# ------------------------------------------------------------------------------
print("\n[STAGE 8] Validating 2-Second IoT Telemetry Stream Simulator...")
from backend.simulators.sensor_stream_sim import sensor_simulator

snapshot = sensor_simulator.get_latest()
record_test("IoT Nodes In Telemetry", len(snapshot.get("nodes", {})) == 7, f"{len(snapshot.get('nodes', {}))} nodes")
record_test("City Mean Water Level", 0.0 <= snapshot.get("city_avg_water_level_pct", -1) <= 100.0)

# Test interactive controls
sensor_simulator.set_surge_simulation(2.5)
record_test("Surge Multiplier Control", sensor_simulator.surge_multiplier == 2.5)
sensor_simulator.set_surge_simulation(1.0)

sensor_simulator.trigger_pollution_event(True)
record_test("Pollution Injection Toggle", sensor_simulator.forced_pollution is True)
sensor_simulator.trigger_pollution_event(False)

# ------------------------------------------------------------------------------
# STAGE 9: FRONTEND WIDGETS, MAPS & QR GENERATORS
# ------------------------------------------------------------------------------
print("\n[STAGE 9] Validating Frontend Components & Action Cards...")
from frontend.components.map_visualizer import indore_map_visualizer
from frontend.components.gauge_widgets import gauge_widgets

folium_map = indore_map_visualizer.create_folium_map(snapshot)
record_test("Folium GIS Interactive Map", folium_map is not None)

gauge_png = gauge_widgets.render_speedometer_gauge(level_pct=65.0)
record_test("Speedometer PNG Buffer", gauge_png.getbuffer().nbytes > 5000)

split_pipe_html = gauge_widgets.render_split_pipe_html(purity_score=85.0)
record_test("Split-Pipe HTML Schematic", "KHAN RIVER DISCHARGE" in split_pipe_html and "80%" in split_pipe_html)

sms = gauge_widgets.generate_citizen_sms_broadcast(
    area_name="Rajwada Confluence",
    area_hi="राजवाड़ा संगम",
    water_level_pct=72.0,
    rainfall_mm_hr=18.0,
)
record_test("GenAI Bilingual Citizen SMS Alert", len(sms.get("hindi", "")) > 40 and len(sms.get("english", "")) > 40)

qr_pass = gauge_widgets.generate_evacuation_qr_pass()
record_test("Emergency Evacuation QR Pass", qr_pass.getbuffer().nbytes > 1500)

# ------------------------------------------------------------------------------
# STAGE 10: FASTAPI REST ENDPOINTS VIA TESTCLIENT
# ------------------------------------------------------------------------------
print("\n[STAGE 10] Validating FastAPI REST Endpoints...")
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 1. Root
r_root = client.get("/")
record_test("GET /", r_root.status_code == 200, f"System: {r_root.json().get('system')}")

# 2. Health
r_health = client.get("/health")
record_test("GET /health", r_health.status_code == 200, f"Status: {r_health.json().get('status')}")

# 3. Water Levels
r_levels = client.get("/api/v1/flood/current-levels")
record_test("GET /api/v1/flood/current-levels", r_levels.status_code == 200, f"{len(r_levels.json().get('nodes', {}))} nodes")

# 4. Rainfall
r_rain = client.get("/api/v1/flood/rainfall")
record_test("GET /api/v1/flood/rainfall", r_rain.status_code == 200)

# 5. Flood Prediction (with PredictionRequest V2 schema)
r_pred = client.post("/api/v1/flood/predict", json={"rainfall_intensity_mmh": 28.0, "surge_multiplier": 1.2, "active_pumps_count": 3})
record_test("POST /api/v1/flood/predict (V2 Schema)", r_pred.status_code == 200, f"Arrival: {r_pred.json().get('peak_flood_arrival_mins')} mins")

# 6. Topology
r_topo = client.get("/api/v1/flood/topology")
record_test("GET /api/v1/flood/topology", r_topo.status_code == 200)

# 7. Elevation Profile
r_elev = client.get("/api/v1/flood/elevation-profile")
record_test("GET /api/v1/flood/elevation-profile", r_elev.status_code == 200, f"{len(r_elev.json().get('profile', []))} profile points")

# 8. CV Purity Analyze (JSON PurityAnalysisRequest)
r_cv_json = client.post("/api/v1/sensors/cv-purity/analyze", json={"turbidity_ntu": 12.0, "color_hue_deg": 210.0, "suspended_solids_ppm": 35.0})
record_test("POST /api/v1/sensors/cv-purity/analyze (JSON V2)", r_cv_json.status_code == 200, f"Purity: {r_cv_json.json().get('purity_score_percent')}%")

# 9. CV Purity Analyze (Multipart/Form Image)
r_cv = client.post("/api/v1/sensors/cv-purity/analyze", data={"sample_type": "clean_rainwater"})
record_test("POST /api/v1/sensors/cv-purity/analyze (Multipart)", r_cv.status_code == 200, f"Gate: {r_cv.json().get('gate_action')}")

# 10. Acoustic Level Analyze (JSON AcousticAnalysisRequest)
r_ac_json = client.post("/api/v1/sensors/acoustic-level/analyze", json={"decibels_db_spl": 74.0, "dominant_frequency_hz": 1250.0})
record_test("POST /api/v1/sensors/acoustic-level/analyze (JSON V2)", r_ac_json.status_code == 200, f"Level: {r_ac_json.json().get('inferred_water_level_pct')}%")

# 11. Acoustic Level Analyze (Multipart/Form Audio)
r_ac = client.post("/api/v1/sensors/acoustic-level/analyze", data={"test_level_pct": 75.0})
record_test("POST /api/v1/sensors/acoustic-level/analyze (Multipart)", r_ac.status_code == 200, f"Level: {r_ac.json().get('inferred_water_level_pct')}%")

# 12. Standalone Engine Smoke Check
from backend.standalone_engine import app as standalone_app
standalone_client = TestClient(standalone_app)
r_sa_root = standalone_client.get("/")
record_test("Standalone Engine V2.0 Root", r_sa_root.status_code == 200, f"Title: {standalone_app.title}")

r_sa_purity = standalone_client.post("/api/v1/sensors/cv-purity/analyze", json={"turbidity_ntu": 10.0, "color_hue_deg": 200.0, "suspended_solids_ppm": 20.0})
record_test("Standalone Engine CV 80% Rule", r_sa_purity.json().get("pass_80pct_rule") is True, f"Purity: {r_sa_purity.json().get('purity_score_percent')}%")

# 10. Live Telemetry
r_telem = client.get("/api/v1/sensors/telemetry/live")
record_test("GET /api/v1/sensors/telemetry/live", r_telem.status_code == 200)

# 11. Simulation Control
r_ctrl = client.post("/api/v1/sensors/simulation/control", json={"surge_multiplier": 1.5})
record_test("POST /api/v1/sensors/simulation/control", r_ctrl.status_code == 200)

# 12. Floating Environmental Summary Endpoint
r_env = client.get("/api/v1/flood/environmental-summary")
record_test(
    "GET /api/v1/flood/environmental-summary",
    r_env.status_code == 200 and "live_rainfall" in r_env.json(),
    f"Rain: {r_env.json().get('live_rainfall', {}).get('value')} mm/h, River: {r_env.json().get('river_level', {}).get('value')}m"
)

# 13. ML Model Info & Evaluation Metrics
r_ml_info = client.get("/api/v1/flood/ml-model/info")
record_test(
    "GET /api/v1/flood/ml-model/info",
    r_ml_info.status_code == 200 and "evaluation_metrics" in r_ml_info.json(),
    f"Acc: {r_ml_info.json().get('evaluation_metrics', {}).get('accuracy') * 100:.1f}%, ROC: {r_ml_info.json().get('evaluation_metrics', {}).get('roc_auc') * 100:.1f}%"
)

# 14. ML Inference Prediction
r_ml_pred = client.post("/api/v1/flood/ml-predict", json={
    "rainfall_intensity_mmh": 45.0,
    "antecedent_rainfall_24h_mm": 50.0,
    "river_stage_khan_m": 3.8,
    "drainage_flow_m3s": 3.2,
    "active_pumps_count": 2,
    "soil_saturation_pct": 75.0,
})
record_test(
    "POST /api/v1/flood/ml-predict",
    r_ml_pred.status_code == 200 and "flood_inundation_probability" in r_ml_pred.json(),
    f"Prob: {r_ml_pred.json().get('flood_inundation_probability')}%, Tier: {r_ml_pred.json().get('risk_tier')}"
)

# 15. SQLite Analysis History Endpoint
r_hist = client.get("/api/v1/sensors/history?limit=10")
record_test(
    "GET /api/v1/sensors/history",
    r_hist.status_code == 200 and "records" in r_hist.json(),
    f"{len(r_hist.json().get('records', []))} records retrieved"
)

# 16. SQLite Database Diagnostic Statistics
r_db_stats = client.get("/api/v1/sensors/db-stats")
record_test(
    "GET /api/v1/sensors/db-stats",
    r_db_stats.status_code == 200 and r_db_stats.json().get("database", {}).get("status") == "HEALTHY",
    f"DB: {r_db_stats.json().get('database', {}).get('total_analysis_records')} analysis records"
)

# ------------------------------------------------------------------------------
# STAGE 11: SAMPLE ASSETS PERSISTENCE & FRONTEND ASSETS
# ------------------------------------------------------------------------------
print("\n[STAGE 11] Verifying Physical Test Assets and Web Frontend on Disk...")
import cv2
cv2.imwrite(str(config.SAMPLE_IMAGE_DIR / "clean_rainwater.jpg"), clean_frame)
cv2.imwrite(str(config.SAMPLE_IMAGE_DIR / "polluted_sludge.jpg"), polluted_frame)
border_frame = cv_detector.generate_synthetic_drain_frame("borderline_runoff")
cv2.imwrite(str(config.SAMPLE_IMAGE_DIR / "borderline_runoff.jpg"), border_frame)

for fname in ["clean_rainwater.jpg", "polluted_sludge.jpg", "borderline_runoff.jpg"]:
    p = config.SAMPLE_IMAGE_DIR / fname
    record_test(f"Asset sample_images/{fname}", p.exists() and p.stat().st_size > 1000, f"{p.stat().st_size} bytes")

for fname in ["trickle_flow_25pct.wav", "moderate_surge_60pct.wav", "critical_flash_surge_92pct.wav"]:
    p = config.SAMPLE_AUDIO_DIR / fname
    record_test(f"Asset sample_audio/{fname}", p.exists() and p.stat().st_size > 1000, f"{p.stat().st_size} bytes")

# Web Frontend Assets
static_dir = PROJECT_ROOT / "frontend" / "static"
record_test("Web Asset index.html", (static_dir / "index.html").exists() and (static_dir / "index.html").stat().st_size > 500)
record_test("Web Asset css/style.css", (static_dir / "css" / "style.css").exists() and (static_dir / "css" / "style.css").stat().st_size > 500)
record_test("Web Asset js/app.js", (static_dir / "js" / "app.js").exists() and (static_dir / "js" / "app.js").stat().st_size > 500)
record_test("Web Asset images/hero_bg.jpg", (static_dir / "images" / "hero_bg.jpg").exists() and (static_dir / "images" / "hero_bg.jpg").stat().st_size > 10000)

# ------------------------------------------------------------------------------
# STAGE 12: SQLITE PERSISTENCE & DATA INTEGRITY ACROSS RECONNECTION
# ------------------------------------------------------------------------------
print("\n[STAGE 12] Validating SQLite Persistence & Data Integrity Across Reconnection...")
import sqlite3
record_test("Database File Existence", config.DB_PATH.exists(), str(config.DB_PATH))

# Re-open raw independent SQLite connection to verify disk persistence
raw_conn = sqlite3.connect(str(config.DB_PATH))
raw_cursor = raw_conn.cursor()

raw_cursor.execute("SELECT COUNT(*) FROM analysis_logs WHERE analysis_type = 'IMAGE_PURITY';")
img_logs_count = raw_cursor.fetchone()[0]
record_test("Persisted Image Analysis Records", img_logs_count > 0, f"{img_logs_count} records")

raw_cursor.execute("SELECT COUNT(*) FROM analysis_logs WHERE analysis_type = 'ACOUSTIC_LEVEL';")
audio_logs_count = raw_cursor.fetchone()[0]
record_test("Persisted Audio Analysis Records", audio_logs_count > 0, f"{audio_logs_count} records")

raw_cursor.execute("SELECT id, analysis_type, primary_metric, status_verdict, gate_action FROM analysis_logs ORDER BY id DESC LIMIT 1;")
latest_row = raw_cursor.fetchone()
record_test(
    "Latest Persisted Analysis Verification",
    latest_row is not None and len(latest_row) == 5,
    f"ID #{latest_row[0]}: {latest_row[1]} = {latest_row[2]} ({latest_row[3]})"
)
raw_conn.close()

print("\n" + "=" * 70)
print(f"  VERIFICATION COMPLETE: {passed_count} PASSED, {failed_count} FAILED")
print("=" * 70)

if failed_count > 0:
    print(f"\n❌ Verification finished with {failed_count} failure(s).")
    sys.exit(1)
else:
    print("\n✅ ALL 12 STAGES AND API CONTRACTS VERIFIED OPERATIONAL WITH 100% PASS RATE!")
    sys.exit(0)
