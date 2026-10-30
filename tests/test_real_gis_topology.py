"""
Focused Regression Test Suite for Real GIS Topology Ingestion in HYDRO-GUARD AI.
Validates:
1. GeoJSON syntax, coordinates, and bounding box compliance for Indore.
2. Metadata provenance, CRS, and OSM attribution.
3. IndoreGISLoader service methods.
4. FastAPI /api/v1/flood/topology response integrity and real waterway schemas.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.osmnx_gis_loader import indore_gis_loader
from backend.services.dem_service import dem_service, DEM_REPORT_PATH, DEM_METADATA_PATH, DEM_LOCAL_PATH
import config


client = TestClient(app)
GIS_DIR = config.GIS_DIR
GEOJSON_FILE = GIS_DIR / "indore_waterways_osm.geojson"
METADATA_FILE = GIS_DIR / "indore_waterways_metadata.json"


def test_geojson_file_structure_and_coordinates():
    """Verify saved indore_waterways_osm.geojson is valid GeoJSON and within Indore basin."""
    assert GEOJSON_FILE.exists(), f"Missing GeoJSON file at {GEOJSON_FILE}"

    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) >= 5, f"Expected at least 5 waterway reaches, got {len(features)}"

    total_coords = 0
    # Indore metropolitan bounds with safety margin: lat [22.60, 22.85], lon [75.75, 75.96]
    for feat in features:
        assert feat.get("type") == "Feature"
        geom = feat.get("geometry", {})
        assert geom.get("type") == "LineString"
        coords = geom.get("coordinates", [])
        assert len(coords) >= 2, f"Feature {feat.get('id')} has fewer than 2 points"
        total_coords += len(coords)

        # Coordinate check: [lon, lat] in EPSG:4326
        for lon, lat in coords:
            assert 22.60 <= lat <= 22.85, f"Latitude {lat} outside Indore bounding box in feature {feat.get('id')}"
            assert 75.75 <= lon <= 75.96, f"Longitude {lon} outside Indore bounding box in feature {feat.get('id')}"

        props = feat.get("properties", {})
        assert props.get("is_real_gis_data") is True
        assert props.get("source") == "OpenStreetMap"
        assert "osm_id" in props

    assert total_coords >= 500, f"Expected >= 500 GPS coordinate points, got {total_coords}"
    print(f"\n[PASS] Verified {len(features)} waterway features with {total_coords} GPS coordinates in Indore.")


def test_metadata_provenance():
    """Verify metadata contains source, CRS, timestamp, and engineering distinction."""
    assert METADATA_FILE.exists(), f"Missing metadata file at {METADATA_FILE}"

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta.get("is_real_gis_data") is True
    assert "OpenStreetMap" in meta.get("source", "")
    assert meta.get("crs") == "EPSG:4326 (WGS84)"
    assert "retrieval_timestamp" in meta
    assert meta.get("total_waterway_length_km", 0) > 20.0
    assert "engineering_distinction" in meta
    print(f"\n[PASS] Metadata verified: {meta.get('total_waterway_length_km')} km mapped in {meta.get('crs')}.")


def test_gis_loader_service():
    """Verify IndoreGISLoader service integrates real waterways with schematic edges."""
    rw = indore_gis_loader.get_real_waterways_geojson()
    assert rw.get("type") == "FeatureCollection"
    assert len(rw.get("features", [])) >= 5

    unified_geojson = indore_gis_loader.to_geojson()
    features = unified_geojson.get("features", [])
    assert len(features) >= 13, f"Expected >= 13 features for backward compatibility, got {len(features)}"

    # Check distinct layer types
    layer_types = set(f.get("properties", {}).get("layer_type") for f in features)
    assert "monitoring_station" in layer_types
    assert "real_waterway" in layer_types
    assert "schematic_flow_edge" in layer_types

    # Ensure real waterways are flagged True and schematic edges are flagged False
    for f in features:
        props = f.get("properties", {})
        if props.get("layer_type") == "real_waterway":
            assert props.get("is_real_gis_data") is True
        elif props.get("layer_type") == "schematic_flow_edge":
            assert props.get("is_real_gis_data") is False
            assert "ILLUSTRATIVE" in props.get("provenance", "")

    print(f"\n[PASS] IndoreGISLoader successfully unified 3 distinct layers ({len(features)} total features).")


def test_topology_api_endpoint():
    """Verify GET /api/v1/flood/topology returns 200 with complete real GIS payload."""
    response = client.get("/api/v1/flood/topology")
    assert response.status_code == 200
    data = response.json()

    assert data.get("status") == "success"
    assert "real_waterways" in data
    assert "metadata" in data
    assert "geojson" in data
    assert "elevation_bounds" in data
    assert "assumed_elevation_bounds" in data
    assert "dem_surface_elevation_bounds" in data
    assert "dem_metadata" in data
    assert data["dem_metadata"]["is_dem_available"] is True

    # Validate separated elevation bounds
    assumed_b = data["assumed_elevation_bounds"]
    dem_b = data["dem_surface_elevation_bounds"]
    assert assumed_b["max_msl_m"] == 560.0
    assert assumed_b["min_msl_m"] == 515.0
    assert assumed_b["elevation_drop_m"] == 45.0
    assert dem_b["max_surface_m"] == 579.61
    assert dem_b["min_surface_m"] == 540.14
    assert dem_b["elevation_drop_m"] == 39.47

    rw_features = data["real_waterways"].get("features", [])
    assert len(rw_features) >= 5

    # Check that Khan River and Saraswati River are explicitly present
    names = [f.get("properties", {}).get("name", "") for f in rw_features]
    has_khan = any("Khan" in n or "Kanh" in n for n in names)
    has_saraswati = any("Saraswati" in n or "Saraswathi" in n for n in names)
    assert has_khan, f"Khan River not found in {names}"
    assert has_saraswati, f"Saraswati River not found in {names}"

    print(f"\n[PASS] /api/v1/flood/topology returned 200 with verified channels, separated bounds (Assumed: 45m drop, DEM Surface: 39.47m drop).")


def test_dem_service_extraction_and_bounds():
    """Verify CopernicusDEMService extraction, bounding checks, and interpolation."""
    assert DEM_LOCAL_PATH.exists(), f"Local DEM raster missing at {DEM_LOCAL_PATH}"
    assert dem_service.is_available, "DEM service failed to load raster"

    # 1. Official NODE_RAJWARA station coordinate (Krishnapura Confluence: lat 22.7186, lon 75.8550)
    rajwada_node = config.DRAINAGE_NODES["NODE_RAJWARA"]
    node_lat, node_lon = rajwada_node["lat"], rajwada_node["lon"]
    elev_node_bilinear = dem_service.get_elevation_at_point(node_lat, node_lon, method="bilinear")
    elev_node_nearest = dem_service.get_elevation_at_point(node_lat, node_lon, method="nearest")
    assert elev_node_bilinear == 556.41, f"Expected 556.41m at NODE_RAJWARA, got {elev_node_bilinear}m"
    assert elev_node_nearest == 556.51, f"Expected 556.51m nearest at NODE_RAJWARA, got {elev_node_nearest}m"

    # 2. Rajwada Palace Chowk historical landmark coordinate (lat 22.7196, lon 75.8577)
    # Situated ~300m northeast of the river confluence; verifies raster spatial differentiation
    chowk_lat, chowk_lon = 22.7196, 75.8577
    elev_chowk_bilinear = dem_service.get_elevation_at_point(chowk_lat, chowk_lon, method="bilinear")
    elev_chowk_nearest = dem_service.get_elevation_at_point(chowk_lat, chowk_lon, method="nearest")
    assert elev_chowk_bilinear == 548.97, f"Expected 548.97m at Rajwada Chowk, got {elev_chowk_bilinear}m"
    assert elev_chowk_nearest == 546.56, f"Expected 546.56m nearest at Rajwada Chowk, got {elev_chowk_nearest}m"

    # 3. Coordinates outside N22-E075 tile boundary should return None safely
    elev_outside_north = dem_service.get_elevation_at_point(24.5, 75.5)
    assert elev_outside_north is None, "Expected None for coordinates outside tile bounds"

    elev_outside_east = dem_service.get_elevation_at_point(22.5, 77.0)
    assert elev_outside_east is None, "Expected None for coordinates outside tile bounds"

    print(f"\n[PASS] DEM service extracted {elev_node_bilinear}m MSL at NODE_RAJWARA (22.7186, 75.8550) matching report, "
          f"and differentiated {elev_chowk_bilinear}m MSL at Rajwada Chowk (22.7196, 75.8577).")


def test_dem_elevation_report_and_metadata():
    """Verify indore_dem_elevation_report.json and indore_dem_metadata.json structure and contents."""
    assert DEM_REPORT_PATH.exists(), f"DEM report missing at {DEM_REPORT_PATH}"
    assert DEM_METADATA_PATH.exists(), f"DEM metadata missing at {DEM_METADATA_PATH}"

    with open(DEM_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    with open(DEM_METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Validate metadata provenance
    assert metadata.get("provenance") == "VERIFIED_DEM_SURFACE_ELEVATION"
    assert metadata.get("resolution") == "30m"
    assert metadata.get("vertical_datum") == "EGM2008"
    assert metadata.get("node_count") == 7

    # Validate report structure
    assert "geography" in report
    assert "scientific_constraints_statement" in report
    assert "basin_gradient_summary" in report
    assert "nodes_elevation_comparison" in report
    assert "edges_hydraulic_validation" in report
    assert "remaining_uncertainties" in report

    # Check 7 nodes
    nodes = report["nodes_elevation_comparison"]
    assert len(nodes) == 7
    expected_node_ids = [
        "NODE_RAU", "NODE_BHANWARKUAN", "NODE_RAMBAGH",
        "NODE_RAJWARA", "NODE_VIJAY_NAGAR", "NODE_PARDESHIPURA", "NODE_KABITHEDI_STP"
    ]
    for nid in expected_node_ids:
        assert nid in nodes, f"Missing node {nid} in DEM report"
        node_data = nodes[nid]
        assert "assumed_elevation_m" in node_data
        assert "dem_surface_elevation_m" in node_data
        assert "elevation_delta_m" in node_data
        assert node_data["dem_surface_elevation_m"] is not None

    # Check Rambagh to Rajwada special investigation
    edges = report["edges_hydraulic_validation"]
    rambagh_rajwada = [e for e in edges if e["from_node"] == "NODE_RAMBAGH" and e["to_node"] == "NODE_RAJWARA"]
    assert len(rambagh_rajwada) == 1
    rr_edge = rambagh_rajwada[0]
    assert rr_edge["scientific_status"] == "SURFACE_SLOPE_ADVERSE"
    assert rr_edge.get("hydraulic_direction_status") == "UNVERIFIED"
    assert rr_edge["special_investigation_note"] is not None
    assert "RAMBAGH-TO-RAJWADA INVESTIGATION" in rr_edge["special_investigation_note"]
    assert "552.26" in rr_edge["special_investigation_note"]

    # Check the other 5 edges: must be SURFACE_SLOPE_CONSISTENT with UNVERIFIED hydraulic status
    downhill_edges = [e for e in edges if e["from_node"] != "NODE_RAMBAGH"]
    assert len(downhill_edges) == 5
    for e in downhill_edges:
        assert e["scientific_status"] == "SURFACE_SLOPE_CONSISTENT"
        assert e["hydraulic_direction_status"] == "UNVERIFIED"
        assert "hydraulic_validation_limitation" in e

    # Check basin gradient: Rau (South) to Kabithedi (North) slope confirmed
    basin = report["basin_gradient_summary"]
    assert basin["regional_south_to_north_gravity_slope_confirmed"] is True
    assert basin["total_dem_surface_drop_m"] > 30.0

    print(f"\n[PASS] Verified DEM report with {len(nodes)} nodes, {len(edges)} edges, and Rambagh-Rajwada investigation.")


def test_dem_elevation_audit_endpoint():
    """Verify GET /api/v1/flood/dem/elevation-audit returns 200 with complete audit report."""
    response = client.get("/api/v1/flood/dem/elevation-audit")
    assert response.status_code == 200
    data = response.json()

    assert data.get("status") == "success"
    assert "report" in data
    report = data["report"]
    assert "nodes_elevation_comparison" in report
    assert "edges_hydraulic_validation" in report
    assert "basin_gradient_summary" in report

    print(f"\n[PASS] GET /api/v1/flood/dem/elevation-audit returned HTTP 200 with complete report payload.")


if __name__ == "__main__":
    test_geojson_file_structure_and_coordinates()
    test_metadata_provenance()
    test_gis_loader_service()
    test_topology_api_endpoint()
    test_dem_service_extraction_and_bounds()
    test_dem_elevation_report_and_metadata()
    test_dem_elevation_audit_endpoint()
    print("\nALL FOCUSED GIS & DEM TESTS PASSED SUCCESSFULLY!")
