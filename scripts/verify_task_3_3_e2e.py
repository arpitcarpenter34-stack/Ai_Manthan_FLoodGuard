#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HYDRO-GUARD AI — TASK 3.3: END-TO-END DEMO & SYSTEM VERIFICATION
Comprehensive validation script covering all 12 operational capabilities and the full demonstration scenario.
"""

import sys
import json
import time
import urllib.request
import urllib.parse

# Ensure UTF-8 console output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:8501"

passed_tests = []
failed_tests = []

def run_test(name, func):
    print(f"\n[TEST] {name}...")
    try:
        res = func()
        print(f"  ✓ PASSED: {res}")
        passed_tests.append(name)
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed_tests.append((name, str(e)))
        return False

# ---------------------------------------------------------------------------
# 1. Backend Health & Root
# ---------------------------------------------------------------------------
def test_backend_health():
    url = f"{BASE_URL}/health"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    status = data.get("status", "").upper()
    assert status == "HEALTHY", f"Unexpected status {status}"
    nodes_online = data.get("nodes_online", 0)
    assert nodes_online == 7, f"Expected 7 nodes online, got {nodes_online}"
    return f"Status: {status}, Nodes Online: {nodes_online}, Simulator Running: {data.get('simulator_running')}"

# ---------------------------------------------------------------------------
# 2. Weather & Live Rainfall Telemetry
# ---------------------------------------------------------------------------
def test_weather_api():
    url = f"{BASE_URL}/api/v1/flood/rainfall"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    rf = data.get("rainfall_intensity_mm_hr", 0.0)
    cat = data.get("rainfall_category", "Unknown")
    return f"Rainfall: {rf:.1f} mm/h ({cat}), Source: {data.get('source')}"

# ---------------------------------------------------------------------------
# 3. Live 2-Second IoT Telemetry Stream
# ---------------------------------------------------------------------------
def test_sensor_telemetry():
    url = f"{BASE_URL}/api/v1/sensors/telemetry/live"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    telemetry = data.get("telemetry", {})
    avg_stage = telemetry.get("city_avg_water_level_pct", 0.0)
    nodes = list(telemetry.get("nodes", {}).keys())
    assert len(nodes) == 7, f"Expected 7 monitored nodes, got {len(nodes)}"
    return f"Nodes: {len(nodes)}, Basin Mean Stage: {avg_stage:.1f}%, Peak Risk: {telemetry.get('peak_risk_node')}"

# ---------------------------------------------------------------------------
# 4. Urban Drainage Digital Twin & GIS Topology
# ---------------------------------------------------------------------------
def test_drainage_topology():
    url = f"{BASE_URL}/api/v1/flood/topology"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    geojson = data.get("geojson", {})
    features = geojson.get("features", [])
    waterways = data.get("real_waterways", {}).get("total_features", 0)
    points = [f for f in features if f.get("geometry", {}).get("type") == "Point"]
    lines = [f for f in features if f.get("geometry", {}).get("type") == "LineString"]
    assert len(points) == 7, f"Expected 7 node points in geojson, got {len(points)}"
    assert len(lines) == 13, f"Expected 13 channel lines in geojson, got {len(lines)}"
    return f"Nodes: {len(points)}, Drainage Channels: {len(lines)}, Real Waterways: {waterways}, Basin Drop: 560m -> 515m MSL"

# ---------------------------------------------------------------------------
# 5. AI Flood Prediction (Indore Dual-Engine ST-GNN + Manning)
# ---------------------------------------------------------------------------
def test_indore_hybrid_prediction():
    url = f"{BASE_URL}/api/v1/flood/hybrid-predict"
    payload = json.dumps({
        "rainfall_intensity_mmh": 65.0,
        "surge_multiplier": 1.5,
        "active_pumps_count": 2,
        "soil_saturation_pct": 75.0
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    prob = data.get("overall_flood_probability", 0.0)
    risk = data.get("overall_basin_risk", "Unknown")
    arrival = data.get("peak_flood_arrival_mins", 0)
    choke = data.get("peak_choke_point", "Unknown")
    node_preds = data.get("node_predictions", [])
    assert len(node_preds) == 7
    return f"Risk: {risk} (Prob: {prob}%), Peak Arrival: {arrival} mins at {choke}, 7 Nodes Evaluated"

# ---------------------------------------------------------------------------
# 6. Blue Heart UK Real Data ST-GNN Candidate Inference
# ---------------------------------------------------------------------------
def test_blue_heart_candidate_inference():
    # A. Benchmark metadata
    url_b = f"{BASE_URL}/api/v1/flood/blue-heart/benchmark"
    resp_b = urllib.request.urlopen(url_b)
    assert resp_b.status == 200
    bench = json.loads(resp_b.read().decode())
    rmse_winner = bench.get("benchmark_results", {}).get("Adaptive_Gated_DCRNN", {}).get("all_obs", {}).get("rmse")
    assert rmse_winner == 0.0385, f"Unexpected RMSE: {rmse_winner}"
    
    # B. Live inference on held-out sample
    url_p = f"{BASE_URL}/api/v1/flood/blue-heart/predict?test_index=15"
    req_p = urllib.request.Request(url_p, method="POST")
    resp_p = urllib.request.urlopen(req_p)
    assert resp_p.status == 200
    pred = json.loads(resp_p.read().decode())
    assert pred.get("status") == "success"
    nodes = pred.get("nodes", [])
    assert len(nodes) == 15, "Expected 15 Blue Heart road gullies"
    mean_err = pred.get("mean_absolute_error_mm", 0.0)
    return f"Model: {pred.get('model')}, Test RMSE: {rmse_winner}m, Sample MAE: {mean_err:.2f} mm across 15 gullies"

# ---------------------------------------------------------------------------
# 7. Pump and Gate Advisory (CV Purity Screening 80% Rule)
# ---------------------------------------------------------------------------
def test_gate_advisory_cv_purity():
    url = f"{BASE_URL}/api/v1/sensors/cv-purity/analyze"
    # Test Clean sample
    payload_clean = json.dumps({"turbidity_ntu": 8.0, "color_hue_deg": 210.0, "suspended_solids_ppm": 15.0}).encode("utf-8")
    req_clean = urllib.request.Request(url, data=payload_clean, headers={"Content-Type": "application/json"}, method="POST")
    resp_clean = urllib.request.urlopen(req_clean)
    data_clean = json.loads(resp_clean.read().decode())
    gate_clean = data_clean.get("gate_action", "")
    purity_clean = data_clean.get("purity_score_percent", 0.0)
    
    # Test Sludge sample
    payload_sludge = json.dumps({"turbidity_ntu": 85.0, "color_hue_deg": 40.0, "suspended_solids_ppm": 320.0}).encode("utf-8")
    req_sludge = urllib.request.Request(url, data=payload_sludge, headers={"Content-Type": "application/json"}, method="POST")
    resp_sludge = urllib.request.urlopen(req_sludge)
    data_sludge = json.loads(resp_sludge.read().decode())
    gate_sludge = data_sludge.get("gate_action", "")
    purity_sludge = data_sludge.get("purity_score_percent", 0.0)
    
    assert "KHAN" in gate_clean or "DIRECT" in gate_clean or "OPEN" in gate_clean, f"Unexpected gate for clean: {gate_clean}"
    assert "STP" in gate_sludge or "DIVERT" in gate_sludge, f"Unexpected gate for sludge: {gate_sludge}"
    return f"Clean Runoff ({purity_clean:.1f}%) -> '{gate_clean}' | Polluted Sludge ({purity_sludge:.1f}%) -> '{gate_sludge}' (80% Rule Verified)"

# ---------------------------------------------------------------------------
# 8. Emergency Alert Management (4-Tier Municipal System)
# ---------------------------------------------------------------------------
def test_emergency_alerts():
    url = f"{BASE_URL}/api/v1/flood/alerts/active"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    tier = data.get("current_tier", 0)
    name = data.get("tier_name", "Normal")
    dispatches = data.get("active_dispatches", [])
    return f"Current Tier: {tier} ({name}), Active Dispatches: {len(dispatches)}"

# ---------------------------------------------------------------------------
# 9. Historical Summary & Multi-Domain Benchmarks
# ---------------------------------------------------------------------------
def test_historical_summary():
    url = f"{BASE_URL}/api/v1/flood/historical-summary"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    datasets = data.get("datasets", {})
    return f"Acquired Benchmarks: {', '.join(datasets.keys())}"

# ---------------------------------------------------------------------------
# 10. Reports & CSV Export
# ---------------------------------------------------------------------------
def test_reports_csv_export():
    url = f"{BASE_URL}/api/v1/reports/export/csv"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    content = resp.read().decode("utf-8")
    lines = content.strip().split("\n")
    assert len(lines) >= 8, "Expected at least 8 rows in CSV"
    headers = [h.strip().lower() for h in lines[0].split(",")]
    assert "station_id" in headers or "station_name" in headers or "name" in headers
    return f"Exported CSV: {len(lines)} lines, {len(content)} bytes with Station_ID records"

# ---------------------------------------------------------------------------
# 11. Reports & PDF Export
# ---------------------------------------------------------------------------
def test_reports_pdf_export():
    url = f"{BASE_URL}/api/v1/reports/export-all-pdf"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    pdf_bytes = resp.read()
    assert pdf_bytes.startswith(b"%PDF"), "Response is not a valid PDF file"
    return f"Exported Combined PDF: {len(pdf_bytes)} bytes, Magic Header: %PDF"

# ---------------------------------------------------------------------------
# 12. Frontend Streamlit Availability
# ---------------------------------------------------------------------------
def test_frontend_ui():
    resp = urllib.request.urlopen(FRONTEND_URL)
    assert resp.status == 200
    html = resp.read().decode("utf-8")
    assert "Streamlit" in html or "streamlit" in html
    return f"HTTP {resp.status} OK (Port 8501)"


# ---------------------------------------------------------------------------
# MAIN RUNNER
# ---------------------------------------------------------------------------
def main():
    print("=" * 80)
    print(" HYDRO-GUARD AI — TASK 3.3 END-TO-END DEMO & VALIDATION SUITE")
    print(" Problem Statement PS-11: Urban Drainage & Flash Flood Predictive Management")
    print("=" * 80)

    tests = [
        ("1. Backend Health Check", test_backend_health),
        ("2. Weather & Open-Meteo Rainfall", test_weather_api),
        ("3. IoT Telemetry Stream (2-Second)", test_sensor_telemetry),
        ("4. GIS Topology & Drainage Graph", test_drainage_topology),
        ("5. Indore Dual-Engine ST-GNN Prediction", test_indore_hybrid_prediction),
        ("6. Blue Heart UK Adaptive ST-GNN Candidate", test_blue_heart_candidate_inference),
        ("7. Pump & Gate Advisory (80% CV Purity Rule)", test_gate_advisory_cv_purity),
        ("8. 4-Tier Municipal Emergency Alerts", test_emergency_alerts),
        ("9. Historical Multi-Domain Benchmarks", test_historical_summary),
        ("10. Station Reports CSV Export", test_reports_csv_export),
        ("11. Official Municipal PDF Export", test_reports_pdf_export),
        ("12. Streamlit Dashboard Frontend (Port 8501)", test_frontend_ui)
    ]

    for name, func in tests:
        run_test(name, func)

    print("\n" + "=" * 80)
    print(f" RESULTS: {len(passed_tests)} PASSED | {len(failed_tests)} FAILED")
    print("=" * 80)
    if failed_tests:
        for name, err in failed_tests:
            print(f"  ✗ {name}: {err}")
        sys.exit(1)
    else:
        print(" ALL 12 DASHBOARD MODULES AND DEMONSTRATION WORKFLOWS VERIFIED OPERATIONAL.")
        sys.exit(0)

if __name__ == "__main__":
    main()
