"""
OpenCV Water Purity & Automated Split-Pipe Gate Diversion AI.
Analyzes drain outfall images for color, turbidity, and floating solid debris.
Enforces the mandatory 80% Purity Rule:
  * Purity >= 80%: "GATE OPEN TO KHAN RIVER" (Clean Rainwater harvesting / river discharge)
  * Purity < 80%:  "DIVERTING TO STP / FILTRATION BASIN" (Polluted sewage diverted to Kabithedi)
"""

import base64
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import config


class CVPurityDetector:
    """
    Computer Vision water clarity, turbidity, and debris detection analyzer.
    Integrates OpenCV colorimetry and morphological solid detection.
    """

    def __init__(self, purity_threshold: float = config.PURITY_THRESHOLD_PCT):
        self.purity_threshold = purity_threshold

    def analyze_image(self, image_input: Any) -> Dict[str, Any]:
        """
        Analyze an image (path, bytes, or numpy ndarray) and return comprehensive purity telemetry.
        Handles grayscale, corrupt, or empty images gracefully.
        """
        img = self._load_image(image_input)
        if img is None or not isinstance(img, np.ndarray) or img.size == 0:
            return {
                "error": "Failed to decode input image or image is empty/corrupt",
                "purity_score": 0.0,
                "gate_status": config.GATE_DIRTY_ACTION,
                "gate_color": "#ff1744",
                "is_clean": False,
                "destination": "Kabithedi 245 MLD STP / Biological Filtration Basins",
                "hindi_action": "छवि अमान्य - सुरक्षात्मक डिफ़ॉल्ट: एसटीपी हेतु डायवर्ट",
                "turbidity_index": 100.0,
                "debris_coverage_pct": 0.0,
                "detected_debris_count": 0,
                "screening_mode": "PROTOTYPE_SIMULATION",
                "disclaimer": "Colorimetric screening prototype. Physical gate remains in simulation mode.",
            }

        # Step 1: Preprocessing & Channel Normalization
        if len(img.shape) == 2:
            # Grayscale to BGR
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            # BGRA to BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        h, w = img.shape[:2]
        resized = cv2.resize(img, (640, 480))
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Step 2: Turbidity / Clarity Analysis
        # High turbidity in storm drains corresponds to brown/grey/black tones, low saturation,
        # and high local contrast variance from suspended solids.
        turbidity_score, clarity_score = self._compute_turbidity(resized, hsv, gray)

        # Step 3: Floating Debris & Solid Waste Contours
        debris_mask, debris_pct, debris_boxes = self._detect_debris(resized, gray)

        # Step 4: Overall Purity Score (0 to 100%)
        # Weighted blend: Clarity (55%) + Inverse Turbidity (25%) + Debris-Free Factor (20%)
        debris_penalty = min(40.0, debris_pct * 4.0)
        purity_score = round(max(0.0, min(100.0, (clarity_score * 0.55) + ((100.0 - turbidity_score) * 0.25) - debris_penalty + 20.0)), 1)

        # Step 5: Enforce the 80% Purity Rule
        is_clean = bool(purity_score >= self.purity_threshold)
        if is_clean:
            gate_status = config.GATE_CLEAN_ACTION
            gate_color = "#00e676"  # Green
            destination = "Khan River Main Basin (River Rejuvenation & Clean Recharge)"
            hindi_action = "शुद्ध वर्षा जल - खान नदी मुख्य चैनल हेतु गेट खोला गया"
        else:
            gate_status = config.GATE_DIRTY_ACTION
            gate_color = "#ff1744"  # Red / Amber
            destination = "Kabithedi 245 MLD STP / Biological Filtration Basins"
            hindi_action = "प्रदूषित सीवरेज जल - कबीटखेड़ी एसटीपी व शोधन बेसिन हेतु डायवर्ट"

        # Step 6: Generate visual annotated frame with bounding boxes and HUD
        annotated = resized.copy()
        for (x, y, bw, bh) in debris_boxes:
            cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
            cv2.putText(annotated, "Debris", (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # Overlay Telemetry HUD
        hud_color = (0, 230, 118) if is_clean else (0, 0, 255)
        cv2.putText(annotated, f"PURITY: {purity_score}% (Threshold: {self.purity_threshold}%)", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, hud_color, 2)
        cv2.putText(annotated, f"ACTION: {gate_status}", (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, hud_color, 2)
        cv2.putText(annotated, f"Turbidity: {turbidity_score:.1f} | Debris Area: {debris_pct:.1f}%", (15, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)

        _, buf = cv2.imencode(".jpg", annotated)
        annotated_b64 = base64.b64encode(buf).decode("utf-8")

        return {
            "purity_score": purity_score,
            "threshold_rule_pct": self.purity_threshold,
            "is_clean": is_clean,
            "gate_status": gate_status,
            "gate_color": gate_color,
            "destination": destination,
            "hindi_action": hindi_action,
            "turbidity_index": round(turbidity_score, 1),
            "debris_coverage_pct": round(debris_pct, 2),
            "detected_debris_count": len(debris_boxes),
            "annotated_frame_b64": annotated_b64,
            "screening_mode": "PROTOTYPE_SIMULATION",
            "disclaimer": "Colorimetric screening prototype. Physical gate remains in simulation mode.",
        }

    def _load_image(self, image_input: Any) -> Optional[np.ndarray]:
        """Helper to safely ingest diverse image formats (file path, raw bytes, or numpy)."""
        if isinstance(image_input, np.ndarray):
            return image_input
        elif isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if path.exists():
                return cv2.imread(str(path))
        elif isinstance(image_input, (bytes, bytearray)):
            nparr = np.frombuffer(image_input, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return None

    def _compute_turbidity(self, bgr: np.ndarray, hsv: np.ndarray, gray: np.ndarray) -> Tuple[float, float]:
        """
        Measure water optical turbidity vs clean chromatic clarity.
        Clean rainwater exhibits higher blue/cyan/white specular highlights and low muddy brown chroma.
        Polluted wastewater / sludge exhibits dark blackish-grey or brown hue with high suspended solids variance.
        """
        # Hue, Saturation, Value channels
        h_chan, s_chan, v_chan = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        # Brown/sludge mask in HSV (H: 10-30, S: 50-255, V: 30-180)
        brown_lower = np.array([8, 40, 25])
        brown_upper = np.array([32, 255, 180])
        brown_mask = cv2.inRange(hsv, brown_lower, brown_upper)
        brown_pct = (np.count_nonzero(brown_mask) / brown_mask.size) * 100.0

        # Dark sewage mask (Low V and Low S)
        dark_lower = np.array([0, 0, 0])
        dark_upper = np.array([180, 80, 50])
        dark_mask = cv2.inRange(hsv, dark_lower, dark_upper)
        dark_pct = (np.count_nonzero(dark_mask) / dark_mask.size) * 100.0

        # Laplacian texture variance (high variance = many small suspended solid specks/turbulence)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_var = float(laplacian.var())
        texture_turbidity = min(100.0, texture_var / 8.0)

        # Composite Turbidity Index (0 to 100)
        turbidity_index = min(100.0, (brown_pct * 0.5) + (dark_pct * 0.3) + (texture_turbidity * 0.2))

        # Chromatic clarity (blue/cyan clean water or clear aerated reflection)
        blue_lower = np.array([85, 30, 70])
        blue_upper = np.array([135, 255, 255])
        blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
        clean_hue_pct = (np.count_nonzero(blue_mask) / blue_mask.size) * 100.0

        clarity_score = max(5.0, min(100.0, 100.0 - turbidity_index + (clean_hue_pct * 0.4)))
        return turbidity_index, clarity_score

    def _detect_debris(self, bgr: np.ndarray, gray: np.ndarray) -> Tuple[np.ndarray, float, List[Tuple[int, int, int, int]]]:
        """Identify discrete floating garbage, plastic bottles, or debris patches."""
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        # Adaptive edge detection for unnatural floating objects
        edges = cv2.Canny(blurred, 60, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        debris_boxes = []
        total_debris_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 150 < area < 15000:  # Size filter for floating trash objects
                x, y, w, h = cv2.boundingRect(cnt)
                debris_boxes.append((x, y, w, h))
                total_debris_area += area

        debris_pct = (total_debris_area / (gray.shape[0] * gray.shape[1])) * 100.0
        return closed, debris_pct, debris_boxes

    def generate_synthetic_drain_frame(self, frame_type: str = "clean_rainwater") -> np.ndarray:
        """
        Generate synthetic high-fidelity camera frames for demonstration and testing.
        Types:
          - 'clean_rainwater': High purity (~88-94%), blue-cyan ripples, clear water -> GATE OPEN TO KHAN RIVER
          - 'polluted_sludge': Low purity (~35-50%), brown muddy effluent, floating waste -> DIVERTING TO STP
          - 'borderline_runoff': Moderate purity (~76-81%), slight turbidity
        """
        img = np.zeros((480, 640, 3), dtype=np.uint8)

        if frame_type == "clean_rainwater":
            # Flowing clean rainwater with light reflections
            base_color = np.array([170, 140, 40], dtype=np.uint8)  # Blueish water in BGR
            noise = np.random.normal(0, 12, (480, 640, 3)).astype(np.int16)
            canvas = np.clip(base_color + noise, 0, 255).astype(np.uint8)

            # Add gentle water ripples
            for y in range(0, 480, 25):
                cv2.ellipse(canvas, (320, y), (280, 15), 0, 0, 360, (210, 185, 90), 2)
            return canvas

        elif frame_type == "polluted_sludge":
            # Dark sewage, brown turbidity, and floating trash/plastic objects
            base_color = np.array([25, 45, 65], dtype=np.uint8)  # Dirty brown-black in BGR
            noise = np.random.normal(0, 22, (480, 640, 3)).astype(np.int16)
            canvas = np.clip(base_color + noise, 0, 255).astype(np.uint8)

            # Add floating debris (simulated bottles/plastic debris)
            np.random.seed(42)
            for _ in range(6):
                px = np.random.randint(60, 580)
                py = np.random.randint(60, 420)
                pw = np.random.randint(25, 65)
                ph = np.random.randint(18, 45)
                # Bright trash color (e.g., white polystyrene or red plastic)
                cv2.rectangle(canvas, (px, py), (px + pw, py + ph), (220, 220, 240), -1)
                cv2.circle(canvas, (px + 10, py + 10), 6, (40, 40, 220), -1)
            return canvas

        else:
            # Borderline storm runoff
            base_color = np.array([80, 95, 110], dtype=np.uint8)
            noise = np.random.normal(0, 15, (480, 640, 3)).astype(np.int16)
            return np.clip(base_color + noise, 0, 255).astype(np.uint8)


# Global detector instance
cv_detector = CVPurityDetector()
