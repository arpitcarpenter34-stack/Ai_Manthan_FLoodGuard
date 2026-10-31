import requests

res = requests.post("http://127.0.0.1:8000/api/v1/data-intel/blue_heart/inference", json={"sample_index": 0})
print(f"Status code: {res.status_code}")
print(f"Response: {res.text[:400]}")

