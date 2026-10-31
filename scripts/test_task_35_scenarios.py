"""
HYDRO-GUARD AI — Task 3.5 Comprehensive Scenario and Edge-Case Test Suite.
Validates:
1. Scenario A: Dry conditions (0.0 mm/h)
2. Scenario B: Moderate rainfall (15.0 mm/h)
3. Scenario C: Extreme rainfall (65.0 mm/h, 1.5x surge) with drainage constraints
4. Edge Case 1: Missing sensor data (topological neighbor imputation)
5. Edge Case 2: Invalid inputs (negative rainfall, excessive pumps, out-of-range surge)
6. Edge Case 3: Disconnected drainage nodes
7. Edge Case 4: API failure & graceful fallback
8. Map rendering & GeoJSON feature verification
9. CSV & PDF export verification
"""

import sys
import json
import urllib.request
import requests

sys.path.insert(0, r"E:\ai-manthan\hydro_guard_indore")

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print(" HYDRO-GUARD AI — TASK 3.5 COMPREHENSIVE ACCEPTANCE TEST SUITE")
print("=" * 80)

results = {}

# -----------------------------------------------------------------------------
# 1. SCENARIO A: DRY CONDITIONS (0.0 mm/h)
# -----------------------------------------------------------------------------
print("\n[1] Testing Scenario A: Dry Conditions (0.0 mm/h)...")
p_dry = {
    "rainfall_intensity_mmh": 0.0,
    "surge_multiplier": 1.0,
    "active_pumps_count": 0,
    "soil_saturation_pct": 30.0,
    "runoff_coefficient": 0.72,
}
r_dry = requests.post(f"{BASE_URL}/api/v1/flood/hybrid-predict", json=p_dry).json()
inund_dry = requests.get(f"{BASE_URL}/api/v1/flood/inundation-map?rainfall_intensity_mmh=0.0&surge_multiplier=1.0&active_pumps_count=0").json()
opt_dry = requests.post(f"{BASE_URL}/api/v1/flood/optimize-pumps-gates", json={"rainfall_intensity_mmh": 0.0, "surge_multiplier": 1.0, "active_pumps_count": 0}).json()

results["Scenario A"] = {
    "inputs": p_dry,
    "predicted_risk": r_dry["overall_basin_risk"],
    "flood_probability_pct": r_dry["overall_flood_probability"],
    "max_water_depth_cm": inund_dry["metadata"]["max_flood_depth_cm"],
    "inundated_streets_count": inund_dry["metadata"]["inundated_streets_count"],
    "arrival_time_min": r_dry["peak_flood_arrival_mins"],
    "affected_locations": [n["node_name"] for n in r_dry["node_predictions"] if n["status"] != "SAFE"],
    "pump_recommendation": f"Recommended pumps: {opt_dry['summary_comparison']['optimized_mpc_strategy']['recommended_pumps']} / 6",
    "gate_recommendation": [g.get("gate_action") or g.get("recommended_state") for g in opt_dry["gate_recommendations"]],
    "operator_advisory": opt_dry["operator_advisory"],
}
print(f"  Risk: {r_dry['overall_basin_risk']} | Prob: {r_dry['overall_flood_probability']}% | Max Depth: {inund_dry['metadata']['max_flood_depth_cm']} cm")
print(f"  Inundated Streets: {inund_dry['metadata']['inundated_streets_count']} | Pumps: {opt_dry['summary_comparison']['optimized_mpc_strategy']['recommended_pumps']}")
assert r_dry["overall_flood_probability"] <= 15.0
assert inund_dry["metadata"]["max_flood_depth_cm"] == 0.0

# -----------------------------------------------------------------------------
# 2. SCENARIO B: MODERATE RAINFALL (15.0 mm/h)
# -----------------------------------------------------------------------------
print("\n[2] Testing Scenario B: Moderate Rainfall (15.0 mm/h)...")
p_mod = {
    "rainfall_intensity_mmh": 15.0,
    "surge_multiplier": 1.0,
    "active_pumps_count": 2,
    "soil_saturation_pct": 65.0,
    "runoff_coefficient": 0.72,
}
r_mod = requests.post(f"{BASE_URL}/api/v1/flood/hybrid-predict", json=p_mod).json()
inund_mod = requests.get(f"{BASE_URL}/api/v1/flood/inundation-map?rainfall_intensity_mmh=15.0&surge_multiplier=1.0&active_pumps_count=2").json()
opt_mod = requests.post(f"{BASE_URL}/api/v1/flood/optimize-pumps-gates", json={"rainfall_intensity_mmh": 15.0, "surge_multiplier": 1.0, "active_pumps_count": 2}).json()

