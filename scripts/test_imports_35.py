"""
Test importing the updated modules and endpoints.
"""
import sys
sys.path.insert(0, r"E:\ai-manthan\hydro_guard_indore")

from backend.services.street_inundation_service import street_inundation_service
from backend.services.pump_gate_optimizer import pump_gate_optimizer
from backend.models.hybrid_prediction_engine import hybrid_prediction_engine
from backend.api.flood_routes import router

print("All imports succeeded!")

# Test inundation service
res_inundation = street_inundation_service.calculate_inundation(rainfall_intensity_mmh=35.0)
print(f"Inundation service: {len(res_inundation['features'])} features, {res_inundation['metadata']['inundated_streets_count']} inundated streets")

# Test pump gate optimizer
res_opt = pump_gate_optimizer.optimize_schedule(rainfall_intensity_mmh=35.0)
print(f"Pump optimizer: recommended pumps = {res_opt['summary_comparison']['optimized_mpc_strategy']['recommended_pumps']}, overflow reduction = {res_opt['summary_comparison']['expected_benefits']['overflow_reduction_pct']}")

# Test hybrid prediction engine
res_pred = hybrid_prediction_engine.predict_hybrid_flood(rainfall_intensity_mmh=35.0)
print(f"Hybrid prediction: risk = {res_pred['overall_basin_risk']}, prob = {res_pred['overall_flood_probability']}%, arrival = {res_pred['peak_flood_arrival_mins']}m")
print(f"Confidence intervals: {res_pred['node_predictions'][0]['confidence_interval_90_depth_cm']}")
print(f"Street corridors in node 0: {res_pred['node_predictions'][0]['affected_street_corridors']}")
print("Test completed successfully!")

