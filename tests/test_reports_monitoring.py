"""
Focused Test Suite for Phase 2B Reports & Monitoring Endpoints.
Validates:
1. GET /api/v1/reports/summary (8 summary cards, weather header).
2. GET /api/v1/reports/stations (7 station records, filters, search, pagination).
3. GET /api/v1/reports/stations/{node_id} (detail record for modal).
4. GET /api/v1/reports/filtration-units (3 filtration facilities).
5. GET /api/v1/reports/areas (4 monitored areas).
6. GET /api/v1/reports/export/csv (CSV download).
7. GET /api/v1/reports/stations/{node_id}/pdf (ReportLab PDF generation).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_reports_summary_endpoint():
    """Verify summary metrics endpoint returns correct 8 metric structure."""
    response = client.get("/api/v1/reports/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "metrics" in data
    m = data["metrics"]
    assert m["total_stations"] == 7
    assert m["filtration_facilities"] == 3
    assert m["monitored_areas"] == 4
    assert "pass_count" in m
    assert "hold_count" in m
    assert "fail_count" in m
    assert "simulated_blocked_routes" in m
    assert "active_alerts" in m
    assert "weather_header" in data
    print(f"\n[PASS] Summary metrics verified: {m['total_stations']} stations, {m['filtration_facilities']} facilities, {m['monitored_areas']} areas.")


def test_stations_report_endpoint_and_filters():
    """Verify station list returns 7 stations with N/A for pH & TDS and optical turbidity."""
    response = client.get("/api/v1/reports/stations")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_count"] == 7
    stations = data["stations"]
    assert len(stations) == 7

    # Check first station fields
    s0 = stations[0]
    assert "display_code" in s0
    assert "station_name" in s0
    assert "zone" in s0
    assert "quality_status" in s0
    assert s0["quality_status"] in ("PASS", "HOLD", "FAIL")

    # Check strict provenance of pH & TDS
    assert s0["ph_measurement"]["display"] == "N/A"
    assert s0["tds_measurement"]["display"] == "N/A"
    assert s0["turbidity_measurement"]["is_optical_estimate"] is True
    
    # Verify s0 (NODE_RAU - natural open headwaters canal) has NOT CONFIGURED gate status per contract
    assert s0["sluice_gate_action"] == "NOT CONFIGURED"
    assert s0["outlet_status"] == "NOT CONFIGURED"
    assert s0["outlet_code"] == "NOT_CONFIGURED"
    assert s0["outlet_is_simulated"] is False

    # Verify all 7 stations adhere to the drain-wise gate status contract
    valid_outlet_codes = {"OPEN", "CLOSED", "PARTIALLY_OPEN", "BLOCKED", "NOT_CONFIGURED", "UNKNOWN"}
    for stn in stations:
        assert stn["outlet_code"] in valid_outlet_codes
        assert "outlet_status" in stn
        assert "sluice_gate_action" in stn
        if stn.get("outlet_is_simulated"):
            assert "SIMULATED" in stn["outlet_status"]
            assert "SIMULATED" in stn["sluice_gate_action"]

    # Test filtering by quality_status
    res_pass = client.get("/api/v1/reports/stations?quality_status=PASS")
    assert res_pass.status_code == 200
    d_pass = res_pass.json()
    for s in d_pass["stations"]:
        assert s["quality_status"] == "PASS"

    # Test search
    res_search = client.get("/api/v1/reports/stations?search=Rajwada")
    assert res_search.status_code == 200
    d_search = res_search.json()
    assert d_search["total_count"] >= 1
    assert any("Rajwada" in s["station_name"] for s in d_search["stations"])

    print(f"\n[PASS] Station reports verified: 7 stations, pH/TDS=N/A, optical turbidity, working filters.")


def test_station_detail_endpoint():
    """Verify single station detail modal endpoint."""
    response = client.get("/api/v1/reports/stations/NODE_RAJWADA")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "station" in data
    stn = data["station"]
    assert stn["node_id"] in ("NODE_RAJWADA", "NODE_RAJWARA")
    assert "Rajwada" in stn["station_name"]
    assert stn["elevation_msl_m"] == 540.0
    print(f"\n[PASS] Station detail verified for NODE_RAJWADA ({stn['station_name']}).")


def test_filtration_units_endpoint():
    """Verify 3 filtration and treatment facilities."""
    response = client.get("/api/v1/reports/filtration-units")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 3
    assert len(data["facilities"]) == 3
    names = [f["name"] for f in data["facilities"]]
    assert any("Kabithedi" in n for n in names)
    assert any("Bilawali" in n for n in names)
    assert any("Krishnapura" in n for n in names)
    print(f"\n[PASS] Filtration facilities verified: {names}.")


def test_monitored_areas_endpoint():
    """Verify 4 monitored hydrological catchment areas."""
    response = client.get("/api/v1/reports/areas")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 4
    assert len(data["areas"]) == 4
    names = [a["name"] for a in data["areas"]]
    assert any("Saraswati" in n for n in names)
    assert any("Confluence" in n for n in names)
    print(f"\n[PASS] Monitored areas verified: {names}.")


def test_csv_export_endpoint():
    """Verify CSV export endpoint streams valid CSV file."""
    response = client.get("/api/v1/reports/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    text = response.text
    assert "Station_ID" in text
    assert "Purity_Score_pct" in text
    assert "NODE_RAJWARA" in text or "NODE_RAJWADA" in text
    assert "N/A" in text  # for pH/TDS
    print(f"\n[PASS] CSV export verified ({len(text)} bytes).")


def test_pdf_export_endpoint():
    """Verify ReportLab PDF generation for single station and batch."""
    response = client.get("/api/v1/reports/stations/NODE_RAJWADA/pdf")
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    pdf_bytes = response.content
    assert pdf_bytes.startswith(b"%PDF"), "Response is not a valid PDF file"
    assert len(pdf_bytes) > 2000, "PDF size is unexpectedly small"
    print(f"\n[PASS] PDF generation verified for NODE_RAJWADA ({len(pdf_bytes)} bytes).")

    # Batch PDF
    res_batch = client.get("/api/v1/reports/export-all-pdf")
    assert res_batch.status_code == 200
    assert res_batch.content.startswith(b"%PDF")
    print(f"\n[PASS] Batch PDF generation verified ({len(res_batch.content)} bytes).")


if __name__ == "__main__":
    test_reports_summary_endpoint()
    test_stations_report_endpoint_and_filters()
    test_station_detail_endpoint()
    test_filtration_units_endpoint()
    test_monitored_areas_endpoint()
    test_csv_export_endpoint()
    test_pdf_export_endpoint()
    print("\nALL REPORTS & MONITORING BACKEND TESTS PASSED SUCCESSFULLY!")
