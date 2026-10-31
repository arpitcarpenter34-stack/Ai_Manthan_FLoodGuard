"""
Configuration and constants for HYDRO-GUARD AI (Indore Municipal Corporation Edition).
Models Indore's south-to-north elevation drop, hydrological parameters, river topology,
and operational threshold rules.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GIS_DIR = DATA_DIR / "indore_gis"
SAMPLE_AUDIO_DIR = DATA_DIR / "sample_audio"
SAMPLE_IMAGE_DIR = DATA_DIR / "sample_images"

# Centralized SQLite Database Path Configuration
# Default: data/hydro_guard.db (repository seed database)
# Persistent Mount (e.g. Render Persistent Disk): Set HYDRO_GUARD_DB_PATH=/var/data/hydro_guard.db
SEED_DB_PATH = DATA_DIR / "hydro_guard.db"
_env_db_path = os.getenv("HYDRO_GUARD_DB_PATH", "").strip()
if _env_db_path:
    DB_PATH = Path(_env_db_path)
else:
    DB_PATH = SEED_DB_PATH

# Ensure data directories and database parent directory exist
for path in [DATA_DIR, GIS_DIR, SAMPLE_AUDIO_DIR, SAMPLE_IMAGE_DIR, DB_PATH.parent]:
    path.mkdir(parents=True, exist_ok=True)

# Geographic Coordinates & Topography for Indore, Madhya Pradesh
INDORE_CENTER_LAT = 22.7196
INDORE_CENTER_LON = 75.8577
INDORE_MAX_MSL_ELEVATION = 560.0  # Rau / South ridge (meters above MSL)
INDORE_MIN_MSL_ELEVATION = 515.0  # Kabithedi STP / Northern river outfall

# Core Drainage & River Network Nodes
# Indore drainage flows predominantly from South (high elevation) to North (low elevation)
DRAINAGE_NODES = {
    "NODE_RAU": {
        "id": "NODE_RAU",
        "name": "Rau Headwaters",
        "hindi_name": "राऊ उद्गम क्षेत्र",
        "lat": 22.6450,
        "lon": 75.8180,
        "elevation_m": 560.0,
        "catchment_km2": 18.5,
        "max_capacity_m3_s": 45.0,
        "type": "headwater",
        "river": "Saraswati Tributary",
    },
    "NODE_BHANWARKUAN": {
        "id": "NODE_BHANWARKUAN",
        "name": "Bhanwarkuan Storm Junction",
        "hindi_name": "भंवरकुआं स्टॉर्म जंक्शन",
        "lat": 22.6891,
        "lon": 75.8653,
        "elevation_m": 552.0,
        "catchment_km2": 24.0,
        "max_capacity_m3_s": 65.0,
        "type": "major_feeder",
        "river": "Khan River Feeder",
    },
    "NODE_RAMBAGH": {
        "id": "NODE_RAMBAGH",
        "name": "Rambagh Urban Drain",
        "hindi_name": "रामबाग शहरी नाला",
        "lat": 22.7100,
        "lon": 75.8620,
        "elevation_m": 536.0,
        "catchment_km2": 14.2,
        "max_capacity_m3_s": 50.0,
        "type": "urban_collector",
        "river": "Khan River Feeder",
    },
    "NODE_RAJWARA": {
        "id": "NODE_RAJWARA",
        "name": "Rajwada / Krishnapura Confluence",
        "hindi_name": "राजवाड़ा / कृष्णपुरा छत्री संगम",
        "lat": 22.7186,
        "lon": 75.8550,
        "elevation_m": 540.0,
        "catchment_km2": 38.0,
        "max_capacity_m3_s": 110.0,
        "type": "confluence",
        "river": "Khan & Saraswati Confluence",
    },
    "NODE_PARDESHIPURA": {
        "id": "NODE_PARDESHIPURA",
        "name": "Pardeshipura Industrial Drain",
        "hindi_name": "परदेशीपुरा औद्योगिक नाला",
        "lat": 22.7410,
        "lon": 75.8750,
        "elevation_m": 526.0,
        "catchment_km2": 21.0,
        "max_capacity_m3_s": 75.0,
        "type": "industrial_drain",
        "river": "Khan River Main Trunk",
    },
    "NODE_VIJAY_NAGAR": {
        "id": "NODE_VIJAY_NAGAR",
        "name": "Vijay Nagar Eastern Sump",
        "hindi_name": "विजय नगर पूर्वी संप",
        "lat": 22.7533,
        "lon": 75.8937,
        "elevation_m": 532.0,
        "catchment_km2": 16.5,
        "max_capacity_m3_s": 60.0,
        "type": "storm_sump",
        "river": "Bhamori / Khan Link",
    },
    "NODE_KABITHEDI_STP": {
        "id": "NODE_KABITHEDI_STP",
        "name": "Kabithedi Main STP & Terminal Outfall",
        "hindi_name": "कबीटखेड़ी मुख्य एसटीपी व टर्मिनल आउटफॉल",
        "lat": 22.7750,
        "lon": 75.8510,
        "elevation_m": 515.0,
        "catchment_km2": 85.0,
        "max_capacity_m3_s": 245.0,  # 245 MLD equivalent capacity
        "type": "treatment_terminal",
        "river": "Khan River Northern Basin",
    },
}

# Directed Topological Flow Edges: (Source -> Destination)
DRAINAGE_EDGES = [
    ("NODE_RAU", "NODE_RAJWARA", {"channel": "Saraswati River", "length_km": 8.5, "roughness_n": 0.035}),
    ("NODE_BHANWARKUAN", "NODE_RAMBAGH", {"channel": "South Khan Trunk", "length_km": 3.2, "roughness_n": 0.028}),
    ("NODE_RAMBAGH", "NODE_RAJWARA", {"channel": "Central Khan Sump", "length_km": 1.4, "roughness_n": 0.025}),
    ("NODE_RAJWARA", "NODE_PARDESHIPURA", {"channel": "Mid-Khan Channel", "length_km": 3.8, "roughness_n": 0.030}),
    ("NODE_VIJAY_NAGAR", "NODE_PARDESHIPURA", {"channel": "Bhamori Feeder", "length_km": 2.6, "roughness_n": 0.032}),
    ("NODE_PARDESHIPURA", "NODE_KABITHEDI_STP", {"channel": "Lower Khan Main Channel", "length_km": 5.2, "roughness_n": 0.025}),
]

# Water Quality & Purity Rules
PURITY_THRESHOLD_PCT = 80.0
GATE_CLEAN_ACTION = "GATE OPEN TO KHAN RIVER"
GATE_DIRTY_ACTION = "DIVERTING TO STP / FILTRATION BASIN"

# Water Level Thresholds (Percentage of capacity)
WATER_LEVEL_SAFE_MAX = 50.0       # 0% - 50%: Safe (Green)
WATER_LEVEL_WARNING_MAX = 75.0    # 51% - 75%: Warning (Yellow)
# > 75%: Danger (Red)

# Acoustic Decibel Thresholds (dB SPL in underground sewers)
ACOUSTIC_DB_MIN = 35.0   # Empty / trickle sewer
ACOUSTIC_DB_MAX = 95.0   # Turbulent pipe-full flash flood surge

# Rainfall Thresholds (mm/hour)
RAIN_LIGHT_MAX = 5.0
RAIN_MODERATE_MAX = 15.0
RAIN_HEAVY_MAX = 30.0

# Open-Meteo Weather API endpoint for Indore
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CACHE_TTL_SEC = 300  # 5-minute cache

# Simulator Configuration
TELEMETRY_INTERVAL_SEC = 2.0
BUFFER_SIZE = 120  # Keeps trailing 4 minutes of 2-second points

# Cross-Origin Resource Sharing (CORS) Configuration
# Supports comma-separated origin list from environment variable ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS.
# Falls back to safe local development origins if not set.
import os

CORS_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", os.getenv("CORS_ALLOWED_ORIGINS", "")).strip()
if CORS_ORIGINS_ENV and CORS_ORIGINS_ENV != "*":
    ALLOWED_ORIGINS = [orig.strip() for orig in CORS_ORIGINS_ENV.split(",") if orig.strip()]
elif CORS_ORIGINS_ENV == "*":
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8501",
        "http://localhost:8501",
        "null",
    ]

