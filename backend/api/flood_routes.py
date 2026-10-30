"""
FastAPI Route Handlers for Water Levels, Rainfall Forecasts, GIS Topology & Inundation Prediction.
Fully unified with V2.0.0 request schemas and topological routing engine.
"""

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

import config
from backend.services.open_meteo_client import weather_client
from backend.services.osmnx_gis_loader import indore_gis_loader
from backend.services.dem_service import dem_service
from backend.services.spatial_network_service import spatial_network_service
from backend.models.indore_routing_engine import routing_engine
from backend.models.flood_ml_model import flood_ml_model
from backend.simulators.sensor_stream_sim import sensor_simulator

router = APIRouter(prefix="/api/v1/flood", tags=["Flood & Hydrology"])

INDORE_NODES_CONFIG = [
    {"id": "NODE_RAU", "name": "Rau Headwaters (South Ridge)", "elevation_msl": 560.0, "zone": "South Indore", "downstream": "NODE_BHANWARKUAN"},
    {"id": "NODE_BHANWARKUAN", "name": "Bhanwarkuan Storm Junction", "elevation_msl": 552.0, "zone": "South-Central Indore", "downstream": "NODE_RAJWADA"},
    {"id": "NODE_RAJWADA", "name": "Rajwada / Krishnapura Chhatri Confluence", "elevation_msl": 540.0, "zone": "Central Heritage Zone", "downstream": "NODE_RAMBAGH"},
    {"id": "NODE_RAMBAGH", "name": "Rambagh Urban Drain Collector", "elevation_msl": 536.0, "zone": "Central-North Zone", "downstream": "NODE_PARDESHIPURA"},
    {"id": "NODE_PARDESHIPURA", "name": "Pardeshipura Industrial Drain", "elevation_msl": 526.0, "zone": "North Industrial Belt", "downstream": "NODE_KABITHEDI"},
    {"id": "NODE_VIJAYNAGAR", "name": "Vijay Nagar Sump Collector", "elevation_msl": 532.0, "zone": "East Commercial Hub", "downstream": "NODE_KABITHEDI"},
    {"id": "NODE_KABITHEDI", "name": "Kabithedi 245 MLD Main STP & Terminal Outfall", "elevation_msl": 515.0, "zone": "Northern Terminal", "downstream": None},
]


class PredictionRequest(BaseModel):
    rainfall_intensity_mmh: Optional[float] = Field(25.0, description="Rainfall intensity in mm/hr")
    rainfall_mm_hr: Optional[float] = Field(None, description="Legacy alias for rainfall_intensity_mmh")
    surge_multiplier: float = Field(1.0, description="Storm surge intensity multiplier")
    active_pumps_count: int = Field(2, description="Number of operational high-lift pumps")
    runoff_coefficient: Optional[float] = Field(0.72, description="Runoff coefficient for Indore black cotton/urban paved surface")


@router.get("/current-levels", summary="Get real-time water levels across Indore")
def get_current_levels() -> Dict[str, Any]:
    """Retrieve real-time water levels, acoustic readings, and flood statuses for all 7 Indore nodes."""
    telemetry = sensor_simulator.get_latest()
    nodes_stream = telemetry.get("nodes", {})

    node_list = []
    for node in INDORE_NODES_CONFIG:
        nid = node["id"]
        # Map matching id
        match_id = "NODE_VIJAY_NAGAR" if nid == "NODE_VIJAYNAGAR" else nid
        live_data = nodes_stream.get(match_id, {})

        water_level = live_data.get("water_level_pct", 35.0)
        purity = live_data.get("cv_purity_score", 85.0)

        status = "NORMAL"
        if water_level > 75.0:
            status = "CRITICAL"
        elif water_level > 50.0:
            status = "WARNING"

        gate_act = "GATE OPEN TO KHAN RIVER" if purity >= 80.0 else "DIVERTING TO STP / FILTRATION BASIN"

        node_list.append({
            "node_id": node["id"],
            "node_name": node["name"],
            "zone": node["zone"],
            "elevation_msl": node["elevation_msl"],
            "water_level_pct": water_level,
            "water_purity_pct": purity,
            "gate_action": gate_act,
            "status": status,
            "downstream": node["downstream"],
        })

    return {
        "status": "success",
        "timestamp": telemetry.get("timestamp"),
        "city_avg_water_level_pct": telemetry.get("city_avg_water_level_pct"),
        "peak_risk_node": telemetry.get("peak_risk_node"),
        "peak_risk_level_pct": telemetry.get("peak_risk_level_pct"),
        "nodes_count": len(node_list),
        "nodes": node_list,
        "nodes_dict": nodes_stream,
    }


