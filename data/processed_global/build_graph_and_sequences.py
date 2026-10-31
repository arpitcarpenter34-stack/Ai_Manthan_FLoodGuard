"""
HYDRO-GUARD AI — Graph Topology & Temporal Sequence Constructor (Updated)
========================================================================
Module: data/processed_global/build_graph_and_sequences.py
Purpose: Construct physically grounded Directed Acyclic Graphs (DAGs) and
         chronologically partitioned ST-GNN sequence tensors for both
         the Aroostook River Network (4 nodes) and Potomac River Network (5 nodes).
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


def build_aroostook_graph(processed_base_dir: str):
    """
    Constructs the 4-node Aroostook River Basin graph from CAMELSH data.
    Node Ordering:
    0: 01015800 (Aroostook River nr Masardis) - Upstream mainstem
    1: 01017060 (Hardwood Brook nr Caribou) - Tributary
    2: 01017290 (Little Madawaska River nr Caribou) - Lateral tributary
    3: 01017000 (Aroostook River at Washburn) - Downstream confluence exit
    """
    node_ids = ["01015800", "01017060", "01017290", "01017000"]
    node_names = [
        "Aroostook River nr Masardis, ME",
        "Hardwood Brook nr Caribou, ME",
        "Little Madawaska River nr Caribou, ME",
        "Aroostook River at Washburn, ME"
    ]
    node_roles = [
        "UPSTREAM_MAINSTEM",
        "TRIBUTARY_INFLOW",
        "LATERAL_TRIBUTARY",
        "DOWNSTREAM_CONFLUENCE"
    ]
    coords = [
        (46.5230, -68.3718),
        (46.7836, -67.9892),
        (46.8886, -67.9450),
        (46.7773, -68.1572)
    ]
    drainage_areas = [2313.75, 14.86, 594.58, 4278.91] # km2
    elevations = [161.5, 140.2, 121.9, 114.3] # meters

    num_nodes = len(node_ids)
    adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)

    # Directed physical reaches:
    # 0 -> 3 (Masardis to Washburn): L = 38.4 km
    # 1 -> 3 (Hardwood Brook to Washburn): L = 14.2 km
    # 2 -> 3 (Little Madawaska to Washburn corridor): L = 22.6 km
    edges = [
        (0, 3, 38.4, 47.2),
        (1, 3, 14.2, 25.9),
        (2, 3, 22.6, 7.6)
    ]

    sigma_L = 40.0
    for u, v, length_km, drop_m in edges:
        area_ratio = np.sqrt(drainage_areas[u] / drainage_areas[v])
        weight = float(np.exp(-(length_km / sigma_L)**2) * area_ratio)
        adj[u, v] = weight

    static_feats = np.array([
        [drainage_areas[i], elevations[i], coords[i][0], coords[i][1]]
        for i in range(num_nodes)
    ], dtype=np.float32)

    metadata = {
        "graph_name": "Aroostook_River_Basin",
        "hydrologic_region": "HUC02-01 (New England)",
        "num_nodes": num_nodes,
        "node_ordering": node_ids,
        "nodes": [
            {
                "index": i,
                "station_id": node_ids[i],
                "name": node_names[i],
                "role": node_roles[i],
                "latitude": coords[i][0],
                "longitude": coords[i][1],
                "drainage_area_km2": drainage_areas[i],
                "elevation_m": elevations[i]
            }
            for i in range(num_nodes)
        ],
        "edges": [
            {"from_node": u, "to_node": v, "from_staid": node_ids[u], "to_staid": node_ids[v], "length_km": l, "drop_m": d, "weight": round(float(adj[u, v]), 4)}
            for u, v, l, d in edges
        ],
        "static_feature_names": ["drainage_area_km2", "elevation_m", "latitude", "longitude"]
    }

    out_dir = os.path.join(processed_base_dir, "graph_data")
    np.save(os.path.join(out_dir, "aroostook_adjacency.npy"), adj)
    np.save(os.path.join(out_dir, "aroostook_static_features.npy"), static_feats)
    with open(os.path.join(out_dir, "aroostook_graph_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return adj, static_feats, metadata


def build_potomac_graph(processed_base_dir: str):
    """
    Constructs the 5-node Potomac River Basin graph from USGS NWIS data.
    Node Ordering:
    0: 01638500 (Potomac at Point of Rocks) - Upstream mainstem
    1: 01643000 (Monocacy River at Jug Bridge) - Tributary
    2: 01644000 (Seneca Creek at Dawsonville) - Tributary
    3: 01647600 (NW Branch Anacostia River) - Urban tributary
    4: 01646500 (Potomac at Little Falls Pump Station) - Downstream mainstem exit
    """
    node_ids = ["01638500", "01643000", "01644000", "01647600", "01646500"]
    node_names = [
        "Potomac River at Point of Rocks, MD",
        "Monocacy River at Jug Bridge, MD",
        "Seneca Creek at Dawsonville, MD",
        "NW Branch Anacostia River, Hyattsville, MD",
        "Potomac River near Little Falls Pump Sta, DC"
    ]
    node_roles = [
        "UPSTREAM_MAINSTEM",
        "MAJOR_TRIBUTARY",
        "LATERAL_TRIBUTARY",
        "URBAN_TRIBUTARY",
        "DOWNSTREAM_TERMINAL"
    ]
    coords = [
        (39.2736, -77.5431),
        (39.4007, -77.3664),
        (39.1297, -77.3308),
        (39.9536, -76.9658),
        (38.9498, -77.1276)
    ]
    drainage_areas = [24993.0, 2116.0, 262.0, 128.0, 29940.0] # km2
    elevations = [61.0, 68.0, 64.0, 15.0, 11.0] # meters

    num_nodes = len(node_ids)
    adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)

    edges = [
        (0, 4, 42.7, 50.0),
        (1, 4, 38.1, 57.0),
        (2, 4, 19.4, 53.0),
        (3, 4, 12.0, 4.0)
    ]

    sigma_L = 40.0
    for u, v, length_km, drop_m in edges:
        area_ratio = np.sqrt(drainage_areas[u] / drainage_areas[v])
        weight = float(np.exp(-(length_km / sigma_L)**2) * area_ratio)
        adj[u, v] = weight

    static_feats = np.array([
        [drainage_areas[i], elevations[i], coords[i][0], coords[i][1]]
        for i in range(num_nodes)
    ], dtype=np.float32)

    metadata = {
        "graph_name": "Potomac_River_Basin",
        "hydrologic_region": "HUC02-02 (Mid-Atlantic)",
        "num_nodes": num_nodes,
        "node_ordering": node_ids,
        "nodes": [
            {
                "index": i,
                "station_id": node_ids[i],
                "name": node_names[i],
                "role": node_roles[i],
                "latitude": coords[i][0],
                "longitude": coords[i][1],
                "drainage_area_km2": drainage_areas[i],
                "elevation_m": elevations[i]
            }
            for i in range(num_nodes)
        ],
        "edges": [
            {"from_node": u, "to_node": v, "from_staid": node_ids[u], "to_staid": node_ids[v], "length_km": l, "drop_m": d, "weight": round(float(adj[u, v]), 4)}
            for u, v, l, d in edges
        ],
        "static_feature_names": ["drainage_area_km2", "elevation_m", "latitude", "longitude"]
    }

    out_dir = os.path.join(processed_base_dir, "graph_data")
    np.save(os.path.join(out_dir, "potomac_adjacency.npy"), adj)
    np.save(os.path.join(out_dir, "potomac_static_features.npy"), static_feats)
    with open(os.path.join(out_dir, "potomac_graph_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return adj, static_feats, metadata


def build_disjoint_combined_graph(processed_base_dir: str):
    """
    Builds the combined block-diagonal graph joining Aroostook (4 nodes) and Potomac (5 nodes)
    with strictly 0.0 cross-basin edges.
    """
    adj_a = np.load(os.path.join(processed_base_dir, "graph_data", "aroostook_adjacency.npy"))
    adj_p = np.load(os.path.join(processed_base_dir, "graph_data", "potomac_adjacency.npy"))
    
    n_a = adj_a.shape[0]
    n_p = adj_p.shape[0]
    n_total = n_a + n_p

    adj_disjoint = np.zeros((n_total, n_total), dtype=np.float32)
    adj_disjoint[:n_a, :n_a] = adj_a
    adj_disjoint[n_a:, n_a:] = adj_p

    np.save(os.path.join(processed_base_dir, "graph_data", "disjoint_combined_adjacency.npy"), adj_disjoint)
    return adj_disjoint


def construct_aroostook_temporal_sequences(
    processed_base_dir: str,
    window_hours: int = 12,
    horizon_hours: int = 3,
    stride_hours: int = 6
):
    """
    Constructs chronological time-series sequence tensors for the 4-node Aroostook graph.
    """
    camels_dir = os.path.join(processed_base_dir, "camels_hourly_processed")
    node_ids = ["01015800", "01017060", "01017290", "01017000"]

    dfs = {}
    for nid in node_ids:
        fp = os.path.join(camels_dir, f"{nid}_hourly_labeled.csv")
        df = pd.read_csv(fp, low_memory=False)
        df["dt"] = pd.to_datetime(df["timestamp"])
        dfs[nid] = df.set_index("dt").sort_index()

    t_start = max(dfs[nid].index.min() for nid in node_ids)
    t_end = min(dfs[nid].index.max() for nid in node_ids)
    hourly_index = pd.date_range(t_start, t_end, freq="1h")
    total_hours = len(hourly_index)

    num_nodes = len(node_ids)
    num_features = 6

    dynamic_tensor = np.zeros((total_hours, num_nodes, num_features), dtype=np.float32)
    target_high_flow = np.zeros((total_hours, num_nodes), dtype=np.float32)
    target_streamflow = np.zeros((total_hours, num_nodes), dtype=np.float32)
    target_depth = np.zeros((total_hours, num_nodes), dtype=np.float32)
    mask_matrix = np.zeros((total_hours, num_nodes), dtype=bool)

    for i, nid in enumerate(node_ids):
        df_reindexed = dfs[nid].reindex(hourly_index)
        
        q = df_reindexed["streamflow_m3s"].values
        h = df_reindexed["water_level_m"].values
        q_mask = df_reindexed["streamflow_measured_mask"].fillna(False).values
        h_mask = df_reindexed["water_level_measured_mask"].fillna(False).values
        dq = df_reindexed["dq_dt_m3s_per_h"].fillna(0.0).values
        dh = df_reindexed["dh_dt_m_per_h"].fillna(0.0).values
        
        q_filled = pd.Series(q).interpolate(method="linear", limit=3).fillna(0.0).values
        h_filled = pd.Series(h).interpolate(method="linear", limit=3).fillna(0.0).values

        dynamic_tensor[:, i, 0] = q_filled
        dynamic_tensor[:, i, 1] = h_filled
        dynamic_tensor[:, i, 2] = dq
        dynamic_tensor[:, i, 3] = dh
        dynamic_tensor[:, i, 4] = q_mask.astype(np.float32)
        dynamic_tensor[:, i, 5] = h_mask.astype(np.float32)

        target_high_flow[:, i] = df_reindexed["label_statistical_high_flow"].fillna(0.0).values
        target_streamflow[:, i] = q_filled
        target_depth[:, i] = df_reindexed["label_estimated_inundation_depth_m"].fillna(0.0).values
        mask_matrix[:, i] = q_mask

    X_list, Y_flow_list, Y_flow_val_list, Y_depth_list = [], [], [], []

    for t_idx in range(0, total_hours - window_hours - horizon_hours, stride_hours):
        window_mask = mask_matrix[t_idx : t_idx + window_hours, 3] # Washburn downstream node
        target_mask = mask_matrix[t_idx + window_hours + horizon_hours - 1, 3]

        if (window_mask.mean() >= 0.70) and target_mask:
            X_window = dynamic_tensor[t_idx : t_idx + window_hours]
            Y_fl = target_high_flow[t_idx + window_hours + horizon_hours - 1]
            Y_qw = target_streamflow[t_idx + window_hours + horizon_hours - 1]
            Y_dp = target_depth[t_idx + window_hours + horizon_hours - 1]

            X_list.append(X_window)
            Y_flow_list.append(Y_fl)
            Y_flow_val_list.append(Y_qw)
            Y_depth_list.append(Y_dp)

    X = np.array(X_list, dtype=np.float32)
    Y_high_flow = np.array(Y_flow_list, dtype=np.float32)
    Y_flow = np.array(Y_flow_val_list, dtype=np.float32)
    Y_depth = np.array(Y_depth_list, dtype=np.float32)

    total_seqs = len(X)
    idx_train_end = int(total_seqs * 0.70)
    buffer_steps = max(1, 24 // stride_hours)
    idx_val_start = idx_train_end + buffer_steps
    idx_val_end = idx_val_start + int(total_seqs * 0.15)
    idx_test_start = idx_val_end + buffer_steps

    out_dir = os.path.join(processed_base_dir, "temporal_sequences")
    out_file = os.path.join(out_dir, f"aroostook_sequences_w{window_hours}_h{horizon_hours}.npz")
    np.savez_compressed(
        out_file,
        X=X,
        Y_statistical_high_flow=Y_high_flow,
        Y_flood=Y_high_flow, # Backward compatibility alias
        Y_flow=Y_flow,
        Y_depth=Y_depth,
        train_idx=np.arange(0, idx_train_end),
        val_idx=np.arange(idx_val_start, idx_val_end),
        test_idx=np.arange(idx_test_start, total_seqs)
    )

    meta = {
        "dataset_name": "Aroostook_River_ST_GNN_Sequences",
        "num_nodes": 4,
        "node_ids": node_ids,
        "window_hours": window_hours,
        "horizon_hours": horizon_hours,
        "stride_hours": stride_hours,
        "total_sequences": total_seqs,
        "tensor_shape_X": list(X.shape),
        "tensor_shape_Y": list(Y_high_flow.shape),
        "feature_names": [
            "streamflow_m3s",
            "water_level_m",
            "dq_dt_m3s_per_h",
            "dh_dt_m_per_h",
            "streamflow_measured_mask",
            "water_level_measured_mask"
        ],
        "target_names": [
            "label_statistical_high_flow",
            "future_streamflow_m3s",
            "future_estimated_inundation_depth_m"
        ],
        "split_strategy": {
            "train_indices": [0, idx_train_end],
            "val_indices": [idx_val_start, idx_val_end],
            "test_indices": [idx_test_start, total_seqs],
            "train_count": idx_train_end,
            "val_count": idx_val_end - idx_val_start,
            "test_count": total_seqs - idx_test_start,
            "purge_buffer_hours": buffer_steps * stride_hours
        }
    }

    with open(os.path.join(out_dir, f"aroostook_sequences_w{window_hours}_h{horizon_hours}_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Saved Aroostook {out_file}: {total_seqs} sequences.")
    return meta


def construct_potomac_temporal_sequences(
    processed_base_dir: str,
    window_hours: int = 12,
    horizon_hours: int = 3,
    stride_hours: int = 1
):
    """
    Constructs chronological time-series sequence tensors for the 5-node Potomac River graph.
    Nodes: 01638500, 01643000, 01644000, 01647600, 01646500.
    """
    usgs_dir = os.path.join(processed_base_dir, "usgs_processed")
    node_ids = ["01638500", "01643000", "01644000", "01647600", "01646500"]

    dfs = {}
    for nid in node_ids:
        fp = os.path.join(usgs_dir, f"{nid}_hourly_labeled.csv")
        df = pd.read_csv(fp, low_memory=False)
        df["dt"] = pd.to_datetime(df["timestamp"])
        dfs[nid] = df.set_index("dt").sort_index()

    t_start = max(dfs[nid].index.min() for nid in node_ids)
    t_end = min(dfs[nid].index.max() for nid in node_ids)
    hourly_index = pd.date_range(t_start, t_end, freq="1h")
    total_hours = len(hourly_index)

    num_nodes = len(node_ids)
    num_features = 6

    dynamic_tensor = np.zeros((total_hours, num_nodes, num_features), dtype=np.float32)
    target_high_flow = np.zeros((total_hours, num_nodes), dtype=np.float32)
    target_off_flood = np.zeros((total_hours, num_nodes), dtype=np.float32)
    target_streamflow = np.zeros((total_hours, num_nodes), dtype=np.float32)
    target_depth = np.zeros((total_hours, num_nodes), dtype=np.float32)
    mask_matrix = np.zeros((total_hours, num_nodes), dtype=bool)

    for i, nid in enumerate(node_ids):
        df_reindexed = dfs[nid].reindex(hourly_index)
        
        q = df_reindexed["streamflow_m3s"].values
        h = df_reindexed["water_level_m"].values
        q_mask = df_reindexed["streamflow_measured_mask"].fillna(False).values
        h_mask = df_reindexed["water_level_measured_mask"].fillna(False).values
        dq = df_reindexed["dq_dt_m3s_per_h"].fillna(0.0).values
        dh = df_reindexed["dh_dt_m_per_h"].fillna(0.0).values

        q_filled = pd.Series(q).interpolate(method="linear", limit=3).fillna(0.0).values
        h_filled = pd.Series(h).interpolate(method="linear", limit=3).fillna(0.0).values

        dynamic_tensor[:, i, 0] = q_filled
        dynamic_tensor[:, i, 1] = h_filled
        dynamic_tensor[:, i, 2] = dq
        dynamic_tensor[:, i, 3] = dh
        dynamic_tensor[:, i, 4] = q_mask.astype(np.float32)
        dynamic_tensor[:, i, 5] = h_mask.astype(np.float32)

        target_high_flow[:, i] = df_reindexed["label_statistical_high_flow"].fillna(0.0).values
        target_off_flood[:, i] = df_reindexed["label_official_flood_observed"].fillna(0.0).values
        target_streamflow[:, i] = q_filled
        target_depth[:, i] = df_reindexed["label_estimated_inundation_depth_m"].fillna(0.0).values
        mask_matrix[:, i] = q_mask

    X_list, Y_flow_list, Y_off_list, Y_flow_val_list, Y_depth_list = [], [], [], [], []

    for t_idx in range(0, total_hours - window_hours - horizon_hours, stride_hours):
        window_mask = mask_matrix[t_idx : t_idx + window_hours, 4] # Little Falls terminal node
        target_mask = mask_matrix[t_idx + window_hours + horizon_hours - 1, 4]

        if (window_mask.mean() >= 0.80) and target_mask:
            X_window = dynamic_tensor[t_idx : t_idx + window_hours]
            Y_fl = target_high_flow[t_idx + window_hours + horizon_hours - 1]
            Y_of = target_off_flood[t_idx + window_hours + horizon_hours - 1]
            Y_qw = target_streamflow[t_idx + window_hours + horizon_hours - 1]
            Y_dp = target_depth[t_idx + window_hours + horizon_hours - 1]

            X_list.append(X_window)
            Y_flow_list.append(Y_fl)
            Y_off_list.append(Y_of)
            Y_flow_val_list.append(Y_qw)
            Y_depth_list.append(Y_dp)

    X = np.array(X_list, dtype=np.float32)
    Y_high_flow = np.array(Y_flow_list, dtype=np.float32)
    Y_official_flood = np.array(Y_off_list, dtype=np.float32)
    Y_flow = np.array(Y_flow_val_list, dtype=np.float32)
    Y_depth = np.array(Y_depth_list, dtype=np.float32)

    total_seqs = len(X)
    idx_train_end = int(total_seqs * 0.70)
    buffer_steps = max(1, 12 // stride_hours)
    idx_val_start = idx_train_end + buffer_steps
    idx_val_end = idx_val_start + int(total_seqs * 0.15)
    idx_test_start = idx_val_end + buffer_steps

    out_dir = os.path.join(processed_base_dir, "temporal_sequences")
    out_file = os.path.join(out_dir, f"potomac_sequences_w{window_hours}_h{horizon_hours}.npz")
    np.savez_compressed(
        out_file,
        X=X,
        Y_statistical_high_flow=Y_high_flow,
        Y_official_flood=Y_official_flood,
        Y_flood=Y_high_flow,
        Y_flow=Y_flow,
        Y_depth=Y_depth,
        train_idx=np.arange(0, idx_train_end),
        val_idx=np.arange(idx_val_start, idx_val_end),
        test_idx=np.arange(idx_test_start, total_seqs)
    )

    meta = {
        "dataset_name": "Potomac_River_ST_GNN_Sequences",
        "num_nodes": 5,
        "node_ids": node_ids,
        "window_hours": window_hours,
        "horizon_hours": horizon_hours,
        "stride_hours": stride_hours,
        "total_sequences": total_seqs,
        "tensor_shape_X": list(X.shape),
        "tensor_shape_Y": list(Y_high_flow.shape),
        "feature_names": [
            "streamflow_m3s",
            "water_level_m",
            "dq_dt_m3s_per_h",
            "dh_dt_m_per_h",
            "streamflow_measured_mask",
            "water_level_measured_mask"
        ],
        "target_names": [
            "label_statistical_high_flow",
            "label_official_flood_observed",
            "future_streamflow_m3s",
            "future_estimated_inundation_depth_m"
        ],
        "split_strategy": {
            "train_indices": [0, idx_train_end],
            "val_indices": [idx_val_start, idx_val_end],
            "test_indices": [idx_test_start, total_seqs],
            "train_count": idx_train_end,
            "val_count": idx_val_end - idx_val_start,
            "test_count": total_seqs - idx_test_start,
            "purge_buffer_hours": buffer_steps * stride_hours
        }
    }

    with open(os.path.join(out_dir, f"potomac_sequences_w{window_hours}_h{horizon_hours}_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Saved Potomac {out_file}: {total_seqs} sequences.")
    return meta


if __name__ == "__main__":
    base_dir = r"E:\ai-manthan\hydro_guard_indore\data\processed_global"
    print("Building Aroostook Graph...")
    build_aroostook_graph(base_dir)
    print("Building Potomac Graph...")
    build_potomac_graph(base_dir)
    print("Building Disjoint Combined Graph...")
    build_disjoint_combined_graph(base_dir)

    print("\n--- Constructing Aroostook Temporal Sequences (CAMELSH) ---")
    construct_aroostook_temporal_sequences(base_dir, window_hours=12, horizon_hours=3, stride_hours=6)
    construct_aroostook_temporal_sequences(base_dir, window_hours=6, horizon_hours=1, stride_hours=6)
    construct_aroostook_temporal_sequences(base_dir, window_hours=24, horizon_hours=6, stride_hours=6)

    print("\n--- Constructing Potomac Temporal Sequences (USGS NWIS) ---")
    construct_potomac_temporal_sequences(base_dir, window_hours=12, horizon_hours=3, stride_hours=1)
    construct_potomac_temporal_sequences(base_dir, window_hours=6, horizon_hours=1, stride_hours=1)
    construct_potomac_temporal_sequences(base_dir, window_hours=24, horizon_hours=6, stride_hours=1)

    print("All Graphs and Sequences Constructed Successfully!")
