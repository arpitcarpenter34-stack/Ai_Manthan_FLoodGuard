"""
Test live Task 3.5 API endpoints on http://127.0.0.1:8000
"""
import requests
import json

base_url = "http://127.0.0.1:8000"

# 1. Inundation Map GET
r1 = requests.get(f"{base_url}/api/v1/flood/inundation-map?rainfall_intensity_mmh=35.0")
assert r1.status_code == 200, f"Error {r1.status_code}: {r1.text}"
d1 = r1.json()
print("1. Inundation Map GET: SUCCESS")
print(f"   Features: {len(d1['features'])}, Inundated Streets: {d1['metadata']['inundated_streets_count']}, Max Depth: {d1['metadata']['max_flood_depth_cm']} cm")
print(f"   Bottlenecks: {len(d1['bottlenecks'])}")

# 2. Inundation Map POST
r2 = requests.post(f"{base_url}/api/v1/flood/inundation-map", json={"rainfall_intensity_mmh": 65.0, "surge_multiplier": 1.5, "active_pumps_count": 2})
assert r2.status_code == 200
d2 = r2.json()
print("2. Inundation Map POST: SUCCESS")
print(f"   Extreme Inundated Streets: {d2['metadata']['inundated_streets_count']}, Max Depth: {d2['metadata']['max_flood_depth_cm']} cm")

# 3. Optimize Pumps Gates POST
r3 = requests.post(f"{base_url}/api/v1/flood/optimize-pumps-gates", json={"rainfall_intensity_mmh": 35.0, "surge_multiplier": 1.0, "active_pumps_count": 2})
assert r3.status_code == 200
d3 = r3.json()
print("3. Optimize Pumps Gates POST: SUCCESS")
print(f"   Recommended Pumps: {d3['summary_comparison']['optimized_mpc_strategy']['recommended_pumps']}")
print(f"   Overflow Reduction: {d3['summary_comparison']['expected_benefits']['overflow_reduction_pct']}")
print(f"   Volume Prevented: {d3['summary_comparison']['expected_benefits']['prevented_flood_volume_m3']}")
print(f"   Operator Advisory: '{d3['operator_advisory']}'")

# 4. Pump Optimization State GET
r4 = requests.get(f"{base_url}/api/v1/flood/pump-optimization-state")
assert r4.status_code == 200
d4 = r4.json()
print("4. Pump Optimization State GET: SUCCESS")

# 5. Hybrid Predict POST
r5 = requests.post(f"{base_url}/api/v1/flood/hybrid-predict", json={"rainfall_intensity_mmh": 35.0, "surge_multiplier": 1.0, "active_pumps_count": 2})
assert r5.status_code == 200
d5 = r5.json()
print("5. Hybrid Predict POST: SUCCESS")
print(f"   Risk: {d5['overall_basin_risk']}")
print(f"   Street Summary Inundated: {d5['street_inundation_summary']['inundated_streets_count']}")
print(f"   Node 0 CI: {d5['node_predictions'][0]['confidence_interval_90_depth_cm']}")
print(f"   Node 0 Streets: {d5['node_predictions'][0]['affected_street_corridors']}")

print("\nALL 5 ENDPOINTS TESTED LIVE AND VERIFIED!")

