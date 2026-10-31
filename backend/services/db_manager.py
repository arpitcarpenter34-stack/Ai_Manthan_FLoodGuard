"""
SQLite Database Persistence Layer for HYDRO-GUARD AI.
Stores Computer Vision water purity analyses, Librosa acoustic flow analyses,
and periodic telemetry snapshots for historical auditing and compliance.
Uses Python's standard library `sqlite3` with parameterized queries and graceful fallbacks.
"""

import json
import logging
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import config

logger = logging.getLogger("hydro_guard.db")
_init_lock = threading.Lock()


class DatabaseManager:
    """Thread-safe SQLite database manager for HYDRO-GUARD AI."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else config.DB_PATH
        self._ensure_database_ready()
        self.init_db()

    def _ensure_database_ready(self) -> None:
        """
        Thread-safe verification and initialization of the database file.
        If a persistent storage path is configured (different from seed) and the target
        database does not exist yet, atomically initialize it from the repository seed database.
        Never overwrites an existing persistent database on restart or redeployment.
        """
        with _init_lock:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            target_abs = str(self.db_path.absolute())
            seed_abs = str(config.SEED_DB_PATH.absolute())

            # Only copy seed if target is at a different location and does not exist yet
            if target_abs != seed_abs and not self.db_path.exists():
                if config.SEED_DB_PATH.exists():
                    logger.info(
                        f"Initializing persistent database at {self.db_path} from seed {config.SEED_DB_PATH}"
                    )
                    temp_init = self.db_path.with_suffix(".tmp_init")
                    try:
                        shutil.copy2(str(config.SEED_DB_PATH), str(temp_init))
                        temp_init.replace(self.db_path)
                        logger.info(f"Successfully initialized persistent database at {self.db_path}")
                    except Exception as e:
                        logger.error(f"Failed to copy seed database to {self.db_path}: {e}")
                        if temp_init.exists():
                            try:
                                temp_init.unlink(missing_ok=True)
                            except Exception:
                                pass
                else:
                    logger.warning(
                        f"Seed database not found at {config.SEED_DB_PATH}. Will initialize clean schema."
                    )

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys enabled, busy timeout, and row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 30000;")
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

                # 3. Drainage Segments (Topographical GIS network segments)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS drainage_segments (
                        id TEXT PRIMARY KEY,
                        city_id TEXT NOT NULL,
                        segment_code TEXT NOT NULL,
                        name TEXT NOT NULL,
                        source_node TEXT,
                        target_node TEXT,
                        channel_type TEXT,
                        coordinates_geojson TEXT,
                        start_lat REAL NOT NULL,
                        start_lon REAL NOT NULL,
                        end_lat REAL NOT NULL,
                        end_lon REAL NOT NULL,
                        mid_lat REAL NOT NULL,
                        mid_lon REAL NOT NULL,
                        elevation_m REAL DEFAULT 0.0,
                        length_m REAL DEFAULT 0.0,
                        slope REAL DEFAULT 0.0,
                        manning_velocity_m_s REAL DEFAULT 0.0,
                        max_capacity_m3_s REAL DEFAULT 0.0,
                        created_at TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_drainage_city ON drainage_segments(city_id);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_drainage_code ON drainage_segments(segment_code);"
                )

                # 4. Blockage Observations (Evidence-based inspection and telemetry verdicts)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blockage_observations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        segment_id TEXT NOT NULL,
                        city_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        confidence_score REAL DEFAULT 0.0,
                        debris_coverage_pct REAL DEFAULT 0.0,
                        silt_depth_cm REAL DEFAULT 0.0,
                        flow_velocity_pct REAL DEFAULT 100.0,
                        water_level_pct REAL DEFAULT 0.0,
                        evidence_summary TEXT,
                        evidence_type TEXT NOT NULL,
                        observation_date TEXT NOT NULL,
                        inspector_name TEXT,
                        action_recommended TEXT,
                        data_source TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (segment_id) REFERENCES drainage_segments(id) ON DELETE CASCADE
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_blockage_segment ON blockage_observations(segment_id);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_blockage_city_status ON blockage_observations(city_id, status);"
                )

                # 5. Drainage Images (Photographic evidence and OpenCV screening metadata)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS drainage_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        segment_id TEXT NOT NULL,
                        image_path TEXT NOT NULL,
                        caption TEXT,
                        capture_date TEXT,
                        image_source TEXT,
                        opencv_analyzed INTEGER DEFAULT 0,
                        debris_pct REAL DEFAULT 0.0,
                        turbidity_score REAL DEFAULT 0.0,
                        purity_score REAL DEFAULT 0.0,
                        annotated_path TEXT,
                        is_blockage_evidence INTEGER DEFAULT 0,
                        notes TEXT,
                        FOREIGN KEY (segment_id) REFERENCES drainage_segments(id) ON DELETE CASCADE
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_drain_img_segment ON drainage_images(segment_id);"
                )

                # 6. Blockage Reports (Historical audit log of generated PDF and CSV reports)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blockage_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_type TEXT NOT NULL,
                        city_id TEXT NOT NULL,
                        segment_id TEXT,
                        generated_at TEXT NOT NULL,
                        report_title TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size_bytes INTEGER DEFAULT 0,
                        summary_json TEXT
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_reports_city_type ON blockage_reports(city_id, report_type);"
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

                cursor.execute("SELECT COUNT(*) FROM drainage_segments;")
                segments_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM blockage_observations;")
                blockages_count = cursor.fetchone()[0]

                file_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0

                target_abs = str(self.db_path.absolute())
                seed_abs = str(config.SEED_DB_PATH.absolute())

                return {
                    "database_file": str(self.db_path),
                    "seed_database_file": str(config.SEED_DB_PATH),
                    "file_exists": self.db_path.exists(),
                    "file_size_bytes": file_size_bytes,
                    "total_analysis_records": analyses_count,
                    "total_telemetry_records": telemetry_count,
                    "total_drainage_segments": segments_count,
                    "total_blockage_observations": blockages_count,
                    "is_persistent_custom_path": target_abs != seed_abs,
                    "status": "HEALTHY",
                }
        except Exception as e:
            return {
                "database_file": str(self.db_path),
                "file_exists": self.db_path.exists(),
                "error": str(e),
                "status": "DEGRADED",
            }

    # =========================================================================
    # DRAINAGE BLOCKAGE MONITORING & GIS EXTENSION METHODS
    # =========================================================================

    def upsert_drainage_segment(self, segment: Dict[str, Any]) -> bool:
        """Insert or replace a drainage network segment record."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            coords_json = json.dumps(segment.get("coordinates", []))

            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO drainage_segments (
                        id, city_id, segment_code, name, source_node, target_node,
                        channel_type, coordinates_geojson, start_lat, start_lon,
                        end_lat, end_lon, mid_lat, mid_lon, elevation_m, length_m,
                        slope, manning_velocity_m_s, max_capacity_m3_s, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        city_id = excluded.city_id,
                        segment_code = excluded.segment_code,
                        name = excluded.name,
                        source_node = excluded.source_node,
                        target_node = excluded.target_node,
                        channel_type = excluded.channel_type,
                        coordinates_geojson = excluded.coordinates_geojson,
                        start_lat = excluded.start_lat,
                        start_lon = excluded.start_lon,
                        end_lat = excluded.end_lat,
                        end_lon = excluded.end_lon,
                        mid_lat = excluded.mid_lat,
                        mid_lon = excluded.mid_lon,
                        elevation_m = excluded.elevation_m,
                        length_m = excluded.length_m,
                        slope = excluded.slope,
                        manning_velocity_m_s = excluded.manning_velocity_m_s,
                        max_capacity_m3_s = excluded.max_capacity_m3_s;
                    """,
                    (
                        segment["id"],
                        segment["city_id"],
                        segment["segment_code"],
                        segment["name"],
                        segment.get("source_node"),
                        segment.get("target_node"),
                        segment.get("channel_type", "Culvert / Open Canal"),
                        coords_json,
                        float(segment["start_lat"]),
                        float(segment["start_lon"]),
                        float(segment["end_lat"]),
                        float(segment["end_lon"]),
                        float(segment.get("mid_lat", (segment["start_lat"] + segment["end_lat"]) / 2)),
                        float(segment.get("mid_lon", (segment["start_lon"] + segment["end_lon"]) / 2)),
                        float(segment.get("elevation_m", 0.0)),
                        float(segment.get("length_m", 0.0)),
                        float(segment.get("slope", 0.0)),
                        float(segment.get("manning_velocity_m_s", 0.0)),
                        float(segment.get("max_capacity_m3_s", 0.0)),
                        now_iso,
                    ),
                )
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to upsert drainage segment: {e}")
            return False

    def get_drainage_segments(
        self, city_id: Optional[str] = None, status: Optional[str] = None, risk: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve drainage segments filtered by city, blockage status, or risk level."""
        try:
            query = """
                SELECT s.id, s.city_id, s.segment_code, s.name, s.source_node, s.target_node,
                       s.channel_type, s.coordinates_geojson, s.start_lat, s.start_lon,
                       s.end_lat, s.end_lon, s.mid_lat, s.mid_lon, s.elevation_m, s.length_m,
                       s.slope, s.manning_velocity_m_s, s.max_capacity_m3_s, s.created_at,
                       b.status AS latest_status, b.risk_level, b.confidence_score,
                       b.debris_coverage_pct, b.silt_depth_cm, b.flow_velocity_pct,
                       b.water_level_pct, b.evidence_summary, b.evidence_type,
                       b.observation_date, b.action_recommended, b.data_source
                FROM drainage_segments s
                LEFT JOIN (
                    SELECT o1.*
                    FROM blockage_observations o1
                    INNER JOIN (
                        SELECT segment_id, MAX(id) as max_id
                        FROM blockage_observations
                        GROUP BY segment_id
                    ) o2 ON o1.id = o2.max_id
                ) b ON s.id = b.segment_id
                WHERE 1=1
            """
            params: List[Any] = []

            if city_id and city_id.lower() != "all":
                query += " AND LOWER(s.city_id) = ?"
                params.append(city_id.lower())

            if status and status.upper() != "ALL":
                query += " AND UPPER(COALESCE(b.status, 'INSUFFICIENT_DATA')) = ?"
                params.append(status.upper())

            if risk and risk.upper() != "ALL":
                query += " AND UPPER(COALESCE(b.risk_level, 'UNKNOWN')) = ?"
                params.append(risk.upper())

            query += " ORDER BY s.segment_code ASC;"

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                segments = []
                for row in rows:
                    coords = []
                    if row["coordinates_geojson"]:
                        try:
                            coords = json.loads(row["coordinates_geojson"])
                        except Exception:
                            pass
                    segments.append({
                        "id": row["id"],
                        "city_id": row["city_id"],
                        "segment_code": row["segment_code"],
                        "name": row["name"],
                        "source_node": row["source_node"],
                        "target_node": row["target_node"],
                        "channel_type": row["channel_type"],
                        "coordinates": coords,
                        "start_lat": row["start_lat"],
                        "start_lon": row["start_lon"],
                        "end_lat": row["end_lat"],
                        "end_lon": row["end_lon"],
                        "mid_lat": row["mid_lat"],
                        "mid_lon": row["mid_lon"],
                        "elevation_m": row["elevation_m"],
                        "length_m": row["length_m"],
                        "slope": row["slope"],
                        "manning_velocity_m_s": row["manning_velocity_m_s"],
                        "max_capacity_m3_s": row["max_capacity_m3_s"],
                        "created_at": row["created_at"],
                        "status": row["latest_status"] or "INSUFFICIENT_DATA",
                        "risk_level": row["risk_level"] or "UNKNOWN",
                        "confidence_score": row["confidence_score"] or 0.0,
                        "debris_coverage_pct": row["debris_coverage_pct"] or 0.0,
                        "silt_depth_cm": row["silt_depth_cm"] or 0.0,
                        "flow_velocity_pct": row["flow_velocity_pct"] or 100.0,
                        "water_level_pct": row["water_level_pct"] or 0.0,
                        "evidence_summary": row["evidence_summary"] or "No field inspection observation recorded.",
                        "evidence_type": row["evidence_type"] or "NONE",
                        "observation_date": row["observation_date"] or "N/A",
                        "action_recommended": row["action_recommended"] or "Routine monitoring.",
                        "data_source": row["data_source"] or "Topographical Baseline",
                    })
                return segments
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch drainage segments: {e}")
            return []

    def get_drainage_segment(self, segment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single drainage segment by ID."""
        segments = self.get_drainage_segments()
        for s in segments:
            if s["id"] == segment_id or s["segment_code"] == segment_id:
                return s
        return None

    def insert_blockage_observation(self, obs: Dict[str, Any]) -> Optional[int]:
        """Record a blockage inspection or telemetry-derived observation."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO blockage_observations (
                        segment_id, city_id, status, risk_level, confidence_score,
                        debris_coverage_pct, silt_depth_cm, flow_velocity_pct,
                        water_level_pct, evidence_summary, evidence_type, observation_date,
                        inspector_name, action_recommended, data_source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        obs["segment_id"],
                        obs["city_id"],
                        obs["status"],
                        obs["risk_level"],
                        float(obs.get("confidence_score", 0.8)),
                        float(obs.get("debris_coverage_pct", 0.0)),
                        float(obs.get("silt_depth_cm", 0.0)),
                        float(obs.get("flow_velocity_pct", 100.0)),
                        float(obs.get("water_level_pct", 0.0)),
                        obs.get("evidence_summary", ""),
                        obs.get("evidence_type", "OPENCV_INSPECTION"),
                        obs.get("observation_date", now_iso[:10]),
                        obs.get("inspector_name", "Municipal Hydro-Survey Team"),
                        obs.get("action_recommended", "Routine inspection"),
                        obs.get("data_source", "Municipal GIS & Sensor Stream"),
                        now_iso,
                    ),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to insert blockage observation: {e}")
            return None

    def insert_drainage_image(self, img_data: Dict[str, Any]) -> Optional[int]:
        """Record drainage photographic inspection evidence."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO drainage_images (
                        segment_id, image_path, caption, capture_date, image_source,
                        opencv_analyzed, debris_pct, turbidity_score, purity_score,
                        annotated_path, is_blockage_evidence, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        img_data["segment_id"],
                        img_data["image_path"],
                        img_data.get("caption", ""),
                        img_data.get("capture_date", datetime.now(timezone.utc).isoformat()[:10]),
                        img_data.get("image_source", "MUNICIPAL_INSPECTION_CAMERA"),
                        int(img_data.get("opencv_analyzed", 0)),
                        float(img_data.get("debris_pct", 0.0)),
                        float(img_data.get("turbidity_score", 0.0)),
                        float(img_data.get("purity_score", 0.0)),
                        img_data.get("annotated_path", ""),
                        int(img_data.get("is_blockage_evidence", 0)),
                        img_data.get("notes", ""),
                    ),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to insert drainage image: {e}")
            return None

    def get_drainage_images(self, segment_id: str) -> List[Dict[str, Any]]:
        """Retrieve all image evidence records for a segment."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, segment_id, image_path, caption, capture_date, image_source,
                           opencv_analyzed, debris_pct, turbidity_score, purity_score,
                           annotated_path, is_blockage_evidence, notes
                    FROM drainage_images
                    WHERE segment_id = ?
                    ORDER BY id DESC;
                    """,
                    (segment_id,),
                )
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch drainage images: {e}")
            return []

    def log_blockage_report(
        self,
        report_type: str,
        city_id: str,
        report_title: str,
        file_path: str,
        segment_id: Optional[str] = None,
        file_size_bytes: int = 0,
        summary: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """Record generated blockage report in audit log."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            summary_str = json.dumps(summary or {})
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO blockage_reports (
                        report_type, city_id, segment_id, generated_at,
                        report_title, file_path, file_size_bytes, summary_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        report_type,
                        city_id,
                        segment_id,
                        now_iso,
                        report_title,
                        str(file_path),
                        file_size_bytes,
                        summary_str,
                    ),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to log blockage report: {e}")
            return None
        except Exception as e:
            return {
                "database_file": str(self.db_path),
                "file_exists": self.db_path.exists(),
                "error": str(e),
                "status": "DEGRADED",
            }


# Global singleton instance
db_manager = DatabaseManager()

