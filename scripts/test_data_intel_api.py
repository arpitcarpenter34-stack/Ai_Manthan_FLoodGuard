"""
Test script for Data Intelligence & Live Inference endpoints.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/data-intel"

tests = [
    ("GET", "/registry", None),
    ("GET", "/weather-radar", None),
    ("GET", "/blue_heart/observations", None),
    ("GET", "/camels_hourly/observations", None),
    ("GET", "/blue_heart/distributions", None),
    ("GET", "/blue_heart/correlations", None),
    ("POST", "/blue_heart/inference", {"sample_index": 5}),
    ("POST", "/indore_municipal/inference", {"sample_index": 2}),
    ("POST", "/camels_hourly/inference", {"sample_index": 0}),
    ("POST", "/what-if", {
        "rainfall_intensity_mmh": 55.0,
        "soil_saturation_pct": 75.0,
        "active_pumps": 3,
        "cumulative_rain_mm": 45.0
    })
]

print("=" * 75)
print(" TESTING DATA INTELLIGENCE & INFERENCE API ENDPOINTS")
print("=" * 75)

all_passed = True
for method, endpoint, payload in tests:
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json=payload, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            keys = list(data.keys())
            status_val = data.get("status", "OK")
            print(f"[PASS] {method} {endpoint} -> HTTP 200 (Status: {status_val}, Keys: {keys[:3]})")
        else:
            print(f"[FAIL] {method} {endpoint} -> HTTP {resp.status_code}: {resp.text[:80]}")
            all_passed = False
    except Exception as e:
        print(f"[ERROR] {method} {endpoint} -> {e}")
        all_passed = False

if all_passed:
    print("\n>>> ALL DATA INTELLIGENCE API ENDPOINTS PASSED! <<<")
else:
    print("\n>>> FAILURES DETECTED <<<")

