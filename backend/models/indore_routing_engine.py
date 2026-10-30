"""
NetworkX Topological Flow, Routing, and Inundation Prediction Engine for Indore.
Models the south-to-north elevation drop (Rau/Bhanwarkuan ~550m -> Kabithedi ~515m).
Calculates flow accumulation, peak flood arrival times, inundation depths, and gate controls.
"""

import math
from typing import Dict, Any, List, Optional
import networkx as nx

import config
from backend.services.osmnx_gis_loader import indore_gis_loader


class IndoreRoutingEngine:
    """
    Hydrological routing and topological flood risk simulator for Indore's drainage basin.
    Uses NetworkX topological sort to calculate downstream cumulative discharge and peak lag times.
    """

    def __init__(self, gis_loader=indore_gis_loader):
        self.gis = gis_loader
        self.graph: nx.DiGraph = self.gis.get_indore_drainage_graph()

    def simulate_routing(self, rainfall_mm_hr: float, runoff_coeff: float = 0.72) -> Dict[str, Any]:
        """
        Compute hydrological runoff and routing across all drainage nodes.
        Returns node inundation depths, flood arrival times, alert statuses, and gate actions.
        """
        # Ensure topological order from headwaters down to terminal outfall
        try:
            topo_nodes = list(nx.topological_sort(self.graph))
        except Exception:
            topo_nodes = list(self.graph.nodes())

        node_flows: Dict[str, float] = {}  # Cumulative m^3/s
        node_results: Dict[str, Dict[str, Any]] = {}
        choke_points: List[Dict[str, Any]] = []

        # Step 1: Compute local sub-catchment runoff via Rational Formula:
        # Q_local (m^3/s) = (C * I * A) / 3.6
        # where C = runoff coefficient, I = rainfall in mm/hr, A = area in km^2
        for node in topo_nodes:
            data = self.graph.nodes[node]
            area_km2 = data.get("catchment_km2", 15.0)
            local_q = (runoff_coeff * rainfall_mm_hr * area_km2) / 3.6
            node_flows[node] = local_q

        # Step 2: Accumulate upstream discharge down the directed topological edges
        for node in topo_nodes:
            data = self.graph.nodes[node]
            in_edges = list(self.graph.in_edges(node, data=True))
            upstream_q_sum = 0.0
            max_upstream_lag = 0.0

            for u, _, edge_attrs in in_edges:
                upstream_q = node_flows.get(u, 0.0)
                # Attenuation coefficient: 0.88 through urban channels
                attenuation = 0.90
                upstream_q_sum += upstream_q * attenuation

                # Travel time along edge
                edge_lag = edge_attrs.get("travel_time_min", 15.0)
                u_result = node_results.get(u, {})
                cumulative_lag = u_result.get("peak_flood_arrival_min", 0.0) + edge_lag
                if cumulative_lag > max_upstream_lag:
                    max_upstream_lag = cumulative_lag

            node_flows[node] += upstream_q_sum

            # Local time of concentration (Tc) in minutes
            # Kirpich formula simplified: Tc ~ 12 to 25 mins for Indore sub-catchments
            local_tc = 15.0 + math.sqrt(data.get("catchment_km2", 15.0)) * 2.0
            peak_arrival_min = round(max(local_tc, max_upstream_lag), 1)

            max_cap = data.get("max_capacity_m3_s", 60.0)
            total_q = node_flows[node]
            utilization_pct = min(100.0, round((total_q / max_cap) * 100.0, 1))

            # Inundation Depth calculation (cm above street/bank level)
            if total_q > max_cap:
                overflow_q = total_q - max_cap
                # Channel bank spill: depth = (overflow_q / channel_width) * flow_factor
                inundation_depth_cm = round(min(150.0, 15.0 + (overflow_q * 1.8)), 1)
            else:
                # Flow inside drain banks; water surface elevation relative to bank
                freeboard_pct = 100.0 - utilization_pct
                inundation_depth_cm = 0.0

            # Traffic-Light Alert Status
            if utilization_pct <= config.WATER_LEVEL_SAFE_MAX:
                alert_status = "SAFE"
                alert_color = "#00e676"  # Bright Emerald
                status_hi = "सुरक्षित (सामान्य प्रवाह)"
            elif utilization_pct <= config.WATER_LEVEL_WARNING_MAX:
                alert_status = "WARNING"
                alert_color = "#ffab00"  # Amber Warning
                status_hi = "चेतावनी (जलस्तर मध्यम)"
            else:
                alert_status = "CRITICAL"
                alert_color = "#ff1744"  # Alert Red
                status_hi = "खतरा (जलभराव की आशंका)"

            # Sluice Gate Control Logic
            gate_decision = self._compute_gate_action(node, utilization_pct, total_q)

            res = {
                "node_id": node,
                "name": data["name"],
                "hindi_name": data["hindi_name"],
                "lat": data["lat"],
                "lon": data["lon"],
                "elevation_m": data["elevation_m"],
                "flow_m3_s": round(total_q, 2),
                "max_capacity_m3_s": max_cap,
                "water_level_pct": utilization_pct,
                "inundation_depth_cm": inundation_depth_cm,
                "peak_flood_arrival_min": peak_arrival_min,
                "alert_status": alert_status,
                "alert_color": alert_color,
                "status_hindi": status_hi,
                "gate_decision": gate_decision,
            }

            node_results[node] = res

            if alert_status == "CRITICAL":
                choke_points.append({
                    "node_id": node,
                    "name": data["name"],
                    "hindi_name": data["hindi_name"],
                    "inundation_depth_cm": inundation_depth_cm,
                    "peak_time_min": peak_arrival_min,
                    "action_required": gate_decision["recommendation_hi"],
                })

        # Basin-wide summary
        overall_severity = "SAFE"
        critical_count = sum(1 for r in node_results.values() if r["alert_status"] == "CRITICAL")
        warning_count = sum(1 for r in node_results.values() if r["alert_status"] == "WARNING")

        if critical_count > 0:
            overall_severity = "CRITICAL"
        elif warning_count > 0:
            overall_severity = "WARNING"

        return {
            "timestamp": "Live Simulation",
            "simulation_mode": True,
            "disclaimer": "Hydrological routing prototype. Not connected to physical municipal actuators.",
            "rainfall_input_mm_hr": rainfall_mm_hr,
            "runoff_coefficient": runoff_coeff,
            "overall_basin_status": overall_severity,
            "choke_points": choke_points,
            "nodes": node_results,
            "elevation_drop_total_m": config.INDORE_MAX_MSL_ELEVATION - config.INDORE_MIN_MSL_ELEVATION,
        }

    def predict_downstream_inundation(
        self,
        rainfall_mm_hr: float = 25.0,
        surge_multiplier: float = 1.0,
        active_pumps: int = 2,
        runoff_coeff: float = 0.72,
    ) -> Dict[str, Any]:
        """
        Predict downstream hydraulic inundation, peak surge arrival, choke points,
        and gate actions across Indore's topological drainage network.
        Integrates Rational runoff routing, Kirpich lag times, and pump relief.
        Used by the Dual-Engine Flood Prediction dashboard and downstream systems.
        """
        effective_rain = float(rainfall_mm_hr) * float(surge_multiplier)
        routing_res = self.simulate_routing(rainfall_mm_hr=effective_rain, runoff_coeff=runoff_coeff)

        # Municipal high-lift pump drawdown relief (~4.5% water level reduction per active pump)
        pump_relief_pct = round(max(0, active_pumps) * 4.5, 1)

        node_predictions: List[Dict[str, Any]] = []
        for node_id, node_data in routing_res.get("nodes", {}).items():
            base_level_pct = node_data.get("water_level_pct", 0.0)
            adjusted_level = max(10.0, round(base_level_pct - pump_relief_pct, 1))

            if adjusted_level <= config.WATER_LEVEL_SAFE_MAX:
                status = "SAFE"
            elif adjusted_level <= config.WATER_LEVEL_WARNING_MAX:
                status = "WARNING"
            else:
                status = "CRITICAL"

            gate_decision = node_data.get("gate_decision", {})
            gate_action = gate_decision.get("gate_state") or gate_decision.get("recommendation_en") or "NORMAL_GRAVITY_FLOW"

            node_predictions.append({
                "node_id": node_id,
                "node_name": node_data.get("name", node_id),
                "elevation_msl": node_data.get("elevation_m", 540.0),
                "water_level_pct": adjusted_level,
                "status": status,
                "gate_action": gate_action,
                "inundation_depth_cm": node_data.get("inundation_depth_cm", 0.0),
                "flow_m3_s": node_data.get("flow_m3_s", 0.0),
            })

        # Identify peak critical choke point
        choke_points = routing_res.get("choke_points", [])
        if choke_points:
            sorted_cp = sorted(choke_points, key=lambda c: c.get("inundation_depth_cm", 0.0), reverse=True)
            peak_choke_point = sorted_cp[0]["name"]
            # Arrival time at first critical bottleneck, buffered by active pump operation
            first_arrival = min(cp.get("peak_time_min", 45.0) for cp in choke_points)
            peak_flood_arrival_mins = max(15, int(round(first_arrival + (active_pumps * 2.0))))
        else:
            # Check warning nodes or safe baseline
            warn_nodes = [n for n in node_predictions if n["status"] == "WARNING"]
            if warn_nodes:
                peak_choke_point = warn_nodes[0]["node_name"]
            else:
                peak_choke_point = "None (All Systems Nominal)"

            node_lags = [n.get("peak_flood_arrival_min", 45.0) for n in routing_res.get("nodes", {}).values()]
            base_arrival = min(node_lags) if node_lags else 45.0
            peak_flood_arrival_mins = max(15, int(round(base_arrival + (active_pumps * 2.0))))

        return {
            "status": "success",
            "rainfall_mm_hr": rainfall_mm_hr,
            "surge_multiplier": surge_multiplier,
            "effective_rainfall_mm_hr": effective_rain,
            "active_pumps": active_pumps,
            "peak_flood_arrival_mins": peak_flood_arrival_mins,
            "peak_choke_point": peak_choke_point,
            "overall_basin_risk": routing_res.get("overall_basin_status", "SAFE"),
            "choke_points": choke_points,
            "node_predictions": node_predictions,
            "routing_simulation": routing_res,
        }

    def _compute_gate_action(self, node_id: str, water_level_pct: float, flow_m3_s: float) -> Dict[str, Any]:
        """Automated sluice gate and pump control decision based on node hydraulic capacity."""
        if node_id == "NODE_RAJWARA":
            # Confluence of Saraswati & Khan River at Krishnapura Chhatri
            if water_level_pct > 75.0:
                return {
                    "gate_state": "DIVERT_TO_BILAWALI_HOLDING",
                    "gate_pct_open": 100,
                    "recommendation_en": "Open emergency diversion spillway to Pipliyahala / Bilawali basin. Close Rajwada bazaar sluice.",
                    "recommendation_hi": "राजवाड़ा बाजार जलभराव रोकने हेतु बिलावली/पिपलियापाला रिटेंशन बेसिन में डायवर्ट करें।",
                }
            elif water_level_pct > 50.0:
                return {
                    "gate_state": "THROTTLE_CONFLUENCE_GATES",
                    "gate_pct_open": 65,
                    "recommendation_en": "Throttle Saraswati discharge to equalize Khan River main channel capacity.",
                    "recommendation_hi": "खान नदी के मुख्य चैनल में क्षमता संतुलित करने हेतु सरस्वती डिस्चार्ज नियंत्रित करें।",
                }
            else:
                return {
                    "gate_state": "NORMAL_GRAVITY_FLOW",
                    "gate_pct_open": 30,
                    "recommendation_en": "Standard gravity drainage active. No sluice throttling needed.",
                    "recommendation_hi": "सामान्य गुरुत्वाकर्षण जलप्रवाह सुचारु। किसी रोक की आवश्यकता नहीं।",
                }

        elif node_id == "NODE_KABITHEDI_STP":
            # Terminal Treatment Plant & River Outfall
            if water_level_pct > 75.0:
                return {
                    "gate_state": "ACTIVATE_AUXILIARY_HIGH_LIFT_PUMPS",
                    "gate_pct_open": 100,
                    "recommendation_en": "Activate all 6 high-lift pumps (245 MLD). Open bypass holding lagoon.",
                    "recommendation_hi": "कबीटखेड़ी मुख्य पंप व सभी 6 हाई-लिफ्ट पंप (245 MLD) पूर्ण क्षमता पर चालू कर दिए गए हैं।",
                }
            else:
                return {
                    "gate_state": "STANDARD_TREATMENT_INFLOW",
                    "gate_pct_open": 50,
                    "recommendation_en": "Standard biological aeration basin flow. STP operating within nominal envelope.",
                    "recommendation_hi": "मानक जैविक वातन बेसिन प्रवाह। एसटीपी सामान्य संचालन में।",
                }

        else:
            if water_level_pct > 75.0:
                return {
                    "gate_state": "DEPLOY_MOBILE_DEWATERING_PUMP",
                    "gate_pct_open": 100,
                    "recommendation_en": "Deploy IMC rapid-response dewatering diesel pump trucks.",
                    "recommendation_hi": "आईएमसी (IMC) त्वरित जल निकासी डीजल पंप वाहन तुरंत तैनात करें।",
                }
            else:
                return {
                    "gate_state": "MONITORING",
                    "gate_pct_open": 0,
                    "recommendation_en": "Inflow is within conduit cross-section design limit.",
                    "recommendation_hi": "जलप्रवाह नाले की डिज़ाइन सीमा के भीतर सुरक्षित है।",
                }


# Global engine instance
routing_engine = IndoreRoutingEngine()
