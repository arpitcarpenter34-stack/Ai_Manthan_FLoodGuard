import requests
import json

res = requests.post("http://127.0.0.1:8000/api/v1/data-intel/indore_municipal/inference", json={"sample_index": 0})
d = res.json()
print("Top-level keys:", list(d.keys()))
if "nodes_breakdown" in d:
    print("nodes_breakdown first:", json.dumps(d["nodes_breakdown"][0], indent=2))
elif "nodes" in d:
    print("nodes first:", json.dumps(d["nodes"][0], indent=2))

