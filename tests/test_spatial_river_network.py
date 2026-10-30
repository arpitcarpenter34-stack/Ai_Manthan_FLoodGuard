"""
Focused Test Suite for Phase 2A Real Spatial River Network & Graph Construction.
Validates:
1. OpenStreetMap GeoJSON loading and LineString validity.
2. Metric distance calculations via UTM Zone 43N (EPSG:32643).
3. Confluence junction detection (Krishnapura Chhatri, Mid-Khan Tributary, Saraswati joint).
4. Connected components and isolated reach detection.
5. Monitoring node spatial snapping distances and classifications.
6. Spatial graph construction (13 nodes, 9 edges, 41.355 km mapped).
7. FastAPI GET /api/v1/flood/spatial-network endpoint schema.
8. Backward compatibility of /topology, /predict, and /dem/elevation-audit.
"""

import json
import sys
from pathlib import Path
from shapely.geometry import shape, LineString

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.spatial_network_service import spatial_network_service
import config

client = TestClient(app)


def test_spatial_network_service_initialization_and_metadata():
    """Verify spatial network service loads 7 OSM features and computes UTM metric length."""
    rep = spatial_network_service.get_spatial_network_report()
    stats = rep["network_statistics"]

    assert stats["total_osm_features"] == 7
    assert stats["total_spatial_edges"] == 9
    assert stats["total_spatial_nodes"] == 13
    assert stats["total_mapped_network_length_km"] > 40.0
    assert stats["duplicate_geometries_count"] == 0
    assert stats["river_confluence_candidates_count"] == 2
    assert stats["continuity_junctions_count"] == 1
    assert stats["total_geometric_junctions_count"] == 3

    # Check scientific provenance statement
    prov = rep.get("provenance_distinction_statement", {})
    assert "OpenStreetMap mapped geometries" in prov.get("REAL_OSM_GEOMETRY", "")
    assert "ODbL 1.0" in prov.get("REAL_OSM_GEOMETRY", "")

    print(f"\n[PASS] Spatial network service initialized: {stats['total_spatial_edges']} edges, "
          f"{stats['total_spatial_nodes']} nodes, {stats['total_mapped_network_length_km']} km mapped, "
          f"{stats['river_confluence_candidates_count']} confluence candidates, {stats['continuity_junctions_count']} continuity junction.")


def test_geometry_validity_and_duplicates():
    """Verify all geometries are valid LineStrings and check for duplicate geometries."""
    features = spatial_network_service.features_data
    assert len(features) == 7

    seen_geoms = set()
    total_pts = 0
    for feat in features:
        geom = shape(feat["geometry"])
        assert geom.is_valid, f"Invalid geometry for {feat.get('id')}"
        assert geom.geom_type == "LineString"
        coords = list(geom.coords)
        assert len(coords) >= 2
        total_pts += len(coords)

        # Hash coordinates tuple to detect duplicates
        h = tuple(coords)
        assert h not in seen_geoms, f"Duplicate geometry found in {feat.get('id')}"
        seen_geoms.add(h)

    assert total_pts >= 1000
    print(f"\n[PASS] Verified {len(features)} valid LineStrings with {total_pts} GPS points and 0 duplicates.")


