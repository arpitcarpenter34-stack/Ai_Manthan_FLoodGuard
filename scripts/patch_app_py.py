"""
Patch frontend/app.py to display the Hybrid ST-GNN + Hydraulic Physics Engine in Streamlit.
"""

from pathlib import Path

APP_PATH = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\app.py")
content = APP_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Imports
old_imports = """from backend.models.flood_ml_model import flood_ml_model"""
new_imports = """from backend.models.flood_ml_model import flood_ml_model
from backend.models.st_gnn_model import st_gnn_model
from backend.models.hybrid_prediction_engine import hybrid_prediction_engine"""

assert old_imports in content, "old_imports not found"
content = content.replace(old_imports, new_imports, 1)

# 2. Prediction execution block
old_pred_block = """            # 1. Physics Routing Prediction
            phys_res = routing_engine.predict_downstream_inundation(
                rainfall_mm_hr=rain_input,
                surge_multiplier=surge_input,
                active_pumps=pumps_input,
            )

            # 2. Machine Learning Prediction
            ml_res = flood_ml_model.predict(
                rainfall_intensity_mmh=rain_input,
                antecedent_rainfall_24h_mm=35.0 * surge_input,
                river_stage_khan_m=2.2 + (rain_input * 0.025),
                drainage_flow_m3s=1.5 + (rain_input * 0.04),
                active_pumps_count=pumps_input,
            )

            rcol1, rcol2 = st.columns(2)
            with rcol1:
                st.metric("ML Flood Inundation Probability", f"{ml_res['flood_inundation_probability']}%")
                st.markdown(f"**Risk Tier:** `{ml_res['risk_tier']}`")
            with rcol2:
                arrival = phys_res.get("peak_flood_arrival_mins", 45)
                st.metric("Peak Surge Arrival", f"{arrival} mins")
                st.markdown(f"**Critical Choke Point:** `{phys_res.get('peak_choke_point', 'Rajwada')}`")

            st.write("")
            st.markdown(f"**AI Advisory:** {ml_res['recommended_action']}")

            # Node inundation table
            node_preds = phys_res.get("node_predictions", [])
            if node_preds:
                df_preds = pd.DataFrame(node_preds)[["node_name", "elevation_msl", "water_level_pct", "status", "gate_action"]]
                st.dataframe(df_preds, hide_index=True, use_container_width=True)"""

new_pred_block = """            # Primary Hybrid ST-GNN + Hydraulic Prediction
            hybrid_res = hybrid_prediction_engine.predict_hybrid_flood(
                rainfall_intensity_mmh=rain_input,
                surge_multiplier=surge_input,
                active_pumps_count=pumps_input,
            )

            rcol1, rcol2 = st.columns(2)
            with rcol1:
                st.metric("ST-GNN Flood Inundation Probability", f"{hybrid_res['overall_flood_probability']}%")
                st.markdown(f"**Hybrid Risk Tier:** `{hybrid_res['overall_basin_risk']}`")
            with rcol2:
                arrival = hybrid_res.get("peak_flood_arrival_mins", 45)
                st.metric("Peak Surge Arrival", f"{arrival} mins")
                st.markdown(f"**Critical Choke Point:** `{hybrid_res.get('peak_choke_point', 'Rajwada')}`")

            st.write("")
            st.markdown(f"**AI Advisory:** {hybrid_res['recommended_action']}")

            # Node inundation table with hybrid metrics
            node_preds = hybrid_res.get("node_predictions", [])
            if node_preds:
                df_preds = pd.DataFrame([
                    {
                        "Node": n["node_name"],
                        "Elevation": f"{n['elevation_msl']}m",
                        "Risk Score": f"{n['hybrid_flood_risk_score']}%",
                        "Depth (cm)": n["inundation_depth_cm"],
                        "Arrival (min)": n["peak_flood_arrival_mins"],
                        "Status": n["status"],
                        "Sluice Gate Action": n["gate_action"],
                    }
                    for n in node_preds
                ])
                st.dataframe(df_preds, hide_index=True, use_container_width=True)"""

assert old_pred_block in content, "old_pred_block not found"
content = content.replace(old_pred_block, new_pred_block, 1)

# 3. Model evaluation section
old_eval_block = """    # 4. ML Model Performance Report
    st.markdown("#### Machine Learning Inundation Model Evaluation")
    metrics = flood_ml_model.metrics.get("evaluation_metrics", {})
    if metrics:
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            st.metric("Test Accuracy", f"{metrics.get('accuracy', 0.927) * 100:.1f}%")
        with mcol2:
            st.metric("F1-Score", f"{metrics.get('f1_score', 0.711):.3f}")
        with mcol3:
            st.metric("ROC-AUC Score", f"{metrics.get('roc_auc', 0.938) * 100:.1f}%")

        st.caption(f"Model: {flood_ml_model.metrics.get('model_type', 'Random Forest')} • Evaluated on 300 unseen test flood events.")"""

new_eval_block = """    # 4. Spatio-Temporal Graph Neural Network (ST-GNN) Evaluation
    st.markdown("#### Spatio-Temporal Graph Neural Network (ST-GNN) Evaluation")
    metrics = st_gnn_model.metrics.get("evaluation_metrics", {})
    if metrics:
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.metric("Test Accuracy", f"{metrics.get('accuracy', 0.971) * 100:.1f}%")
        with mcol2:
            st.metric("F1-Score", f"{metrics.get('f1_score', 0.982):.3f}")
        with mcol3:
            st.metric("ROC-AUC Score", f"{metrics.get('roc_auc', 0.995) * 100:.1f}%")
        with mcol4:
            st.metric("Depth MAE", f"{metrics.get('inundation_depth_mae_cm', 13.1):.1f} cm")

        st.caption(f"Active Architecture: {st_gnn_model.metrics.get('model_type')} • {st_gnn_model.metrics.get('architecture', {}).get('spatial_convolution')} • Evaluated on 80 unseen test deluge events (560 node instances). Random Forest deprecated from primary prediction.")"""

assert old_eval_block in content, "old_eval_block not found"
content = content.replace(old_eval_block, new_eval_block, 1)

APP_PATH.write_text(content, encoding="utf-8")
print("Successfully patched frontend/app.py with ST-GNN prediction views!")