@router.get("/rainfall", summary="Get live rain forecast for Indore from Open-Meteo")
def get_rainfall(force_refresh: bool = Query(False, description="Bypass cache and poll Open-Meteo directly")) -> Dict[str, Any]:
    """Fetch live meteorological precipitation telemetry for Indore (Lat: 22.7196, Lon: 75.8577)."""
    weather = weather_client.fetch_live_weather(force_refresh=force_refresh)
    precip = weather.get("rainfall_intensity_mm_hr", 0.0)

    return {
        "status": "success",
        "city": "Indore",
        "latitude": 22.7196,
        "longitude": 75.8577,
        "live_api_connected": weather.get("is_live_api", True),
        "current_precipitation_mm": precip,
        "weather_condition": "Heavy Rain" if precip > 5.0 else "Moderate / Clear",
        "source": weather.get("data_source", "Open-Meteo Weather API"),
        "data": weather,
    }


@router.post("/predict", summary="Predict peak flood time & inundation depths")
def predict_flood(req: PredictionRequest) -> Dict[str, Any]:
    """
    Run NetworkX routing engine across Khan & Saraswati River networks.
    Predicts peak flood arrival time, water level percentage, inundation depth, and pump actions.
    """
    # Accept rainfall_intensity_mmh or rainfall_mm_hr
    base_rain = req.rainfall_intensity_mmh if req.rainfall_intensity_mmh is not None else (req.rainfall_mm_hr or 25.0)
    intensity = base_rain * req.surge_multiplier
    total_drop_m = 560.0 - 515.0
    estimated_peak_arrival_mins = max(15, int(90.0 - (intensity * 0.8) - (req.active_pumps_count * 5)))

    overall_basin_risk = "SAFE"
    if intensity > 40.0:
        overall_basin_risk = "CRITICAL"
    elif intensity > 20.0:
        overall_basin_risk = "WARNING"

    node_predictions = []
    for node in INDORE_NODES_CONFIG:
        accumulated_depth_cm = round((560.0 - node["elevation_msl"]) * 0.8 * (intensity / 10.0), 1)
        node_predictions.append({
            "node_id": node["id"],
            "node_name": node["name"],
            "elevation_msl": node["elevation_msl"],
            "predicted_inundation_cm": accumulated_depth_cm,
            "risk_level": "RED" if accumulated_depth_cm > 30.0 else ("YELLOW" if accumulated_depth_cm > 15.0 else "GREEN"),
        })

    # Detailed topological flow routing
    routing_result = routing_engine.simulate_routing(
        rainfall_mm_hr=intensity,
        runoff_coeff=req.runoff_coefficient or 0.72,
    )

    return {
        "status": "success",
        "rainfall_intensity_mmh": intensity,
        "overall_basin_risk": overall_basin_risk,
        "total_elevation_drop_m": total_drop_m,
        "peak_flood_arrival_mins": estimated_peak_arrival_mins,
        "automated_action": f"Actuating Kabithedi Pump Station ({req.active_pumps_count} pumps online)",
        "node_predictions": node_predictions,
        "prediction": routing_result,
    }


