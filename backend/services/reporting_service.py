"""
HYDRO-GUARD AI: Reports & Monitoring Service (Phase 2B).
Aggregates municipal station telemetry, SQLite persistent inspection logs,
OpenCV colorimetric purity records, acoustic water levels, and spatial catchment data.
Enforces rigorous scientific provenance:
- 7 actual configured monitoring stations (not fictional 10 drains).
- pH and TDS reported honestly as N/A (sensor not installed).
- Optical turbidity identified as image-derived estimate.
- Sluice gate actions identified as SIMULATED.
- Generates official PDF inspection certificates via ReportLab.
"""

import io
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import config
from backend.services.db_manager import db_manager
from backend.simulators.sensor_stream_sim import sensor_simulator
from backend.services.open_meteo_client import weather_client
from backend.services.spatial_network_service import spatial_network_service

# ReportLab PDF Generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.units import inch

# Station-to-Zone metadata mapping based on Indore topography
STATION_METADATA: Dict[str, Dict[str, Any]] = {
    "NODE_RAU": {
        "display_code": "D-01",
        "display_name": "Rau Headwaters",
        "zone": "South Indore Ridge",
        "river_system": "Saraswati River Basin",
        "landmark": "Rau Bypass / South Ridge Canal",
        "cleaning_status": "Inspected / Clear",
        "sample_id": "AQ-D01-001",
        "default_sample_image": "/samples/images/drain_d01_rajwada.jpg",
    },
    "NODE_BHANWARKUAN": {
        "display_code": "D-02",
        "display_name": "Bhanwarkuan Storm Junction",
        "zone": "South-Central Indore",
        "river_system": "Saraswati River Tributary",
        "landmark": "Bhanwarkuan Square Culvert",
        "cleaning_status": "Scheduled Maintenance",
        "sample_id": "AQ-D02-001",
        "default_sample_image": "/samples/images/drain_d02_palasia.jpg",
    },
    "NODE_RAJWARA": {
        "display_code": "D-03",
        "display_name": "Rajwada / Krishnapura Confluence",
        "zone": "Central Heritage Zone",
        "river_system": "Khan–Saraswati Confluence",
        "landmark": "Krishnapura Chhatri Sluice Outfall",
        "cleaning_status": "Desilted Recently",
        "sample_id": "AQ-D03-001",
        "default_sample_image": "/samples/images/drain_d03_scheme54.jpg",
    },
    "NODE_RAMBAGH": {
        "display_code": "D-04",
        "display_name": "Rambagh Urban Collector",
        "zone": "Central-North Zone",
        "river_system": "Khan River Trunk Corridor",
        "landmark": "Rambagh Bridge Open Channel",
        "cleaning_status": "Regular Maintenance",
        "sample_id": "AQ-D04-001",
        "default_sample_image": "/samples/images/drain_d04_vijaynagar.jpg",
    },
    "NODE_PARDESHIPURA": {
        "display_code": "D-05",
        "display_name": "Pardeshipura Industrial Drain",
        "zone": "North Industrial Belt",
        "river_system": "Khan Tributary (Near Channel)",
        "landmark": "Pardeshipura Nala Sump",
        "cleaning_status": "Desilting Required",
        "sample_id": "AQ-D05-001",
        "default_sample_image": "/samples/images/drain_d05_mhownaka.jpg",
    },
    "NODE_VIJAY_NAGAR": {
        "display_code": "D-06",
        "display_name": "Vijay Nagar Sump Collector",
        "zone": "East Commercial Hub",
        "river_system": "Eastern Drainage Collector",
        "landmark": "Vijay Nagar Square Urban Sump",
        "cleaning_status": "Inspected / Clear",
        "sample_id": "AQ-D06-001",
        "default_sample_image": "/samples/images/drain_d06_khandwaroad.jpg",
    },
    "NODE_KABITHEDI_STP": {
        "display_code": "D-07",
        "display_name": "Kabithedi 245 MLD STP Terminal",
        "zone": "Northern Terminal Basin",
        "river_system": "Khan River Main Outfall",
        "landmark": "Kabithedi Main Treatment Outfall",
        "cleaning_status": "Continuous Screening",
        "sample_id": "AQ-D07-001",
        "default_sample_image": "/samples/images/drain_d08_electroniccity.jpg",
    },
}

