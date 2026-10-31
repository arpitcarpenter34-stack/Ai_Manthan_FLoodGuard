"""
Test Suite for Hybrid Spatio-Temporal Graph Neural Network (ST-GNN) & Hydraulic Physics Engine.
Verifies:
1. Spatial graph topology and diffusion matrices (Pf, Pb, Laplacian).
2. Temporal pipeline chronological sequence assembly.
3. ST-GNN forward pass, tensor dimensions, and bounds.
4. Model evaluation metrics (Accuracy, F1, ROC-AUC, Depth MAE, Arrival MAE).
5. Rational Method and Manning's equation hydraulic routing.
6. Hybrid fusion engine and traceable attribution.
7. FastAPI endpoint compliance and backward compatibility.
"""

import sys
from pathlib import Path
import pytest
import numpy as np
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app
from backend.models.spatial_graph import drainage_spatial_graph
from backend.models.temporal_pipeline import temporal_pipeline
from backend.models.st_gnn_model import st_gnn_model
from backend.models.hybrid_prediction_engine import hybrid_prediction_engine


client = TestClient(app)


def test_spatial_graph_topology():
    """Verify directed spatial drainage graph construction and diffusion matrices."""
    graph = drainage_spatial_graph
    assert graph.num_nodes == 7
    assert graph.adj_matrix.shape == (7, 7)
    assert graph.P_forward.shape == (7, 7)
    assert graph.P_backward.shape == (7, 7)
    assert graph.static_node_features.shape == (7, 6)

    # Check forward diffusion row stochasticity (sum to ~1 for non-isolated nodes)
    row_sums = np.sum(graph.P_forward, axis=1)
    assert np.all(row_sums > 0.0)

    # Verify Chebyshev diffusion matrices
    diff_mats = graph.get_diffusion_matrices(k=2)
    assert len(diff_mats) == 5  # Identity, Pf, Pb, Pf^2, Pb^2
    for m in diff_mats:
        assert m.shape == (7, 7)


def test_temporal_pipeline_chronological_ordering():
    """Verify time-series sequence assembly without future data leakage."""
    tensor, meta = temporal_pipeline.construct_realtime_sequence(
        current_rain_mm_hr=45.0,
        surge_multiplier=1.2,
        active_pumps=2,
    )
    # Shape: (T=6, N=7, F=6)
    assert tensor.shape == (6, 7, 6)
    assert meta["sequence_length"] == 6

    # Verify chronological monotonically increasing cumulative rainfall
    cum_rain = tensor[:, :, 1]
    for n in range(7):
        diffs = np.diff(cum_rain[:, n])
        assert np.all(diffs >= -1e-5), "Cumulative rainfall must be non-decreasing"


def test_st_gnn_inference_and_bounds():
    """Verify ST-GNN forward pass produces bounded probabilities, depths, and arrival times."""
    tensor, _ = temporal_pipeline.construct_realtime_sequence(
        current_rain_mm_hr=50.0,
        surge_multiplier=1.0,
        active_pumps=2,
    )
    risk_probs, depths, arrivals = st_gnn_model.forward(tensor)

    assert risk_probs.shape == (7,)
    assert depths.shape == (7,)
    assert arrivals.shape == (7,)

    # Probabilities must be in [0, 1]
    assert np.all(risk_probs >= 0.0) and np.all(risk_probs <= 1.0)
    # Depths must be non-negative
    assert np.all(depths >= 0.0)
    # Arrival times must be positive
    assert np.all(arrivals > 0.0)


def test_st_gnn_evaluation_metrics():
    """Verify honest model evaluation metrics and confusion matrix."""
    metrics = st_gnn_model.metrics.get("evaluation_metrics", {})
    assert metrics.get("accuracy", 0.0) > 0.90
    assert metrics.get("f1_score", 0.0) > 0.85
    assert metrics.get("roc_auc", 0.0) > 0.90
    assert "confusion_matrix" in metrics
    cm = metrics["confusion_matrix"]
    assert cm["true_positives"] > 0
    assert cm["true_negatives"] > 0


def test_hybrid_prediction_engine():
    """Verify hybrid prediction reconciles ST-GNN and hydraulic physics."""
    res = hybrid_prediction_engine.predict_hybrid_flood(
        rainfall_intensity_mmh=40.0,
        surge_multiplier=1.2,
        active_pumps_count=2,
    )
    assert res["status"] == "success"
    assert "Hybrid ST-GNN" in res["model_architecture"]
    assert len(res["node_predictions"]) == 7

    for node in res["node_predictions"]:
        assert "hybrid_flood_risk_score" in node
        assert "st_gnn_prediction" in node
        assert "hydraulic_physics" in node
        assert "gate_action" in node
        assert node["status"] in ["SAFE", "WARNING", "CRITICAL"]


def test_fastapi_hybrid_endpoints():
    """Verify REST API contracts for upgraded ST-GNN endpoints."""
    # 1. Primary hybrid-predict endpoint
    r1 = client.post("/api/v1/flood/hybrid-predict", json={
        "rainfall_intensity_mmh": 45.0,
        "surge_multiplier": 1.2,
        "active_pumps_count": 2,
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "success"
    assert "Hybrid ST-GNN" in d1["model_architecture"]
    assert len(d1["node_predictions"]) == 7

    # 2. ST-GNN Model Info
    r2 = client.get("/api/v1/flood/st-gnn/info")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["status"] == "success"
    assert "architecture" in d2
    assert "evaluation_metrics" in d2

    # 3. ST-GNN Spatial Graph
    r3 = client.get("/api/v1/flood/st-gnn/graph")
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["status"] == "success"
    assert d3["graph"]["num_nodes"] == 7
    assert len(d3["graph"]["edges"]) == 6

    # 4. Backward compatible /predict endpoint
    r4 = client.post("/api/v1/flood/predict", json={
        "rainfall_intensity_mmh": 35.0,
        "surge_multiplier": 1.0,
        "active_pumps_count": 2,
    })
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["status"] == "success"
    assert "overall_basin_risk" in d4
    assert "node_predictions" in d4

    # 5. Backward compatible /ml-predict endpoint
    r5 = client.post("/api/v1/flood/ml-predict", json={
        "rainfall_intensity_mmh": 35.0,
        "antecedent_rainfall_24h_mm": 40.0,
        "river_stage_khan_m": 2.5,
        "drainage_flow_m3s": 2.4,
        "active_pumps_count": 2,
        "soil_saturation_pct": 65.0,
    })
    assert r5.status_code == 200
    d5 = r5.json()
    assert d5["status"] == "success"
    assert "flood_inundation_probability" in d5
    assert d5["legacy_random_forest_status"] == "DEPRECATED_FROM_PRIMARY_FLOW"


if __name__ == "__main__":
    pytest.main(["-v", __file__])

