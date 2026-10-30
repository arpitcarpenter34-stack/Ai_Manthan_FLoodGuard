"""
Open-Meteo Weather Service Client for Indore, Madhya Pradesh.
Fetches real-time precipitation, humidity, temperature, and hourly rain forecasts.
Includes hydrological runoff calculation and offline fallback simulation.
"""

import time
import requests
from typing import Dict, Any, List
import config


class OpenMeteoClient:
    """Client for Open-Meteo API tailored for Indore urban catchment."""

    def __init__(self, lat: float = config.INDORE_CENTER_LAT, lon: float = config.INDORE_CENTER_LON):
        self.lat = lat
        self.lon = lon
        self.base_url = config.OPEN_METEO_URL
        self._cache_data: Dict[str, Any] = {}
        self._cache_timestamp: float = 0.0
        self.cache_ttl: float = config.WEATHER_CACHE_TTL_SEC

    def fetch_live_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch real-time weather and precipitation for Indore.
        Returns cached data if within TTL. Fallback to realistic hydrological model on error.
        """
        now = time.time()
        if not force_refresh and self._cache_data and (now - self._cache_timestamp < self.cache_ttl):
            return self._cache_data

        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m,surface_pressure",
            "hourly": "precipitation,rain,relative_humidity_2m",
            "forecast_days": 1,
            "timezone": "Asia/Kolkata",
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=4.0)
            if response.status_code == 200:
                data = response.json()
                parsed = self._parse_api_response(data)
                self._cache_data = parsed
                self._cache_timestamp = now
                return parsed
        except Exception as exc:
            # Graceful fallback to meteorological simulation for offline/sandboxed execution
            pass

        simulated = self._generate_fallback_weather()
        self._cache_data = simulated
        self._cache_timestamp = now
        return simulated

    def _parse_api_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured hydrological fields from raw Open-Meteo response."""
        current = data.get("current", {})
        hourly = data.get("hourly", {})

        precip_mm = float(current.get("precipitation", 0.0))
        rain_mm = float(current.get("rain", 0.0))
        effective_rain = max(precip_mm, rain_mm)

        temp_c = float(current.get("temperature_2m", 28.5))
        humidity_pct = float(current.get("relative_humidity_2m", 75.0))
        wind_speed_kmh = float(current.get("wind_speed_10m", 12.0))
        weather_code = int(current.get("weather_code", 0))

        # Hourly rain forecast for next 6 hours
        hourly_precip = hourly.get("precipitation", [])[:6]
        hourly_times = hourly.get("time", [])[:6]
        forecast_6h = [
            {"time": t, "rain_mm": float(r)}
            for t, r in zip(hourly_times, hourly_precip)
        ]

        category = self._categorize_rainfall(effective_rain)
        runoff_factor = self._estimate_runoff_coefficient(effective_rain, humidity_pct)

        return {
            "city": "Indore",
            "state": "Madhya Pradesh",
            "latitude": self.lat,
            "longitude": self.lon,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S IST", time.localtime()),
            "rainfall_intensity_mm_hr": effective_rain,
            "rainfall_category": category,
            "temperature_c": temp_c,
            "relative_humidity_pct": humidity_pct,
            "wind_speed_kmh": wind_speed_kmh,
            "weather_code": weather_code,
            "runoff_coefficient": runoff_factor,
            "forecast_6h": forecast_6h,
            "is_live_api": True,
            "data_source": "Open-Meteo Live API",
        }

    def _generate_fallback_weather(self) -> Dict[str, Any]:
        """Realistic monsoon/pre-monsoon hydrological model for Indore."""
        # Indore historical monsoon pattern: periodic shower surges (12 - 28 mm/hr)
        cycle_minute = (time.time() / 60) % 30
        if cycle_minute < 10:
            rain = 4.2
        elif cycle_minute < 20:
            rain = 18.5  # Heavy burst in South Indore
        else:
            rain = 8.0

        return {
            "city": "Indore",
            "state": "Madhya Pradesh",
            "latitude": self.lat,
            "longitude": self.lon,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S IST", time.localtime()),
            "rainfall_intensity_mm_hr": round(rain, 2),
            "rainfall_category": self._categorize_rainfall(rain),
            "temperature_c": 27.8,
            "relative_humidity_pct": 82.0,
            "wind_speed_kmh": 14.5,
            "weather_code": 61,  # Rain, slight/moderate
            "runoff_coefficient": 0.72,
            "forecast_6h": [
                {"time": f"+{i}h", "rain_mm": max(0.0, round(rain * (0.85 ** i), 1))}
                for i in range(1, 7)
            ],
            "is_live_api": False,
            "data_source": "Simulated Monsoon Model (Offline Fallback)",
        }

    def _categorize_rainfall(self, rain_mm: float) -> str:
        """Classify rainfall intensity according to IMD / Urban Drainage Standards."""
        if rain_mm <= 0.1:
            return "No Rain (शुष्क)"
        elif rain_mm <= config.RAIN_LIGHT_MAX:
            return "Light Rain (हल्की वर्षा)"
        elif rain_mm <= config.RAIN_MODERATE_MAX:
            return "Moderate Rain (मध्यम वर्षा)"
        elif rain_mm <= config.RAIN_HEAVY_MAX:
            return "Heavy Rain (भारी वर्षा)"
        else:
            return "Severe Torrential (अति भारी वर्षा - अलर्ट)"

    def _estimate_runoff_coefficient(self, rain_mm: float, humidity_pct: float) -> float:
        """
        Rational Method Runoff Coefficient C:
        Indore urban soil (black cotton soil with 65-75% paved impervious asphalt/concrete).
        """
        base_c = 0.65
        if humidity_pct > 80:
            base_c += 0.10  # Saturated antecedent moisture condition (AMC III)
        if rain_mm > 15.0:
            base_c += 0.08
        return min(0.92, round(base_c, 2))


# Global client instance
weather_client = OpenMeteoClient()

