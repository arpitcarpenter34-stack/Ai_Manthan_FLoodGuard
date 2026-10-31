import urllib.request
import json
import sys
sys.path.insert(0, r"E:\ai-manthan\hydro_guard_indore")

# 1. Check Module 6
from frontend.components.map_visualizer import IndoreMapVisualizer
mv = IndoreMapVisualizer()
m = mv.create_folium_map()
print("[Module 6] create_folium_map success:", m is not None)

# 2. Check Module 7
from backend.services.osmnx_gis_loader import indore_gis_loader
methods = [m for m in dir(indore_gis_loader) if "profile" in m.lower() or "reach" in m.lower()]
print("[Module 7] methods in indore_gis_loader:", methods)

# 3. Check Module 8
url = "http://127.0.0.1:8000/api/v1/sensors/cv-purity/analyze"
p1 = json.dumps({"turbidity_ntu": 8.0, "total_suspended_solids_mg_l": 15.0, "chemical_oxygen_demand_mg_l": 30.0}).encode()
with urllib.request.urlopen(urllib.request.Request(url, data=p1, headers={"Content-Type": "application/json"})) as r:
    data8 = json.loads(r.read().decode())
print("[Module 8] keys in cv-purity response:", list(data8.keys()))
print("[Module 8] purity score:", data8.get("purity_score"), "action:", data8.get("sluice_gate_action"))

# 4. Check Module 12
url12 = "http://127.0.0.1:8000/api/v1/flood/blue-heart/benchmark"
with urllib.request.urlopen(url12) as r:
    data12 = json.loads(r.read().decode())
print("[Module 12] keys in benchmark response:", list(data12.keys()))
print("[Module 12] candidate_models keys:", list(data12.get("candidate_models", {}).keys()))

