"""
Spatial Graph Representation for Indore Urban Drainage Network.
Constructs directed topological graph, node/edge physical feature matrices,
and bi-directional diffusion matrices (Pf, Pb) for Spatio-Temporal Graph Neural Networks.
Grounds node elevations using Copernicus DEM GLO-30 (560m South down to 515m North).
"""

import math
from typing import Dict, Any, List, Tuple, Optional
import networkx as nx
import numpy as np

import config
from backend.services.osmnx_gis_loader import indore_gis_loader
from backend.services.dem_service import dem_service


class DrainageSpatialGraph:
    """
    Constructs and maintains the spatial graph representation of the Indore drainage basin
    for message-passing graph neural networks and hydraulic flow routing.
    """

    NODE_ORDER = [
        "NODE_RAU",
        "NODE_BHANWARKUAN",
        "NODE_RAMBAGH",
        "NODE_RAJWARA",
        "NODE_VIJAY_NAGAR",
        "NODE_PARDESHIPURA",
        "NODE_KABITHEDI_STP",
    ]

    NODE_FEATURE_NAMES = [
        "elevation_m",
        "catchment_km2",
        "max_capacity_m3_s",
        "latitude",
        "longitude",
        "distance_to_outfall_km",
    ]

    EDGE_FEATURE_NAMES = [
        "length_km",
        "slope",
        "manning_roughness_n",
        "manning_velocity_m_s",
        "travel_time_min",
    ]

    def __init__(self):
        self.node_ids = list(self.NODE_ORDER)
        self.node_index = {nid: i for i, nid in enumerate(self.node_ids)}
        self.num_nodes = len(self.node_ids)
        self.graph: nx.DiGraph = indore_gis_loader.get_indore_drainage_graph()
        self._build_matrices()

    def _build_matrices(self) -> None:
        """Compute adjacency, forward/backward transition diffusion, and physical attribute tensors."""
        n = self.num_nodes
        adj = np.zeros((n, n), dtype=np.float32)

        # Build directed adjacency matrix based on flow connectivity
        for u, v, data in self.graph.edges(data=True):
            if u in self.node_index and v in self.node_index:
                i = self.node_index[u]
                j = self.node_index[v]
                # Weight by inverted hydraulic impedance (higher flow capacity = stronger coupling)
                capacity = float(data.get("length_km", 1.0))
                weight = 1.0 / max(0.5, capacity)
                adj[i, j] = weight

        self.adj_matrix = adj

        # Forward transition matrix (downstream flow diffusion)
        out_degree = np.sum(adj, axis=1)
        out_degree_safe = np.where(out_degree == 0, 1.0, out_degree)
        self.P_forward = adj / out_degree_safe[:, np.newaxis]
        # For terminal sink node (Kabithedi outfall), retain discharge in self-loop
        for i in range(n):
            if out_degree[i] == 0:
                self.P_forward[i, i] = 1.0

        # Backward transition matrix (upstream backwater diffusion)
        adj_t = adj.T
        in_degree = np.sum(adj_t, axis=1)
        in_degree_safe = np.where(in_degree == 0, 1.0, in_degree)
        self.P_backward = adj_t / in_degree_safe[:, np.newaxis]
        # For headwater source nodes (Rau / Bhanwarkuan / Vijay Nagar), self-loop
        for i in range(n):
            if in_degree[i] == 0:
                self.P_backward[i, i] = 1.0

        # Symmetric normalized Laplacian for undirected spatial convolution
        adj_sym = np.maximum(adj, adj_t)
        np.fill_diagonal(adj_sym, 1.0)  # Self-loops
        d_sym = np.sum(adj_sym, axis=1)
        d_inv_sqrt = np.power(d_sym, -0.5)
        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
        self.laplacian_sym = np.eye(n) - np.diag(d_inv_sqrt) @ adj_sym @ np.diag(d_inv_sqrt)

        # Static Node Features Matrix (N x F_node)
        self.static_node_features = np.zeros((n, len(self.NODE_FEATURE_NAMES)), dtype=np.float32)
        outfall_lat = config.DRAINAGE_NODES["NODE_KABITHEDI_STP"]["lat"]
        outfall_lon = config.DRAINAGE_NODES["NODE_KABITHEDI_STP"]["lon"]

        for nid, idx in self.node_index.items():
            nd = config.DRAINAGE_NODES.get(nid, {})
            elev = float(nd.get("elevation_m", 540.0))
            # Verify with Copernicus DEM if available
            dem_elev = dem_service.get_elevation_at_point(nd.get("lat", 0), nd.get("lon", 0)) if dem_service.is_available else None
            effective_elev = dem_elev if dem_elev is not None else elev

            lat = float(nd.get("lat", 22.7))
            lon = float(nd.get("lon", 75.8))
            dist_km = math.sqrt(((lat - outfall_lat) * 111.0) ** 2 + ((lon - outfall_lon) * 102.0) ** 2)

            self.static_node_features[idx] = [
                effective_elev,
                float(nd.get("catchment_km2", 15.0)),
                float(nd.get("max_capacity_m3_s", 60.0)),
                lat,
                lon,
                dist_km,
            ]

    def get_diffusion_matrices(self, k: int = 2) -> List[np.ndarray]:
        """
        Compute Chebyshev/diffusion polynomial powers [P^0, P^1, ..., P^K]
        for both forward (downstream) and backward (upstream) flow propagation.
        """
        matrices = [np.eye(self.num_nodes, dtype=np.float32)]
        p_f_power = np.eye(self.num_nodes, dtype=np.float32)
        p_b_power = np.eye(self.num_nodes, dtype=np.float32)

        for step in range(1, k + 1):
            p_f_power = p_f_power @ self.P_forward
            p_b_power = p_b_power @ self.P_backward
            matrices.append(p_f_power.astype(np.float32))
            matrices.append(p_b_power.astype(np.float32))

        return matrices

    def get_topology_summary(self) -> Dict[str, Any]:
        """Return structured summary of the drainage graph."""
        nodes_info = []
        for nid, idx in self.node_index.items():
            nd = config.DRAINAGE_NODES.get(nid, {})
            feats = self.static_node_features[idx].tolist()
            nodes_info.append({
                "node_id": nid,
                "node_index": idx,
                "name": nd.get("name"),
                "hindi_name": nd.get("hindi_name"),
                "elevation_m": round(feats[0], 2),
                "catchment_km2": feats[1],
                "capacity_m3_s": feats[2],
                "coordinates": [feats[3], feats[4]],
                "dist_to_outfall_km": round(feats[5], 2),
            })

        edges_info = []
        for u, v, data in self.graph.edges(data=True):
            edges_info.append({
                "source": u,
                "target": v,
                "channel_name": data.get("channel", "Culvert"),
                "length_km": data.get("length_km"),
                "slope": round(float(data.get("slope", 0.001)), 5),
                "manning_roughness_n": data.get("roughness_n", 0.030),
                "velocity_m_s": data.get("manning_velocity_m_s", 1.5),
                "travel_time_min": data.get("travel_time_min", 20.0),
            })

        return {
            "num_nodes": self.num_nodes,
            "num_edges": len(edges_info),
            "nodes": nodes_info,
            "edges": edges_info,
            "adjacency_matrix": self.adj_matrix.tolist(),
            "forward_transition_matrix": self.P_forward.tolist(),
            "backward_transition_matrix": self.P_backward.tolist(),
            "elevation_drop_total_m": config.INDORE_MAX_MSL_ELEVATION - config.INDORE_MIN_MSL_ELEVATION,
        }


# Global spatial graph instance
drainage_spatial_graph = DrainageSpatialGraph()
