"""
API routers for HYDRO-GUARD AI FastAPI backend.
"""

from .flood_routes import router as flood_router
from .sensor_routes import router as sensor_router
from .report_routes import router as report_router

__all__ = ["flood_router", "sensor_router", "report_router"]

