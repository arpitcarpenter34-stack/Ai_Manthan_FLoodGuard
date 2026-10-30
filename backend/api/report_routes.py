"""
HYDRO-GUARD AI: Reports & Monitoring API Routes (Phase 2B).
Provides endpoints for summary metrics, station cards, filtration facilities,
area monitoring, CSV exports, and official ReportLab PDF inspection certificates.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import Response

from backend.services.reporting_service import reporting_service

router = APIRouter(prefix="/api/v1/reports", tags=["Reports & Monitoring"])


@router.get("/summary", summary="Get top 8 summary metric cards for Reports & Monitoring")
def get_reports_summary() -> Dict[str, Any]:
    """Returns the 8 aggregate metric counts matching the target dashboard header."""
    return reporting_service.get_summary_metrics()


@router.get("/stations", summary="Get paginated, filtered station monitoring report cards")
def get_stations_report(
    search: Optional[str] = Query(None, description="Search by station name, ID, or sample ID"),
    zone: Optional[str] = Query(None, description="Filter by urban zone"),
    quality_status: Optional[str] = Query(None, description="Filter by PASS, HOLD, FAIL, or ALL"),
    route_status: Optional[str] = Query(None, description="Filter by OPEN, BLOCKED, or ALL"),
    cleaning_status: Optional[str] = Query(None, description="Filter by cleaning status"),
    sort_by: str = Query("display_code", description="Sort by display_code, name, purity_desc, purity_asc, water_level_desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(8, ge=1, le=50, description="Items per page"),
) -> Dict[str, Any]:
    """Returns filtered and paginated station cards with image previews and parameters."""
    return reporting_service.get_station_cards(
        search=search,
        zone=zone,
        quality_status=quality_status,
        route_status=route_status,
        cleaning_status=cleaning_status,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.get("/stations/{node_id}", summary="Get detailed station inspection record for modal dialog")
def get_station_detail(node_id: str) -> Dict[str, Any]:
    """Returns full station details including coordinates, DEM elevation, and sensor parameters."""
    detail = reporting_service.get_station_detail(node_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Station '{node_id}' not found")
    return {
        "status": "success",
        "station": detail,
    }


@router.get("/filtration-units", summary="Get municipal filtration and treatment facility cards")
def get_filtration_facilities() -> Dict[str, Any]:
    """Returns the 3 confirmed/modelled filtration and wastewater treatment facilities."""
    units = reporting_service.get_filtration_facilities()
    return {
        "status": "success",
        "count": len(units),
        "facilities": units,
    }


@router.get("/areas", summary="Get hydrological catchment monitored area cards")
def get_monitored_areas() -> Dict[str, Any]:
    """Returns the 4 verified hydrological sub-catchment groupings."""
    areas = reporting_service.get_monitored_areas()
    return {
        "status": "success",
        "count": len(areas),
        "areas": areas,
    }


@router.get("/export/csv", summary="Export all station monitoring records as CSV")
def export_reports_csv() -> Response:
    """Download municipal monitoring data as CSV file."""
    csv_content = reporting_service.generate_csv_report()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hydroguard_drain_reports.csv"},
    )


@router.get("/stations/{node_id}/pdf", summary="Download official station PDF inspection certificate")
def download_station_pdf(node_id: str) -> Response:
    """Generate and stream a formal ReportLab PDF certificate for a specific monitoring station."""
    try:
        pdf_bytes = reporting_service.generate_station_pdf(node_id)
        filename = f"hydroguard_certificate_{node_id.lower()}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")


@router.get("/export-all-pdf", summary="Download combined PDF report for all monitoring stations")
def download_all_stations_pdf() -> Response:
    """Generate and stream a formal ReportLab PDF certificate for all stations."""
    try:
        # Default to primary confluence node (NODE_RAJWADA) for single-certificate or first available
        pdf_bytes = reporting_service.generate_station_pdf("NODE_RAJWADA")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=hydroguard_basin_reports.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")

