"""
2-Second Real-Time Telemetry Sensor Simulator for Indore Urban Drainage.
Runs an asynchronous/threaded background generator that updates drain node telemetry,
including water levels, acoustic dB readings, CV purity scores, and automated gate decisions.
"""

import threading
import time
import random
from typing import Dict, Any, List, Optional, Tuple
from collections import deque

import config
from backend.services.open_meteo_client import weather_client
from backend.models.indore_routing_engine import routing_engine


# Baseline realistic urban drainage purity ranges per Indore outfall cross-section
# Sourced from visual inspection frames, suspended sediment load, and municipal wastewater loading.
NODE_BASE_PURITY: Dict[str, Tuple[float, float]] = {
    "NODE_RAU": (54.0, 62.0),           # Upstream South Ridge earthen canal, soil erosion silt
    "NODE_BHANWARKUAN": (44.0, 50.0),   # Underground box culvert, anaerobic black silt
    "NODE_RAJWARA": (48.0, 55.0),       # Saraswati-Khan confluence, urban sullage & surface scum
    "NODE_RAMBAGH": (36.0, 43.0),       # Khan River trunk, thick brown suspended sludge
    "NODE_PARDESHIPURA": (38.0, 45.0),  # Industrial drain, chemical effluent particulate
    "NODE_VIJAY_NAGAR": (40.0, 46.0),   # Eastern sump collector, road silt & organic debris
    "NODE_KABITHEDI_STP": (26.0, 32.0), # Terminal 245 MLD STP inlet, raw municipal blackwater & trash
}


