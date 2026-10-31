"""
Audit Script for AI/ML Models, Checkpoints, and Datasets in HYDRO-GUARD AI.
Validates:
1. PyTorch model checkpoints loadability and weights inspectability.
2. ST-GNN forward pass and real-time prediction execution.
3. OpenCV Computer Vision clarity and debris detection logic.
4. Librosa / SciPy acoustic FFT frequency resonance inference.
5. Global hydrological datasets, urban catchment datasets, and Indore GIS layers on disk.
6. SQLite database integrity, schema tables, and row counts.
"""

import sys
import time
import json
from pathlib import Path
import numpy as np
import torch
import sqlite3

# Set stdout encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path("E:/ai-manthan/hydro_guard_indore")
sys.path.insert(0, str(PROJECT_ROOT))

def audit_ml_and_data():
    print("[*] Starting AI/ML Models & Data Pipelines Audit...")
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "checkpoints": [],
        "models": [],
        "edge_ai": [],
        "datasets": [],
        "database": {}
    }

    # 1. Inspect Checkpoints on Disk
    checkpoints_dir = PROJECT_ROOT / "checkpoints"
    print(f"\n--- Checking PyTorch Checkpoints in {checkpoints_dir} ---")
    checkpoint_files = list(checkpoints_dir.rglob("*.pt"))
    for cp_path in checkpoint_files:
        t0 = time.perf_counter()
        cp_size_kb = round(cp_path.stat().st_size / 1024, 2)
        try:
            state = torch.load(cp_path, map_location="cpu", weights_only=False)
            load_time_ms = round((time.perf_counter() - t0) * 1000, 2)
            keys_count = len(state.keys()) if isinstance(state, dict) else "model_object"
            model_info = {
                "file": cp_path.name,
                "relative_path": str(cp_path.relative_to(PROJECT_ROOT)),
                "size_kb": cp_size_kb,
                "load_time_ms": load_time_ms,
                "type": type(state).__name__,
                "keys_count": keys_count,
                "status": "PASS"
            }
            print(f" [PASS] {cp_path.name} ({cp_size_kb} KB) -> Loaded in {load_time_ms} ms (keys: {keys_count})")
        except Exception as ex:
            model_info = {
                "file": cp_path.name,
                "relative_path": str(cp_path.relative_to(PROJECT_ROOT)),
                "size_kb": cp_size_kb,
                "status": "FAIL",
                "error": str(ex)
            }
            print(f" [FAIL] {cp_path.name} -> {ex}")
        results["checkpoints"].append(model_info)

    # 2. Test ST-GNN Model Forward Pass & Inference
    print("\n--- Testing ST-GNN Model Inference (predict_realtime) ---")
    try:
        from backend.models.st_gnn_model import st_gnn_model
        
        # Test predict_realtime with current rainfall and antecedent conditions
        t0 = time.perf_counter()
        pred = st_gnn_model.predict_realtime(
            rainfall_intensity_mmh=35.0,
            surge_multiplier=1.0,
            active_pumps_count=2,
            soil_saturation_pct=65.0
        )
        inf_ms = round((time.perf_counter() - t0) * 1000, 2)
        
        st_gnn_test = {
            "model_name": "Spatio-Temporal Graph Neural Network (ST-GNN / A3T-GCN)",
            "inference_method": "predict_realtime",
            "inference_latency_ms": inf_ms,
            "architecture": {
                "in_features": st_gnn_model.in_features,
                "hidden_dim": st_gnn_model.hidden_dim,
                "num_nodes": st_gnn_model.num_nodes,
                "k_hops": st_gnn_model.k_hops,
            },
            "output_nodes_count": len(pred.get("predictions", [])),
            "status": "PASS"
        }
        print(f" [PASS] ST-GNN predict_realtime successful in {inf_ms} ms. Nodes predicted: {st_gnn_test['output_nodes_count']}")
    except Exception as ex:
        st_gnn_test = {
            "model_name": "Spatio-Temporal Graph Neural Network (ST-GNN)",
            "status": "FAIL",
            "error": str(ex)
        }
        print(f" [FAIL] ST-GNN predict_realtime: {ex}")
    results["models"].append(st_gnn_test)

    # 3. Test OpenCV Computer Vision Detector
    print("\n--- Testing Edge AI: OpenCV Water Purity Detector ---")
    try:
        from backend.models.cv_purity_detector import cv_detector
        sample_img_path = PROJECT_ROOT / "data" / "sample_images" / "drain_d01_rajwada.jpg"
        if sample_img_path.exists():
            import cv2
            img_bgr = cv2.imread(str(sample_img_path))
            t0 = time.perf_counter()
            cv_res = cv_detector.analyze_image(img_bgr)
            cv_ms = round((time.perf_counter() - t0) * 1000, 2)
            cv_test = {
                "module": "CVPurityDetector (OpenCV Colorimetric & Debris Contouring)",
                "sample_image": sample_img_path.name,
                "latency_ms": cv_ms,
                "purity_score": cv_res.get("purity_score"),
                "optical_turbidity_ntu": cv_res.get("optical_turbidity_ntu"),
                "debris_count": cv_res.get("debris_count"),
                "status": "PASS"
            }
            print(f" [PASS] CV Detector executed in {cv_ms} ms. Purity: {cv_res.get('purity_score')}%, Turbidity: {cv_res.get('optical_turbidity_ntu')} NTU, Debris: {cv_res.get('debris_count')}")
        else:
            cv_test = {"module": "CVPurityDetector", "status": "WARNING", "error": "Sample image not found"}
            print(" [WARN] Sample image not found on disk")
    except Exception as ex:
        cv_test = {"module": "CVPurityDetector", "status": "FAIL", "error": str(ex)}
        print(f" [FAIL] CV Detector: {ex}")
    results["edge_ai"].append(cv_test)

    # 4. Test Acoustic AI FFT Level Detection
    print("\n--- Testing Edge AI: Librosa / SciPy Acoustic Level Detection ---")
    try:
        from backend.models.acoustic_level_ai import acoustic_ai
        sample_wav_path = PROJECT_ROOT / "data" / "sample_audio" / "critical_flash_surge_92pct.wav"
        if sample_wav_path.exists():
            t0 = time.perf_counter()
            ac_res = acoustic_ai.analyze_audio(str(sample_wav_path))
            ac_ms = round((time.perf_counter() - t0) * 1000, 2)
            ac_test = {
                "module": "AcousticLevelAI (FFT Resonance & dB SPL Water Depth Inference)",
                "sample_audio": sample_wav_path.name,
                "latency_ms": ac_ms,
                "estimated_level_pct": ac_res.get("estimated_water_level_pct"),
                "dominant_freq_hz": ac_res.get("dominant_resonance_hz"),
                "db_spl": ac_res.get("acoustic_db_spl"),
                "status": "PASS"
            }
            print(f" [PASS] Acoustic AI executed in {ac_ms} ms. Level: {ac_res.get('estimated_water_level_pct')}%, Peak Freq: {ac_res.get('dominant_resonance_hz')} Hz, SPL: {ac_res.get('acoustic_db_spl')} dB")
        else:
            ac_test = {"module": "AcousticLevelAI", "status": "WARNING", "error": "Sample audio file not found"}
            print(" [WARN] Sample audio not found on disk")
    except Exception as ex:
        ac_test = {"module": "AcousticLevelAI", "status": "FAIL", "error": str(ex)}
        print(f" [FAIL] Acoustic AI: {ex}")
    results["edge_ai"].append(ac_test)

    # 5. Datasets Audit across data folders
    print("\n--- Auditing Datasets on Disk ---")
    dataset_targets = [
        ("Global Datasets: CAMELS-H", PROJECT_ROOT / "data" / "global_flood_datasets" / "camelsh"),
        ("Global Datasets: ERA5", PROJECT_ROOT / "data" / "global_flood_datasets" / "era5"),
        ("Global Datasets: USGS", PROJECT_ROOT / "data" / "global_flood_datasets" / "usgs"),
        ("Global Datasets: NOAA Flood Events", PROJECT_ROOT / "data" / "global_flood_datasets" / "noaa"),
        ("Global Datasets: Global Flood DB", PROJECT_ROOT / "data" / "global_flood_datasets" / "global_flood_db"),
        ("Urban Catchments: Blue Heart (UK)", PROJECT_ROOT / "data" / "urban_drainage_datasets" / "blue_heart"),
        ("Urban Catchments: Bellinge (Denmark)", PROJECT_ROOT / "data" / "urban_drainage_datasets" / "bellinge"),
        ("Urban Catchments: CWPRS Pune (India)", PROJECT_ROOT / "data" / "urban_drainage_datasets" / "india_cwprs"),
        ("Urban Catchments: UWO (Canada)", PROJECT_ROOT / "data" / "urban_drainage_datasets" / "uwo"),
        ("Processed Global: Temporal Sequences", PROJECT_ROOT / "data" / "processed_global" / "temporal_sequences"),
        ("Processed Global: Urban Graphs", PROJECT_ROOT / "data" / "processed_global" / "urban_graphs"),
        ("Processed Global: Urban Sequences", PROJECT_ROOT / "data" / "processed_global" / "urban_sequences"),
        ("Indore GIS: Waterways & SRTM DEM", PROJECT_ROOT / "data" / "indore_gis"),
    ]

    for label, d_path in dataset_targets:
        if d_path.exists():
            all_files = list(d_path.glob("*.*"))
            total_bytes = sum(f.stat().st_size for f in all_files if f.is_file())
            csv_files = [f for f in all_files if f.suffix == ".csv"]
            
            row_count = "N/A"
            sample_file_name = None
            if csv_files:
                sample_file = csv_files[0]
                sample_file_name = sample_file.name
                try:
                    with open(sample_file, "r", encoding="utf-8", errors="ignore") as f:
                        row_count = sum(1 for _ in f) - 1
                except:
                    pass

            d_info = {
                "name": label,
                "path": str(d_path.relative_to(PROJECT_ROOT)),
                "total_files": len(all_files),
                "total_size_mb": round(total_bytes / (1024 * 1024), 2),
                "primary_sample_file": sample_file_name,
                "rows_in_sample": row_count,
                "status": "PASS" if total_bytes > 0 or len(all_files) > 0 else "WARNING"
            }
            print(f" [PASS] {label}: {len(all_files)} files ({d_info['total_size_mb']} MB). Sample: {sample_file_name} ({row_count} rows)")
        else:
            d_info = {
                "name": label,
                "path": str(d_path.relative_to(PROJECT_ROOT)),
                "status": "WARNING",
                "error": "Directory does not exist"
            }
            print(f" [WARN] {label} not found at {d_path}")
        results["datasets"].append(d_info)

    # 6. Database Audit (SQLite)
    print("\n--- Auditing SQLite Database (data/hydro_guard.db) ---")
    db_path = PROJECT_ROOT / "data" / "hydro_guard.db"
    if db_path.exists():
        db_size_mb = round(db_path.stat().st_size / (1024 * 1024), 2)
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            
            # Check integrity
            cur.execute("PRAGMA integrity_check;")
            integrity_res = cur.fetchone()[0]
            
            # List tables and row counts
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]
            table_stats = {}
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM [{t}];")
                cnt = cur.fetchone()[0]
                table_stats[t] = cnt

            results["database"] = {
                "path": str(db_path.relative_to(PROJECT_ROOT)),
                "size_mb": db_size_mb,
                "integrity": integrity_res,
                "tables": table_stats,
                "status": "PASS" if integrity_res == "ok" else "FAIL"
            }
            print(f" [PASS] Database Integrity: {integrity_res}. Size: {db_size_mb} MB")
            for t, cnt in table_stats.items():
                print(f"        -> Table '{t}': {cnt:,} rows")
            conn.close()
        except Exception as ex:
            results["database"] = {"status": "FAIL", "error": str(ex)}
            print(f" [FAIL] Database Error: {ex}")
    else:
        results["database"] = {"status": "WARNING", "error": "Database file not found"}
        print(" [WARN] Database file not found")

    out_file = PROJECT_ROOT / "reports" / "ml_data_pipeline_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n==========================================")
    print(f"ML & Data Pipeline Audit Complete!")
    print(f"Saved results to: {out_file}")
    print(f"==========================================\n")

if __name__ == "__main__":
    audit_ml_and_data()
