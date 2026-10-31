"""
Test Suite for AQUAGUARD AI: Drainage Blockage Monitoring, Topographical Mapping & Reports Module.
Verifies all 10 module requirements:
- City selection & zero-fabrication protocol (Pune disclaimer)
- Topographical drainage network segments & Copernicus DEM elevation
- Confirmed (RED) and Suspected (ORANGE) blockage classification
- OpenCV image evidence screening
- ReportLab individual PDF generation & download
- ReportLab city-wide PDF generation & download
- Tabular CSV dataset export
- Preservation of existing FastAPI endpoints & database tables
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.db_manager import db_manager
from backend.services.drainage_blockage_service import drainage_blockage_service

client = TestClient(app)


def test_get_supported_cities():
    """Verify city registry, geographic coverage, and data limitation disclaimers."""
    response = client.get("/api/v1/blockage/cities")
    assert response.status_code == 200
    cities = response.json()
    assert len(cities) >= 4

    city_map = {c["city_id"]: c for c in cities}
    assert "indore" in city_map
    assert "eastbourne" in city_map
    assert "pune" in city_map
    assert "bellinge" in city_map

    # Verify Indore has full coverage
    indore = city_map["indore"]
    assert indore["has_drainage_network"] is True
    assert indore["has_blockage_evidence"] is True
    assert "Copernicus DEM GLO-30" in indore["elevation_source"]

    # Verify Pune has strict zero-fabrication disclaimer
    pune = city_map["pune"]
    assert pune["has_drainage_network"] is False
    assert pune["has_blockage_evidence"] is False
    assert "Strict Scientific Integrity" in pune["data_limitations"]
    assert "no simulated or fake blockage markers are created" in pune["data_limitations"]


def test_get_indore_drainage_segments():
    """Verify Indore drainage network segments, Copernicus DEM elevation, and coordinates."""
    response = client.get("/api/v1/blockage/segments?city_id=indore")
    assert response.status_code == 200
    segments = response.json()
    assert len(segments) == 9

    # Verify all expected codes are present
    codes = [s["segment_code"] for s in segments]
    for c in ["DS-01", "DS-02", "DS-03", "DS-04", "DS-05", "DS-06", "DS-07", "DS-08", "DS-09"]:
        assert c in codes

    # Verify real coordinates and positive elevations (>500m MSL for Indore)
    for s in segments:
        assert 22.60 <= s["start_lat"] <= 22.85
        assert 75.75 <= s["start_lon"] <= 75.95
        assert s["elevation_m"] >= 500.0, f"Elevation for {s['segment_code']} should be >500m"
        assert len(s["coordinates"]) >= 2


def test_blockage_status_categories_and_evidence():
    """Verify RED (Confirmed), ORANGE (Suspected), GREEN (Normal), and GREY (Insufficient Data)."""
    response = client.get("/api/v1/blockage/segments?city_id=indore")
    assert response.status_code == 200
    segments = response.json()

    status_map = {s["segment_code"]: s for s in segments}

    # DS-05 (Pardeshipura) & DS-08 (Mhow Naka) must be CONFIRMED_BLOCKAGE (RED)
    assert status_map["DS-05"]["status"] == "CONFIRMED_BLOCKAGE"
    assert status_map["DS-05"]["risk_level"] == "CRITICAL"
    assert status_map["DS-05"]["debris_coverage_pct"] >= 65.0
    assert status_map["DS-05"]["silt_depth_cm"] >= 70.0

    assert status_map["DS-08"]["status"] == "CONFIRMED_BLOCKAGE"
    assert status_map["DS-08"]["risk_level"] == "CRITICAL"

    # DS-03 (Rambagh) & DS-06 (Vijay Nagar) must be SUSPECTED_BLOCKAGE (ORANGE)
    assert status_map["DS-03"]["status"] == "SUSPECTED_BLOCKAGE"
    assert status_map["DS-03"]["risk_level"] == "WARNING"

    assert status_map["DS-06"]["status"] == "SUSPECTED_BLOCKAGE"
    assert status_map["DS-06"]["risk_level"] == "WARNING"

    # DS-01 (Rau) & DS-04 (Rajwada) must be NORMAL_MONITORED (GREEN)
    assert status_map["DS-01"]["status"] == "NORMAL_MONITORED"
    assert status_map["DS-01"]["risk_level"] == "LOW"

    # DS-09 (Scheme 54 lateral) must be INSUFFICIENT_DATA (GREY)
    assert status_map["DS-09"]["status"] == "INSUFFICIENT_DATA"
    assert status_map["DS-09"]["risk_level"] == "UNKNOWN"


def test_status_filter_parameter():
    """Verify API filtering by status."""
    # Filter RED confirmed
    r_red = client.get("/api/v1/blockage/segments?city_id=indore&status=CONFIRMED_BLOCKAGE")
    assert r_red.status_code == 200
    red_segs = r_red.json()
    assert len(red_segs) == 2
    for s in red_segs:
        assert s["status"] == "CONFIRMED_BLOCKAGE"

    # Filter ORANGE suspected
    r_orange = client.get("/api/v1/blockage/segments?city_id=indore&status=SUSPECTED_BLOCKAGE")
    assert r_orange.status_code == 200
    orange_segs = r_orange.json()
    assert len(orange_segs) == 2
    for s in orange_segs:
        assert s["status"] == "SUSPECTED_BLOCKAGE"

    # Filter GREEN normal
    r_green = client.get("/api/v1/blockage/segments?city_id=indore&status=NORMAL_MONITORED")
    assert r_green.status_code == 200
    green_segs = r_green.json()
    assert len(green_segs) == 4

    # Filter GREY insufficient
    r_grey = client.get("/api/v1/blockage/segments?city_id=indore&status=INSUFFICIENT_DATA")
    assert r_grey.status_code == 200
    grey_segs = r_grey.json()
    assert len(grey_segs) == 1


def test_segment_detail_and_image_evidence():
    """Verify segment detail endpoint with attached OpenCV photographic inspection records."""
    response = client.get("/api/v1/blockage/segments/SEG_IND_05")
    assert response.status_code == 200
    data = response.json()
    assert data["segment_code"] == "DS-05"
    assert data["name"] == "Pardeshipura Industrial Drain & Culvert"
    assert data["has_image"] is True
    assert len(data["images"]) >= 1

    img = data["images"][0]
    assert img["image_path"].startswith("/samples/images/")
    assert img["opencv_analyzed"] == 1
    assert img["is_blockage_evidence"] == 1
    assert data["debris_coverage_pct"] >= 65.0
    assert data["silt_depth_cm"] >= 70.0


def test_segment_without_image_evidence():
    """Verify unmonitored segment returns honest no-image notice without fake photos."""
    response = client.get("/api/v1/blockage/segments/SEG_IND_09")
    assert response.status_code == 200
    data = response.json()
    assert data["segment_code"] == "DS-09"
    assert data["has_image"] is False
    assert len(data["images"]) == 0

    img_res = client.get("/api/v1/blockage/segments/SEG_IND_09/images")
    assert img_res.status_code == 200
    assert img_res.json()["disclaimer"] == "No drainage inspection image available."


def test_pune_scientific_zero_fabrication():
    """Verify Pune CWPRS dataset returns 0 drainage segments and no fake blockage markers."""
    response = client.get("/api/v1/blockage/segments?city_id=pune")
    assert response.status_code == 200
    segments = response.json()
    assert len(segments) == 0

    summary_res = client.get("/api/v1/blockage/summary?city_id=pune")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_segments"] == 0
    assert summary["confirmed_blockages_red"] == 0
    assert summary["suspected_hotspots_orange"] == 0
    assert summary["has_drainage_network"] is False
    assert "Strict Scientific Integrity" in summary["data_limitations"]


def test_individual_report_pdf_generation():
    """Verify ReportLab generation of official individual drainage blockage PDF."""
    response = client.get("/api/v1/blockage/reports/individual/SEG_IND_05/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-"), "Generated file must have valid PDF header"
    assert len(response.content) > 50000, "PDF with embedded image must be substantial in size"


def test_city_report_pdf_generation():
    """Verify ReportLab generation of official city-wide drainage blockage PDF."""
    response = client.get("/api/v1/blockage/reports/city/indore/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 4000


def test_city_report_csv_export():
    """Verify tabular CSV export with all required headers and accurate row values."""
    response = client.get("/api/v1/blockage/reports/city/indore/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=" in response.headers["content-disposition"]

    csv_text = response.text
    lines = csv_text.strip().split("\n")
    assert len(lines) >= 10  # Header + 9 segments
    header = lines[0]
    assert "segment_code" in header
    assert "debris_coverage_pct" in header
    assert "silt_depth_cm" in header
    assert "elevation_m_msl" in header
    assert "DS-05" in csv_text
    assert "CONFIRMED_BLOCKAGE" in csv_text


def test_invalid_segment_returns_404():
    """Verify 404 response for nonexistent drainage segment."""
    response = client.get("/api/v1/blockage/segments/SEG_NONEXISTENT_999")
    assert response.status_code == 404

    pdf_res = client.get("/api/v1/blockage/reports/individual/SEG_NONEXISTENT_999/pdf")
    assert pdf_res.status_code == 404


def test_database_stats_reports_healthy_counts():
    """Verify SQLite database manager includes new drainage and blockage tables in stats."""
    stats = db_manager.get_db_stats()
    assert stats["status"] == "HEALTHY"
    assert stats["total_drainage_segments"] >= 9
    assert stats["total_blockage_observations"] >= 9


def test_existing_system_endpoints_preserved():
    """Ensure no regression in existing core system endpoints."""
    # Health check
    r_health = client.get("/health")
    assert r_health.status_code == 200

    # Environmental summary
    r_env = client.get("/api/v1/flood/environmental-summary")
    assert r_env.status_code == 200

    # Topology
    r_topo = client.get("/api/v1/flood/topology")
    assert r_topo.status_code == 200

    # Reports
    r_rep = client.get("/api/v1/reports/summary")
    assert r_rep.status_code == 200
