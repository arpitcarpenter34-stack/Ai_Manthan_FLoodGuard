"""
FastAPI Route Handlers for CV Water Purity Check, Acoustic Level Detection, and Telemetry Streams.
Supports both JSON API payloads and raw file/sample form uploads.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Query
from pydantic import BaseModel, Field

import config
from backend.models.cv_purity_detector import cv_detector
from backend.models.acoustic_level_ai import acoustic_ai
from backend.simulators.sensor_stream_sim import sensor_simulator
from backend.services.db_manager import db_manager

router = APIRouter(prefix="/api/v1/sensors", tags=["Sensors & Edge AI"])


class PurityAnalysisRequest(BaseModel):
    turbidity_ntu: Optional[float] = Field(15.0, description="Turbidity in Nephelometric Turbidity Units (NTU)")
    color_hue_deg: Optional[float] = Field(210.0, description="Color Hue (0-360 deg) - e.g. 210 for cyan/blue rainwater vs 30 for brown sewage")
    suspended_solids_ppm: Optional[float] = Field(45.0, description="Total Suspended Solids (TSS) in ppm")


class AcousticAnalysisRequest(BaseModel):
    decibels_db_spl: float = Field(72.0, description="Sound Pressure Level in dB SPL")
    dominant_frequency_hz: float = Field(1200.0, description="Dominant resonant frequency in Hz")


class SimulationControlRequest(BaseModel):
    surge_multiplier: Optional[float] = Field(None, ge=0.1, le=10.0, description="Storm surge intensity multiplier")
    trigger_pollution: Optional[bool] = Field(None, description="Force high turbidity sewage pollution burst")


def calculate_water_purity(turbidity: float, hue: float, solids: float) -> dict:
    """
    Evaluates 80% Water Purity Rule for Khan River Protection.
    Purity >= 80% -> GATE OPEN TO KHAN RIVER
    Purity < 80%  -> DIVERTING TO STP / FILTRATION BASIN
    """
    turbidity_score = max(0.0, min(100.0, 100.0 - (turbidity * 1.2)))
    solids_score = max(0.0, min(100.0, 100.0 - (solids * 0.8)))

    if 160 <= hue <= 250:
        hue_score = 95.0
    elif 15 <= hue <= 60:
        hue_score = 30.0
    else:
        hue_score = 65.0

    purity_score = round(0.4 * turbidity_score + 0.4 * solids_score + 0.2 * hue_score, 1)
    purity_score = max(0.0, min(100.0, purity_score))

    is_safe = bool(purity_score >= 80.0)
    gate_action = "GATE OPEN TO KHAN RIVER" if is_safe else "DIVERTING TO STP / FILTRATION BASIN"

    return {
        "purity_score_percent": purity_score,
        "pass_80pct_rule": is_safe,
        "gate_action": gate_action,
        "parameters_analyzed": {
            "turbidity_ntu": turbidity,
            "color_hue_deg": hue,
            "suspended_solids_ppm": solids,
        },
        "reasoning": (
            "Safe rainwater allowed to aid river flow"
            if is_safe
            else "Contaminated water diverted to Kabithedi 245 MLD STP"
        ),
        "screening_mode": "PROTOTYPE_SIMULATION",
    }


def calculate_acoustic_water_level(decibels: float, frequency: float) -> dict:
    """
    Acoustic AI Level Detection for Dark Underground Culverts.
    Maps Sound Pressure Level (dB) and Frequency to Water Level %.
    """
    inferred_level = max(0.0, min(100.0, (decibels - 35.0) / (95.0 - 35.0) * 100.0))
    inferred_level = round(inferred_level, 1)

    if inferred_level < 40.0:
        regime = "Normal Trickle Flow"
        risk_color = "GREEN"
    elif inferred_level < 75.0:
        regime = "Moderate Surge Flow"
        risk_color = "YELLOW"
    else:
        regime = "Pressurized Flash Surge (Heavy Turbulence)"
        risk_color = "RED"

    return {
        "acoustic_decibels_db": decibels,
        "frequency_hz": frequency,
        "inferred_water_level_pct": inferred_level,
        "flow_regime": regime,
        "risk_level": risk_color,
        "sensor_health": "100% Operational (Acoustic Hydrophone)",
        "model_type": "HEURISTIC_SPECTRAL_RESONANCE",
    }


@router.post("/cv-purity/analyze", summary="Analyze drain outfall image or CV parameters for 80% purity rule")
async def analyze_cv_purity(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Drain outfall camera image"),
    sample_type: Optional[str] = Form(None, description="Synthetic sample type: clean_rainwater, polluted_sludge, borderline_runoff"),
) -> Dict[str, Any]:
    """
    Apply OpenCV color & turbidity analysis or evaluate numerical sensor parameters:
    - Purity >= 80%: GATE OPEN TO KHAN RIVER
    - Purity < 80%: DIVERTING TO STP / FILTRATION BASIN
    """
    content_type = request.headers.get("content-type", "")

    # Handle direct JSON body
    if "application/json" in content_type:
        body = await request.json()
        req = PurityAnalysisRequest(**body)
        turbidity = req.turbidity_ntu if req.turbidity_ntu is not None else 15.0
        hue = req.color_hue_deg if req.color_hue_deg is not None else 210.0
        solids = req.suspended_solids_ppm if req.suspended_solids_ppm is not None else 45.0
        res = calculate_water_purity(turbidity, hue, solids)

        # Persist to SQLite
        record_id = db_manager.log_image_analysis(
            input_source="json_payload",
            purity_score=res["purity_score_percent"],
            is_clean=res["pass_80pct_rule"],
            gate_action=res["gate_action"],
            turbidity_estimate=turbidity,
            debris_count=0,
            details=res.get("parameters_analyzed"),
        )

        return {
            "status": "success",
            "record_id": record_id,
            **res,
            "analysis": {
                "purity_score": res["purity_score_percent"],
                "is_clean": res["pass_80pct_rule"],
                "gate_status": res["gate_action"],
            },
        }

    # Handle multipart file or form parameter
    source_name = (file.filename if file and file.filename else None) or sample_type or "clean_rainwater"
    if file:
        content = await file.read()
        result = cv_detector.analyze_image(content)
    elif sample_type:
        frame = cv_detector.generate_synthetic_drain_frame(sample_type)
        result = cv_detector.analyze_image(frame)
    else:
        frame = cv_detector.generate_synthetic_drain_frame("clean_rainwater")
        result = cv_detector.analyze_image(frame)

    purity_val = result.get("purity_score", 0.0)
    is_clean = bool(result.get("is_clean", False))
    gate = result.get("gate_status", config.GATE_DIRTY_ACTION)
    turb = result.get("turbidity_ntu_estimate")
    debris = result.get("floating_debris_count", 0)

    # Persist to SQLite
    record_id = db_manager.log_image_analysis(
        input_source=source_name,
        purity_score=purity_val,
        is_clean=is_clean,
        gate_action=gate,
        turbidity_estimate=turb,
        debris_count=debris,
        details={k: v for k, v in result.items() if k != "annotated_frame_base64"},
    )

    return {
        "status": "success",
        "record_id": record_id,
        "purity_score_percent": purity_val,
        "pass_80pct_rule": is_clean,
        "gate_action": gate,
        "analysis": result,
    }


@router.post("/acoustic-level/analyze", summary="Analyze sewer audio or decibel metrics for water level estimation")
async def analyze_acoustic_level(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Underground sewer hydrophone audio (WAV)"),
    test_level_pct: Optional[float] = Form(None, ge=0, le=100, description="Synthetic target level percentage"),
) -> Dict[str, Any]:
    """
    Process audio waveform and spectrogram or evaluate numerical acoustic dB metrics:
    Maps decibels and frequency to water level (0% to 100%) in dark underground sewers.
    """
    content_type = request.headers.get("content-type", "")

    # Handle direct JSON body
    if "application/json" in content_type:
        body = await request.json()
        req = AcousticAnalysisRequest(**body)
        res = calculate_acoustic_water_level(req.decibels_db_spl, req.dominant_frequency_hz)

        # Persist to SQLite
        record_id = db_manager.log_audio_analysis(
            input_source="json_payload",
            decibels_db=res["acoustic_decibels_db"],
            inferred_level_pct=res["inferred_water_level_pct"],
            flow_regime=res["flow_regime"],
            dominant_frequency_hz=req.dominant_frequency_hz,
            alert_status=res.get("risk_level", "SAFE"),
            details=res,
        )

        return {
            "status": "success",
            "record_id": record_id,
            **res,
            "analysis": {
                "estimated_water_level_pct": res["inferred_water_level_pct"],
                "decibel_spl": res["acoustic_decibels_db"],
                "flow_regime": res["flow_regime"],
            },
        }

    # Handle multipart file or form parameter
    source_name = (file.filename if file and file.filename else None) or (f"Sample ({test_level_pct}%)" if test_level_pct is not None else "Sample Default")
    if file:
        content = await file.read()
        result = acoustic_ai.analyze_audio(content)
    elif test_level_pct is not None:
        raw_wav = acoustic_ai.generate_synthetic_sewer_audio(target_level_pct=test_level_pct)
        result = acoustic_ai.analyze_audio(raw_wav)
    else:
        raw_wav = acoustic_ai.generate_synthetic_sewer_audio(target_level_pct=65.0)
        result = acoustic_ai.analyze_audio(raw_wav)

    db_spl = result.get("decibel_spl", 0.0)
    inferred_pct = result.get("estimated_water_level_pct", 0.0)
    flow_regime = result.get("flow_regime", "Unknown")
    freq = result.get("dominant_frequency_hz")
    alert = result.get("alert_status", "SAFE")

    # Persist to SQLite
    record_id = db_manager.log_audio_analysis(
        input_source=source_name,
        decibels_db=db_spl,
        inferred_level_pct=inferred_pct,
        flow_regime=flow_regime,
        dominant_frequency_hz=freq,
        alert_status=alert,
        details={k: v for k, v in result.items() if k not in ("spectrogram_image_b64", "spectrogram_base64")},
    )

    return {
        "status": "success",
        "record_id": record_id,
        "acoustic_decibels_db": db_spl,
        "inferred_water_level_pct": inferred_pct,
        "flow_regime": flow_regime,
        "analysis": result,
    }


@router.get("/history", summary="Get persisted analysis history from SQLite database")
def get_analysis_history(
    limit: int = Query(50, ge=1, le=500, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Records offset for pagination"),
    analysis_type: Optional[str] = Query(None, description="Filter by IMAGE_PURITY or ACOUSTIC_LEVEL"),
) -> Dict[str, Any]:
    """Retrieve historical image and acoustic analysis records saved in SQLite."""
    records = db_manager.get_recent_analyses(limit=limit, offset=offset, analysis_type=analysis_type)
    stats = db_manager.get_db_stats()
    return {
        "status": "success",
        "count": len(records),
        "limit": limit,
        "offset": offset,
        "database_status": stats.get("status", "HEALTHY"),
        "total_records": stats.get("total_analysis_records", len(records)),
        "records": records,
    }


@router.get("/db-stats", summary="Get SQLite database health and record statistics")
def get_database_statistics() -> Dict[str, Any]:
    """Return SQLite database health, total records, and file size."""
    return {
        "status": "success",
        "database": db_manager.get_db_stats(),
    }


@router.get("/telemetry/live", summary="Get live 2-second telemetry stream snapshot")
def get_live_telemetry() -> Dict[str, Any]:
    """Fetch the latest 2-second IoT sensor telemetry across Indore."""
    return {
        "status": "success",
        "telemetry": sensor_simulator.get_latest(),
    }


@router.get("/telemetry/history", summary="Get recent telemetry history for time-series charts")
def get_telemetry_history(count: int = 30) -> Dict[str, Any]:
    """Fetch trailing telemetry points from memory buffer."""
    return {
        "status": "success",
        "history": sensor_simulator.get_history(count=count),
    }


@router.post("/simulation/control", summary="Configure simulator parameters interactively")
def control_simulation(request: SimulationControlRequest) -> Dict[str, Any]:
    """Dynamically control storm surge multiplier or trigger sewage contamination."""
    if request.surge_multiplier is not None:
        sensor_simulator.set_surge_simulation(request.surge_multiplier)
    if request.trigger_pollution is not None:
        sensor_simulator.trigger_pollution_event(request.trigger_pollution)

    return {
        "status": "success",
        "message": "Simulator parameters updated",
        "current_surge_multiplier": sensor_simulator.surge_multiplier,
        "forced_pollution": sensor_simulator.forced_pollution,
    }
