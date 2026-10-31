"""
FastAPI Route Handlers for Dataset Intelligence, Traceability & Live Model Execution.
Mounted under /api/v1/data-intel.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, Path
from pydantic import BaseModel, Field

from backend.services.dataset_intelligence_service import dataset_intel_service
from backend.services.model_intel_service import model_intel_service
from backend.services.weather_radar_service import weather_radar_service

router = APIRouter(prefix="/api/v1/data-intel", tags=["Dataset Intelligence & Model Execution"])


class InferenceRequest(BaseModel):
    sample_index: int = Field(0, ge=0, description="Test sample sequence index to feed into the model")


class WhatIfRequest(BaseModel):
    rainfall_intensity_mmh: float = Field(35.0, ge=0.0, le=150.0, description="Rainfall intensity in mm/h")
    soil_saturation_pct: float = Field(65.0, ge=0.0, le=100.0, description="Catchment soil saturation %")
    active_pumps: int = Field(2, ge=0, le=6, description="Operational high-lift drainage pumps")
    cumulative_rain_mm: float = Field(40.0, ge=0.0, le=200.0, description="Antecedent 6-hour cumulative rain in mm")


@router.get("/registry", summary="Unified Dataset Inventory & Lineage Registry")
def get_registry() -> Dict[str, Any]:
    """Returns verified dataset registry across all 8 datasets with training eligibility and checkpoint provenance."""
    return dataset_intel_service.get_dataset_registry()


@router.get("/weather-radar", summary="Weather Radar & Precipitation Telemetry Intelligence Dashboard Data")
def get_weather_radar_info(
    region: str = Query("indore", description="Catchment region: indore, pune_cwprs, eastbourne, aroostook")
) -> Dict[str, Any]:
    """
    Authentic weather radar intelligence & precipitation dashboard:
    - Dynamic 5 KPIs (current rain, 24h accumulated, 1h forecast, 6h forecast, alert classification)
    - Doppler radar availability audit (no fabrication)
    - Multi-scale rainfall intensity analytics (6h, 12h, 24h)
    - Hourly forecast and hydraulic drainage impact assessment
    - Nowcast atmospheric outlook (wind, humidity, pressure, trend)
    - Station and data health monitoring table (CWPRS, Blue Heart, CAMELS, Open-Meteo)
    - Real historical storm hyetograph comparison
    """
    return weather_radar_service.get_weather_radar_dashboard(region_key=region)


@router.get("/{dataset_id}/observations", summary="Get actual dataset observation rows from disk")
def get_observations(
    dataset_id: str = Path(..., description="Dataset ID (e.g. blue_heart, camels_hourly, usgs_potomac, india_cwprs)"),
    limit: int = Query(50, ge=1, le=200, description="Max observation rows to retrieve")
) -> Dict[str, Any]:
    """Returns actual observation rows from disk CSV/NPZ files for preview and tabular visualization."""
    return dataset_intel_service.get_dataset_observations(dataset_id=dataset_id, limit=limit)


@router.get("/{dataset_id}/distributions", summary="Feature distribution statistics and histogram bins")
def get_distributions(
    dataset_id: str = Path(..., description="Dataset ID")
) -> Dict[str, Any]:
    """Computes statistical quartiles (min, 25%, median, 75%, max, mean, std) and histogram bins for numeric variables."""
    return dataset_intel_service.get_dataset_distributions(dataset_id=dataset_id)


@router.get("/{dataset_id}/correlations", summary="Pairwise feature correlation matrix")
def get_correlations(
    dataset_id: str = Path(..., description="Dataset ID")
) -> Dict[str, Any]:
    """Returns Pearson correlation coefficient matrix between numeric features."""
    return dataset_intel_service.get_dataset_correlations(dataset_id=dataset_id)


@router.get("/{dataset_id}/intelligence", summary="Comprehensive Hydrological Intelligence Package (Task 4.1)")
def get_dataset_intelligence(
    dataset_id: str = Path(..., description="Dataset ID (e.g. blue_heart, camels_hourly, usgs_potomac, india_cwprs, bellinge_swmm, uwo_kearney)")
) -> Dict[str, Any]:
    """Returns comprehensive multi-dimensional intelligence package for the 6 white-theme explorer tabs."""
    return dataset_intel_service.get_hydrological_intelligence(dataset_id=dataset_id)


@router.post("/{dataset_id}/inference", summary="Feed actual dataset sample into compatible trained model")
def execute_inference(
    dataset_id: str = Path(..., description="Dataset ID"),
    req: Optional[InferenceRequest] = None
) -> Dict[str, Any]:
    """
    Traces and executes the actual data pipeline:
    Raw Observation -> Scaling -> Input Tensor -> Trained Checkpoint -> Prediction & XAI
    - If Blue Heart: Loads real test sequence, runs PyTorch Adaptive Gated ST-GNN, compares with observed stage.
    - If Indore Municipal: Runs calibrated Hybrid ST-GNN diffusion network across 7 nodes.
    - If CAMELS / USGS / Bellinge: Informs user that dataset is exploration-only and displays historical observations.
    """
    s_idx = req.sample_index if req else 0
    return dataset_intel_service.execute_dataset_inference(dataset_id=dataset_id, sample_index=s_idx)


@router.post("/what-if", summary="Interactive What-If Scenario Sensitivity Simulator")
def post_what_if_analysis(req: WhatIfRequest) -> Dict[str, Any]:
    """
    Calculates multi-point sensitivity response curves:
    - Rainfall intensity vs Inundation Depth (cm) & Risk (%)
    - Soil saturation vs Inundation Depth (cm)
    - Active pumps vs Depth relief & mitigation (%)
    - Dynamic waterfall risk attribution breakdown
    """
    return model_intel_service.calculate_what_if_response(
        rainfall_intensity_mmh=req.rainfall_intensity_mmh,
        soil_saturation_pct=req.soil_saturation_pct,
        active_pumps=req.active_pumps,
        cumulative_rain_mm=req.cumulative_rain_mm
    )

