"""
AQUAGUARD AI: Drainage Blockage Intelligence API Routes.
Exposes endpoints for topographical drainage mapping, blockage observations,
OpenCV visual evidence screening, and downloadable PDF/CSV reports.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from backend.services.drainage_blockage_service import drainage_blockage_service

blockage_router = APIRouter(prefix="/api/v1/blockage", tags=["Drainage Blockage Intelligence"])


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================

class CityMetadataResponse(BaseModel):
    city_id: str
    name: str
    governing_body: str
    has_drainage_network: bool
    has_blockage_evidence: bool
    has_elevation_context: bool
    elevation_source: str
    elevation_gradient_m: str
    monitored_segments_count: int
    blockage_status_summary: str
    rainfall_source: str
    image_evidence_available: bool
    data_limitations: str


class DrainageSegmentSummary(BaseModel):
    id: str
    city_id: str
    segment_code: str
    name: str
    source_node: Optional[str]
    target_node: Optional[str]
    channel_type: Optional[str]
    coordinates: List[List[float]]
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    mid_lat: float
    mid_lon: float
    elevation_m: float
    length_m: float
    slope: float
    manning_velocity_m_s: float
    max_capacity_m3_s: float
    status: str
    risk_level: str
    confidence_score: float
    debris_coverage_pct: float
    silt_depth_cm: float
    flow_velocity_pct: float
    water_level_pct: float
    evidence_summary: str
    evidence_type: str
    observation_date: str
    action_recommended: str
    data_source: str


class CityBlockageSummaryResponse(BaseModel):
    city_id: str
    city_name: str
    total_segments: int
    confirmed_blockages_red: int
    suspected_hotspots_orange: int
    normal_monitored_green: int
    insufficient_data_grey: int
    average_silt_depth_cm: float
    critical_segments_count: int
    critical_segment_codes: List[str]
    has_drainage_network: bool
    has_blockage_evidence: bool
    data_limitations: str
    generated_at: str


# =============================================================================
# API ENDPOINTS
# =============================================================================

@blockage_router.get(
    "/cities",
    response_model=List[CityMetadataResponse],
    summary="Get Available Cities & Geographical Coverage",
    description="Returns geographical areas supported by project datasets with explicit coverage limitations and scientific integrity declarations.",
)
def get_supported_cities():
    """Retrieve supported cities and metadata."""
    return drainage_blockage_service.get_cities()


@blockage_router.get(
    "/segments",
    response_model=List[DrainageSegmentSummary],
    summary="Get Drainage Segments & Blockage Observations",
    description="Retrieve mapped drainage segments filtered by city, blockage status (CONFIRMED_BLOCKAGE, SUSPECTED_BLOCKAGE, NORMAL_MONITORED, INSUFFICIENT_DATA), or risk level.",
)
def get_drainage_segments(
    city_id: str = Query("indore", description="Target city identifier (indore, eastbourne, pune, bellinge)"),
    status: str = Query("ALL", description="Filter by status (CONFIRMED_BLOCKAGE, SUSPECTED_BLOCKAGE, NORMAL_MONITORED, INSUFFICIENT_DATA, or ALL)"),
    risk: str = Query("ALL", description="Filter by risk level (CRITICAL, WARNING, LOW, UNKNOWN, or ALL)"),
):
    """Retrieve filtered drainage segments."""
    return drainage_blockage_service.get_drainage_segments(city_id=city_id, status=status, risk=risk)


@blockage_router.get(
    "/segments/{segment_id}",
    summary="Get Drainage Segment Details",
    description="Retrieve complete topographical geometry, DEM elevation, observation history, and image evidence for a specific drainage segment.",
)
def get_drainage_segment_detail(segment_id: str):
    """Retrieve full details of an individual drainage segment."""
    segment = drainage_blockage_service.get_drainage_segment_detail(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail=f"Drainage segment '{segment_id}' not found.")
    return segment


@blockage_router.get(
    "/segments/{segment_id}/images",
    summary="Get Drainage Image Evidence",
    description="Retrieve all photographic inspection frames, OpenCV debris analyses, and colorimetric clarity metrics attached to a drainage segment.",
)
def get_drainage_images(segment_id: str):
    """Retrieve attached image evidence records for a segment."""
    segment = drainage_blockage_service.get_drainage_segment_detail(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail=f"Drainage segment '{segment_id}' not found.")

    images = segment.get("images", [])
    return {
        "segment_id": segment_id,
        "segment_code": segment["segment_code"],
        "name": segment["name"],
        "has_images": len(images) > 0,
        "image_count": len(images),
        "disclaimer": "No drainage inspection image available." if not images else "Inspection photographic evidence verified.",
        "images": images,
    }


@blockage_router.get(
    "/summary",
    response_model=CityBlockageSummaryResponse,
    summary="Get City-Wide Blockage Scorecard",
    description="High-level statistical summary of confirmed blockages (RED), suspected hotspots (ORANGE), normal monitored drains (GREEN), and insufficient data segments (GREY).",
)
def get_city_summary(
    city_id: str = Query("indore", description="Target city identifier (indore, eastbourne, pune, bellinge)")
):
    """Retrieve statistical blockage scorecard for a city."""
    return drainage_blockage_service.get_city_summary(city_id=city_id)


@blockage_router.get(
    "/reports/individual/{segment_id}/pdf",
    summary="Download Individual Drainage Blockage Report (PDF)",
    description="Generate and stream an official, high-resolution ReportLab PDF certificate for an individual drainage segment.",
)
def download_individual_pdf(segment_id: str):
    """Stream individual drainage blockage report as PDF."""
    try:
        pdf_bytes, filename = drainage_blockage_service.generate_individual_report_pdf(segment_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate drainage PDF report: {e}")


@blockage_router.get(
    "/reports/city/{city_id}/pdf",
    summary="Download City-Wide Blockage Report (PDF)",
    description="Generate and stream an official city-wide drainage blockage & topographical audit ReportLab PDF.",
)
def download_city_pdf(city_id: str):
    """Stream city-wide drainage blockage report as PDF."""
    try:
        pdf_bytes, filename = drainage_blockage_service.generate_city_report_pdf(city_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate city blockage PDF report: {e}")


@blockage_router.get(
    "/reports/city/{city_id}/csv",
    summary="Export Drainage Blockage Data (CSV)",
    description="Export tabular drainage network, topographical elevation, and blockage diagnostic data as a standard downloadable CSV file.",
)
def download_city_csv(city_id: str):
    """Stream tabular drainage dataset as CSV."""
    try:
        csv_str, filename = drainage_blockage_service.generate_city_report_csv(city_id)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export drainage CSV: {e}")

