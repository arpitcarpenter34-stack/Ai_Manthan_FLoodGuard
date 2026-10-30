"""
Indore Elevation & Drainage Network Loader using NetworkX & OSMnx.
Models Indore's south-to-north elevation drop (Rau/Bhanwarkuan ~550m down to Kabithedi ~515m)
and provides graph representations of Khan & Saraswati River topology.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
import networkx as nx

import config
from backend.services.dem_service import dem_service


class IndoreGISLoader:
    """
    Constructs and persists the topological directed graph for Indore's urban drainage network.
    Grounds node elevations from MSL 560m (South - Rau) down to 515m (North - Kabithedi).
    """

    def __init__(
        self,
        data_path: Path = config.GIS_DIR / "indore_drainage_network.json",
        real_waterways_path: Path = config.GIS_DIR / "indore_waterways_osm.geojson",
        metadata_path: Path = config.GIS_DIR / "indore_waterways_metadata.json",
    ):
        self.data_path = data_path
        self.real_waterways_path = real_waterways_path
        self.metadata_path = metadata_path
        self.graph: nx.DiGraph = nx.DiGraph()
        self._build_or_load_graph()

    def _build_or_load_graph(self) -> None:
        """Initialize or load network from JSON cache."""
        if self.data_path.exists():
            try:
                self.load_from_json(self.data_path)
                if self.graph.number_of_nodes() > 0:
                    return
            except Exception:
                pass

        self._build_default_indore_network()
        self.save_to_json(self.data_path)

    def _build_default_indore_network(self) -> None:
        """Construct the foundational hydraulic topology of Indore's Khan & Saraswati system."""
        self.graph.clear()

        # Add Nodes with spatial and elevation properties
        for node_id, data in config.DRAINAGE_NODES.items():
            self.graph.add_node(
                node_id,
                name=data["name"],
                hindi_name=data["hindi_name"],
                lat=data["lat"],
                lon=data["lon"],
                elevation_m=data["elevation_m"],
                catchment_km2=data["catchment_km2"],
                max_capacity_m3_s=data["max_capacity_m3_s"],
                type=data["type"],
                river=data["river"],
            )

        # Add Directed Hydraulic Edges (Gravity flows from higher to lower elevation)
        for u, v, attrs in config.DRAINAGE_EDGES:
            u_elev = self.graph.nodes[u]["elevation_m"]
            v_elev = self.graph.nodes[v]["elevation_m"]
            length_m = attrs["length_km"] * 1000.0
            elev_drop = u_elev - v_elev
            slope = max(0.0005, elev_drop / length_m) if length_m > 0 else 0.001

            # Estimate Manning's velocity: v = (1/n) * R^(2/3) * S^(1/2)
            # Assuming average hydraulic radius R = 1.8 m for major Indore channels
            n = attrs.get("roughness_n", 0.030)
            r = 1.8
            manning_v = (1.0 / n) * (r ** (2.0 / 3.0)) * math.sqrt(slope)

            # Travel time in minutes
            travel_time_min = (length_m / manning_v) / 60.0 if manning_v > 0 else 30.0

            self.graph.add_edge(
                u,
                v,
                channel=attrs["channel"],
                length_km=attrs["length_km"],
                length_m=length_m,
                elev_drop_m=elev_drop,
                slope=slope,
                roughness_n=n,
                manning_velocity_m_s=round(manning_v, 2),
                travel_time_min=round(travel_time_min, 1),
            )

    def get_indore_drainage_graph(self) -> nx.DiGraph:
        """Return the NetworkX DiGraph instance."""
        return self.graph

    def get_elevation_profile(self) -> List[Dict[str, Any]]:
        """
        Extract the elevation profile along the primary south-to-north hydraulic path:
        NODE_RAU -> NODE_RAJWARA -> NODE_PARDESHIPURA -> NODE_KABITHEDI_STP.
        """
        primary_path = ["NODE_RAU", "NODE_RAJWARA", "NODE_PARDESHIPURA", "NODE_KABITHEDI_STP"]
        profile = []
        cumulative_dist = 0.0

        for i, node_id in enumerate(primary_path):
            node_data = self.graph.nodes[node_id]
            if i > 0:
                prev_id = primary_path[i - 1]
                edge_data = self.graph.get_edge_data(prev_id, node_id, {})
                cumulative_dist += edge_data.get("length_km", 0.0)

            lat = node_data["lat"]
            lon = node_data["lon"]
            dem_elev = dem_service.get_elevation_at_point(lat, lon) if dem_service.is_available else None

            profile.append({
                "node_id": node_id,
                "name": node_data["name"],
                "hindi_name": node_data["hindi_name"],
                "distance_km": round(cumulative_dist, 2),
                "elevation_m": node_data["elevation_m"],
                "dem_surface_elevation_m": dem_elev,
                "elevation_source": "Copernicus DEM GLO-30 (30m)",
                "lat": lat,
                "lon": lon,
            })

        return profile

    def get_real_waterways_geojson(self) -> Dict[str, Any]:
        """Load and return verified real OSM waterway geometries if available, or return fallback."""
        if self.real_waterways_path.exists():
            try:
                with open(self.real_waterways_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "type": "FeatureCollection",
            "metadata": {
                "source": "Fallback (OSM offline)",
                "is_real_gis_data": False,
                "provenance": "ILLUSTRATIVE_FALLBACK",
                "provenance_warning": "Real OSM waterways not available. Fallback is illustrative."
            },
            "features": []
        }

    def get_gis_metadata(self) -> Dict[str, Any]:
        """Return metadata summary for real GIS waterways."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "is_real_gis_data": False,
            "provenance": "ILLUSTRATIVE_FALLBACK",
            "source": "None"
        }

    def to_geojson(self) -> Dict[str, Any]:
        """Convert drainage nodes, verified real OSM waterways, and schematic edges into GeoJSON FeatureCollection."""
        features = []

        # 1. Point features for municipal monitoring stations
        for node_id, d in self.graph.nodes(data=True):
            lat = d["lat"]
            lon = d["lon"]
            dem_elev = dem_service.get_elevation_at_point(lat, lon) if dem_service.is_available else None

            features.append({
                "type": "Feature",
                "id": node_id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "node_id": node_id,
                    "name": d["name"],
                    "hindi_name": d["hindi_name"],
                    "elevation_m": d["elevation_m"],
                    "dem_surface_elevation_m": dem_elev,
                    "dem_source": "Copernicus DEM GLO-30 (ESA / Airbus via AWS Open Data)",
                    "catchment_km2": d["catchment_km2"],
                    "max_capacity_m3_s": d["max_capacity_m3_s"],
                    "type": d["type"],
                    "river": d["river"],
                    "layer_type": "monitoring_station",
                    "is_real_gis_data": False,
                    "provenance": "MUNICIPAL_MONITORING_POINT",
                },
            })

        # 2. Verified Real OSM Waterways (Khan & Saraswati Rivers)
        real_waterways = self.get_real_waterways_geojson()
        for f in real_waterways.get("features", []):
            prop = dict(f.get("properties", {}))
            prop["layer_type"] = "real_waterway"
            prop["is_real_gis_data"] = True
            features.append({
                "type": "Feature",
                "id": f.get("id"),
                "geometry": f.get("geometry"),
                "properties": prop,
            })

        # 3. Schematic Hydraulic Graph Edges (Illustrative routing lines)
        for u, v, d in self.graph.edges(data=True):
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [u_data["lon"], u_data["lat"]],
                        [v_data["lon"], v_data["lat"]],
                    ],
                },
                "properties": {
                    "from_node": u,
                    "to_node": v,
                    "channel": d["channel"],
                    "length_km": d["length_km"],
                    "elev_drop_m": d["elev_drop_m"],
                    "travel_time_min": d["travel_time_min"],
                    "slope": d["slope"],
                    "layer_type": "schematic_flow_edge",
                    "is_real_gis_data": False,
                    "provenance": "ILLUSTRATIVE_MUNICIPAL_SCHEMATIC",
                    "provenance_note": "Schematic hydraulic routing line between municipal stations; not surveyed pipe geometry.",
                },
            })

        return {
            "type": "FeatureCollection",
            "metadata": self.get_gis_metadata(),
            "features": features,
        }

    def save_to_json(self, filepath: Path) -> None:
        """Persist graph structure to JSON."""
        data = {
            "nodes": [
                {"id": n, **d} for n, d in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **d} for u, v, d in self.graph.edges(data=True)
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_json(self, filepath: Path) -> None:
        """Load network graph from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.graph.clear()
        for node in data.get("nodes", []):
            node_id = node.pop("id")
            self.graph.add_node(node_id, **node)

        for edge in data.get("edges", []):
            u = edge.pop("source")
            v = edge.pop("target")
            self.graph.add_edge(u, v, **edge)


# Global loader instance
indore_gis_loader = IndoreGISLoader()