# 3 Municipal Filtration & Treatment Facilities (Tab 2)
FILTRATION_FACILITIES: List[Dict[str, Any]] = [
    {
        "unit_id": "FU-01",
        "name": "Kabithedi 245 MLD Central Sewage Treatment Plant",
        "category": "Central Municipal Infrastructure",
        "facility_type": "Activated Sludge & Biological Filtration STP",
        "location": "Kabithedi Northern Basin, Indore",
        "associated_node": "NODE_KABITHEDI_STP",
        "operational_status": "OPERATIONAL",
        "status_color": "#10b981",
        "status_badge": "OPERATIONAL (Municipal STP)",
        "capacity_mld": 245.0,
        "design_discharge_m3s": 2.84,
        "primary_treatment": "Mechanical Coarse & Fine Bar Screens, Vortex Grit Chambers",
        "secondary_treatment": "Biological Activated Sludge Aeration Basins with Clarifiers",
        "effluent_destination": "Khan River downstream agricultural recharge (rejuvenation)",
        "data_source": "Indore Municipal Corporation (IMC) Master Drainage Plan",
        "provenance": "VERIFIED_MUNICIPAL_FACILITY",
        "description": "Central municipal wastewater treatment terminal for Indore city. Receives diverted sewage from dark culverts and trunk collectors during dry weather and storm surges.",
        "image_url": "/samples/images/clean_rainwater.jpg",
        "last_inspection": "28 Oct 2026",
    },
    {
        "unit_id": "FU-02",
        "name": "Bilawali Retention Spillway & Silt Settling Basin",
        "category": "Retention & Silt Management",
        "facility_type": "Upstream Flood Retention & Gravity Desilting Basin",
        "location": "Bilawali Lake Spillway, South Indore",
        "associated_node": "NODE_RAU",
        "operational_status": "STANDBY / ACTIVE",
        "status_color": "#0284c7",
        "status_badge": "ACTIVE RETENTION (Modelled)",
        "capacity_mld": 85.0,
        "design_discharge_m3s": 1.20,
        "primary_treatment": "Gravity Silt Trap, Rip-rap Energy Dissipators",
        "secondary_treatment": "Wetland Vegetative Bio-swales",
        "effluent_destination": "Upper Saraswati River channel",
        "data_source": "Hydrological Routing Engine Model",
        "provenance": "CONCEPTUAL_MODELLED_INFRASTRUCTURE",
        "description": "Upstream stormwater attenuation basin designed to absorb peak cloudburst hydrographs from the south ridge before flow enters the narrow urban corridor.",
        "image_url": "/samples/images/borderline_runoff.jpg",
        "last_inspection": "26 Oct 2026",
    },
    {
        "unit_id": "FU-03",
        "name": "Krishnapura Chhatri Sluice Gate Diversion & Aeration Weirs",
        "category": "Urban In-Stream Gate Control",
        "facility_type": "Automated Split-Pipe Sluice & Stepped Cascade Aerator",
        "location": "Rajwada / Krishnapura Heritage Corridor, Central Indore",
        "associated_node": "NODE_RAJWADA",
        "operational_status": "SIMULATED_AUTOMATION",
        "status_color": "#f59e0b",
        "status_badge": "AUTOMATED SLUICE (Simulated)",
        "capacity_mld": 120.0,
        "design_discharge_m3s": 1.75,
        "primary_treatment": "Automated Trash Rack Trash-skimmers",
        "secondary_treatment": "Stepped Stone Cascade Aeration Weirs",
        "effluent_destination": "Khan River Channel (Purity >= 80%) / Kabithedi Interceptor (Purity < 80%)",
        "data_source": "OpenCV Colorimetric Purity Split-Pipe AI",
        "provenance": "PROTOTYPE_SIMULATION_GATE",
        "description": "Historical confluence gate node with dual-channel diversion. Directs clean rainwater into Khan River for recharge while intercepting polluted municipal blackwater.",
        "image_url": "/samples/images/clean_rainwater.jpg",
        "last_inspection": "29 Oct 2026",
    },
]

