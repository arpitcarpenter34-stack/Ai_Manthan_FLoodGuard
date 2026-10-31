import sys
import urllib.request
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Wait for server ready
url = "http://127.0.0.1:8000/api/v1/reports/stations?page_size=20"
for _ in range(15):
    try:
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode("utf-8"))
        break
    except Exception:
        time.sleep(1)
else:
    print("Server failed to respond within 15 seconds")
    sys.exit(1)

# Check summary metrics
summary_url = "http://127.0.0.1:8000/api/v1/reports/summary"
req_sum = urllib.request.urlopen(summary_url)
sum_data = json.loads(req_sum.read().decode("utf-8"))

print("=" * 80)
print(f"VERIFYING 7 DRAIN CARDS & SUMMARY METRICS FROM API")
print("=" * 80)
print("Summary Metrics:", json.dumps(sum_data.get("metrics"), indent=2))
print(f"\nTotal Stations Returned: {data.get('total_count')}\n")

outlet_counts = {}
quality_counts = {}

for s in data.get("stations", []):
    code = s.get("display_code")
    name = s.get("station_name")
    node = s.get("node_id")
    q_stat = s.get("quality_status")
    q_color = s.get("quality_color")
    turb = s.get("turbidity_measurement")
    purity = s.get("purity_score_pct")
    treat = s.get("treatment_route")
    outlet_stat = s.get("outlet_status")
    outlet_code = s.get("outlet_code")
    outlet_color = s.get("outlet_color")
    outlet_sim = s.get("outlet_is_simulated")
    assessment = s.get("ai_assessment")

    outlet_counts[outlet_code] = outlet_counts.get(outlet_code, 0) + 1
    quality_counts[q_stat] = quality_counts.get(q_stat, 0) + 1

    print(f"[{code}] {name} ({node}):")
    print(f"   • Quality Status:   {q_stat} (Color: {q_color}) | Purity: {purity}%")
    print(f"   • Turbidity:        {turb.get('value')} NTU (Acceptable: {turb.get('is_acceptable')})")
    print(f"   • Treatment Route:  {treat}")
    print(f"   • Main Outlet:      {outlet_stat} (Code: {outlet_code}, Color: {outlet_color})")
    print(f"   • AI Assessment:    {assessment}")
    print("-" * 80)

print("\nQuality Status Distribution:")
for k, v in quality_counts.items():
    print(f"   • {k}: {v} drain(s)")

print("\nOutlet Code Distribution:")
for k, v in outlet_counts.items():
    print(f"   • {k}: {v} drain(s)")

# Acceptance Assertions
assert data.get("total_count") == 7, "Must return exactly 7 drains!"
assert quality_counts.get("FAIL", 0) == 7, f"Expected 7 FAIL due to dirty urban water, got {quality_counts.get('FAIL')}"
assert quality_counts.get("PASS", 0) == 0, f"Cannot have false PASS on dirty water! Got {quality_counts.get('PASS')}"
assert sum_data.get("metrics", {}).get("fail_count") == 7, "Summary metric fail_count must be 7"
assert sum_data.get("metrics", {}).get("pass_count") == 0, "Summary metric pass_count must be 0"
assert outlet_counts.get("NOT_CONFIGURED", 0) == 3, f"Expected 3 NOT CONFIGURED, got {outlet_counts.get('NOT_CONFIGURED')}"
assert outlet_counts.get("PARTIALLY_OPEN", 0) == 1, f"Expected 1 PARTIALLY OPEN, got {outlet_counts.get('PARTIALLY_OPEN')}"
assert outlet_counts.get("CLOSED", 0) == 1, f"Expected 1 CLOSED, got {outlet_counts.get('CLOSED')}"
assert outlet_counts.get("BLOCKED", 0) == 1, f"Expected 1 BLOCKED, got {outlet_counts.get('BLOCKED')}"
assert outlet_counts.get("UNKNOWN", 0) == 1, f"Expected 1 UNKNOWN, got {outlet_counts.get('UNKNOWN')}"

print("\n>>> ALL 7 DRAIN RECORD ACCEPTANCE TESTS PASSED (100% SUCCESS) <<<")