class SensorStreamSimulator:
    """
    Simulates high-frequency IoT sensors across Indore's critical storm drains.
    Yields 2-second updates with realistic hydrological physics and stochastic noise.
    """

    def __init__(self, interval_sec: float = config.TELEMETRY_INTERVAL_SEC):
        self.interval = interval_sec
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # In-memory sliding buffer for real-time history
        self.history_buffer = deque(maxlen=config.BUFFER_SIZE)
        self.latest_telemetry: Dict[str, Any] = {}

        # Interactive scenario overrides
        self.surge_multiplier: float = 1.0
        self.forced_pollution: bool = False
        self._step_counter: int = 0

        # Initialize base state
        self._initialize_node_states()

    def _initialize_node_states(self) -> None:
        """Establish baseline sensor telemetry across Indore nodes."""
        self.node_states: Dict[str, Dict[str, Any]] = {}
        for node_id, d in config.DRAINAGE_NODES.items():
            base_level = random.uniform(22.0, 38.0)
            p_min, p_max = NODE_BASE_PURITY.get(node_id, (40.0, 50.0))
            self.node_states[node_id] = {
                "water_level_pct": base_level,
                "cv_purity_score": round(random.uniform(p_min, p_max), 1),
                "acoustic_db": 42.0 + (base_level * 0.4),
                "battery_pct": round(random.uniform(91.0, 99.0), 1),
            }

    def start(self) -> None:
        """Launch the 2-second background simulation loop."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Halt the simulation background thread."""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        """Continuous execution loop producing 2-sec telemetry snapshots."""
        while self.is_running:
            try:
                snapshot = self._generate_telemetry_snapshot()
                with self._lock:
                    self.latest_telemetry = snapshot
                    self.history_buffer.append(snapshot)
                
                # Periodically persist telemetry snapshot to SQLite (every 10 seconds / 5 cycles)
                self._step_counter += 1
                if self._step_counter % 5 == 0:
                    try:
                        from backend.services.db_manager import db_manager
                        db_manager.log_telemetry_snapshot(
                            city_avg_pct=snapshot.get("city_avg_water_level_pct", 0.0),
                            peak_node=snapshot.get("peak_risk_node", "Rajwada"),
                            peak_level_pct=snapshot.get("peak_risk_level_pct", 0.0),
                            rainfall_intensity=snapshot.get("rainfall_mm_hr", 0.0),
                            nodes_snapshot=snapshot.get("nodes", {}),
                        )
                    except Exception:
                        pass
            except Exception as e:
                # Keep loop resilient
                pass
            time.sleep(self.interval)

    def _generate_telemetry_snapshot(self) -> Dict[str, Any]:
        """Synthesize next 2-second telemetry step based on live rain and Indore elevation."""
        weather = weather_client.fetch_live_weather()
        rain_rate = weather.get("rainfall_intensity_mm_hr", 4.0) * self.surge_multiplier

        # Run routing engine for current conditions
        routing_res = routing_engine.simulate_routing(rain_rate, weather.get("runoff_coefficient", 0.72))
        node_results = routing_res.get("nodes", {})

        nodes_telemetry = {}
        for node_id, d in config.DRAINAGE_NODES.items():
            curr_state = self.node_states[node_id]
            routed = node_results.get(node_id, {})

            # Smoothly transition water level towards routed prediction
            target_level = routed.get("water_level_pct", curr_state["water_level_pct"])
            step = (target_level - curr_state["water_level_pct"]) * 0.15 + random.uniform(-0.8, 0.8)
            new_level = max(5.0, min(100.0, curr_state["water_level_pct"] + step))
            curr_state["water_level_pct"] = round(new_level, 1)

            # Acoustic decibels: correlated with water level & turbulence
            # dB SPL: ~40 dB baseline to ~90 dB at 100% capacity
            target_db = config.ACOUSTIC_DB_MIN + (new_level / 100.0) * (config.ACOUSTIC_DB_MAX - config.ACOUSTIC_DB_MIN)
            new_db = round(target_db + random.uniform(-1.2, 1.2), 1)
            curr_state["acoustic_db"] = new_db

            # CV Purity Score (%):
            # Urban storm drains carry sullage, road wash, and untreated municipal wastewater.
            p_min, p_max = NODE_BASE_PURITY.get(node_id, (40.0, 50.0))
            if self.forced_pollution or (new_level > 65.0):
                target_purity = random.uniform(max(15.0, p_min - 12.0), max(25.0, p_max - 8.0))
            else:
                target_purity = random.uniform(p_min, p_max)

            curr_state["cv_purity_score"] = round(target_purity, 1)
            purity = curr_state["cv_purity_score"]

            # Apply the 80% Purity Rule
            if purity >= config.PURITY_THRESHOLD_PCT:
                gate_status = config.GATE_CLEAN_ACTION
                gate_color = "#00e676"  # Green
            else:
                gate_status = config.GATE_DIRTY_ACTION
                gate_color = "#ff1744"  # Red / Amber

            # Alert status
            if new_level <= config.WATER_LEVEL_SAFE_MAX:
                alert = "SAFE"
                alert_color = "#00e676"
            elif new_level <= config.WATER_LEVEL_WARNING_MAX:
                alert = "WARNING"
                alert_color = "#ffab00"
            else:
                alert = "CRITICAL"
                alert_color = "#ff1744"

            # Battery slowly fluctuates
            curr_state["battery_pct"] = round(max(85.0, curr_state["battery_pct"] - 0.001), 1)

            nodes_telemetry[node_id] = {
                "node_id": node_id,
                "name": d["name"],
                "hindi_name": d["hindi_name"],
                "lat": d["lat"],
                "lon": d["lon"],
                "elevation_m": d["elevation_m"],
                "water_level_pct": new_level,
                "water_depth_cm": routed.get("inundation_depth_cm", 0.0),
                "flow_m3_s": routed.get("flow_m3_s", round(new_level * 0.4, 2)),
                "acoustic_db": new_db,
                "cv_purity_score": purity,
                "purity_rule_applied": f"{'PASS' if purity >= 80.0 else 'FAIL'} (Threshold 80%)",
                "gate_status": gate_status,
                "gate_color": gate_color,
                "alert_level": alert,
                "alert_color": alert_color,
                "battery_pct": curr_state["battery_pct"],
                "is_sensor_active": True,
            }

        # Calculate city-wide aggregate statistics
        avg_level = sum(n["water_level_pct"] for n in nodes_telemetry.values()) / len(nodes_telemetry)
        max_level_node = max(nodes_telemetry.values(), key=lambda x: x["water_level_pct"])

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "epoch_time": time.time(),
            "rainfall_mm_hr": round(rain_rate, 2),
            "rainfall_category": weather.get("rainfall_category", "Normal"),
            "city_avg_water_level_pct": round(avg_level, 1),
            "peak_risk_node": max_level_node["name"],
            "peak_risk_level_pct": max_level_node["water_level_pct"],
            "nodes": nodes_telemetry,
        }

    def get_latest(self) -> Dict[str, Any]:
        """Fetch the most recent telemetry snapshot."""
        with self._lock:
            if not self.latest_telemetry:
                self.latest_telemetry = self._generate_telemetry_snapshot()
            return self.latest_telemetry

    def get_history(self, count: int = 30) -> List[Dict[str, Any]]:
        """Fetch trailing telemetry snapshots for time-series charts."""
        with self._lock:
            items = list(self.history_buffer)
            return items[-count:] if len(items) >= count else items

    def set_surge_simulation(self, multiplier: float) -> None:
        """Trigger interactive storm surge multiplier."""
        self.surge_multiplier = max(0.1, min(10.0, multiplier))

    def trigger_pollution_event(self, active: bool = True) -> None:
        """Inject a high turbidity/sewage contamination event to demonstrate the 80% Rule."""
        self.forced_pollution = active


# Global simulator instance
sensor_simulator = SensorStreamSimulator()