@router.get("/topology", summary="Get Indore GIS drainage graph and nodes")
def get_topology() -> Dict[str, Any]:
    """Returns the directed hydraulic graph, elevations, Manning parameters, and verified real OSM river channels."""
    assumed_bounds = {
        "max_msl_m": config.INDORE_MAX_MSL_ELEVATION,
        "min_msl_m": config.INDORE_MIN_MSL_ELEVATION,
        "elevation_drop_m": config.INDORE_MAX_MSL_ELEVATION - config.INDORE_MIN_MSL_ELEVATION,
        "source": "Assumed model elevations (config.py)",
    }
    dem_bounds = dem_service.get_dem_elevation_bounds()

    return {
        "status": "success",
        "geojson": indore_gis_loader.to_geojson(),
        "real_waterways": indore_gis_loader.get_real_waterways_geojson(),
        "metadata": indore_gis_loader.get_gis_metadata(),
        "dem_metadata": {
            "source": "Copernicus DEM GLO-30 (30m)",
            "vertical_datum": "EGM2008",
            "is_dem_available": dem_service.is_available,
        },
        "assumed_elevation_bounds": assumed_bounds,
        "dem_surface_elevation_bounds": dem_bounds,
        # Backward compatibility alias for legacy callers
        "elevation_bounds": assumed_bounds,
    }


@router.get("/dem/elevation-audit", summary="Get Copernicus DEM GLO-30 vs Assumed Elevation Audit")
def get_dem_elevation_audit() -> Dict[str, Any]:
    """Returns the comprehensive Phase 1 DEM extraction, elevation comparison, and edge validation report."""
    return {
        "status": "success",
        "report": dem_service.generate_full_report(),
    }


@router.get("/spatial-network", summary="Get real OSM spatial river network graph and snapping report")
def get_spatial_network(snapping_tolerance_m: float = Query(50.0, description="Snapping tolerance in meters")) -> Dict[str, Any]:
    """
    Returns the real OpenStreetMap spatial river network:
    - 7 OSM features partitioned into 9 topological reaches
    - Exact detected river confluences (e.g. Krishnapura Chhatri)
    - Separated connected components and isolated segments
    - 7 municipal monitoring stations with nearest waterway distance & classification
    - Clear distinction between real geometry, derived spatial relations, and unverified hydraulic flow
    """
    report = spatial_network_service.get_spatial_network_report()
    geojson_data = spatial_network_service.to_spatial_geojson()

    return {
        "status": "success",
        "network_statistics": report.get("network_statistics"),
        "provenance_distinction": report.get("provenance_distinction_statement"),
        "confluence_candidates": report.get("confluence_candidates"),
        "continuity_junctions": report.get("continuity_junctions"),
        "junction_candidates": report.get("junction_candidates"),
        "connected_components": report.get("connected_components"),
        "disconnected_mapped_segments": report.get("disconnected_mapped_segments"),
        "possible_subsurface_connections": report.get("possible_subsurface_connections"),
        "hydraulic_direction_status": report.get("hydraulic_direction_status"),
        "monitoring_stations_snapping": report.get("monitoring_stations_snapping"),
        "spatial_graph_nodes": report.get("spatial_graph_nodes"),
        "spatial_graph_edges": report.get("spatial_graph_edges"),
        "spatial_geojson": geojson_data,
    }


@router.get("/elevation-profile", summary="Get South-to-North elevation drop profile")
def get_elevation_profile() -> Dict[str, Any]:
    """Returns elevation drop along the primary Khan River channel (550m to 515m)."""
    profile = indore_gis_loader.get_elevation_profile()
    return {
        "status": "success",
        "profile": profile,
    }


class MLPredictionRequest(BaseModel):
    rainfall_intensity_mmh: float = Field(25.0, description="Storm rainfall intensity in mm/h")
    antecedent_rainfall_24h_mm: float = Field(35.0, description="24-hour antecedent rainfall in mm")
    river_stage_khan_m: float = Field(2.5, description="Khan river level in meters at Krishnapura Chhatri")
    drainage_flow_m3s: float = Field(2.4, description="Trunk drainage discharge in m3/s")
    active_pumps_count: int = Field(2, description="Number of operational pumps")
    soil_saturation_pct: float = Field(65.0, description="Soil saturation percentage")


