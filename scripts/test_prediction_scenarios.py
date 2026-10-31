import urllib.request
import json

scenarios = [
    ("Dry weather (0 mm/h)", {
        "rainfall_intensity_mmh": 0.0,
        "surge_multiplier": 1.0,
        "active_pumps_count": 2,
        "soil_saturation_pct": 30.0,
        "runoff_coefficient": 0.72
    }),
    ("Light rain (5 mm/h)", {
        "rainfall_intensity_mmh": 5.0,
        "surge_multiplier": 1.0,
        "active_pumps_count": 2,
        "soil_saturation_pct": 40.0,
        "runoff_coefficient": 0.72
    }),
    ("Moderate rain (15 mm/h)", {
        "rainfall_intensity_mmh": 15.0,
        "surge_multiplier": 1.0,
        "active_pumps_count": 2,
        "soil_saturation_pct": 50.0,
        "runoff_coefficient": 0.72
    }),
    ("Heavy rain (65 mm/h)", {
        "rainfall_intensity_mmh": 65.0,
        "surge_multiplier": 1.5,
        "active_pumps_count": 2,
        "soil_saturation_pct": 75.0,
        "runoff_coefficient": 0.72
    }),
]

for name, payload in scenarios:
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/flood/hybrid-predict",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    print(f"\n=======================================================")
    print(f" SCENARIO: {name}")
    print(f"=======================================================")
    print(f"Input Rain: {payload['rainfall_intensity_mmh']} mm/h | Surge: {payload['surge_multiplier']}x | Pumps: {payload['active_pumps_count']}")
    print(f"Overall Basin Risk: {res.get('overall_basin_risk')}")
    print(f"Overall Flood Probability: {res.get('overall_flood_probability')}%")
    print(f"Peak Flood Arrival: {res.get('peak_flood_arrival_mins')} mins")
    print(f"Peak Choke Point: {res.get('peak_choke_point')}")
    print(f"Critical Nodes: {res.get('critical_nodes_count')} | Warning Nodes: {res.get('warning_nodes_count')}")
    print(f"Recommended Action: {res.get('recommended_action')}")
    print("\nNode Breakdown:")
    for n in res.get("node_predictions", []):
        st = n.get("status")
        score = n.get("hybrid_flood_risk_score")
        depth = n.get("inundation_depth_cm")
        arr = n.get("peak_flood_arrival_mins")
        p_lvl = n.get("hydraulic_physics", {}).get("water_level_pct")
        q = n.get("hydraulic_physics", {}).get("discharge_m3_s")
        g_prob = n.get("st_gnn_prediction", {}).get("probability_pct")
        print(f"  [{st:8s}] {n['node_id']} ({n['node_name']}): RiskScore={score:5.1f}% | Depth={depth:4.1f}cm | Arr={arr:4.1f}m | PhysLevel={p_lvl:5.1f}% | Q={q:5.1f}m3/s | GNN_prob={g_prob:5.1f}%")
