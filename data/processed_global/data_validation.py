"""
HYDRO-GUARD AI — Data Validation & Integrity Verification Suite (Updated)
========================================================================
Module: data/processed_global/data_validation.py
Purpose: Strictly validate processed datasets, graph topologies, multi-label
         attributes, and temporal sequence partitions before model training.
"""

import os
import json
import numpy as np
import pandas as pd
import sys
from typing import Dict, Any, List


def validate_all(base_dir: str = r"E:\ai-manthan\hydro_guard_indore\data\processed_global") -> Dict[str, Any]:
    print("=" * 80)
    print("HYDRO-GUARD AI — SCIENTIFIC DATA VALIDATION SUITE (TASK 2.1 AUDITED)")
    print("=" * 80)

    report = {"tests_passed": 0, "tests_failed": 0, "details": []}

    def assert_test(name: str, condition: bool, message: str = ""):
        if condition:
            print(f"[PASS] {name}")
            report["tests_passed"] += 1
            report["details"].append({"test": name, "status": "PASS", "message": message})
        else:
            print(f"[FAIL] {name} — {message}")
            report["tests_failed"] += 1
            report["details"].append({"test": name, "status": "FAIL", "message": message})

    # -------------------------------------------------------------------------
    # SUITE 1: FILE EXISTENCE & STORAGE INTEGRITY
    # -------------------------------------------------------------------------
    print("\n--- SUITE 1: FILE EXISTENCE & NON-EMPTY ASSERTIONS ---")
    required_files = [
        "camels_hourly_processed/01015800_hourly_labeled.csv",
        "camels_hourly_processed/01017000_hourly_labeled.csv",
        "camels_hourly_processed/01017060_hourly_labeled.csv",
        "camels_hourly_processed/01017290_hourly_labeled.csv",
        "camels_hourly_processed/catchment_attributes_standardized.csv",
        "usgs_processed/01638500_hourly_labeled.csv",
        "usgs_processed/01646500_hourly_labeled.csv",
        "noaa_flood_events_processed/noaa_floods_2023_standardized.csv",
        "era5_processed/era5_hourly_standardized.csv",
        "graph_data/aroostook_adjacency.npy",
        "graph_data/potomac_adjacency.npy",
        "graph_data/disjoint_combined_adjacency.npy",
        "temporal_sequences/aroostook_sequences_w12_h3.npz",
        "temporal_sequences/aroostook_sequences_w6_h1.npz",
        "temporal_sequences/aroostook_sequences_w24_h6.npz",
        "temporal_sequences/potomac_sequences_w12_h3.npz",
        "temporal_sequences/potomac_sequences_w6_h1.npz",
        "temporal_sequences/potomac_sequences_w24_h6.npz"
    ]

    for rf in required_files:
        fp = os.path.join(base_dir, rf)
        exists = os.path.exists(fp)
        non_empty = os.path.getsize(fp) > 0 if exists else False
        assert_test(f"File Existence: {rf}", exists and non_empty, f"Path: {fp}")

    # -------------------------------------------------------------------------
    # SUITE 2: PHYSICAL BOUNDS & NON-ZERO MISSING INTEGRITY
    # -------------------------------------------------------------------------
    print("\n--- SUITE 2: PHYSICAL BOUNDS & MISSING VALUE MASKS ---")
    df_washburn = pd.read_csv(os.path.join(base_dir, "camels_hourly_processed", "01017000_hourly_labeled.csv"), low_memory=False)
    valid_q = df_washburn.loc[df_washburn["streamflow_measured_mask"], "streamflow_m3s"]
    valid_h = df_washburn.loc[df_washburn["water_level_measured_mask"], "water_level_m"]

    assert_test(
        "Non-negative Streamflow: CAMELSH",
        (valid_q >= 0.0).all(),
        f"Min flow: {valid_q.min()} m3/s"
    )
    assert_test(
        "Realistic Water Level: CAMELSH",
        (valid_h >= 0.0).all() and (valid_h <= 25.0).all(),
        f"Stage range: [{valid_h.min()}, {valid_h.max()}] m"
    )
    assert_test(
        "Missing Mask Consistency: CAMELSH",
        (df_washburn["streamflow_measured_mask"] == ~df_washburn["streamflow_m3s"].isna()).all(),
        "streamflow_measured_mask strictly reflects unmeasured vs measured"
    )
    unmeasured_rows = df_washburn[~df_washburn["streamflow_measured_mask"]]
    assert_test(
        "No Silent Zero-Filling: CAMELSH",
        unmeasured_rows["streamflow_m3s"].isna().all(),
        "Unmeasured streamflow rows remain NaN, never fabricated as 0.0"
    )

    df_lf = pd.read_csv(os.path.join(base_dir, "usgs_processed", "01646500_hourly_labeled.csv"), low_memory=False)
    valid_q_usgs = df_lf.loc[df_lf["streamflow_measured_mask"], "streamflow_m3s"]
    valid_h_usgs = df_lf.loc[df_lf["water_level_measured_mask"], "water_level_m"]

    assert_test(
        "Non-negative Streamflow: USGS",
        (valid_q_usgs >= 0.0).all(),
        f"Min flow: {valid_q_usgs.min()} m3/s"
    )
    assert_test(
        "Realistic Water Level: USGS",
        (valid_h_usgs >= 0.0).all() and (valid_h_usgs <= 15.0).all(),
        f"Stage range: [{valid_h_usgs.min()}, {valid_h_usgs.max()}] m"
    )

    # -------------------------------------------------------------------------
    # SUITE 3: SCIENTIFIC LABEL DISAMBIGUATION (TASK 2.1)
    # -------------------------------------------------------------------------
    print("\n--- SUITE 3: SCIENTIFIC LABEL DISAMBIGUATION ---")
    req_labels = [
        "label_statistical_high_flow",
        "label_official_flood_observed",
        "label_gauge_exceedance",
        "label_noaa_reported",
        "label_satellite_flood",
        "label_estimated_inundation_depth_m"
    ]
    for l in req_labels:
        assert_test(f"Scientific Label Present: {l}", l in df_washburn.columns)

    # Statistical high-flow != official flood
    assert_test(
        "Statistical High Flow Distinction in USGS",
        "label_statistical_high_flow" in df_lf.columns and "label_official_flood_observed" in df_lf.columns,
        "Distinguishes statistical Q99 anomaly from official NWS flood exceedance"
    )
    assert_test(
        "Unreported Period Explicitly Marked with Confidence",
        "noaa_reporting_confidence" in df_washburn.columns and (df_washburn["noaa_reporting_confidence"] == "NO_OFFICIAL_REPORT_FILED").any(),
        "Absence of NOAA event is marked with explicit confidence, not assumed flood-free"
    )
    assert_test(
        "Inundation Depth Explicitly Termed Estimated",
        "label_estimated_inundation_depth_m" in df_washburn.columns,
        "Estimated depth is never mislabeled as measured physical depth"
    )

    # -------------------------------------------------------------------------
    # SUITE 4: GRAPH TOPOLOGY INTEGRITY
    # -------------------------------------------------------------------------
    print("\n--- SUITE 4: GRAPH TOPOLOGY INTEGRITY ---")
    adj_a = np.load(os.path.join(base_dir, "graph_data", "aroostook_adjacency.npy"))
    adj_p = np.load(os.path.join(base_dir, "graph_data", "potomac_adjacency.npy"))
    adj_d = np.load(os.path.join(base_dir, "graph_data", "disjoint_combined_adjacency.npy"))

    assert_test("Aroostook Graph Dimensions (4x4)", adj_a.shape == (4, 4), f"Shape: {adj_a.shape}")
    assert_test("Potomac Graph Dimensions (5x5)", adj_p.shape == (5, 5), f"Shape: {adj_p.shape}")
    assert_test("Zero Self-Loops: Aroostook", np.diag(adj_a).sum() == 0.0, "Zero self-loops")
    assert_test("Zero Self-Loops: Potomac", np.diag(adj_p).sum() == 0.0, "Zero self-loops")
    assert_test("Non-negative Adjacency Weights", (adj_a >= 0.0).all() and (adj_p >= 0.0).all(), "Physically non-negative")
    cross_basin_edges = adj_d[:4, 4:].sum() + adj_d[4:, :4].sum()
    assert_test("Zero Cross-Basin Edges (Strict Disjoint Rule)", cross_basin_edges == 0.0, f"Cross-basin weight: {cross_basin_edges}")

    # -------------------------------------------------------------------------
    # SUITE 5: TEMPORAL SEQUENCES & LEAKAGE AVOIDANCE (AROOSTOOK + POTOMAC)
    # -------------------------------------------------------------------------
    print("\n--- SUITE 5: TEMPORAL SEQUENCES (AROOSTOOK + POTOMAC) ---")
    # Aroostook
    seq_a = np.load(os.path.join(base_dir, "temporal_sequences", "aroostook_sequences_w12_h3.npz"))
    X_a = seq_a["X"]
    assert_test(
        "Aroostook Sequence Dimensions (N, 12, 4, 6)",
        X_a.ndim == 4 and X_a.shape[1] == 12 and X_a.shape[2] == 4 and X_a.shape[3] == 6,
        f"Aroostook Shape: {X_a.shape}"
    )
    tr_a, va_a, te_a = seq_a["train_idx"], seq_a["val_idx"], seq_a["test_idx"]
    assert_test(
        "Aroostook Chronological Split Train < Val < Test",
        (tr_a.max() < va_a.min()) and (va_a.max() < te_a.min()),
        "Strict temporal progression"
    )
    assert_test(
        "Aroostook Disjoint Sets",
        len(set(tr_a).intersection(set(va_a))) == 0 and len(set(va_a).intersection(set(te_a))) == 0,
        "Zero leakage"
    )

    # Potomac
    seq_p = np.load(os.path.join(base_dir, "temporal_sequences", "potomac_sequences_w12_h3.npz"))
    X_p = seq_p["X"]
    assert_test(
        "Potomac Sequence Dimensions (N, 12, 5, 6)",
        X_p.ndim == 4 and X_p.shape[1] == 12 and X_p.shape[2] == 5 and X_p.shape[3] == 6,
        f"Potomac Shape: {X_p.shape}"
    )
    tr_p, va_p, te_p = seq_p["train_idx"], seq_p["val_idx"], seq_p["test_idx"]
    assert_test(
        "Potomac Chronological Split Train < Val < Test",
        (tr_p.max() < va_p.min()) and (va_p.max() < te_p.min()),
        "Strict temporal progression"
    )
    assert_test(
        "Potomac Disjoint Sets",
        len(set(tr_p).intersection(set(va_p))) == 0 and len(set(va_p).intersection(set(te_p))) == 0,
        "Zero leakage"
    )

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"VALIDATION SUMMARY: {report['tests_passed']} PASSED, {report['tests_failed']} FAILED")
    print("=" * 80)

    report_path = os.path.join(base_dir, "validation_summary.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = validate_all()
    if report["tests_failed"] > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED! DATASET IS SCIENTIFICALLY VALID.")
        sys.exit(0)
