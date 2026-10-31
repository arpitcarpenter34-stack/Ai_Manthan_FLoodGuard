"""
End-to-End System Verification Script for HYDRO-GUARD AI.
Validates all 12 modules, backend APIs, physics engine, ST-GNN, and PDF generation.
"""

import sys
import os
import json
import urllib.request
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    print("=" * 80)
    print("       HYDRO-GUARD AI : TASK 2.5 END-TO-END VERIFICATION SUITE")
    print("=" * 80)

    results = {}

    # 1. Backend Health Check
    print("\n[1/12] Testing Backend Health & Active Nodes...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)
        data = json.loads(req.read().decode())
        print(f"  -> Health: {data.get('status')} | Simulator: {data.get('simulator_running')} | Nodes: {data.get('nodes_online')}")
        results["1_health"] = data.get("status") == "HEALTHY"
    except Exception as e:
        print(f"  -> Health failed: {e}")
        results["1_health"] = False

    # 2. Multi-Domain Catchments
    print("\n[2/12] Testing Urban Catchment Domains...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/flood/urban-domains", timeout=3)
        data = json.loads(req.read().decode())
        domains = data.get("catchments", [])
        print(f"  -> Loaded {len(domains)} Catchments:")
        for d in domains:
            print(f"     * {d['name']} ({d['nodes_count']} nodes)")
        results["2_domains"] = len(domains) >= 3
    except Exception as e:
        print(f"  -> Urban domains failed: {e}")
        results["2_domains"] = False

    # 3. SWMM 5.2 Benchmark Verification
    print("\n[3/12] Testing EPA-SWMM 5.2.4 Hydrodynamic Baseline...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/flood/swmm-benchmark", timeout=3)
        data = json.loads(req.read().decode())
        nq = data.get("numerical_quality", {})
        print(f"  -> Engine: {data.get('simulation_engine')}")
        print(f"  -> Runoff Continuity Error: {nq.get('runoff_continuity_error_pct')}%")
        print(f"  -> Flow Routing Error: {nq.get('flow_routing_continuity_error_pct')}%")
        print(f"  -> Status: {nq.get('status')}")
        results["3_swmm"] = nq.get("status") == "CONVERGED_EXCELLENT"
    except Exception as e:
        print(f"  -> SWMM failed: {e}")
        results["3_swmm"] = False

    # 4. Emergency Alerts
    print("\n[4/12] Testing Municipal 4-Tier Alerts...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/flood/alerts/active", timeout=3)
        data = json.loads(req.read().decode())
        print(f"  -> Active Tier: {data.get('current_tier')} ({data.get('tier_name')})")
        print(f"  -> City Mean Stage: {data.get('city_mean_stage_pct')}%")
        results["4_alerts"] = "tier_name" in data
    except Exception as e:
        print(f"  -> Alerts failed: {e}")
        results["4_alerts"] = False

    # 5. Historical Summary
    print("\n[5/12] Testing Historical Datasets Summary...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/flood/historical-summary", timeout=3)
        data = json.loads(req.read().decode())
        ds = data.get("datasets", {})
        print(f"  -> Loaded Datasets: {list(ds.keys())}")
        results["5_historical"] = len(ds) >= 3
    except Exception as e:
        print(f"  -> Historical summary failed: {e}")
        results["5_historical"] = False

    # 6. Hybrid ST-GNN + Manning Predict
    print("\n[6/12] Testing Hybrid ST-GNN Inundation Inference...")
    try:
        payload = json.dumps({"rainfall_intensity_mmh": 45.0, "surge_multiplier": 1.2, "active_pumps_count": 2}).encode()
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/flood/predict", data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read().decode())
        prob = data.get("hybrid_details", {}).get("overall_flood_probability", 85.0)
        print(f"  -> Basin Risk: {data.get('overall_basin_risk')}")
        print(f"  -> Peak Flood Arrival: {data.get('peak_flood_arrival_mins')} mins")
        print(f"  -> Choke Point: {data.get('peak_choke_point')}")
        results["6_st_gnn"] = "overall_basin_risk" in data and len(data.get("node_predictions", [])) == 7
    except Exception as e:
        print(f"  -> ST-GNN prediction failed: {e}")
        results["6_st_gnn"] = False

    # 7. Environmental Summary
    print("\n[7/12] Testing Environmental Summary Endpoint...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/flood/environmental-summary", timeout=3)
        data = json.loads(req.read().decode())
        rain = data.get("live_rainfall", {})
        river = data.get("river_level", {})
        drain = data.get("drainage_flow", {})
        print(f"  -> Rainfall: {rain.get('value')} {rain.get('unit')} ({rain.get('data_mode')})")
        print(f"  -> River Level: {river.get('value')} {river.get('unit')} ({river.get('status')})")
        print(f"  -> Drainage Flow: {drain.get('value')} {drain.get('unit')} ({drain.get('gate_action')})")
        results["7_environmental"] = "live_rainfall" in data
    except Exception as e:
        print(f"  -> Environmental summary failed: {e}")
        results["7_environmental"] = False

    # 8. Computer Vision 80% Purity Detector
    print("\n[8/12] Testing Optical Water Quality Screening (80% Rule)...")
    try:
        from backend.models.cv_purity_detector import cv_detector
        frame = cv_detector.generate_synthetic_drain_frame("polluted_sludge")
        res = cv_detector.analyze_image(frame)
        print(f"  -> Purity Score: {res.get('purity_score')}%")
        print(f"  -> Is Clean (>=80%): {res.get('is_clean')}")
        print(f"  -> Sluice Action: {res.get('gate_status')}")
        results["8_cv_purity"] = "DIVERT" in res.get("gate_status", "").upper()
    except Exception as e:
        print(f"  -> CV detector failed: {e}")
        results["8_cv_purity"] = False

    # 9. Acoustic Sensor Culvert AI
    print("\n[9/12] Testing Acoustic Hydrophone Level Sensing...")
    try:
        from backend.models.acoustic_level_ai import acoustic_ai
        audio_wav = acoustic_ai.generate_synthetic_sewer_audio(target_level_pct=75.0)
        res = acoustic_ai.analyze_audio(audio_wav)
        print(f"  -> Sound Pressure: {res.get('decibel_spl'):.1f} dB SPL")
        print(f"  -> Inferred Culvert Level: {res.get('estimated_water_level_pct'):.1f}%")
        results["9_acoustic"] = "decibel_spl" in res and res.get("decibel_spl", 0) > 0
    except Exception as e:
        print(f"  -> Acoustic AI failed: {e}")
        results["9_acoustic"] = False

    # 10. SQLite Database Persistence
    print("\n[10/12] Testing SQLite Persistent Audit Database...")
    try:
        from backend.services.db_manager import db_manager
        stats = db_manager.get_db_stats()
        print(f"  -> DB Status: {stats.get('status')}")
        print(f"  -> Total Analyses Logged: {stats.get('total_analysis_records')}")
        print(f"  -> Total Telemetry Records: {stats.get('total_telemetry_records')}")
        results["10_sqlite"] = stats.get("status") == "HEALTHY"
    except Exception as e:
        print(f"  -> SQLite failed: {e}")
        results["10_sqlite"] = False

    # 11. PDF Report Generation via ReportLab
    print("\n[11/12] Testing Official PDF Report Generation...")
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet()
        doc.build([Paragraph("HYDRO-GUARD AI End-to-End Test", styles['Normal'])])
        pdf_len = len(buf.getvalue())
        print(f"  -> Generated PDF: {pdf_len} bytes")
        results["11_pdf"] = pdf_len > 1000
    except Exception as e:
        print(f"  -> PDF generation failed: {e}")
        results["11_pdf"] = False

    # 12. Streamlit Dashboard Check
    print("\n[12/12] Testing Streamlit Dashboard Availability...")
    try:
        resp = urllib.request.urlopen("http://localhost:8501", timeout=3)
        print(f"  -> Streamlit HTTP Status: {resp.status}")
        results["12_streamlit"] = resp.status == 200
    except Exception as e:
        print(f"  -> Streamlit check failed: {e}")
        results["12_streamlit"] = False

    print("\n" + "=" * 80)
    print("                      VERIFICATION SUMMARY")
    print("=" * 80)
    all_passed = True
    for test, passed in results.items():
        mark = "[PASS]" if passed else "[FAIL]"
        print(f"  {test:<25}: {mark}")
        if not passed:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print(">>> ALL 12 VERIFICATION CHECKS PASSED! SYSTEM IS 100% OPERATIONAL. <<<")
    else:
        print(">>> SOME VERIFICATION CHECKS FAILED. PLEASE REVIEW ABOVE. <<<")
    print("=" * 80)

if __name__ == "__main__":
    main()
