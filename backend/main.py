"""
Primary FastAPI Application for HYDRO-GUARD AI.
Tailored for the City of Indore (Madhya Pradesh).
Integrates live Open-Meteo weather, NetworkX topological routing, OpenCV water purity,
Librosa acoustic level detection, and 2-second background telemetry streaming.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

import config
from backend.api import (
    flood_router,
    sensor_router,
    report_router,
    model_intel_router,
    dataset_intel_router,
    blockage_router,
)
from backend.simulators.sensor_stream_sim import sensor_simulator
from backend.models.cv_purity_detector import cv_detector
from backend.models.acoustic_level_ai import acoustic_ai
from backend.services.db_manager import db_manager


def populate_initial_samples() -> None:
    """Pre-generate sample audio waveforms and CV camera frames for immediate evaluation."""
    try:
        # Pre-generate sample sewer audio files (WAV)
        clean_wav = acoustic_ai.generate_synthetic_sewer_audio(
            target_level_pct=25.0, duration_sec=3.0, filename="trickle_flow_25pct.wav"
        )
        moderate_wav = acoustic_ai.generate_synthetic_sewer_audio(
            target_level_pct=60.0, duration_sec=3.0, filename="moderate_surge_60pct.wav"
        )
        surge_wav = acoustic_ai.generate_synthetic_sewer_audio(
            target_level_pct=92.0, duration_sec=3.0, filename="critical_flash_surge_92pct.wav"
        )

        # Generate sample camera frames only if genuine real-world drain photos do not exist
        import cv2
        clean_path = config.SAMPLE_IMAGE_DIR / "clean_rainwater.jpg"
        polluted_path = config.SAMPLE_IMAGE_DIR / "polluted_sludge.jpg"
        borderline_path = config.SAMPLE_IMAGE_DIR / "borderline_runoff.jpg"

        if not clean_path.exists():
            clean_img = cv_detector.generate_synthetic_drain_frame("clean_rainwater")
            cv2.imwrite(str(clean_path), clean_img)
        if not polluted_path.exists():
            polluted_img = cv_detector.generate_synthetic_drain_frame("polluted_sludge")
            cv2.imwrite(str(polluted_path), polluted_img)
        if not borderline_path.exists():
            borderline_img = cv_detector.generate_synthetic_drain_frame("borderline_runoff")
            cv2.imwrite(str(borderline_path), borderline_img)
    except Exception as e:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: Start background telemetry simulator, initialize SQLite DB, and preload assets."""
    db_manager.init_db()
    populate_initial_samples()
    sensor_simulator.start()
    yield
    sensor_simulator.stop()


app = FastAPI(
    title="HYDRO-GUARD AI: Indore Drainage, Flood & Water Quality Management",
    description="High-frequency urban hydrology and edge AI platform for Indore Municipal Corporation (IMC).",
    version="1.0.0",
    lifespan=lifespan,
)

# Environment-based Cross-Origin Resource Sharing (CORS) configuration
allow_creds = "*" not in config.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?:\/\/.*\.vercel\.app$",
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for frontend assets
static_dir = config.BASE_DIR / "frontend" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount sample audio and images for client playback and inspection
sample_audio_dir = config.DATA_DIR / "sample_audio"
sample_img_dir = config.DATA_DIR / "sample_images"
if sample_audio_dir.exists():
    app.mount("/samples/audio", StaticFiles(directory=str(sample_audio_dir)), name="sample_audio")
if sample_img_dir.exists():
    app.mount("/samples/images", StaticFiles(directory=str(sample_img_dir)), name="sample_images")

# Mount API Routers
app.include_router(flood_router)
app.include_router(sensor_router)
app.include_router(report_router)
app.include_router(model_intel_router)
app.include_router(dataset_intel_router)
app.include_router(blockage_router)


@app.get("/", summary="System Root & Hydrological Info")
def root_info(request: Request):
    """
    If requested from a web browser (Accept: text/html), serve the reference-matched FloodGuard web UI.
    If requested by API clients, tests, or JSON callers, return system JSON.
    """
    accept = request.headers.get("accept", "")
    html_file = static_dir / "index.html"
    if "text/html" in accept and html_file.exists():
        return FileResponse(str(html_file))

    return {
        "system": "HYDRO-GUARD AI",
        "branding": "FLOODGUARD AI",
        "subtitle": "Urban Drainage Intelligence",
        "city": "Indore, Madhya Pradesh",
        "governing_body": "Indore Municipal Corporation (IMC)",
        "elevation_drop_msl": {
            "south_headwaters_rau": f"{config.INDORE_MAX_MSL_ELEVATION} m",
            "north_outfall_kabithedi": f"{config.INDORE_MIN_MSL_ELEVATION} m",
            "net_gradient_drop": f"{config.INDORE_MAX_MSL_ELEVATION - config.INDORE_MIN_MSL_ELEVATION} m",
        },
        "rivers_monitored": ["Khan (Kahn) River", "Saraswati River"],
        "critical_nodes_monitored": len(config.DRAINAGE_NODES),
        "status": "OPERATIONAL",
        "endpoints": {
            "web_ui": "/",
            "docs": "/docs",
            "current_levels": "/api/v1/flood/current-levels",
            "live_rainfall": "/api/v1/flood/rainfall",
            "flood_prediction": "/api/v1/flood/predict",
            "environmental_summary": "/api/v1/flood/environmental-summary",
            "ml_model_info": "/api/v1/flood/ml-model/info",
            "ml_predict": "/api/v1/flood/ml-predict",
            "cv_purity_check": "/api/v1/sensors/cv-purity/analyze",
            "acoustic_level_check": "/api/v1/sensors/acoustic-level/analyze",
            "telemetry_stream": "/api/v1/sensors/telemetry/live",
        },
    }


@app.get("/app", summary="Direct Web Application UI")
def direct_web_ui():
    """Direct route to access the interactive single-page application."""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return FileResponse(str(html_file))
    return {"message": "Web UI frontend compiling..."}


@app.get("/health", summary="Health check endpoint")
def health_check():
    """Verify backend and background simulator health."""
    return {
        "status": "HEALTHY",
        "simulator_running": sensor_simulator.is_running,
        "nodes_online": len(config.DRAINAGE_NODES),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