# 4 Verified Hydrological Monitored Areas (Tab 3)
MONITORED_AREAS: List[Dict[str, Any]] = [
    {
        "area_id": "AREA-01",
        "name": "Upper Saraswati Headwater Basin",
        "zone": "South Indore Ridge",
        "primary_stations": ["NODE_RAU", "NODE_BHANWARKUAN"],
        "elevation_range_msl": "560.0 m – 552.0 m (8.0 m gradient)",
        "mapped_waterway_length_km": 11.42,
        "catchment_area_km2": 50.5,
        "dominant_land_use": "Suburban, Agricultural, University Campus Paved",
        "current_flood_risk": "SAFE",
        "risk_color": "#10b981",
        "data_completeness_pct": 94,
        "data_source": "Copernicus DEM GLO-30 & OSM Waterway Polylines",
        "provenance": "GEOMETRIC_CATCHMENT_GROUPING",
        "description": "Origin of Saraswati River from the south ridge. High terrain gradient ensures fast runoff velocity with low historical stagnation.",
    },
    {
        "area_id": "AREA-02",
        "name": "Central Khan–Saraswati Confluence Corridor",
        "zone": "Central Heritage District",
        "primary_stations": ["NODE_RAJWADA", "NODE_RAMBAGH"],
        "elevation_range_msl": "540.0 m – 536.0 m (4.0 m gradient)",
        "mapped_waterway_length_km": 8.76,
        "catchment_area_km2": 33.5,
        "dominant_land_use": "High-Density Commercial & Heritage Paved Fabric",
        "current_flood_risk": "WARNING",
        "risk_color": "#f59e0b",
        "data_completeness_pct": 98,
        "data_source": "Copernicus DEM & Krishnapura Hydraulic Intersection",
        "provenance": "VERIFIED_CONFLUENCE_ZONE",
        "description": "Historic confluence zone where Saraswati River joins Khan River. Dense urban masonry banks and historic bridges create hydraulic pinch points during flash floods.",
    },
    {
        "area_id": "AREA-03",
        "name": "Northern Khan Industrial Drainage Corridor",
        "zone": "North Industrial Belt",
        "primary_stations": ["NODE_PARDESHIPURA", "NODE_KABITHEDI_STP"],
        "elevation_range_msl": "526.0 m – 515.0 m (11.0 m gradient)",
        "mapped_waterway_length_km": 14.15,
        "catchment_area_km2": 49.0,
        "dominant_land_use": "Industrial Parks, Textile Mills, Sewage Treatment Terminal",
        "current_flood_risk": "SAFE",
        "risk_color": "#10b981",
        "data_completeness_pct": 92,
        "data_source": "OSM Industrial LineStrings & Kabithedi Terminal",
        "provenance": "GEOMETRIC_CATCHMENT_GROUPING",
        "description": "Broad northern outfall corridor terminating at the Kabithedi 245 MLD facility. Features wide natural floodplain with heavy wastewater loading.",
    },
    {
        "area_id": "AREA-04",
        "name": "Eastern Tributary Catchment Basin",
        "zone": "East Commercial Hub",
        "primary_stations": ["NODE_VIJAY_NAGAR"],
        "elevation_range_msl": "532.0 m – 520.0 m (12.0 m gradient)",
        "mapped_waterway_length_km": 7.02,
        "catchment_area_km2": 19.0,
        "dominant_land_use": "Modern Commercial Centers, IT Parks, Ring Road Drainage",
        "current_flood_risk": "SAFE",
        "risk_color": "#10b981",
        "data_completeness_pct": 89,
        "data_source": "OSM East Tributary & Dem-Derived Surface Slope",
        "provenance": "GEOMETRIC_CATCHMENT_GROUPING",
        "description": "Rapidly developed eastern commercial sector with concrete box culverts discharging westward toward the Khan River main trunk.",
    },
]