@router.get("/environmental-summary", summary="Get real-time environmental metrics for hero cards")
def get_environmental_summary() -> Dict[str, Any]:
    """
    Returns live environmental data specifically powering the 3 floating hero cards:
    - Live Rainfall (mm/h)
    - River Level (m)
    - Drainage Flow (m3/s)
    Clearly distinguishes live weather API vs calibrated hydraulic simulation.
    """
    weather = weather_client.fetch_live_weather()
    telemetry = sensor_simulator.get_latest()
    live_rain = weather.get("rainfall_intensity_mm_hr", 0.0)

    # In case live weather is 0 mm/h during dry periods, provide demo baseline if requested, but clearly labeled
    display_rain = live_rain if live_rain > 0 else 42.6  # Default to reference demo value if dry
    is_live_rain = bool(live_rain > 0)

    # Khan river stage calculation based on hydraulic loading
    city_avg_level = telemetry.get("city_avg_water_level_pct", 38.0)
    # 0-100% capacity maps to 1.2m (baseflow) - 5.5m (danger level)
    river_stage = round(1.2 + (city_avg_level / 100.0) * (5.5 - 1.2), 2)

    # Drainage flow calculation based on rainfall and surge multiplier
    drainage_flow = round(1.2 + (display_rain * 0.045) * sensor_simulator.surge_multiplier, 1)

    return {
        "status": "success",
        "timestamp": telemetry.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
        "live_rainfall": {
            "value": round(display_rain, 1),
            "unit": "mm/h",
            "source": weather.get("data_source", "Open-Meteo Weather API"),
            "is_live_api": is_live_rain,
            "data_mode": "Live Open-Meteo API" if is_live_rain else "Calibrated Demo Surge (42.6 mm/h)",
            "category": weather.get("rainfall_category", "Heavy Rain" if display_rain > 30 else "Moderate"),
        },
        "river_level": {
            "value": round(river_stage, 2),
            "unit": "m",
            "location": "Krishnapura Chhatri (Khan River)",
            "danger_threshold_m": 5.0,
            "data_mode": "Calibrated Hydraulic Gauge (Telemetry)",
            "status": "ELEVATED" if river_stage > 3.8 else "NORMAL",
        },
        "drainage_flow": {
            "value": round(drainage_flow, 1),
            "unit": "m³/s",
            "location": "Rajwada Trunk Sluice",
            "capacity_m3s": 6.5,
            "data_mode": "Hydraulic Sensor Stream",
            "gate_action": "DIVERTED TO STP" if sensor_simulator.forced_pollution else "DISCHARGE TO KHAN RIVER",
        },
        "basin_summary": {
            "city": "Indore, Madhya Pradesh",
            "monitored_nodes": len(INDORE_NODES_CONFIG),
            "elevation_drop_m": config.INDORE_MAX_MSL_ELEVATION - config.INDORE_MIN_MSL_ELEVATION,
            "peak_risk_node": telemetry.get("peak_risk_node", "Rajwada / Krishnapura Confluence"),
        },
    }


@router.get("/ml-model/info", summary="Get FloodGuard ML model training and evaluation metrics")
def get_ml_model_info() -> Dict[str, Any]:
    """Returns honest evaluation metrics, confusion matrix, and feature importances for the trained Random Forest classifier."""
    return {
        "status": "success",
        **flood_ml_model.metrics,
    }


@router.post("/ml-predict", summary="Run ML flood inundation prediction")
def predict_ml_flood(req: MLPredictionRequest) -> Dict[str, Any]:
    """Execute Random Forest inference for flash flood risk classification and action recommendation."""
    result = flood_ml_model.predict(
        rainfall_intensity_mmh=req.rainfall_intensity_mmh,
        antecedent_rainfall_24h_mm=req.antecedent_rainfall_24h_mm,
        river_stage_khan_m=req.river_stage_khan_m,
        drainage_flow_m3s=req.drainage_flow_m3s,
        active_pumps_count=req.active_pumps_count,
        soil_saturation_pct=req.soil_saturation_pct,
    )
    return result
