"""
FastAPI Routes for Task 3.8: AI Model Intelligence, Traceability & Explainability.
Provides scientific endpoints grounded in actual training artifacts and model checkpoints.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from backend.services.model_intel_service import model_intel_service

router = APIRouter(prefix="/api/v1/model-intel", tags=["AI Model Intelligence & Explainability"])


class WhatIfRequest(BaseModel):
    rainfall_intensity_mmh: float = Field(35.0, ge=0.0, le=150.0, description="Rainfall intensity in mm/h")
    soil_saturation_pct: float = Field(65.0, ge=0.0, le=100.0, description="Catchment soil saturation %")
    active_pumps: int = Field(2, ge=0, le=6, description="Operational high-lift drainage pumps")
    cumulative_rain_mm: float = Field(40.0, ge=0.0, le=200.0, description="Antecedent 6-hour cumulative rain in mm")


@router.get("/lineage", summary="Dataset-to-Model Traceability Matrix")
def get_dataset_model_lineage() -> Dict[str, Any]:
    """
    Returns complete dataset-to-model lineage matrix:
    - Raw datasets (Blue Heart, CAMELS-Hourly, USGS, Bellinge, CWPRS, Indore)
    - Input tensor shapes and features
    - Checkpoint provenance, parameter counts, and production inference roles
    """
    return model_intel_service.get_lineage()


@router.get("/training-curves", summary="Epoch-by-Epoch Training & Validation Loss Curves")
def get_training_curves() -> Dict[str, Any]:
    """
    Returns actual epoch-by-epoch training and validation loss curves from:
    results/blue_heart/v2/BLUE_HEART_V2_TRAINING_HISTORY.csv
    Covers Adaptive Gated ST-GNN, Res-GRU, Res-DCRNN, and Graph WaveNet.
    """
    return model_intel_service.get_training_curves()


@router.get("/evaluation", summary="Scientific Evaluation & Residual Diagnostics")
def get_evaluation_diagnostics() -> Dict[str, Any]:
    """
    Returns:
    - Multi-model benchmark metrics (Persistence vs Ridge vs Res-GRU vs Res-DCRNN vs Adaptive ST-GNN vs GWNet)
    - Actual vs Predicted scatter points from 16,396 test samples
    - Residual error histogram (e = y_true - y_pred)
    - Per-sensor metrics across all 15 Blue Heart gullies
    - Indore municipal classification matrix (97.14% accuracy, ROC-AUC 0.995)
    """
    return model_intel_service.get_evaluation_metrics()


@router.get("/feature-importance", summary="Explainable AI & Feature Attribution")
def get_feature_importance() -> Dict[str, Any]:
    """
    Returns:
    - Permutation feature importance rankings across all 12 hydrological features
    - Per-node sensitivity breakdown (% influence of rain, inflow, elevation, pumps)
    - Temporal lag attribution (t-60m down to t=0)
    - Blue Heart 3-feature importance
    """
    return model_intel_service.get_feature_importance()


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


@router.get("/dataset-explorer", summary="Dataset Statistical Distributions & Missingness")
def get_dataset_explorer() -> Dict[str, Any]:
    """
    Returns feature distributions (mean, std, quartiles, min/max) and missingness telemetry
    for Blue Heart, Indore, CAMELS-Hourly, and CWPRS datasets.
    """
    return model_intel_service.get_dataset_explorer_stats()

