"""
Verification script for Model Intelligence & Explainability API endpoints.
Tests all 6 new Task 3.8 endpoints.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/model-intel"

endpoints = [
    ("/lineage", "GET", None),
    ("/training-curves", "GET", None),
    ("/evaluation", "GET", None),
    ("/feature-importance", "GET", None),
    ("/what-if", "POST", {
        "rainfall_intensity_mmh": 45.0,
        "soil_saturation_pct": 70.0,
        "active_pumps": 3,
        "cumulative_rain_mm": 50.0
    }),
    ("/dataset-explorer", "GET", None)
]

print("=" * 70)
print(" TESTING TASK 3.8 MODEL INTELLIGENCE API ENDPOINTS")
print("=" * 70)

all_passed = True

for path, method, payload in endpoints:
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json=payload, timeout=5)

        status = resp.status_code
        if status == 200:
            data = resp.json()
            keys = list(data.keys())
            print(f"[PASS] {method} {path} -> HTTP 200 (Keys: {keys[:4]}...)")
        else:
            print(f"[FAIL] {method} {path} -> HTTP {status}: {resp.text[:100]}")
            all_passed = False
    except Exception as e:
        print(f"[ERROR] {method} {path} -> {e}")
        all_passed = False

if all_passed:
    print("\n>>> ALL 6 MODEL INTELLIGENCE ENDPOINTS PASSED VALIDATION! <<<")
else:
    print("\n>>> SOME ENDPOINTS FAILED <<<")

