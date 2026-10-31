import requests
import json

res = requests.post("http://127.0.0.1:8000/api/v1/data-intel/blue_heart/inference", json={"sample_index": 0})
d = res.json()
print("sequence_performance:", json.dumps(d.get("sequence_performance"), indent=2))
print("First item in nodes_breakdown:", json.dumps(d.get("nodes_breakdown", [{}])[0], indent=2))