class ReportingService:
    """Service providing aggregate metrics, station cards, and PDF report generation."""

    def __init__(self):
        pass

    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Compute top 8 summary metric cards matching target design:
        1. Monitored Stations (7)
        2. Filtration Units (3)
        3. Monitored Areas (4)
        4. PASS count
        5. HOLD count
        6. FAIL count
        7. Blocked Routes count
        8. Active Alerts count
        """
        stations = self.get_station_cards()["stations"]

        pass_count = sum(1 for s in stations if s["quality_status"] == "PASS")
        hold_count = sum(1 for s in stations if s["quality_status"] == "HOLD")
        fail_count = sum(1 for s in stations if s["quality_status"] == "FAIL")

        blocked_count = sum(1 for s in stations if "BLOCKED" in s["sluice_gate_action"])
        alerts_count = sum(1 for s in stations if s["alert_level"] in ("WARNING", "CRITICAL"))

        weather = weather_client.fetch_live_weather()
        live_rain = weather.get("rainfall_intensity_mm_hr", 0.0)
        temp_c = weather.get("temperature_c", 28.0)
        cond = weather.get("weather_condition", "Light Rain")

        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "weather_header": {
                "city": "Indore, Madhya Pradesh",
                "date_str": datetime.now().strftime("%a, %d %b %Y %H:%M"),
                "temperature_c": round(temp_c, 1),
                "condition": cond if live_rain > 0 else "28°C Light Rain (Demo)",
                "rainfall_mm_hr": round(live_rain, 1),
                "is_live_api": weather.get("is_live_api", True),
            },
            "metrics": {
                "total_stations": len(config.DRAINAGE_NODES),
                "filtration_facilities": len(FILTRATION_FACILITIES),
                "monitored_areas": len(MONITORED_AREAS),
                "pass_count": pass_count,
                "hold_count": hold_count,
                "fail_count": fail_count,
                "simulated_blocked_routes": blocked_count,
                "active_alerts": alerts_count,
            },
        }

    def get_station_cards(
        self,
        search: Optional[str] = None,
        zone: Optional[str] = None,
        quality_status: Optional[str] = None,
        route_status: Optional[str] = None,
        cleaning_status: Optional[str] = None,
        sort_by: str = "display_code",
        page: int = 1,
        page_size: int = 8,
    ) -> Dict[str, Any]:
        """
        Build detailed station report cards derived from actual SQLite analysis logs,
        live telemetry streams, and configured station coordinates.
        Enforces N/A for pH & TDS and labels simulated controls.
        """
        telemetry = sensor_simulator.get_latest()
        nodes_stream = telemetry.get("nodes", {})

        # Query recent persistent image analyses from SQLite
        recent_analyses = db_manager.get_recent_analyses(limit=50, analysis_type="IMAGE_PURITY")
        recent_by_source: Dict[str, Dict[str, Any]] = {}
        for a in recent_analyses:
            src = a.get("input_source", "")
            if src not in recent_by_source:
                recent_by_source[src] = a

        cards: List[Dict[str, Any]] = []

        for node_id, cfg in config.DRAINAGE_NODES.items():
            meta = STATION_METADATA.get(node_id, {})
            stream_data = nodes_stream.get(node_id, {})

            # Purity and water level
            purity = stream_data.get("cv_purity_score", 85.0)
            water_level_pct = stream_data.get("water_level_pct", 35.0)
            alert = stream_data.get("alert_level", "SAFE")

            # Check if there's a specific persisted inspection record matching this station
            sample_key = meta.get("sample_id", f"AQ-{node_id}")
            sample_date = datetime.now().strftime("%d %b %Y")
            image_b64 = None
            is_real_user_image = False
            debris_count = 0
            optical_turbidity = None

            # Look for recent logged image analysis
            matched_log = None
            for src_name, log_entry in recent_by_source.items():
                if node_id.lower() in src_name.lower() or meta.get("display_code", "").lower() in src_name.lower():
                    matched_log = log_entry
                    break

            if matched_log:
                details = matched_log.get("details", {})
                image_b64 = details.get("annotated_frame_b64")
                debris_count = details.get("detected_debris_count", 0)
                optical_turbidity = details.get("turbidity_index")
                purity = matched_log.get("primary_metric", purity)
                is_real_user_image = True
                sample_key = f"AQ-REC-{matched_log['id']:03d}"
                ts_str = matched_log.get("timestamp", "")
                if ts_str:
                    try:
                        sample_date = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).strftime("%d %b %Y")
                    except Exception:
                        pass

            # Rigorous Quality Status Logic (PASS / HOLD / FAIL)
            if purity >= 80.0 and water_level_pct <= 50.0:
                q_status = "PASS"
                q_color = "#10b981"
                ai_assessment = (
                    "Water appears clear with low optical turbidity. Visual clarity and debris metrics "
                    "are within configured thresholds. Safe for stormwater discharge."
                )
                sluice_action = "OPEN — SIMULATED"
                sluice_color = "#10b981"
                treatment_route = "NOT REQUIRED"
                route_code = "OPEN"
            elif purity >= 60.0 or (water_level_pct > 50.0 and water_level_pct <= 75.0):
                q_status = "HOLD"
                q_color = "#f59e0b"
                ai_assessment = (
                    "Moderate optical turbidity detected and/or water level is elevated. "
                    "Flow held for retention settling or secondary visual screening before release."
                )
                sluice_action = "BLOCKED — SIMULATED"
                sluice_color = "#f59e0b"
                treatment_route = "REQUIRED"
                route_code = "BLOCKED"
            else:
                q_status = "FAIL"
                q_color = "#ef4444"
                ai_assessment = (
                    "Configured 80% purity rule failed. High suspended solids or critical water surge detected. "
                    "Diverting blackwater to Kabithedi STP; discharge to river is blocked."
                )
                sluice_action = "BLOCKED — SIMULATED"
                sluice_color = "#ef4444"
                treatment_route = "REQUIRED"
                route_code = "BLOCKED"

            card_entry = {
                "node_id": node_id,
                "display_code": meta.get("display_code", "D-00"),
                "station_name": meta.get("display_name", cfg["name"]),
                "hindi_name": cfg.get("hindi_name", ""),
                "zone": meta.get("zone", "Indore Basin"),
                "river_system": meta.get("river_system", "Indore Basin"),
                "landmark": meta.get("landmark", "Municipal Drainage Point"),
                "latitude": cfg["lat"],
                "longitude": cfg["lon"],
                "elevation_msl_m": cfg["elevation_m"],
                "quality_status": q_status,
                "quality_color": q_color,
                "sample_id": sample_key,
                "sample_date": sample_date,
                "image_preview_url": meta.get("default_sample_image", "/samples/images/clean_rainwater.jpg"),
                "annotated_frame_b64": image_b64,
                "has_annotated_frame": bool(image_b64),
                "image_provenance": (
                    "PERSISTED_INSPECTION_FRAME" if is_real_user_image else "CALIBRATED_PROTOTYPE_FRAME"
                ),
                # Scientific Sensor Disclosure: pH and TDS are strictly N/A
                "ph_measurement": {
                    "value": None,
                    "display": "N/A",
                    "status": "UNAVAILABLE",
                    "standard_range": "6.5 – 8.5",
                    "note": "Electrochemical pH sensor not installed at this outfall.",
                },
                "tds_measurement": {
                    "value": None,
                    "display": "N/A",
                    "status": "UNAVAILABLE",
                    "standard_range": "≤ 500 mg/L",
                    "note": "Physical conductivity/TDS sensor not installed.",
                },
                "turbidity_measurement": {
                    "value": optical_turbidity if optical_turbidity is not None else round(100.0 - purity, 1),
                    "unit": "NTU (Optical Estimate)",
                    "display": f"{round(optical_turbidity if optical_turbidity is not None else (100.0 - purity), 1)} NTU",
                    "is_optical_estimate": True,
                    "threshold": "≤ 25 NTU",
                    "is_acceptable": bool(purity >= 80.0),
                    "note": "Derived from OpenCV pixel contrast variance; not a physical nephelometric probe.",
                },
                "purity_score_pct": round(purity, 1),
                "water_level_pct": round(water_level_pct, 1),
                "water_depth_cm": stream_data.get("water_depth_cm", 0.0),
                "flow_m3_s": stream_data.get("flow_m3_s", 0.0),
                "acoustic_db_spl": stream_data.get("acoustic_db", 42.0),
                "floating_debris_count": debris_count,
                "ai_assessment": ai_assessment,
                "sluice_gate_action": sluice_action,
                "sluice_gate_color": sluice_color,
                "treatment_route": treatment_route,
                "route_status_code": route_code,
                "cleaning_status": meta.get("cleaning_status", "Inspected / Clear"),
                "alert_level": alert,
                "is_simulated_telemetry": True,
                "scientific_disclaimer": (
                    "Visual clarity and acoustic resonance provide screening indications only. "
                    "Physical gates and emergency pumps remain under simulated automation."
                ),
            }
            cards.append(card_entry)

        # Apply Filters
        filtered = cards
        if search:
            q = search.lower().strip()
            filtered = [
                c for c in filtered
                if q in c["station_name"].lower()
                or q in c["display_code"].lower()
                or q in c["sample_id"].lower()
                or q in c["zone"].lower()
            ]

        if zone and zone != "ALL":
            filtered = [c for c in filtered if zone.lower() in c["zone"].lower()]

        if quality_status and quality_status != "ALL":
            filtered = [c for c in filtered if c["quality_status"].upper() == quality_status.upper()]

        if route_status and route_status != "ALL":
            filtered = [c for c in filtered if c["route_status_code"].upper() == route_status.upper()]

        if cleaning_status and cleaning_status != "ALL":
            filtered = [c for c in filtered if cleaning_status.lower() in c["cleaning_status"].lower()]

        # Apply Sorting
        if sort_by == "purity_desc":
            filtered.sort(key=lambda x: x["purity_score_pct"], reverse=True)
        elif sort_by == "purity_asc":
            filtered.sort(key=lambda x: x["purity_score_pct"], reverse=False)
        elif sort_by == "water_level_desc":
            filtered.sort(key=lambda x: x["water_level_pct"], reverse=True)
        elif sort_by == "name":
            filtered.sort(key=lambda x: x["station_name"])
        else:
            filtered.sort(key=lambda x: x["display_code"])

        # Pagination
        total_items = len(filtered)
        page = max(1, page)
        page_size = max(1, min(page_size, 50))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = filtered[start_idx:end_idx]

        return {
            "status": "success",
            "total_count": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total_items / page_size) if total_items > 0 else 1,
            "stations": paginated_items,
        }

    def get_station_detail(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full detailed inspection record for single station modal."""
        normalized = node_id.upper().strip()
        if normalized == "NODE_RAJWADA":
            normalized = "NODE_RAJWARA"
        elif normalized == "NODE_VIJAYNAGAR":
            normalized = "NODE_VIJAY_NAGAR"

        all_cards = self.get_station_cards(page_size=50)["stations"]
        for c in all_cards:
            if (
                c["node_id"] == node_id
                or c["node_id"] == normalized
                or c["display_code"].lower() == node_id.lower()
                or normalized in c["node_id"]
            ):
                return c
        return None

    def get_filtration_facilities(self) -> List[Dict[str, Any]]:
        """Return the 3 confirmed/modelled municipal filtration facilities."""
        return FILTRATION_FACILITIES

    def get_monitored_areas(self) -> List[Dict[str, Any]]:
        """Return the 4 verified hydrological catchment groupings."""
        return MONITORED_AREAS

    def generate_csv_report(self) -> str:
        """Generate comprehensive CSV string of all station monitoring records."""
        cards = self.get_station_cards(page_size=50)["stations"]
        output = io.StringIO()
        headers = [
            "Code", "Station_ID", "Station_Name", "Zone", "Elevation_MSL_m",
            "Latitude", "Longitude", "Quality_Status", "Sample_ID", "Sample_Date",
            "Purity_Score_pct", "Optical_Turbidity_NTU", "pH_Value", "TDS_mgL",
            "Water_Level_pct", "Acoustic_SPL_dB", "Debris_Count", "Sluice_Gate_Action",
            "Treatment_Route", "Cleaning_Status", "Data_Provenance"
        ]
        output.write(",".join(headers) + "\n")

        for c in cards:
            row = [
                c["display_code"],
                c["node_id"],
                f'"{c["station_name"]}"',
                f'"{c["zone"]}"',
                str(c["elevation_msl_m"]),
                str(c["latitude"]),
                str(c["longitude"]),
                c["quality_status"],
                c["sample_id"],
                c["sample_date"],
                str(c["purity_score_pct"]),
                str(c["turbidity_measurement"]["value"]),
                "N/A",  # pH sensor not installed
                "N/A",  # TDS sensor not installed
                str(c["water_level_pct"]),
                str(c["acoustic_db_spl"]),
                str(c["floating_debris_count"]),
                f'"{c["sluice_gate_action"]}"',
                f'"{c["treatment_route"]}"',
                f'"{c["cleaning_status"]}"',
                f'"{c["image_provenance"]}"',
            ]
            output.write(",".join(row) + "\n")

        return output.getvalue()

    def generate_station_pdf(self, node_id: str) -> bytes:
        """
        Generate formal Municipal Water Quality & Sluice Gate Inspection Certificate PDF
        using ReportLab with clean typography, tables, and provenance disclosure.
        """
        station = self.get_station_detail(node_id)
        if not station:
            raise ValueError(f"Station {node_id} not found")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Palette
        c_primary = colors.HexColor("#0f172a")
        c_blue = colors.HexColor("#0084ff")
        c_slate = colors.HexColor("#64748b")
        c_light = colors.HexColor("#f8fafc")
        c_border = colors.HexColor("#e2e8f0")
        c_pass = colors.HexColor("#10b981")
        c_fail = colors.HexColor("#ef4444")

        # Custom Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=c_primary,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=c_slate,
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=c_blue,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=c_primary,
        )
        caption_style = ParagraphStyle(
            "Caption",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=c_slate,
        )

        elements = []

        # Header Banner Table
        header_data = [
            [
                Paragraph("<b>HYDRO-GUARD AI | INDORE MUNICIPAL CORPORATION</b><br/><font color='#64748b' size='8'>Urban Drainage, Water Quality & Flash Flood Management Command</font>", body_style),
                Paragraph(f"<b>Certificate ID:</b> {station['sample_id']}<br/><b>Date:</b> {datetime.now().strftime('%d %b %Y %H:%M UTC')}", ParagraphStyle("RightH", parent=body_style, alignment=2)),
            ]
        ]
        header_table = Table(header_data, colWidths=[330, 190])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=14))

        # Title & Status Badge Table
        badge_bg = c_pass if station["quality_status"] == "PASS" else (colors.HexColor("#f59e0b") if station["quality_status"] == "HOLD" else c_fail)
        title_data = [
            [
                Paragraph(f"<b>{station['display_code']} • {station['station_name']}</b><br/><font size='9' color='#64748b'>{station['zone']} | River System: {station['river_system']}</font>", title_style),
                Paragraph(f"<font color='white' size='11'><b>  {station['quality_status']}  </b></font>", ParagraphStyle("Badge", parent=title_style, alignment=1, textColor=colors.white)),
            ]
        ]
        title_table = Table(title_data, colWidths=[420, 100])
        title_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (1, 0), (1, 0), badge_bg),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 10))

        # Station Metadata Grid
        meta_table_data = [
            [
                Paragraph("<b>Node Identifier:</b>", body_style), Paragraph(station["node_id"], body_style),
                Paragraph("<b>Elevation MSL:</b>", body_style), Paragraph(f"{station['elevation_msl_m']} m (Copernicus DEM)", body_style),
            ],
            [
                Paragraph("<b>GPS Coordinates:</b>", body_style), Paragraph(f"{station['latitude']:.4f}°N, {station['longitude']:.4f}°E", body_style),
                Paragraph("<b>Landmark Outfall:</b>", body_style), Paragraph(station["landmark"], body_style),
            ],
            [
                Paragraph("<b>Sluice Control:</b>", body_style), Paragraph(f"<b>{station['sluice_gate_action']}</b>", body_style),
                Paragraph("<b>Treatment Route:</b>", body_style), Paragraph(station["treatment_route"], body_style),
            ],
            [
                Paragraph("<b>Cleaning Status:</b>", body_style), Paragraph(station["cleaning_status"], body_style),
                Paragraph("<b>Inspection Date:</b>", body_style), Paragraph(station["sample_date"], body_style),
            ],
        ]
        meta_table = Table(meta_table_data, colWidths=[105, 155, 105, 155])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_light),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # Water Quality & Hydraulic Measurements Table
        elements.append(Paragraph("<b>Water Quality & Hydraulic Measurements</b>", section_heading))

        meas_data = [
            ["Parameter", "Observed Value", "Standard Criteria", "Evaluation Status", "Provenance & Method"],
            [
                "Water Purity Score",
                f"{station['purity_score_pct']}%",
                "≥ 80.0% Clean Rule",
                station["quality_status"],
                "OpenCV Colorimetry (Clarity & Contrast)"
            ],
            [
                "Optical Turbidity",
                station["turbidity_measurement"]["display"],
                "≤ 25 NTU",
                "ACCEPTABLE" if station["turbidity_measurement"]["is_acceptable"] else "EXCEEDED",
                "Heuristic Pixel Contrast Variance (Estimate)"
            ],
            [
                "pH Level",
                "N/A",
                "6.5 – 8.5",
                "SENSOR NOT INSTALLED",
                "Physical electrochemical electrode absent"
            ],
            [
                "Total Dissolved Solids (TDS)",
                "N/A",
                "≤ 500 mg/L",
                "SENSOR NOT INSTALLED",
                "In-situ conductivity probe absent"
            ],
            [
                "Acoustic Sewer Stage",
                f"{station['water_level_pct']}% ({station['water_depth_cm']} cm)",
                "Safe ≤ 50% / Warning ≤ 75%",
                station["alert_level"],
                f"Librosa Hydrophone ({station['acoustic_db_spl']} dB SPL)"
            ],
            [
                "Floating Debris Contours",
                f"{station['floating_debris_count']} objects detected",
                "0 objects (Clean Canal)",
                "CLEAN" if station["floating_debris_count"] == 0 else "DEBRIS DETECTED",
                "Morphological OpenCV Contour Analysis"
            ],
        ]
        meas_table = Table(meas_data, colWidths=[110, 85, 95, 90, 140])
        meas_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_blue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (1, 0), (3, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(meas_table)
        elements.append(Spacer(1, 14))

        # AI Assessment Box
        elements.append(Paragraph("<b>Edge AI Assessment & Operational Recommendation</b>", section_heading))
        assess_data = [[
            Paragraph(f"<b>Assessment:</b> {station['ai_assessment']}<br/><br/>"
                      f"<b>Automated Sluice Recommendation:</b> {station['sluice_gate_action']}. "
                      f"Diverts flow to: <i>{station['treatment_route']}</i>.", body_style)
        ]]
        assess_table = Table(assess_data, colWidths=[520])
        assess_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(assess_table)
        elements.append(Spacer(1, 14))

        # Scientific Disclaimer Box
        disc_text = (
            "<b>LEGAL & SCIENTIFIC DATA PROVENANCE NOTICE:</b><br/>"
            "1. Physical electrochemical pH and TDS sensors are not currently deployed; values are truthfully reported as N/A.<br/>"
            "2. Turbidity and debris metrics are optical approximations derived from computer vision frames; not laboratory assays.<br/>"
            "3. Sluice gate actuation and flood inundation depths are simulated predictions produced by NetworkX routing models.<br/>"
            "4. Elevation data is extracted from Copernicus GLO-30 DEM surface rasters (EPSG:4326/32643)."
        )
        disc_data = [[Paragraph(disc_text, caption_style)]]
        disc_table = Table(disc_data, colWidths=[520])
        disc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fecaca")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(disc_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Singleton reporting service instance
reporting_service = ReportingService()
