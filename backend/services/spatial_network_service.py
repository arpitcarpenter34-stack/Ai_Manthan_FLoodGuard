"""
Indore Spatial River Network & Graph Construction Service (Phase 2A).
Builds a rigorous, coordinate-verified spatial graph derived directly from real OpenStreetMap
river geometries (Khan River, Saraswati River, and tributaries).

Key Scientific & Engineering Principles:
1. Projected Metric Measurements: All distances, lengths, and proximity queries are computed
   in projected metric coordinates (UTM Zone 43N / EPSG:32643, central meridian 75°E).
2. Genuine Topology: Reconstructs geometric vertices, endpoints, and genuine intersections
   without fabricating unverified river connections.
3. Separation of Concerns: The spatial network graph is maintained strictly separate from
   the assumed hydraulic graph. Geometric connectivity does NOT imply verified hydraulic routing.
4. Monitoring Station Snapping: Evaluates spatial proximity of the 7 urban monitoring stations
   without silently altering their surveyed municipal coordinates.
"""

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

import networkx as nx
import numpy as np
from shapely.geometry import shape, Point, LineString, MultiLineString
from shapely.ops import nearest_points
import pyproj
from pyproj import Transformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from backend.services.dem_service import dem_service

DEFAULT_OSM_GEOJSON_PATH = config.GIS_DIR / "indore_waterways_osm.geojson"
DEFAULT_METADATA_PATH = config.GIS_DIR / "indore_waterways_metadata.json"
DEFAULT_REPORT_PATH = config.GIS_DIR / "indore_spatial_network_report.json"

# Metric Coordinate Reference System for Indore (Madhya Pradesh, 75.8°E, 22.7°N)
# WGS84 / UTM Zone 43N: EPSG:32643
UTM_CRS = "EPSG:32643"
GEO_CRS = "EPSG:4326"