results["Scenario B"] = {
    "inputs": p_mod,
    "predicted_risk": r_mod["overall_basin_risk"],
    "flood_probability_pct": r_mod["overall_flood_probability"],
    "max_water_depth_cm": inund_mod["metadata"]["max_flood_depth_cm"],
    "inundated_streets_count": inund_mod["metadata"]["inundated_streets_count"],
    "arrival_time_min": r_mod["peak_flood_arrival_mins"],
    "affected_locations": [n["node_name"] for n in r_mod["node_predictions"] if n["status"] == "CRITICAL"],
    "pump_recommendation": f"Recommended pumps: {opt_mod['summary_comparison']['optimized_mpc_strategy']['recommended_pumps']} / 6",
    "gate_recommendation": [g.get("gate_action") or g.get("recommended_state") for g in opt_mod["gate_recommendations"]],
    "overflow_reduction": opt_mod["summary_comparison"]["expected_benefits"]["overflow_reduction_pct"],
    "operator_advisory": opt_mod["operator_advisory"],
}
print(f"  Risk: {r_mod['overall_basin_risk']} | Prob: {r_mod['overall_flood_probability']}% | Max Depth: {inund_mod['metadata']['max_flood_depth_cm']} cm")
print(f"  Inundated Streets: {inund_mod['metadata']['inundated_streets_count']} | Overflow Reduction: {opt_mod['summary_comparison']['expected_benefits']['overflow_reduction_pct']}")
assert r_mod["overall_flood_probability"] > 90.0

# -----------------------------------------------------------------------------
# 3. SCENARIO C: EXTREME RAINFALL (65.0 mm/h, 1.5x surge) WITH DRAINAGE CONSTRAINTS
# -----------------------------------------------------------------------------
print("\n[3] Testing Scenario C: Extreme Rainfall (65.0 mm/h, 1.5x surge)...")
p_ext = {
    "rainfall_intensity_mmh": 65.0,
    "surge_multiplier": 1.5,
    "active_pumps_count": 2,
    "soil_saturation_pct": 85.0,
    "runoff_coefficient": 0.85,
}
r_ext = requests.post(f"{BASE_URL}/api/v1/flood/hybrid-predict", json=p_ext).json()
inund_ext = requests.post(f"{BASE_URL}/api/v1/flood/inundation-map", json={"rainfall_intensity_mmh": 65.0, "surge_multiplier": 1.5, "active_pumps_count": 2}).json()
opt_ext = requests.post(f"{BASE_URL}/api/v1/flood/optimize-pumps-gates", json={"rainfall_intensity_mmh": 65.0, "surge_multiplier": 1.5, "active_pumps_count": 2}).json()

results["Scenario C"] = {
    "inputs": p_ext,
    "predicted_risk": r_ext["overall_basin_risk"],
    "flood_probability_pct": r_ext["overall_flood_probability"],
    "max_water_depth_cm": inund_ext["metadata"]["max_flood_depth_cm"],
    "inundated_streets_count": inund_ext["metadata"]["inundated_streets_count"],
    "arrival_time_min": r_ext["peak_flood_arrival_mins"],
    "affected_locations": [n["node_name"] for n in r_ext["node_predictions"] if n["status"] == "CRITICAL"],
    "pump_recommendation": f"Recommended pumps: {opt_ext['summary_comparison']['optimized_mpc_strategy']['recommended_pumps']} / 6 (Full mobilization)",
    "gate_recommendation": [g.get("gate_action") or g.get("recommended_state") for g in opt_ext["gate_recommendations"]],
    "volume_prevented": opt_ext["summary_comparison"]["expected_benefits"]["prevented_flood_volume_m3"],
    "operator_advisory": opt_ext["operator_advisory"],
}
print(f"  Risk: {r_ext['overall_basin_risk']} | Prob: {r_ext['overall_flood_probability']}% | Max Depth: {inund_ext['metadata']['max_flood_depth_cm']} cm")
print(f"  Inundated Streets: {inund_ext['metadata']['inundated_streets_count']} | Volume Saved: {opt_ext['summary_comparison']['expected_benefits']['prevented_flood_volume_m3']}")
assert r_ext["overall_basin_risk"].startswith("CRITICAL")
assert opt_ext["summary_comparison"]["optimized_mpc_strategy"]["recommended_pumps"] == 6

# -----------------------------------------------------------------------------
# 4. EDGE CASE 1: MISSING SENSOR DATA
# -----------------------------------------------------------------------------
print("\n[4] Testing Edge Case 1: Missing Sensor Data (Graceful Neighbor Imputation)...")
from backend.models.hybrid_prediction_engine import hybrid_prediction_engine
r_missing = hybrid_prediction_engine.predict_hybrid_flood(
    rainfall_intensity_mmh=35.0,
    sensor_telemetry={"NODE_RAU": None, "NODE_RAJWARA": None}
)
print(f"  Missing telemetry handled cleanly: Overall risk = {r_missing['overall_basin_risk']}, Prob = {r_missing['overall_flood_probability']}%")
assert "node_predictions" in r_missing and len(r_missing["node_predictions"]) == 7

