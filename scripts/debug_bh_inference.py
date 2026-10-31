import sys
sys.path.insert(0, ".")
from backend.services.dataset_intelligence_service import dataset_intel_service
import traceback

try:
    res = dataset_intel_service.execute_dataset_inference("blue_heart", 5)
    print("SUCCESS keys:", list(res.keys()))
except Exception as e:
    traceback.print_exc()
