"""
Indore GIS Map Visualizer Component for HYDRO-GUARD AI.
Renders interactive Folium map with river topology, south-to-north hydraulic flow lines,
traffic-light node statuses, elevation tooltips, and inundation heatmaps.
Includes Matplotlib fallback for static/offline rendering.
"""

from typing import Dict, Any, List, Optional
import io
import folium
from folium.plugins import HeatMap, AntPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config


class IndoreMapVisualizer:
    """Renders geospatial layers and hydraulic topologies for Indore."""

    def __init__(self):
        self.center_lat = config.INDORE_CENTER_LAT
        self.center_lon = config.INDORE_CENTER_LON

    def create_folium_map(self, telemetry_data: Optional[Dict[str, Any]] = None) -> folium.Map:
        """
        Build full-featured Folium map with:
        - Dark matter / CartoDB tiles
        - Khan & Saraswati River reaches
        - Nodes color-coded by water level % (Green, Yellow, Red)
        - Inundation hazard heatmap
        """
        nodes_dict = telemetry_data.get("nodes", {}) if telemetry_data else {}

        # Base Map centered on Indore (OpenStreetMap tiles - 100% free, no API key required)
        m = folium.Map(
            location=[self.center_lat, self.center_lon],
            zoom_start=12,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        # Draw Directed River Flow Channels (AntPath animated or Polylines)
        for u, v, edge_data in config.DRAINAGE_EDGES:
            u_node = config.DRAINAGE_NODES.get(u)
            v_node = config.DRAINAGE_NODES.get(v)
            if not u_node or not v_node:
                continue

            coords = [[u_node["lat"], u_node["lon"]], [v_node["lat"], v_node["lon"]]]
            channel_name = edge_data.get("channel", "Drain")
            travel_min = edge_data.get("travel_time_min", 15)

            # Draw directional flow line
            folium.PolyLine(
                locations=coords,
                color="#00e5ff",
                weight=4,
                opacity=0.8,
                tooltip=f"<b>{channel_name}</b><br>Slope: {(u_node['elevation_m'] - v_node['elevation_m']):.1f}m drop<br>Flow Travel Time: ~{travel_min} mins",
            ).add_to(m)

        # Plot Drainage & Outfall Nodes
        heatmap_points = []
        for node_id, data in config.DRAINAGE_NODES.items():
            live = nodes_dict.get(node_id, {})
            water_level = live.get("water_level_pct", 35.0)
            alert = live.get("alert_level", "SAFE")
            color = live.get("alert_color", "#00e676")
            purity = live.get("cv_purity_score", 85.0)
            gate = live.get("gate_status", config.GATE_CLEAN_ACTION)
            depth_cm = live.get("water_depth_cm", 0.0)

            # Build heatmap weighting based on water level
            if water_level > 50.0:
                heatmap_points.append([data["lat"], data["lon"], water_level / 100.0])

            # Marker Popup HTML (Dark Tech Style)
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; min-width: 200px; color: #111b2e;">
                <h4 style="margin: 0 0 5px 0; color: #0f172a;">{data['name']}</h4>
                <div style="color: #475569; font-size: 11px; margin-bottom: 8px;">{data['hindi_name']}</div>
                <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                    <tr><td><b>Elevation:</b></td><td style="text-align: right;">{data['elevation_m']} m MSL</td></tr>
                    <tr><td><b>Water Level:</b></td><td style="text-align: right; color: {color}; font-weight: bold;">{water_level}%</td></tr>
                    <tr><td><b>Inundation:</b></td><td style="text-align: right;">{depth_cm} cm</td></tr>
                    <tr><td><b>Purity:</b></td><td style="text-align: right;">{purity}%</td></tr>
                    <tr><td><b>Gate:</b></td><td style="text-align: right; font-weight: bold;">{gate}</td></tr>
                </table>
            </div>
            """

            # Node Marker Circle
            radius = 10 if alert == "SAFE" else (14 if alert == "WARNING" else 18)
            folium.CircleMarker(
                location=[data["lat"], data["lon"]],
                radius=radius,
                color="#ffffff",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                tooltip=f"<b>{data['name']}</b> ({water_level}%) - {alert}",
                popup=folium.Popup(popup_html, max_width=280),
            ).add_to(m)

        # Add Heatmap Layer for Inundation Risk
        if heatmap_points:
            HeatMap(
                heatmap_points,
                radius=25,
                blur=18,
                min_opacity=0.4,
                gradient={0.2: "#00e676", 0.6: "#ffab00", 1.0: "#ff1744"},
            ).add_to(m)

        return m

    def render_elevation_profile_chart(self, profile_data: List[Dict[str, Any]]) -> io.BytesIO:
        """Render high-contrast elevation drop plot showing Rau (560m) to Kabithedi (515m)."""
        names = [p["name"].replace(" Headwaters", "").replace(" Main STP & Terminal Outfall", "") for p in profile_data]
        elevations = [p["elevation_m"] for p in profile_data]
        distances = [p["distance_km"] for p in profile_data]

        fig, ax = plt.subplots(figsize=(8, 3.2), facecolor="#0a0f1d")
        ax.set_facecolor("#111b2e")

        # Plot gradient slope fill
        ax.fill_between(distances, elevations, 500, color="#00e5ff", alpha=0.15)
        ax.plot(distances, elevations, color="#00e5ff", linewidth=2.5, marker="o", markersize=6, markerfacecolor="#ffffff")

        # Annotations
        for d, e, name in zip(distances, elevations, names):
            ax.annotate(
                f"{name}\n{e:.0f}m",
                (d, e),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontsize=8,
                color="#e0f2fe",
                fontweight="bold",
            )

        ax.set_title("Indore South-to-North Topographical Hydraulic Gradient (Khan River Basin)",
                     color="#ffffff", fontsize=10, fontweight="bold", pad=14)
        ax.set_xlabel("Hydraulic Distance (km) [South Rau -> North Kabithedi]", color="#90caf9", fontsize=8)
        ax.set_ylabel("Elevation (m MSL)", color="#90caf9", fontsize=8)
        ax.set_ylim(505, 575)
        ax.tick_params(colors="#90caf9", labelsize=8)
        ax.grid(True, color="#1e293b", linestyle="--", alpha=0.6)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf


# Global visualizer instance
indore_map_visualizer = IndoreMapVisualizer()
