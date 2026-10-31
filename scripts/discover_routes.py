import sys
from pathlib import Path

ROOT = Path("E:/ai-manthan/hydro_guard_indore")
sys.path.insert(0, str(ROOT))

from backend.api import flood_router, sensor_router, report_router, model_intel_router, dataset_intel_router

routers = [
    ("flood_router", flood_router),
    ("sensor_router", sensor_router),
    ("report_router", report_router),
    ("model_intel_router", model_intel_router),
    ("dataset_intel_router", dataset_intel_router),
]

for name, router in routers:
    print(f"\n=== ROUTER: {name} (prefix='{router.prefix}') ===")
    for r in router.routes:
        methods = getattr(r, "methods", None)
        path = getattr(r, "path", None)
        endpoint = getattr(r, "endpoint", None)
        func_name = getattr(endpoint, "__name__", str(endpoint))
        print(f"  {methods} {router.prefix}{path} -> {func_name}")
