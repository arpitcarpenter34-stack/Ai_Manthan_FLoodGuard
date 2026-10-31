import os
import sys

file_path = r"E:\ai-manthan\hydro_guard_indore\backend\api\flood_routes.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import_target = "from backend.simulators.sensor_stream_sim import sensor_simulator"
import_replacement = "from backend.simulators.sensor_stream_sim import sensor_simulator\nfrom backend.models.blue_heart_st_gnn import blue_heart_st_gnn"

if "from backend.models.blue_heart_st_gnn import blue_heart_st_gnn" not in content:
    content = content.replace(import_target, import_replacement, 1)

endpoint_code = """

@router.get("/blue-heart/benchmark", summary="Get Task 3.2 Blue Heart ST-GNN Benchmark Results")
def get_blue_heart_benchmark() -> Dict[str, Any]:
    \"\"\"Returns the validated Task 3.2 multi-model benchmark results on real Blue Heart road gully telemetry.\"\"\"
    return blue_heart_st_gnn.get_benchmark_metadata()


@router.post("/blue-heart/predict", summary="Run Adaptive Gated ST-GNN Inundation Prediction on Blue Heart Gully")
def predict_blue_heart(test_index: int = Query(0, ge=0, description="Held-out test sequence index (0 to 1092)")) -> Dict[str, Any]:
    \"\"\"Runs forward inference using the Task 3.2 Adaptive Gated ST-GNN candidate on a real held-out test sample.\"\"\"
    return blue_heart_st_gnn.predict_sample(test_index=test_index)
"""

if "/blue-heart/benchmark" not in content:
    content += endpoint_code

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully added Blue Heart endpoints to flood_routes.py")

