"""
SQLite Database Persistence Layer for HYDRO-GUARD AI.
Stores Computer Vision water purity analyses, Librosa acoustic flow analyses,
and periodic telemetry snapshots for historical auditing and compliance.
Uses Python's standard library `sqlite3` with parameterized queries and graceful fallbacks.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import config

logger = logging.getLogger("hydro_guard.db")


class DatabaseManager:
    """Thread-safe SQLite database manager for HYDRO-GUARD AI."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.DB_PATH
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys enabled and row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        try:
            with self._get_connection() as conn:
                # 1. Analysis Logs (Image CV & Acoustic Hydrophone analyses)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analysis_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        input_source TEXT,
                        primary_metric REAL NOT NULL,
                        secondary_metric REAL,
                        status_verdict TEXT NOT NULL,
                        gate_action TEXT NOT NULL,
                        details_json TEXT
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analysis_type_ts ON analysis_logs(analysis_type, timestamp DESC);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analysis_ts ON analysis_logs(timestamp DESC);"
                )

                # 2. Telemetry Logs (Historical IoT basin snapshots)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS telemetry_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        city_avg_water_level_pct REAL NOT NULL,
                        peak_risk_node TEXT NOT NULL,
                        peak_risk_level_pct REAL NOT NULL,
                        rainfall_intensity_mm_hr REAL DEFAULT 0.0,
                        nodes_snapshot_json TEXT
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry_logs(timestamp DESC);"
                )
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize SQLite database: {e}")

    def log_image_analysis(
        self,
        input_source: str,
        purity_score: float,
        is_clean: bool,
        gate_action: str,
        turbidity_estimate: Optional[float] = None,
        debris_count: int = 0,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Record a successful CV water purity screening result.
        Returns the new record ID, or None if logging failed.
        """
        try:
            status_verdict = "PASS" if is_clean else "FAIL"
            now_iso = datetime.now(timezone.utc).isoformat()
            details_str = json.dumps(details or {})

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO analysis_logs (
                        analysis_type, timestamp, input_source, primary_metric,
                        secondary_metric, status_verdict, gate_action, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        "IMAGE_PURITY",
                        now_iso,
                        str(input_source)[:255],
                        float(purity_score),
                        float(turbidity_estimate) if turbidity_estimate is not None else 0.0,
                        status_verdict,
                        str(gate_action)[:255],
                        details_str,
                    ),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to insert image analysis log: {e}")
            return None

    def log_audio_analysis(
        self,
        input_source: str,
        decibels_db: float,
        inferred_level_pct: float,
        flow_regime: str,
        dominant_frequency_hz: Optional[float] = None,
        alert_status: str = "SAFE",
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Record a successful acoustic culvert flow analysis result.
        Returns the new record ID, or None if logging failed.
        """
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            gate_action = "SURGE PRE-WARNING" if inferred_level_pct > 75 else "NORMAL FLOW"
            details_str = json.dumps(details or {})

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO analysis_logs (
                        analysis_type, timestamp, input_source, primary_metric,
                        secondary_metric, status_verdict, gate_action, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        "ACOUSTIC_LEVEL",
                        now_iso,
                        str(input_source)[:255],
                        float(inferred_level_pct),
                        float(decibels_db),
                        str(alert_status),
                        gate_action,
                        details_str,
                    ),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to insert acoustic analysis log: {e}")
            return None

    def log_telemetry_snapshot(
        self,
        city_avg_pct: float,
        peak_node: str,
        peak_level_pct: float,
        rainfall_intensity: float = 0.0,
        nodes_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """Record periodic basin IoT telemetry state."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            snapshot_str = json.dumps(nodes_snapshot or {})

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO telemetry_logs (
                        timestamp, city_avg_water_level_pct, peak_risk_node,
                        peak_risk_level_pct, rainfall_intensity_mm_hr, nodes_snapshot_json
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        now_iso,
                        float(city_avg_pct),
                        str(peak_node)[:255],
                        float(peak_level_pct),
                        float(rainfall_intensity),
                        snapshot_str,
                    ),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to insert telemetry snapshot log: {e}")
            return None

    def get_recent_analyses(
        self, limit: int = 50, offset: int = 0, analysis_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve recent image and acoustic analysis records with pagination."""
        try:
            limit = max(1, min(limit, 500))
            offset = max(0, offset)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                if analysis_type:
                    cursor.execute(
                        """
                        SELECT id, analysis_type, timestamp, input_source, primary_metric,
                               secondary_metric, status_verdict, gate_action, details_json
                        FROM analysis_logs
                        WHERE analysis_type = ?
                        ORDER BY id DESC
                        LIMIT ? OFFSET ?;
                        """,
                        (analysis_type, limit, offset),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, analysis_type, timestamp, input_source, primary_metric,
                               secondary_metric, status_verdict, gate_action, details_json
                        FROM analysis_logs
                        ORDER BY id DESC
                        LIMIT ? OFFSET ?;
                        """,
                        (limit, offset),
                    )
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    details = {}
                    if row["details_json"]:
                        try:
                            details = json.loads(row["details_json"])
                        except Exception:
                            pass
                    results.append({
                        "id": row["id"],
                        "analysis_type": row["analysis_type"],
                        "timestamp": row["timestamp"],
                        "input_source": row["input_source"],
                        "primary_metric": row["primary_metric"],
                        "secondary_metric": row["secondary_metric"],
                        "status_verdict": row["status_verdict"],
                        "gate_action": row["gate_action"],
                        "details": details,
                    })
                return results
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch analysis records: {e}")
            return []

    def get_recent_telemetry_logs(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve historical telemetry snapshots."""
        try:
            limit = max(1, min(limit, 500))
            offset = max(0, offset)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, timestamp, city_avg_water_level_pct, peak_risk_node,
                           peak_risk_level_pct, rainfall_intensity_mm_hr, nodes_snapshot_json
                    FROM telemetry_logs
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?;
                    """,
                    (limit, offset),
                )
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    nodes = {}
                    if row["nodes_snapshot_json"]:
                        try:
                            nodes = json.loads(row["nodes_snapshot_json"])
                        except Exception:
                            pass
                    results.append({
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "city_avg_water_level_pct": row["city_avg_water_level_pct"],
                        "peak_risk_node": row["peak_risk_node"],
                        "peak_risk_level_pct": row["peak_risk_level_pct"],
                        "rainfall_intensity_mm_hr": row["rainfall_intensity_mm_hr"],
                        "nodes": nodes,
                    })
                return results
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch telemetry records: {e}")
            return []

    def get_db_stats(self) -> Dict[str, Any]:
        """Return diagnostic metrics about database state."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM analysis_logs;")
                analyses_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM telemetry_logs;")
                telemetry_count = cursor.fetchone()[0]

                file_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0

                return {
                    "database_file": str(self.db_path),
                    "file_exists": self.db_path.exists(),
                    "file_size_bytes": file_size_bytes,
                    "total_analysis_records": analyses_count,
                    "total_telemetry_records": telemetry_count,
                    "status": "HEALTHY",
                }
        except Exception as e:
            return {
                "database_file": str(self.db_path),
                "file_exists": self.db_path.exists(),
                "error": str(e),
                "status": "DEGRADED",
            }


# Global singleton instance
db_manager = DatabaseManager()