def test_metric_junction_detection():
    """Verify detection of real river confluences with UTM metric coordinates and proper junction classification."""
    rep = spatial_network_service.get_spatial_network_report()
    junctions = rep["junction_candidates"]
    assert len(junctions) == 3, f"Expected 3 geometric junctions, got {len(junctions)}"

    # Check separated collections
    confluences = rep.get("confluence_candidates", [])
    continuity = rep.get("continuity_junctions", [])
    assert len(confluences) == 2, f"Expected 2 confluence candidates, got {len(confluences)}"
    assert len(continuity) == 1, f"Expected 1 continuity junction, got {len(continuity)}"

    # Check Krishnapura Chhatri Confluence (Khan River & Saraswati River)
    krishnapura = [j for j in confluences if any("Saraswathi" in f or "Saraswati" in f for f in j["intersecting_features"])
                   and any("Kanh" in f or "Khan" in f for f in j["intersecting_features"])]
    assert len(krishnapura) >= 1
    k_junc = krishnapura[0]
    assert k_junc["junction_type"] == "RIVER_CONFLUENCE_CANDIDATE"
    assert abs(k_junc["lat"] - 22.718464) < 1e-4
    assert abs(k_junc["lon"] - 75.858849) < 1e-4
    assert k_junc["provenance"] == "DERIVED_GEOMETRIC_INTERSECTION"
    assert k_junc["hydraulic_status"] == "UNVERIFIED_PHYSICAL_CONFLUENCE"

    # Check Mid-Khan Confluence (Khan River & Khan Tributary)
    mid_khan = [j for j in confluences if any("tributary" in f for f in j["intersecting_features"])]
    assert len(mid_khan) >= 1
    m_junc = mid_khan[0]
    assert m_junc["junction_type"] == "RIVER_CONFLUENCE_CANDIDATE"
    assert abs(m_junc["lat"] - 22.746302) < 1e-4
    assert abs(m_junc["lon"] - 75.864860) < 1e-4

    # Check Saraswati Reach Continuity Joint
    s_cont = continuity[0]
    assert s_cont["junction_type"] == "CONTINUITY_JUNCTION"
    assert "Saraswati" in s_cont["classification_description"]
    assert s_cont["hydraulic_status"] == "CONTINUOUS_CHANNEL_JOINT"

    # Check Subsurface connections
    subsurface = rep.get("possible_subsurface_connections", [])
    assert len(subsurface) >= 1
    p_gap = subsurface[0]
    assert p_gap["status"] == "POSSIBLE_SUBSURFACE_CONNECTION_UNVERIFIED"
    assert p_gap["from_feature"] == "way/191774909"
    assert p_gap["spatial_disconnection_maintained"] is True
    assert 50.0 <= p_gap["gap_distance_m"] <= 55.0

    print(f"\n[PASS] Junctions classified: 2 confluence candidates (Krishnapura at {k_junc['lat']:.5f}, {k_junc['lon']:.5f}; "
          f"Mid-Khan at {m_junc['lat']:.5f}, {m_junc['lon']:.5f}), 1 continuity junction ({s_cont['name']}), "
          f"and Pipliyahana {p_gap['gap_distance_m']}m gap verified unverified/disconnected.")


def test_connected_components_and_isolation():
    """Verify multi-reach continuous network vs. disconnected/isolated reaches."""
    rep = spatial_network_service.get_spatial_network_report()
    cc = rep["connected_components"]

    assert cc["total_connected_components"] == 4, f"Expected 4 components, got {cc['total_connected_components']}"
    assert cc["isolated_reaches_count"] == 3

    comps = cc["components"]
    main_comp = [c for c in comps if not c["is_isolated_segment"]][0]
    assert main_comp["edge_count"] == 6
    assert main_comp["total_length_km"] > 35.0

    isolated_comps = [c for c in comps if c["is_isolated_segment"]]
    assert len(isolated_comps) == 3

    # Verify edge direction status and unverified hydraulic status on all spatial edges
    for e in rep.get("spatial_graph_edges", []):
        assert e["direction_status"] == "GEOMETRIC_DIGITIZATION_ORDER_HYDRAULIC_UNVERIFIED"
        assert e["hydraulic_validation_status"] == "UNVERIFIED"

    assert rep.get("hydraulic_direction_status") == "UNVERIFIED_ALL_SPATIAL_EDGES"

    print(f"\n[PASS] Graph topology verified: 1 main connected river network ({main_comp['total_length_km']} km), "
          f"3 isolated reach components, and all edges marked GEOMETRIC_DIGITIZATION_ORDER_HYDRAULIC_UNVERIFIED.")


def test_monitoring_node_spatial_snapping():
    """Verify snapping distances and spatial classification for all 7 monitoring stations."""
    rep = spatial_network_service.get_spatial_network_report()
    snapping = rep["monitoring_stations_snapping"]
    counts = snapping["classification_counts"]

    assert counts["NEAR_CHANNEL"] == 1
    assert counts["OFF_CHANNEL"] == 6
    assert counts["ON_CHANNEL"] == 0

    evals = snapping["station_evaluations"]
    assert len(evals) == 7

    # Check Pardeshipura: NEAR_CHANNEL (~70.8m)
    p_info = evals["NODE_PARDESHIPURA"]
    assert p_info["spatial_classification"] == "NEAR_CHANNEL"
    assert 60.0 <= p_info["distance_to_nearest_waterway_m"] <= 80.0
    assert "Khan tributary" in p_info["nearest_waterway_name"]

    # Check Rajwada: OFF_CHANNEL (~354.9m)
    r_info = evals["NODE_RAJWARA"]
    assert r_info["spatial_classification"] == "OFF_CHANNEL"
    assert 340.0 <= r_info["distance_to_nearest_waterway_m"] <= 370.0
    assert "Kanh" in r_info["nearest_waterway_name"] or "Khan" in r_info["nearest_waterway_name"]

    # Check Rau: OFF_CHANNEL (~2575m)
    rau_info = evals["NODE_RAU"]
    assert rau_info["spatial_classification"] == "OFF_CHANNEL"
    assert rau_info["distance_to_nearest_waterway_m"] > 2000.0

    # Ensure original station coordinates are preserved
    for nid, s in evals.items():
        orig_lat = s["original_coordinates"]["lat"]
        orig_lon = s["original_coordinates"]["lon"]
        assert orig_lat == config.DRAINAGE_NODES[nid]["lat"]
        assert orig_lon == config.DRAINAGE_NODES[nid]["lon"]

    print(f"\n[PASS] Monitoring snapping verified: 1 NEAR_CHANNEL (Pardeshipura: {p_info['distance_to_nearest_waterway_m']}m), "
          f"6 OFF_CHANNEL, all original coordinates preserved.")


