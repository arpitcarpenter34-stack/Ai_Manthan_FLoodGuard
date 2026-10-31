import requests
import json

res = requests.post("http://127.0.0.1:8000/api/v1/data-intel/blue_heart/inference", json={"sample_index": 0})
d = res.json()
print("Top-level keys:", list(d.keys()))
print("Status:", d.get("status"))
if "nodes" in d:
    print("Nodes count:", len(d["nodes"]))
    print("First node:", json.dumps(d["nodes"][0], indent=2))
else:
    print("No nodes key!")

