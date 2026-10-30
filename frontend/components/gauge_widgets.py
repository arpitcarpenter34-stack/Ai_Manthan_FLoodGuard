"""
UI Widgets for HYDRO-GUARD AI:
- Speedometer / Dial Gauge (0 - 100%)
- Split-Pipe Diversion Diagram (80% Purity Rule)
- Plain-Language Bilingual Action Cards (English & Hindi)
- GenAI Citizen SMS Broadcast Generator
- Scannable QR Emergency Evacuation Pass
"""

import io
import base64
import math
import qrcode
from typing import Dict, Any, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config


class GaugeWidgets:
    """Specialized widgets for non-technical municipal operators and citizen alerts."""

    @staticmethod
    def render_speedometer_gauge(level_pct: float, title: str = "Khan River Basin Water Level") -> io.BytesIO:
        """
        Render a modern dark-tech semi-circular speedometer gauge (0 - 100%).
        Green (0-50%) -> Yellow (50-75%) -> Red (75-100%).
        """
        level_pct = max(0.0, min(100.0, float(level_pct)))

        fig, ax = plt.subplots(figsize=(4.5, 2.6), subplot_kw={"projection": "polar"}, facecolor="#0a0f1d")
        ax.set_facecolor("#0a0f1d")

        # Semi-circle angles (from pi to 0 radians)
        theta_start = np.pi
        theta_end = 0

        # Background colored arc segments
        # Safe zone: 0 to 50%
        ax.bar(x=(np.pi - (np.pi * 0.25)), height=0.35, width=np.pi * 0.5, bottom=0.65,
               color="#00e676", alpha=0.35, edgecolor="#00e676", linewidth=1.2)
        # Warning zone: 50 to 75%
        ax.bar(x=(np.pi - (np.pi * 0.625)), height=0.35, width=np.pi * 0.25, bottom=0.65,
               color="#ffab00", alpha=0.45, edgecolor="#ffab00", linewidth=1.2)
        # Danger zone: 75 to 100%
        ax.bar(x=(np.pi - (np.pi * 0.875)), height=0.35, width=np.pi * 0.25, bottom=0.65,
               color="#ff1744", alpha=0.55, edgecolor="#ff1744", linewidth=1.2)

        # Needle Calculation
        needle_angle = np.pi - (level_pct / 100.0) * np.pi
        needle_color = "#00e676" if level_pct <= 50 else ("#ffab00" if level_pct <= 75 else "#ff1744")

        # Draw needle
        ax.annotate(
            "",
            xy=(needle_angle, 0.95),
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color=needle_color, lw=3, mutation_scale=15),
        )
        ax.plot(0, 0, "o", color="#ffffff", markersize=8)

        # Display digital readout at bottom
        ax.text(
            np.pi / 2, 0.25,
            f"{level_pct:.0f}%",
            ha="center", va="center",
            color="#ffffff", fontsize=18, fontweight="bold",
        )
        ax.text(
            np.pi / 2, 0.0,
            title,
            ha="center", va="center",
            color="#94a3b8", fontsize=7.5, fontweight="bold",
        )

        ax.set_thetamin(0)
        ax.set_thetamax(180)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["polar"].set_visible(False)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=110, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf

    @staticmethod
    def render_split_pipe_html(purity_score: float) -> str:
        """
        Generate dynamic HTML/CSS diagram illustrating the 80% Purity Split-Pipe rule.
        Demonstrates motorized diversion gate routing:
        - Water Purity >= 80%: Blue Clean Stream -> Khan River
        - Water Purity < 80%: Muddy/Red Stream -> Kabithedi STP
        """
        is_clean = purity_score >= config.PURITY_THRESHOLD_PCT
        river_active = is_clean
        stp_active = not is_clean

        river_glow = "0 0 15px #00e676" if river_active else "none"
        stp_glow = "0 0 15px #ff1744" if stp_active else "none"

        river_color = "#00e676" if river_active else "#334155"
        stp_color = "#ff1744" if stp_active else "#334155"

        status_text = "PASS: GATE OPEN TO KHAN RIVER" if is_clean else "FAIL: DIVERTING TO KABITHEDI STP"
        status_badge_bg = "#00e67622" if is_clean else "#ff174422"
        status_border = "#00e676" if is_clean else "#ff1744"

        html = f"""
        <div style="background-color: #0b1329; border: 1px solid #1e293b; border-radius: 12px; padding: 16px; font-family: 'Segoe UI', Tahoma, sans-serif; color: #e2e8f0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 13px; font-weight: bold; color: #38bdf8;">⚡ AUTOMATED SPLIT-PIPE DIVERSION SYSTEM (80% RULE)</span>
                <span style="background: {status_badge_bg}; border: 1px solid {status_border}; color: {status_border}; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: bold;">
                    PURITY: {purity_score}% ({'CLEAN' if is_clean else 'CONTAMINATED'})
                </span>
            </div>

            <!-- SVG Schematic Diagram -->
            <svg viewBox="0 0 540 180" style="width: 100%; height: auto; display: block;">
                <defs>
                    <linearGradient id="cleanGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#00e5ff"/>
                        <stop offset="100%" stop-color="#00e676"/>
                    </linearGradient>
                    <linearGradient id="dirtyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#f59e0b"/>
                        <stop offset="100%" stop-color="#ff1744"/>
                    </linearGradient>
                </defs>

                <!-- Main Inflow Pipe -->
                <rect x="20" y="70" width="160" height="40" rx="6" fill="#1e293b" stroke="#475569" stroke-width="2"/>
                <text x="100" y="95" fill="#cbd5e1" font-size="12" font-weight="bold" text-anchor="middle">DRAIN INFLOW</text>

                <!-- Central CV Inspection Node -->
                <circle cx="210" cy="90" r="28" fill="#0f172a" stroke="{status_border}" stroke-width="3" style="filter: drop-shadow(0 0 8px {status_border});"/>
                <text x="210" y="87" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">CV AI</text>
                <text x="210" y="101" fill="{status_border}" font-size="9" font-weight="bold" text-anchor="middle">{purity_score}%</text>

                <!-- Upper Pipe: Clean River Route -->
                <path d="M 235 78 C 290 75, 310 35, 360 35 L 500 35" fill="none" stroke="{river_color}" stroke-width="8" stroke-linecap="round" style="box-shadow: {river_glow};"/>
                <!-- Lower Pipe: Dirty STP Route -->
                <path d="M 235 102 C 290 105, 310 145, 360 145 L 500 145" fill="none" stroke="{stp_color}" stroke-width="8" stroke-linecap="round" style="box-shadow: {stp_glow};"/>

                <!-- Upper Gate Label -->
                <rect x="360" y="15" width="160" height="40" rx="6" fill="#0f172a" stroke="{river_color}" stroke-width="1.5"/>
                <text x="440" y="32" fill="#e2e8f0" font-size="10" font-weight="bold" text-anchor="middle">KHAN RIVER DISCHARGE</text>
                <text x="440" y="47" fill="{river_color}" font-size="9" text-anchor="middle">{'[GATE OPEN: ACTIVE]' if river_active else '[CLOSED]'}</text>

                <!-- Lower Gate Label -->
                <rect x="360" y="125" width="160" height="40" rx="6" fill="#0f172a" stroke="{stp_color}" stroke-width="1.5"/>
                <text x="440" y="142" fill="#e2e8f0" font-size="10" font-weight="bold" text-anchor="middle">KABITHEDI STP 245 MLD</text>
                <text x="440" y="157" fill="{stp_color}" font-size="9" text-anchor="middle">{'[DIVERTING: ACTIVE]' if stp_active else '[STANDBY]'}</text>
            </svg>

            <div style="margin-top: 10px; font-size: 11px; color: #94a3b8; text-align: center;">
                <b>Automated Action:</b> <span style="color: {status_border}; font-weight: bold;">{status_text}</span>
            </div>
        </div>
        """
        return html

    @staticmethod
    def render_action_card(
        title_en: str,
        title_hi: str,
        desc_en: str,
        desc_hi: str,
        severity: str = "SAFE",
        timestamp: str = "Just now",
    ) -> str:
        """
        Bilingual high-visibility operational action card for municipal crews.
        Severity: 'SAFE', 'WARNING', 'CRITICAL'
        """
        color_map = {
            "SAFE": ("#00e676", "#00e67615", "✅ सामान्य (NORMAL)"),
            "WARNING": ("#ffab00", "#ffab0018", "⚠️ चेतावनी (WARNING)"),
            "CRITICAL": ("#ff1744", "#ff174422", "🚨 आपातकालीन अलर्ट (CRITICAL EMERGENCY)"),
        }
        border_col, bg_col, badge_text = color_map.get(severity, color_map["SAFE"])

        return f"""
        <div style="background-color: #0b1329; border-left: 6px solid {border_col}; border-top: 1px solid #1e293b; border-right: 1px solid #1e293b; border-bottom: 1px solid #1e293b; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; font-family: 'Segoe UI', Tahoma, sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 11px; font-weight: bold; background: {bg_col}; color: {border_col}; border: 1px solid {border_col}44; padding: 2px 8px; border-radius: 12px;">{badge_text}</span>
                <span style="font-size: 10px; color: #64748b;">🕒 {timestamp}</span>
            </div>
            <div style="font-size: 14px; font-weight: bold; color: #f8fafc; margin-bottom: 2px;">{title_en}</div>
            <div style="font-size: 13px; font-weight: 600; color: #38bdf8; margin-bottom: 6px;">{title_hi}</div>
            <div style="font-size: 12px; color: #94a3b8; line-height: 1.4;">{desc_en}</div>
            <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px; line-height: 1.4;">{desc_hi}</div>
        </div>
        """

    @staticmethod
    def generate_citizen_sms_broadcast(
        area_name: str,
        area_hi: str,
        water_level_pct: float,
        rainfall_mm_hr: float,
        shelter_location: str = "होलकर स्टेडियम / ब्रिलियंट कन्वेंशन सेंटर",
    ) -> Dict[str, str]:
        """
        GenAI bilingual emergency SMS broadcast text for citizens of Indore.
        """
        sms_hindi = (
            f"🚨 [इंदौर नगर निगम - बाढ़ चेतावनी]\n"
            f"क्षेत्र: {area_hi} में भारी वर्षा ({rainfall_mm_hr} मिमी/घंटा) के कारण जलस्तर {water_level_pct}% पहुंच गया है। "
            f"कृपया निचले इलाकों से सुरक्षित ऊंचे स्थानों की ओर जाएं। "
            f"निकटतम सुरक्षित आश्रय: {shelter_location}। "
            f"आपातकालीन सहायता: 112 या IMC कंट्रोल रूम: 0731-2535555।"
        )

        sms_english = (
            f"🚨 [IMC FLOOD ALERT - INDORE]\n"
            f"Location: {area_name}. Severe rain ({rainfall_mm_hr} mm/hr) has raised drain water level to {water_level_pct}%. "
            f"Please avoid waterlogged subways and low-lying river banks. "
            f"Safe Shelter: {shelter_location}. "
            f"Emergency Helpline: 112 | IMC Control Room: 0731-2535555."
        )

        return {"hindi": sms_hindi, "english": sms_english}

    @staticmethod
    def generate_evacuation_qr_pass(
        citizen_id: str = "IND-IMC-2026-904",
        node_name: str = "Rajwada / Krishnapura Basin",
        shelter_name: str = "Holkar Stadium High-Ground Shelter, Indore",
    ) -> io.BytesIO:
        """
        Generate a scannable QR code containing digital evacuation pass and emergency geo-coordinates.
        """
        payload = (
            f"https://smartindore.gov.in/evacuate?"
            f"pass_id={citizen_id}&"
            f"zone={node_name}&"
            f"shelter={shelter_name}&"
            f"emergency_contact=07312535555"
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#00e5ff", back_color="#0a0f1d")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf


# Global widgets instance
gauge_widgets = GaugeWidgets()