def test_spatial_network_api_endpoint():
    """Verify GET /api/v1/flood/spatial-network returns 200 with complete payload and separated junction metrics."""
    response = client.get("/api/v1/flood/spatial-network")
    assert response.status_code == 200
    data = response.json()

    assert data.get("status") == "success"
    assert "network_statistics" in data
    assert "provenance_distinction" in data
    assert "confluence_candidates" in data
    assert "continuity_junctions" in data
    assert "junction_candidates" in data
    assert "connected_components" in data
    assert "disconnected_mapped_segments" in data
    assert "possible_subsurface_connections" in data
    assert "hydraulic_direction_status" in data
    assert "monitoring_stations_snapping" in data
    assert "spatial_graph_nodes" in data
    assert "spatial_graph_edges" in data
    assert "spatial_geojson" in data

    # Verify separated counts
    stats = data["network_statistics"]
    assert stats["river_confluence_candidates_count"] == 2
    assert stats["continuity_junctions_count"] == 1
    assert stats["total_geometric_junctions_count"] == 3
    assert len(data["confluence_candidates"]) == 2
    assert len(data["continuity_junctions"]) == 1
    assert len(data["possible_subsurface_connections"]) >= 1
    assert data["hydraulic_direction_status"] == "UNVERIFIED_ALL_SPATIAL_EDGES"

    # Validate GeoJSON features
    geojson = data["spatial_geojson"]
    assert geojson.get("type") == "FeatureCollection"
    features = geojson.get("features", [])
    assert len(features) == 19  # 9 reaches + 3 junctions + 7 stations

    layer_types = set(f.get("properties", {}).get("layer_type") for f in features)
    assert "spatial_waterway_reach" in layer_types
    assert "river_confluence_junction" in layer_types
    assert "monitoring_station" in layer_types

    print(f"\n[PASS] GET /api/v1/flood/spatial-network returned 200 with {len(features)} GeoJSON features across 3 layers.")


def test_existing_apis_backward_compatibility():
    """Verify existing APIs continue functioning without regression."""
    # 1. /topology
    res_topo = client.get("/api/v1/flood/topology")
    assert res_topo.status_code == 200
    d_topo = res_topo.json()
    assert "assumed_elevation_bounds" in d_topo
    assert "dem_surface_elevation_bounds" in d_topo
    assert "elevation_bounds" in d_topo
    assert len(d_topo.get("real_waterways", {}).get("features", [])) >= 5

    # 2. /predict
    res_pred = client.post("/api/v1/flood/predict", json={
        "rainfall_intensity_mmh": 25.0,
        "surge_multiplier": 1.0,
        "active_pumps_count": 2
    })
    assert res_pred.status_code == 200
    d_pred = res_pred.json()
    assert d_pred.get("status") == "success"
    assert len(d_pred.get("node_predictions", [])) == 7

    # 3. /dem/elevation-audit
    res_dem = client.get("/api/v1/flood/dem/elevation-audit")
    assert res_dem.status_code == 200
    d_dem = res_dem.json()
    assert d_dem.get("status") == "success"
    assert "report" in d_dem

    print(f"\n[PASS] All existing endpoints (/topology, /predict, /dem/elevation-audit) verified backward compatible.")


if __name__ == "__main__":
    test_spatial_network_service_initialization_and_metadata()
    test_geometry_validity_and_duplicates()
    test_metric_junction_detection()
    test_connected_components_and_isolation()
    test_monitoring_node_spatial_snapping()
    test_spatial_network_api_endpoint()
    test_existing_apis_backward_compatibility()
    print("\nALL PHASE 2A SPATIAL RIVER NETWORK TESTS PASSED SUCCESSFULLY!")

