import os
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set env var before importing config
temp_mount = Path(tempfile.mkdtemp(prefix="render_test_env_var_"))
custom_db = temp_mount / "var_data" / "hydro_guard.db"
os.environ["HYDRO_GUARD_DB_PATH"] = str(custom_db)

try:
    import config
    from backend.services.db_manager import db_manager

    print("Config DB_PATH:", config.DB_PATH)
    print("Seed DB_PATH:", config.SEED_DB_PATH)
    assert str(config.DB_PATH) == str(custom_db), "Config DB_PATH mismatch"
    assert custom_db.exists(), "Persistent database file must have been automatically created from seed"

    stats = db_manager.get_db_stats()
    print("DB Stats:", stats)
    assert stats["is_persistent_custom_path"] is True, "is_persistent_custom_path should be True"
    assert stats["status"] == "HEALTHY", "Status should be HEALTHY"
    assert stats["total_telemetry_records"] > 0, "Telemetry records should be inherited"
    print("\n[PASS] HYDRO_GUARD_DB_PATH Environment Variable Successfully Verified!")
finally:
    shutil.rmtree(temp_mount, ignore_errors=True)