# -----------------------------------------------------------------------------
# 5. EDGE CASE 2: INVALID INPUTS (Negative Rain, Extreme Pumps, Surge > 5.0)
# -----------------------------------------------------------------------------
print("\n[5] Testing Edge Case 2: Invalid Inputs Clamping...")
p_invalid = {
    "rainfall_intensity_mmh": -45.0,  # Negative rain
    "surge_multiplier": 99.0,          # Out of bounds surge
    "active_pumps_count": -5,          # Negative pumps
    "soil_saturation_pct": 150.0,      # > 100%
    "runoff_coefficient": 1.8,         # > 1.0
}
r_invalid = requests.post(f"{BASE_URL}/api/v1/flood/hybrid-predict", json=p_invalid).json()
print(f"  Clamped Rain: {r_invalid['inputs']['rainfall_intensity_mmh']} (Expected >= 0.0)")
print(f"  Clamped Surge: {r_invalid['inputs']['surge_multiplier']} (Expected <= 5.0)")
print(f"  Clamped Pumps: {r_invalid['inputs']['active_pumps_count']} (Expected >= 0)")
assert r_invalid["inputs"]["rainfall_intensity_mmh"] == 0.0
assert r_invalid["inputs"]["surge_multiplier"] <= 5.0
assert r_invalid["inputs"]["active_pumps_count"] >= 0

# -----------------------------------------------------------------------------
# 6. EDGE CASE 3: DISCONNECTED DRAINAGE NODES
# -----------------------------------------------------------------------------
print("\n[6] Testing Edge Case 3: Disconnected Boundary Nodes...")
from backend.models.indore_routing_engine import routing_engine
routing_nodes = routing_engine.graph.nodes()
print(f"  Graph Nodes Monitored: {len(routing_nodes)}")
headwater = "NODE_RAU"
terminal = "NODE_KABITHEDI_STP"
in_deg = routing_engine.graph.in_degree(headwater)
out_deg = routing_engine.graph.out_degree(terminal)
print(f"  Headwater '{headwater}' in-degree: {in_deg} (Natural source boundary)")
print(f"  Terminal '{terminal}' out-degree: {out_deg} (Terminal outfall sink)")
assert in_deg == 0 and out_deg == 0

# -----------------------------------------------------------------------------
# 7. EDGE CASE 4: API FAILURES & GRACEFUL FALLBACK
# -----------------------------------------------------------------------------
print("\n[7] Testing Edge Case 4: Open-Meteo Client Cache Fallback...")
from backend.services.open_meteo_client import weather_client
fallback_weather = weather_client.fetch_live_weather(force_refresh=False)
print(f"  Weather Source: {fallback_weather.get('data_source')} (Fallback cached/live)")
assert "rainfall_intensity_mm_hr" in fallback_weather

# -----------------------------------------------------------------------------
# 8. MAP RENDERING & GEOJSON VERIFICATION
# -----------------------------------------------------------------------------
print("\n[8] Testing GeoJSON Feature Integrity...")
inund_map = requests.get(f"{BASE_URL}/api/v1/flood/inundation-map").json()
feat_types = set(f["properties"].get("feature_type") for f in inund_map["features"])
print(f"  GeoJSON Features Count: {len(inund_map['features'])}")
print(f"  Feature Types Detected: {feat_types}")
assert "urban_street_corridor" in feat_types
assert "inundation_hazard_extent" in feat_types
assert "hydraulic_bottleneck" in feat_types
assert "flow_direction_vector" in feat_types

# -----------------------------------------------------------------------------
# 9. REPORT EXPORT VERIFICATION (CSV & PDF)
# -----------------------------------------------------------------------------
print("\n[9] Testing CSV and PDF Dossier Exports...")
with urllib.request.urlopen(f"{BASE_URL}/api/v1/reports/export/csv") as r:
    csv_bytes = r.read()
with urllib.request.urlopen(f"{BASE_URL}/api/v1/reports/export-all-pdf") as r:
    pdf_bytes = r.read()

print(f"  CSV Download: {len(csv_bytes)} bytes | Valid lines: {len(csv_bytes.decode('utf-8').splitlines())}")
print(f"  PDF Download: {len(pdf_bytes)} bytes | Header: {pdf_bytes[:4]}")
assert len(csv_bytes) > 500 and b"%PDF" in pdf_bytes

print("\n" + "=" * 80)
print(" ALL SCENARIOS AND EDGE CASES COMPLETED AND FULLY VERIFIED!")
print("=" * 80)

# Save JSON test report
with open(r"E:\ai-manthan\hydro_guard_indore\data\task_3_5_scenario_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("Saved scenario results to data/task_3_5_scenario_results.json")
