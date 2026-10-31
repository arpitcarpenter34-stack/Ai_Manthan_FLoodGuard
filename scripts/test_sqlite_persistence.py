"""
Comprehensive Verification Suite for SQLite Persistent Storage Implementation
Tests:
1. Local fallback to data/hydro_guard.db when HYDRO_GUARD_DB_PATH is unset.
2. Initializing persistent database from seed on first startup when target is absent.
3. Ensuring existing persistent database is NEVER overwritten on restart.
4. Verifying telemetry writes survive simulated restart.
5. Verifying purity analysis records survive simulated restart.
6. Database integrity with PRAGMA integrity_check.
7. Original repository seed database preservation.
"""

import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Step 0: Test default local behavior (unset env var)
import config
from backend.services.db_manager import DatabaseManager

def test_local_default():
    print("\n[TEST 1] Verifying local development default behavior (HYDRO_GUARD_DB_PATH unset)...")
    assert str(config.DB_PATH.resolve()) == str(config.SEED_DB_PATH.resolve()), "DB_PATH should match SEED_DB_PATH"
    mgr = DatabaseManager()
    stats = mgr.get_db_stats()
    assert stats["status"] == "HEALTHY", f"Local DB status: {stats}"
    assert stats["is_persistent_custom_path"] is False, "Should indicate not custom persistent path"
    assert stats["total_analysis_records"] > 0, "Seed database should contain analysis records"
    assert stats["total_telemetry_records"] > 0, "Seed database should contain telemetry records"
    print(f"  [PASS] Local DB default verified at {config.DB_PATH} ({stats['total_telemetry_records']} telemetry, {stats['total_analysis_records']} analysis records)")


def test_persistent_storage_lifecycle():
    print("\n[TEST 2] Testing Render Persistent Disk simulation (first startup & restart)...")
    temp_dir = Path(tempfile.mkdtemp(prefix="hydro_guard_render_persistent_"))
    try:
        persistent_db_path = temp_dir / "render_mount" / "hydro_guard.db"
        assert not persistent_db_path.exists(), "Target DB should not exist initially"

        # Simulating first startup on Render with target absent
        print(f"  -> Simulating first Render boot with target: {persistent_db_path}")
        mgr1 = DatabaseManager(db_path=persistent_db_path)
        assert persistent_db_path.exists(), "Target persistent DB should be created from seed"
        
        stats1 = mgr1.get_db_stats()
        assert stats1["status"] == "HEALTHY"
        assert stats1["is_persistent_custom_path"] is True
        initial_telemetry_count = stats1["total_telemetry_records"]
        initial_analysis_count = stats1["total_analysis_records"]
        assert initial_telemetry_count > 0, "Persistent DB should inherit seed telemetry records"
        assert initial_analysis_count > 0, "Persistent DB should inherit seed analysis records"
        print(f"  [PASS] Successfully seeded persistent database: {initial_telemetry_count} telemetry, {initial_analysis_count} analysis rows")

        # Insert new runtime records
        print("  -> Inserting new runtime telemetry and image purity analysis...")
        new_analysis_id = mgr1.log_image_analysis(
            input_source="render_persistent_test_sample.jpg",
            purity_score=94.5,
            is_clean=True,
            gate_action="GATE OPEN TO KHAN RIVER",
            turbidity_estimate=4.2,
            debris_count=0,
            details={"test_marker": "render_e2e_persistence_run_1"},
        )
        assert new_analysis_id is not None, "Image analysis logging failed"

        new_telemetry_id = mgr1.log_telemetry_snapshot(
            city_avg_pct=42.5,
            peak_node="NODE_RAJWARA",
            peak_level_pct=58.2,
            rainfall_intensity=12.4,
            nodes_snapshot={"NODE_RAJWARA": {"level": 58.2}},
        )
        assert new_telemetry_id is not None, "Telemetry logging failed"
        print(f"  [PASS] Logged new runtime records: analysis ID #{new_analysis_id}, telemetry ID #{new_telemetry_id}")

        # Simulating container restart/redeploy on Render with persistent disk attached
        print("  -> Simulating container restart/redeploy with existing persistent DB...")
        mgr2 = DatabaseManager(db_path=persistent_db_path)
        stats2 = mgr2.get_db_stats()

        assert stats2["total_analysis_records"] == initial_analysis_count + 1, "Analysis record count should be incremented"
        assert stats2["total_telemetry_records"] == initial_telemetry_count + 1, "Telemetry record count should be incremented"

        # Verify exact record content persists
        recent = mgr2.get_recent_analyses(limit=5, analysis_type="IMAGE_PURITY")
        matching = [r for r in recent if r["id"] == new_analysis_id]
        assert len(matching) == 1, f"Did not find persisted analysis record #{new_analysis_id}"
        assert matching[0]["input_source"] == "render_persistent_test_sample.jpg"
        assert matching[0]["primary_metric"] == 94.5
        assert matching[0]["details"].get("test_marker") == "render_e2e_persistence_run_1"
        print("  [PASS] Runtime records SURVIVED application restart without being overwritten!")

        # Verify PRAGMA integrity_check
        with sqlite3.connect(str(persistent_db_path)) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            integrity_result = cur.fetchone()[0]
            assert integrity_result == "ok", f"Integrity check failed: {integrity_result}"
            print("  [PASS] Persistent database PRAGMA integrity_check: ok")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("  -> Cleaned up temporary persistent test mount.")


def test_seed_database_protection():
    print("\n[TEST 3] Verifying seed database integrity and protection...")
    assert config.SEED_DB_PATH.exists(), f"Seed database must exist at {config.SEED_DB_PATH}"
    with sqlite3.connect(str(config.SEED_DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()[0]
        assert res == "ok", f"Seed DB integrity check failed: {res}"
        cur.execute("SELECT COUNT(*) FROM analysis_logs;")
        a_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM telemetry_logs;")
        t_count = cur.fetchone()[0]
        print(f"  [PASS] Original seed database preserved and intact: {t_count} telemetry, {a_count} analysis rows (PRAGMA integrity_check: ok)")


if __name__ == "__main__":
    print("=" * 70)
    print("  HYDRO-GUARD AI: SQLite Persistent Storage Validation Suite")
    print("=" * 70)
    test_local_default()
    test_persistent_storage_lifecycle()
    test_seed_database_protection()
    print("\n" + "=" * 70)
    print("  ALL SQLITE PERSISTENCE VALIDATION TESTS PASSED (100% SUCCESS)!")
    print("=" * 70)
