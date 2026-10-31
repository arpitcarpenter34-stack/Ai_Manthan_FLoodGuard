"""
API routers for HYDRO-GUARD AI FastAPI backend.
"""

from .flood_routes import router as flood_router
from .sensor_routes import router as sensor_router
from .report_routes import router as report_router
from .model_intel_routes import router as model_intel_router
from .dataset_intelligence_routes import router as dataset_intel_router

__all__ = ["flood_router", "sensor_router", "report_router", "model_intel_router", "dataset_intel_router"]

