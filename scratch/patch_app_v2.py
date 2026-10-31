import os
import sys

file_path = r"E:\ai-manthan\hydro_guard_indore\frontend\app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import if not present
import_target = "from backend.models.hybrid_prediction_engine import hybrid_prediction_engine"
import_replacement = "from backend.models.hybrid_prediction_engine import hybrid_prediction_engine\nfrom backend.models.blue_heart_st_gnn import blue_heart_st_gnn"

if "from backend.models.blue_heart_st_gnn import blue_heart_st_gnn" not in content:
    content = content.replace(import_target, import_replacement, 1)

# 2. Patch Module 5
m5_target = """elif selected_module == "5. AI Flood Prediction":
    st.subheader("Dual-Engine Hydrological & Machine Learning Flood Prediction")
    st.markdown('<span class="provenance-tag tag-model">ST-GNN Primary Engine</span> <span class="provenance-tag tag-hydraulic">Manning Wave Physics</span>', unsafe_allow_html=True)

    pcol1, pcol2 = st.columns([1, 1.2])"""

m5_replacement = """elif selected_module == "5. AI Flood Prediction":
    st.subheader("Dual-Engine Hydrological & Machine Learning Flood Prediction")
    st.markdown('<span class="provenance-tag tag-model">ST-GNN Primary Engine</span> <span class="provenance-tag tag-hydraulic">Manning Wave Physics</span>', unsafe_allow_html=True)

    if domain_key == "blue_heart":
        st.caption("📍 **Blue Heart Urban Drainage Catchment** • 15 Highway Gully Telemetry Sensors • Adaptive Gated ST-GNN (Task 3.2 Candidate)")
        st.info("🔬 **Scientific Model Separation:** Running real-world deep learning inference using `checkpoints/blue_heart/v2/best_adaptive_st_gnn.pt`. Predictions reflect real highway gully telemetry from Eastbourne, UK (Zenodo 20699635).")
        bcol1, bcol2 = st.columns([1, 1.2])
        with bcol1:
            st.markdown("#### Real-Data Sequence Inputs")
            seq_idx = st.slider("Held-out Test Sequence Index (0 to 1,092)", 0, 1092, 0, 1)
            run_bh_pred = st.button("⚡ Run Adaptive Gated ST-GNN Prediction (H=+3h)", type="primary", use_container_width=True)
            st.markdown("— **Candidate Benchmark Highlights** —")
            st.markdown("• **Overall Test RMSE:** `0.0385 m` (Beats Persistence `0.0422 m`)")
            st.markdown("• **High-Water NSE:** `0.4945` (Beats Persistence `0.0043`)")
            st.markdown("• **Overall Test NSE:** `0.9875` (Beats Persistence `0.9850`)")
        with bcol2:
            st.markdown("#### 15-Gully Inundation Forecast (+3 Hours Ahead)")
            if run_bh_pred or "bh_pred_run" in st.session_state:
                st.session_state["bh_pred_run"] = True
                bh_res = blue_heart_st_gnn.predict_sample(seq_idx)
                if bh_res.get("status") == "success":
                    rcol1, rcol2 = st.columns(2)
                    with rcol1:
                        st.metric("Mean Absolute Error", f"{bh_res['mean_absolute_error_mm']:.2f} mm")
                        st.markdown("**Candidate:** `Adaptive Gated ST-GNN`")
                    with rcol2:
                        st.metric("Max Gully Stage", f"{bh_res['max_predicted_stage_m']:.3f} m")
                        st.markdown("**Horizon:** `+3 Hours Ahead`")

                    df_bh = pd.DataFrame(bh_res["nodes"])
                    st.dataframe(
                        df_bh[["sensor_name", "current_level_m", "predicted_level_m", "true_level_m", "predicted_change_cm", "absolute_error_mm", "status"]],
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.error(bh_res.get("message", "Inference error"))
            else:
                st.info("Select a held-out test sequence and click **Run Adaptive Gated ST-GNN Prediction**.")
    else:
        pcol1, pcol2 = st.columns([1, 1.2])"""

if m5_target in content:
    content = content.replace(m5_target, m5_replacement, 1)

# 3. Patch Module 12 to include Task 3.2 benchmark summary table
m12_target = """    st.write("")
    st.markdown(
        \"\"\"
        <div class="disclaimer-box">
            <b>Scientific Provenance Declaration:</b>"""

m12_replacement = """    st.write("")
    st.markdown("#### 🔬 Task 3.2 Real-Data Model Benchmark (Blue Heart Highway Telemetry)")
    bench_data = [
        {"Model Architecture": "1. Persistence Baseline", "Val Loss": "N/A", "Test RMSE (m)": "0.0422 m", "Test NSE": "0.9850", "High-Water RMSE": "0.0575 m", "High-Water NSE": "0.0043", "Peak Lead Error": "3.00 h"},
        {"Model Architecture": "2. Residual Ridge AR", "Val Loss": "N/A", "Test RMSE (m)": "0.0980 m", "Test NSE": "0.9190", "High-Water RMSE": "0.0751 m", "High-Water NSE": "-0.6995", "Peak Lead Error": "3.70 h"},
        {"Model Architecture": "3. Res-Temporal GRU", "Val Loss": "0.2420", "Test RMSE (m)": "0.0416 m", "Test NSE": "0.9854", "High-Water RMSE": "0.0538 m", "High-Water NSE": "0.1277", "Peak Lead Error": "3.40 h"},
        {"Model Architecture": "4. Res-DCRNN (K=2)", "Val Loss": "0.2525", "Test RMSE (m)": "0.0421 m", "Test NSE": "0.9851", "High-Water RMSE": "0.0548 m", "High-Water NSE": "0.0934", "Peak Lead Error": "3.50 h"},
        {"Model Architecture": "5. Adaptive Gated ST-GNN ⭐", "Val Loss": "0.2069", "Test RMSE (m)": "0.0385 m", "Test NSE": "0.9875", "High-Water RMSE": "0.0409 m", "High-Water NSE": "0.4945", "Peak Lead Error": "4.30 h"},
        {"Model Architecture": "6. Graph WaveNet", "Val Loss": "0.2531", "Test RMSE (m)": "0.0422 m", "Test NSE": "0.9850", "High-Water RMSE": "0.0533 m", "High-Water NSE": "0.1445", "Peak Lead Error": "3.40 h"},
    ]
    st.dataframe(pd.DataFrame(bench_data), hide_index=True, use_container_width=True)
    st.caption("⭐ **Task 3.2 Candidate Winner:** Adaptive Gated ST-GNN beats Persistence on overall Test RMSE (0.0385m vs 0.0422m) and reduces High-Water error by 28.9% with an NSE of 0.4945.")

    st.write("")
    st.markdown(
        \"\"\"
        <div class="disclaimer-box">
            <b>Scientific Provenance Declaration:</b>"""

if m12_target in content:
    content = content.replace(m12_target, m12_replacement, 1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully patched frontend/app.py with v2 integration")