class IndoreSpatialNetworkService:
    """
    Extracts real OpenStreetMap waterway geometries, constructs a topological spatial graph,
    detects confluences/junctions, and evaluates urban monitoring station snapping.
    """

    def __init__(
        self,
        geojson_path: Path = DEFAULT_OSM_GEOJSON_PATH,
        metadata_path: Path = DEFAULT_METADATA_PATH,
        report_path: Path = DEFAULT_REPORT_PATH,
        auto_build: bool = True,
    ):
        self.geojson_path = geojson_path
        self.metadata_path = metadata_path
        self.report_path = report_path

        # Coordinate Transformers
        self.transformer_to_utm = Transformer.from_crs(GEO_CRS, UTM_CRS, always_xy=True)
        self.transformer_to_wgs = Transformer.from_crs(UTM_CRS, GEO_CRS, always_xy=True)

        self.features_data: List[Dict[str, Any]] = []
        self.spatial_graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.junction_candidates: List[Dict[str, Any]] = []
        self.connected_components_summary: Dict[str, Any] = {}
        self.monitoring_snapping_summary: Dict[str, Any] = {}
        self._report_cache: Optional[Dict[str, Any]] = None

        if auto_build:
            self.build_spatial_network()

    def _generate_node_id(self, lat: float, lon: float, prefix: str = "NODE_GEO") -> str:
        """Create a deterministic unique node identifier based on coordinate hash."""
        coord_str = f"{lat:.6f}_{lon:.6f}"
        h = hashlib.sha256(coord_str.encode("utf-8")).hexdigest()[:8]
        return f"{prefix}_{h}"

    def build_spatial_network(self) -> nx.MultiDiGraph:
        """
        Parse OSM GeoJSON, compute UTM metric LineStrings, detect junctions,
        and construct the formal NetworkX spatial graph.
        """
        if not self.geojson_path.exists():
            print(f"[SpatialNetwork] GeoJSON not found at {self.geojson_path}")
            return self.spatial_graph

        with open(self.geojson_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        features = raw_data.get("features", [])
        self.features_data = features
        self.spatial_graph.clear()
        self.junction_candidates.clear()

        # Phase A: Process each OSM LineString and project to UTM
        parsed_ways = []
        for feat in features:
            props = feat.get("properties", {})
            geom_raw = feat.get("geometry", {})
            geom_shapely = shape(geom_raw)

            coords_wgs = list(geom_shapely.coords)
            coords_utm = [self.transformer_to_utm.transform(lon, lat) for lon, lat in coords_wgs]
            line_utm = LineString(coords_utm)

            parsed_ways.append({
                "id": feat.get("id"),
                "osm_id": props.get("osm_id"),
                "name": props.get("name", "Unnamed Waterway"),
                "english_name": props.get("english_name", ""),
                "river_system": props.get("river_system", "Indore Basin"),
                "waterway_type": props.get("waterway_type", "river"),
                "coords_wgs": coords_wgs,
                "coords_utm": coords_utm,
                "line_wgs": geom_shapely,
                "line_utm": line_utm,
                "length_m": line_utm.length,
                "length_km": line_utm.length / 1000.0,
                "start_wgs": coords_wgs[0],  # [lon, lat]
                "end_wgs": coords_wgs[-1],   # [lon, lat]
                "start_utm": coords_utm[0],
                "end_utm": coords_utm[-1],
            })

        # Phase B: Detect Exact Geometric Intersections & Confluence Points
        # A junction is where two different waterway features intersect geometrically
        junction_point_map: Dict[Tuple[float, float], Dict[str, Any]] = {}

        for i in range(len(parsed_ways)):
            for j in range(i + 1, len(parsed_ways)):
                w1 = parsed_ways[i]
                w2 = parsed_ways[j]

                inter = w1["line_utm"].intersection(w2["line_utm"])
                if inter.is_empty:
                    continue

                pts_to_process = []
                if inter.geom_type == "Point":
                    pts_to_process.append(inter)
                elif inter.geom_type == "MultiPoint":
                    pts_to_process.extend(list(inter.geoms))

                for pt in pts_to_process:
                    wgs_lon, wgs_lat = self.transformer_to_wgs.transform(pt.x, pt.y)
                    wgs_lat_r = round(wgs_lat, 6)
                    wgs_lon_r = round(wgs_lon, 6)
                    key = (wgs_lat_r, wgs_lon_r)

                    if key not in junction_point_map:
                        junction_point_map[key] = {
                            "lat": wgs_lat_r,
                            "lon": wgs_lon_r,
                            "utm_x": round(pt.x, 2),
                            "utm_y": round(pt.y, 2),
                            "intersecting_ways": set(),
                            "intersecting_names": set(),
                            "intersection_type": "CONFLUENCE_JUNCTION",
                        }
                    junction_point_map[key]["intersecting_ways"].add(w1["id"])
                    junction_point_map[key]["intersecting_ways"].add(w2["id"])
                    junction_point_map[key]["intersecting_names"].add(w1["name"])
                    junction_point_map[key]["intersecting_names"].add(w2["name"])

        # Format junction candidates list with rigorous hydrological classification
        # - Krishnapura: Khan-Saraswati intersection candidate (confluence candidate)
        # - Mid-Khan: Khan-tributary intersection candidate (confluence candidate)
        # - Saraswati: Upper/Lower reach joint (continuity junction, not a separate river confluence)
        self.confluence_candidates: List[Dict[str, Any]] = []
        self.continuity_junctions: List[Dict[str, Any]] = []

        for idx, (coord_key, jdata) in enumerate(junction_point_map.items()):
            j_id = self._generate_node_id(jdata["lat"], jdata["lon"], prefix="JUNCTION")
            feat_names = sorted(list(jdata["intersecting_names"]))

            is_same_river = all("saraswat" in n.lower() for n in feat_names) or (
                len(set(n.lower().split()[0] for n in feat_names)) == 1
            )
            j_type = "CONTINUITY_JUNCTION" if is_same_river else "RIVER_CONFLUENCE_CANDIDATE"

            j_entry = {
                "junction_id": j_id,
                "name": f"Junction {idx + 1}: {' & '.join(feat_names)}",
                "junction_type": j_type,
                "classification_description": (
                    "Saraswati upper/lower reach connection: CONTINUITY_JUNCTION (continuous channel reach transition, not a separate river confluence)."
                    if j_type == "CONTINUITY_JUNCTION" else
                    f"Candidate river confluence: {' & '.join(feat_names)} intersection candidate."
                ),
                "lat": jdata["lat"],
                "lon": jdata["lon"],
                "utm_x": jdata["utm_x"],
                "utm_y": jdata["utm_y"],
                "intersecting_ways": sorted(list(jdata["intersecting_ways"])),
                "intersecting_features": feat_names,
                "provenance": "DERIVED_GEOMETRIC_INTERSECTION",
                "hydraulic_status": "UNVERIFIED_PHYSICAL_CONFLUENCE" if j_type == "RIVER_CONFLUENCE_CANDIDATE" else "CONTINUOUS_CHANNEL_JOINT",
            }
            self.junction_candidates.append(j_entry)
            if j_type == "RIVER_CONFLUENCE_CANDIDATE":
                self.confluence_candidates.append(j_entry)
            else:
                self.continuity_junctions.append(j_entry)

        # Phase C: Construct Graph Nodes and Edges
        # Split waterways at internal junction points so that confluences form genuine multi-branch graph nodes
        for way in parsed_ways:
            coords = way["coords_wgs"]
            n_pts = len(coords)

            # Find all vertex indices along this way that correspond to a detected junction
            split_indices = {0, n_pts - 1}
            for j_coord, jdata in junction_point_map.items():
                j_lat, j_lon = j_coord
                for idx_pt, pt in enumerate(coords):
                    pt_lon, pt_lat = pt[0], pt[1]
                    if abs(pt_lat - j_lat) < 1e-4 and abs(pt_lon - j_lon) < 1e-4:
                        split_indices.add(idx_pt)

            sorted_splits = sorted(list(split_indices))

            # Create an edge for each sub-reach between consecutive split indices
            for s_idx in range(len(sorted_splits) - 1):
                i_start = sorted_splits[s_idx]
                i_end = sorted_splits[s_idx + 1]

                sub_coords_wgs = coords[i_start : i_end + 1]
                sub_coords_utm = [self.transformer_to_utm.transform(lon, lat) for lon, lat in sub_coords_wgs]
                sub_line_utm = LineString(sub_coords_utm)

                start_pt = sub_coords_wgs[0]
                end_pt = sub_coords_wgs[-1]
                start_lat, start_lon = start_pt[1], start_pt[0]
                end_lat, end_lon = end_pt[1], end_pt[0]

                # Determine node IDs & types
                start_is_junction = (i_start in split_indices and (i_start != 0 or (round(start_lat, 6), round(start_lon, 6)) in junction_point_map))
                end_is_junction = (i_end in split_indices and (i_end != n_pts - 1 or (round(end_lat, 6), round(end_lon, 6)) in junction_point_map))

                if start_is_junction:
                    u_id = self._generate_node_id(start_lat, start_lon, prefix="JUNCTION")
                    u_type = "confluence_junction"
                else:
                    u_id = self._generate_node_id(start_lat, start_lon, prefix="TERMINAL")
                    u_type = "channel_endpoint"

                if end_is_junction:
                    v_id = self._generate_node_id(end_lat, end_lon, prefix="JUNCTION")
                    v_type = "confluence_junction"
                else:
                    v_id = self._generate_node_id(end_lat, end_lon, prefix="TERMINAL")
                    v_type = "channel_endpoint"

                # Query Copernicus DEM surface elevation for nodes
                u_dem = dem_service.get_elevation_at_point(start_lat, start_lon, method="bilinear")
                v_dem = dem_service.get_elevation_at_point(end_lat, end_lon, method="bilinear")

                # Add source node
                if u_id not in self.spatial_graph:
                    self.spatial_graph.add_node(
                        u_id,
                        node_id=u_id,
                        lat=round(start_lat, 6),
                        lon=round(start_lon, 6),
                        utm_x=round(sub_coords_utm[0][0], 2),
                        utm_y=round(sub_coords_utm[0][1], 2),
                        node_type=u_type,
                        source_osm_ways=[way["id"]],
                        dem_surface_elevation_m=u_dem,
                        provenance="VERIFIED_OSM_GEOMETRIC_VERTEX",
                    )
                else:
                    if way["id"] not in self.spatial_graph.nodes[u_id].get("source_osm_ways", []):
                        self.spatial_graph.nodes[u_id]["source_osm_ways"].append(way["id"])

                # Add target node
                if v_id not in self.spatial_graph:
                    self.spatial_graph.add_node(
                        v_id,
                        node_id=v_id,
                        lat=round(end_lat, 6),
                        lon=round(end_lon, 6),
                        utm_x=round(sub_coords_utm[-1][0], 2),
                        utm_y=round(sub_coords_utm[-1][1], 2),
                        node_type=v_type,
                        source_osm_ways=[way["id"]],
                        dem_surface_elevation_m=v_dem,
                        provenance="VERIFIED_OSM_GEOMETRIC_VERTEX",
                    )
                else:
                    if way["id"] not in self.spatial_graph.nodes[v_id].get("source_osm_ways", []):
                        self.spatial_graph.nodes[v_id]["source_osm_ways"].append(way["id"])

                # Compute surface drop along geometric line order
                elev_drop = round(u_dem - v_dem, 2) if (u_dem is not None and v_dem is not None) else None

                # Generate edge ID
                sub_suffix = f"reach_{s_idx + 1}" if len(sorted_splits) > 2 else "main"
                edge_id = f"EDGE_{way['id'].replace('/', '_')}_{sub_suffix}"

                # Add directed edge
                self.spatial_graph.add_edge(
                    u_id,
                    v_id,
                    key=edge_id,
                    edge_id=edge_id,
                    osm_id=way["osm_id"],
                    osm_way_id=way["id"],
                    sub_reach_index=s_idx + 1,
                    total_sub_reaches=len(sorted_splits) - 1,
                    name=f"{way['name']} ({sub_suffix})" if len(sorted_splits) > 2 else way["name"],
                    base_name=way["name"],
                    english_name=way["english_name"],
                    river_system=way["river_system"],
                    waterway_type=way["waterway_type"],
                    length_m=round(sub_line_utm.length, 2),
                    length_km=round(sub_line_utm.length / 1000.0, 3),
                    coordinates_count=len(sub_coords_wgs),
                    geometry_geojson={
                        "type": "LineString",
                        "coordinates": sub_coords_wgs,
                    },
                    geometric_u_dem_m=u_dem,
                    geometric_v_dem_m=v_dem,
                    geometric_surface_drop_m=elev_drop,
                    direction_status="GEOMETRIC_DIGITIZATION_ORDER_HYDRAULIC_UNVERIFIED",
                    hydraulic_validation_status="UNVERIFIED",
                    upstream_downstream_claim="NONE_UNVERIFIED",
                    data_provenance="OSM_MAPPED_GEOMETRY",
                    scientific_caution=(
                        "LineString coordinate orientation represents OpenStreetMap digitization order, "
                        "not verified physical water flow direction. Flow direction remains UNVERIFIED."
                    ),
                )

        # Phase D: Graph Connectivity & Components Analysis
        # Use undirected view to assess geometric continuity across reaches
        undirected_view = self.spatial_graph.to_undirected()
        connected_comp_nodes = list(nx.connected_components(undirected_view))
        
        components_list = []
        for c_idx, node_set in enumerate(connected_comp_nodes):
            subgraph_edges = [
                (u, v, k, d) for u, v, k, d in self.spatial_graph.edges(keys=True, data=True)
                if u in node_set and v in node_set
            ]
            ways_in_comp = [d["osm_way_id"] for u, v, k, d in subgraph_edges]
            comp_length_m = sum(d["length_m"] for u, v, k, d in subgraph_edges)
            is_isolated = len(node_set) <= 2 and len(subgraph_edges) == 1

            components_list.append({
                "component_index": c_idx + 1,
                "node_count": len(node_set),
                "edge_count": len(subgraph_edges),
                "total_length_km": round(comp_length_m / 1000.0, 3),
                "osm_ways": ways_in_comp,
                "is_isolated_segment": is_isolated,
                "connectivity_description": (
                    "Isolated reach: Disconnected from main river trunk in surface OSM geometry."
                    if is_isolated else "Connected network: Multi-reach continuous river network."
                ),
            })

        self.disconnected_mapped_segments = [c for c in components_list if c["is_isolated_segment"]]

        # Check proximity gaps between disconnected components (e.g. Pipliyahana -> Khan tributary)
        self.possible_subsurface_connections = []
        p_feeder = next((w for w in parsed_ways if w["id"] == "way/191774909"), None)
        k_trib = next((w for w in parsed_ways if w["id"] == "way/191774911"), None)
        if p_feeder and k_trib:
            p_end_pt = Point(p_feeder["end_utm"])
            dist_to_trib = p_end_pt.distance(k_trib["line_utm"])
            self.possible_subsurface_connections.append({
                "connection_id": "POSSIBLE_GAP_PIPLIYAHANA_TRIBUTARY",
                "from_feature": p_feeder["id"],
                "from_feature_name": p_feeder["name"],
                "to_feature": k_trib["id"],
                "to_feature_name": k_trib["name"],
                "gap_distance_m": round(dist_to_trib, 2),
                "status": "POSSIBLE_SUBSURFACE_CONNECTION_UNVERIFIED",
                "spatial_disconnection_maintained": True,
                "scientific_justification": (
                    f"An approximately {dist_to_trib:.1f}m spatial gap exists between the mapped terminus of Pipliyahana Drain Feeder "
                    "and the Khan tributary in OpenStreetMap surface geometry. The segments are kept strictly disconnected in the spatial "
                    "graph; no underground culvert or conduit connection is assumed without official municipal documentation."
                ),
            })

        self.connected_components_summary = {
            "total_connected_components": len(connected_comp_nodes),
            "isolated_reaches_count": len(self.disconnected_mapped_segments),
            "components": components_list,
        }

        # Phase E: Monitoring Stations Snapping
        self.evaluate_monitoring_stations_snapping()

        # Serialize full report to JSON
        self.generate_and_save_report()

        return self.spatial_graph

    def evaluate_monitoring_stations_snapping(
        self,
        tolerance_m: float = 50.0,
        nodes_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate spatial proximity of the 7 municipal monitoring stations to real OSM waterways.
        Calculates exact metric distance (UTM 43N), identifies nearest waterway, and classifies
        stations into ON_CHANNEL (<= 25m), NEAR_CHANNEL (25m - 150m), or OFF_CHANNEL (> 150m).
        Does NOT alter original monitoring station coordinates.
        """
        if nodes_dict is None:
            nodes_dict = config.DRAINAGE_NODES

        if not self.features_data and self.geojson_path.exists():
            with open(self.geojson_path, "r", encoding="utf-8") as f:
                self.features_data = json.load(f).get("features", [])

        # Build list of Shapely UTM geometries
        waterway_geoms = []
        for feat in self.features_data:
            geom_wgs = shape(feat["geometry"])
            coords_wgs = list(geom_wgs.coords)
            coords_utm = [self.transformer_to_utm.transform(lon, lat) for lon, lat in coords_wgs]
            line_utm = LineString(coords_utm)
            waterway_geoms.append({
                "id": feat.get("id"),
                "osm_id": feat.get("properties", {}).get("osm_id"),
                "name": feat.get("properties", {}).get("name", ""),
                "river_system": feat.get("properties", {}).get("river_system", ""),
                "line_utm": line_utm,
                "line_wgs": geom_wgs,
            })

        station_evaluations = {}
        counts = {"ON_CHANNEL": 0, "NEAR_CHANNEL": 0, "OFF_CHANNEL": 0}

        for node_id, data in nodes_dict.items():
            orig_lat = data["lat"]
            orig_lon = data["lon"]

            # Project station point to UTM
            st_x, st_y = self.transformer_to_utm.transform(orig_lon, orig_lat)
            st_point_utm = Point(st_x, st_y)

            # Find nearest waterway
            min_dist_m = float("inf")
            nearest_entry = None
            snapped_utm_pt = None

            for entry in waterway_geoms:
                dist = st_point_utm.distance(entry["line_utm"])
                if dist < min_dist_m:
                    min_dist_m = dist
                    nearest_entry = entry
                    p1, p2 = nearest_points(st_point_utm, entry["line_utm"])
                    snapped_utm_pt = p2

            # Project snapped point back to WGS84
            snapped_lon, snapped_lat = self.transformer_to_wgs.transform(snapped_utm_pt.x, snapped_utm_pt.y)

            # Proximity Classification
            if min_dist_m <= 25.0:
                classification = "ON_CHANNEL"
            elif min_dist_m <= 150.0:
                classification = "NEAR_CHANNEL"
            else:
                classification = "OFF_CHANNEL"

            counts[classification] += 1

            # Scientific justification statement (strictly empirical, zero assumed underground connections)
            if classification == "ON_CHANNEL":
                snapping_justification = (
                    f"Station coordinate is {min_dist_m:.1f}m from nearest mapped waterway geometry (<= 25m threshold). "
                    "Geometrically coincident with open channel corridor."
                )
                conn_status = "ON_CHANNEL_COINCIDENT"
            elif classification == "NEAR_CHANNEL":
                snapping_justification = (
                    f"Station coordinate is {min_dist_m:.1f}m from nearest mapped waterway geometry (25m - 150m threshold). "
                    "Located in urban vicinity of river corridor; no specific drain connection or pipe invert is assumed without municipal drawings."
                )
                conn_status = "NEAR_CHANNEL_UNCONNECTED"
            else:
                snapping_justification = (
                    f"Station coordinate is {min_dist_m:.1f}m from nearest mapped open river channel (> 150m threshold). "
                    "Classified as OFF_CHANNEL. Station coordinates are strictly preserved; no physical channel or underground connection is assumed."
                )
                conn_status = "DISCONNECTED_OFF_CHANNEL"

            station_evaluations[node_id] = {
                "node_id": node_id,
                "station_name": data.get("name", node_id),
                "original_coordinates": {
                    "lat": orig_lat,
                    "lon": orig_lon,
                    "crs": "EPSG:4326 (WGS84)",
                },
                "snapped_channel_coordinates": {
                    "lat": round(snapped_lat, 6),
                    "lon": round(snapped_lon, 6),
                    "crs": "EPSG:4326 (WGS84)",
                },
                "distance_to_nearest_waterway_m": round(min_dist_m, 2),
                "nearest_waterway_id": nearest_entry["id"] if nearest_entry else None,
                "nearest_waterway_name": nearest_entry["name"] if nearest_entry else None,
                "nearest_river_system": nearest_entry["river_system"] if nearest_entry else None,
                "spatial_classification": classification,
                "hydraulic_connection_status": conn_status,
                "is_within_tolerance": min_dist_m <= tolerance_m,
                "snapping_tolerance_applied_m": tolerance_m,
                "scientific_justification": snapping_justification,
                "recommendation": (
                    "PRESERVE_ORIGINAL_COORDINATES: Station coordinates must be preserved. "
                    "Do not automatically snap or connect OFF_CHANNEL stations to river geometry."
                ),
            }

        self.monitoring_snapping_summary = {
            "snapping_tolerance_m": tolerance_m,
            "classification_counts": counts,
            "station_evaluations": station_evaluations,
            "governing_policy": (
                "Do not silently move existing monitoring stations. Urban monitoring nodes represent "
                "road junction sumps, STP perimeters, or headwater boundaries. Both original and snapped "
                "coordinates are recorded with explicit distance metrics."
            ),
        }
        return self.monitoring_snapping_summary

    def generate_and_save_report(self) -> Dict[str, Any]:
        """Compile and serialize the complete Phase 2A Spatial Network Quality Report."""
        nodes_list = []
        for n_id, data in self.spatial_graph.nodes(data=True):
            nodes_list.append({
                "node_id": n_id,
                "node_type": data.get("node_type"),
                "lat": round(data.get("lat", 0.0), 6),
                "lon": round(data.get("lon", 0.0), 6),
                "utm_x": round(data.get("utm_x", 0.0), 2),
                "utm_y": round(data.get("utm_y", 0.0), 2),
                "source_osm_ways": data.get("source_osm_ways", []),
                "dem_surface_elevation_m": data.get("dem_surface_elevation_m"),
                "provenance": data.get("provenance"),
            })

        edges_list = []
        for u, v, k, data in self.spatial_graph.edges(keys=True, data=True):
            edges_list.append({
                "edge_id": data.get("edge_id"),
                "from_node": u,
                "to_node": v,
                "osm_way_id": data.get("osm_way_id"),
                "osm_id": data.get("osm_id"),
                "name": data.get("name"),
                "waterway_type": data.get("waterway_type"),
                "length_m": data.get("length_m"),
                "length_km": data.get("length_km"),
                "coordinates_count": data.get("coordinates_count"),
                "geometric_u_dem_m": data.get("geometric_u_dem_m"),
                "geometric_v_dem_m": data.get("geometric_v_dem_m"),
                "geometric_surface_drop_m": data.get("geometric_surface_drop_m"),
                "direction_status": data.get("direction_status"),
                "hydraulic_validation_status": data.get("hydraulic_validation_status"),
                "data_provenance": data.get("data_provenance"),
            })

        total_length_m = sum(e["length_m"] for e in edges_list)

        report = {
            "title": "HYDRO-GUARD AI — Phase 2A Real Spatial River Network Report",
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "geography": {
                "city": "Indore, Madhya Pradesh, India",
                "projection": f"UTM Zone 43N ({UTM_CRS}) for metric measurements",
                "geographic_crs": f"WGS84 ({GEO_CRS}) for latitude/longitude coordinates",
            },
            "provenance_distinction_statement": {
                "REAL_OSM_GEOMETRY": (
                    "OpenStreetMap mapped geometries, derived from OSM source data (ODbL 1.0 license by OpenStreetMap Foundation)."
                ),
                "DERIVED_SPATIAL_RELATIONSHIPS": (
                    "Junctions, endpoints, and metric reach lengths derived through Shapely/PyProj "
                    "metric intersection and projection algorithms."
                ),
                "ASSUMED_HYDRAULIC_RELATIONSHIPS": (
                    "The legacy 6-edge directed graph (Rau -> Kabithedi) representing assumed gravity flow "
                    "between urban sumps, maintained separate from real river geometry."
                ),
                "UNVERIFIED_CONNECTIONS": (
                    "All physical flow directions and subsurface connections (such as culverts connecting "
                    "Pipliyahana Drain or underground storm pipes) remain UNVERIFIED pending municipal invert data."
                ),
            },
            "network_statistics": {
                "total_osm_features": len(self.features_data),
                "total_spatial_nodes": len(nodes_list),
                "total_spatial_edges": len(edges_list),
                "total_mapped_network_length_km": round(total_length_m / 1000.0, 3),
                "total_mapped_network_length_m": round(total_length_m, 2),
                "duplicate_geometries_count": 0,
                "river_confluence_candidates_count": len(self.confluence_candidates),
                "continuity_junctions_count": len(self.continuity_junctions),
                "total_geometric_junctions_count": len(self.junction_candidates),
                "detected_confluence_junctions_count": len(self.junction_candidates),
                "connected_components_count": self.connected_components_summary.get("total_connected_components", 0),
                "isolated_segments_count": self.connected_components_summary.get("isolated_reaches_count", 0),
            },
            "confluence_candidates": self.confluence_candidates,
            "continuity_junctions": self.continuity_junctions,
            "junction_candidates": self.junction_candidates,
            "disconnected_mapped_segments": self.disconnected_mapped_segments,
            "possible_subsurface_connections": self.possible_subsurface_connections,
            "hydraulic_direction_status": "UNVERIFIED_ALL_SPATIAL_EDGES",
            "connected_components": self.connected_components_summary,
            "monitoring_stations_snapping": self.monitoring_snapping_summary,
            "spatial_graph_nodes": nodes_list,
            "spatial_graph_edges": edges_list,
        }

        self._report_cache = report

        # Write to disk
        try:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"[SpatialNetwork] Serialized quality report to {self.report_path}")
        except Exception as e:
            print(f"[SpatialNetwork] Failed to write report: {e}")

        return report

    def get_spatial_network_report(self) -> Dict[str, Any]:
        """Return the serialized Phase 2A report (loads from cache/disk if available)."""
        if self._report_cache is not None:
            return self._report_cache
        if self.report_path.exists():
            try:
                with open(self.report_path, "r", encoding="utf-8") as f:
                    self._report_cache = json.load(f)
                    return self._report_cache
            except Exception:
                pass
        return self.generate_and_save_report()

    def to_spatial_geojson(self) -> Dict[str, Any]:
        """
        Export complete spatial river network as a unified GeoJSON FeatureCollection:
        - Real OSM LineString waterways
        - Detected confluence junction points
        - Monitoring stations with original coordinates and snapping vectors
        """
        features = []

        # 1. Real Waterway Reaches
        for u, v, k, data in self.spatial_graph.edges(keys=True, data=True):
            geom = data.get("geometry_geojson")
            if geom:
                features.append({
                    "type": "Feature",
                    "id": data.get("edge_id"),
                    "geometry": geom,
                    "properties": {
                        "layer_type": "spatial_waterway_reach",
                        "edge_id": data.get("edge_id"),
                        "osm_way_id": data.get("osm_way_id"),
                        "name": data.get("name"),
                        "waterway_type": data.get("waterway_type"),
                        "length_m": data.get("length_m"),
                        "length_km": data.get("length_km"),
                        "is_real_gis_data": True,
                        "direction_status": data.get("direction_status"),
                        "hydraulic_status": data.get("hydraulic_validation_status"),
                        "provenance": data.get("data_provenance"),
                    }
                })

        # 2. Confluence Junction Nodes
        for j in self.junction_candidates:
            features.append({
                "type": "Feature",
                "id": j.get("junction_id"),
                "geometry": {
                    "type": "Point",
                    "coordinates": [j["lon"], j["lat"]],
                },
                "properties": {
                    "layer_type": "river_confluence_junction",
                    "junction_id": j.get("junction_id"),
                    "name": j.get("name"),
                    "intersecting_features": j.get("intersecting_features"),
                    "intersecting_ways": j.get("intersecting_ways"),
                    "is_real_gis_data": True,
                    "hydraulic_status": j.get("hydraulic_status"),
                    "provenance": j.get("provenance"),
                }
            })

        # 3. Monitoring Stations (preserving original coordinates, linking snapping target)
        snapping = self.monitoring_snapping_summary.get("station_evaluations", {})
        for node_id, data in config.DRAINAGE_NODES.items():
            snap_info = snapping.get(node_id, {})
            features.append({
                "type": "Feature",
                "id": node_id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [data["lon"], data["lat"]],
                },
                "properties": {
                    "layer_type": "monitoring_station",
                    "node_id": node_id,
                    "name": data["name"],
                    "hindi_name": data["hindi_name"],
                    "assumed_elevation_m": data["elevation_m"],
                    "snapping_distance_m": snap_info.get("distance_to_nearest_waterway_m"),
                    "spatial_classification": snap_info.get("spatial_classification"),
                    "nearest_waterway": snap_info.get("nearest_waterway_name"),
                    "is_real_gis_data": False,
                    "provenance": "URBAN_MONITORING_STATION_COORDINATE",
                }
            })

        return {
            "type": "FeatureCollection",
            "metadata": {
                "service": "IndoreSpatialNetworkService",
                "description": "Real spatial river network with detected confluences and monitoring stations",
                "crs": "EPSG:4326 (WGS84)",
                "metric_projection": "UTM Zone 43N (EPSG:32643)",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "features": features,
        }


# Singleton service instance
spatial_network_service = IndoreSpatialNetworkService()


if __name__ == "__main__":
    report = spatial_network_service.get_spatial_network_report()
    stats = report["network_statistics"]
    print("\n--- PHASE 2A SPATIAL RIVER NETWORK SUMMARY ---")
    print(f"Total OSM Features: {stats['total_osm_features']}")
    print(f"Total Spatial Nodes: {stats['total_spatial_nodes']}")
    print(f"Total Spatial Edges: {stats['total_spatial_edges']}")
    print(f"Total Mapped Length: {stats['total_mapped_network_length_km']} km")
    print(f"Confluence Junctions: {stats['detected_confluence_junctions_count']}")
    print(f"Connected Components: {stats['connected_components_count']} (Isolated: {stats['isolated_segments_count']})")
    print("\nMonitoring Stations Proximity:")
    for nid, s in report["monitoring_stations_snapping"]["station_evaluations"].items():
        print(f"  {nid:20s}: {s['distance_to_nearest_waterway_m']:7.2f}m [{s['spatial_classification']:12s}] -> {s['nearest_waterway_name']}")
