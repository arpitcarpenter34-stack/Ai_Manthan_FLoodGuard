"""
Script to append Task 3.5 Core Flood Intelligence endpoints to backend/api/flood_routes.py
"""

from pathlib import Path

target_file = Path(r"E:\ai-manthan\hydro_guard_indore\backend\api\flood_routes.py")
content = target_file.read_text(encoding="utf-8")

import_target = "from backend.models.blue_heart_st_gnn import blue_heart_st_gnn"
import_replacement = """from backend.models.blue_heart_st_gnn import blue_heart_st_gnn
from backend.services.street_inundation_service import street_inundation_service
from backend.services.pump_gate_optimizer import pump_gate_optimizer"""

new_endpoints = """

# ==============================================================================
# TASK 3.5 CORE FLOOD INTELLIGENCE ENDPOINTS (STREET INUNDATION & PUMP OPTIMIZATION)
# ==============================================================================

class InundationMapRequest(BaseModel):
    rainfall_intensity_mmh: Optional[float] = Field(35.0, description="Storm rainfall intensity in mm/hr")
    surge_multiplier: float = Field(1.0, description="Storm surge intensity multiplier")
    active_pumps_count: int = Field(2, description="Number of operational high-lift pumps")


class PumpOptimizationRequest(BaseModel):
    rainfall_intensity_mmh: Optional[float] = Field(35.0, description="Storm rainfall intensity in mm/hr")
    surge_multiplier: float = Field(1.0, description="Storm surge intensity multiplier")
    active_pumps_count: int = Field(2, description="Number of operational high-lift pumps")
    current_water_levels: Optional[Dict[str, float]] = Field(None, description="Node water stages in %")
    water_purity_scores: Optional[Dict[str, float]] = Field(None, description="Water purity scores in %")


@router.get("/inundation-map", summary="Get spatial street-level flood inundation GeoJSON")
def get_street_inundation_map(
    rainfall_intensity_mmh: float = Query(35.0, ge=0.0, description="Rainfall intensity in mm/h"),
    surge_multiplier: float = Query(1.0, ge=0.1, le=5.0, description="Storm surge multiplier"),
    active_pumps_count: int = Query(2, ge=0, le=10, description="Active pumps count"),
) -> Dict[str, Any]:
    \"\"\"
    Returns spatial GeoJSON FeatureCollection containing:
    - Street hazard corridors and overland inundation polygons
    - Submerged streets with water depths (cm) and wave arrival times (min)
    - Hydraulic flow direction vectors (South-to-North Khan drainage)
    - Critical drainage bottlenecks with physical diagnostic root causes
    \"\"\"
    return street_inundation_service.calculate_inundation(
        rainfall_intensity_mmh=rainfall_intensity_mmh,
        surge_multiplier=surge_multiplier,
        active_pumps_count=active_pumps_count,
    )


@router.post("/inundation-map", summary="Calculate scenario-driven street flood inundation GeoJSON")
def post_street_inundation_map(req: InundationMapRequest) -> Dict[str, Any]:
    \"\"\"Calculates street inundation GeoJSON from POST scenario controls.\"\"\"
    return street_inundation_service.calculate_inundation(
        rainfall_intensity_mmh=req.rainfall_intensity_mmh or 35.0,
        surge_multiplier=req.surge_multiplier,
        active_pumps_count=req.active_pumps_count,
    )


@router.post("/optimize-pumps-gates", summary="Run intelligent pump scheduling and gate optimization")
def optimize_pumps_gates_endpoint(req: PumpOptimizationRequest) -> Dict[str, Any]:
    \"\"\"
    Executes Model Predictive Control (MPC) optimization:
    - Anticipatory pre-pumping schedule 20 min before storm peak
    - Saraswati confluence gate throttling to safeguard Rajwada heritage core
    - Dual-gate 80% water quality enforcement (River discharge vs STP treatment)
    - Quantitative comparison of Baseline Reactive vs Optimized MPC strategies
    \"\"\"
    return pump_gate_optimizer.optimize_schedule(
        rainfall_intensity_mmh=req.rainfall_intensity_mmh or 35.0,
        surge_multiplier=req.surge_multiplier,
        active_pumps_input=req.active_pumps_count,
        current_water_levels=req.current_water_levels,
        water_purity_scores=req.water_purity_scores,
    )


@router.get("/pump-optimization-state", summary="Get active pump scheduling & gate optimization advisory")
def get_pump_optimization_state() -> Dict[str, Any]:
    \"\"\"Returns the latest intelligent pump & gate optimization state using live telemetry.\"\"\"
    telemetry = sensor_simulator.get_latest()
    nodes_stream = telemetry.get("nodes", {})
    live_levels = {nid: data.get("water_level_pct", 35.0) for nid, data in nodes_stream.items()}
    live_purity = {nid: data.get("cv_purity_score", 85.0) for nid, data in nodes_stream.items()}

    return pump_gate_optimizer.optimize_schedule(
        rainfall_intensity_mmh=35.0,
        surge_multiplier=sensor_simulator.surge_multiplier,
        active_pumps_input=2,
        current_water_levels=live_levels if live_levels else None,
        water_purity_scores=live_purity if live_purity else None,
    )
"""

if import_target in content:
    content = content.replace(import_target, import_replacement, 1)
content = content + new_endpoints

target_file.write_text(content, encoding="utf-8")
print("Updated flood_routes.py successfully!")

