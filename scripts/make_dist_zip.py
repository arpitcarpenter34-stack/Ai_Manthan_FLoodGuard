"""
Script to package HYDRO-GUARD AI into a clean, distributable ZIP file.
Excludes compiled Python bytecode, caches, and temporary files.
"""

import os
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SOURCE_DIR = Path(r"E:\ai-manthan\hydro_guard_indore")
OUTPUT_ZIP = Path(r"E:\ai-manthan\hydro_guard_indore.zip")

EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".idea",
    ".vscode",
}

EXCLUDED_FILE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
}

EXCLUDED_FILES = {
    "map_verified.png",
    "map_snap.png",
    "edge_snap.png",
    "snap.png",
    "test_map_screenshot.png",
}


def should_exclude(rel_path: Path) -> bool:
    # Check directory parts
    for part in rel_path.parts[:-1]:
        if part in EXCLUDED_DIR_NAMES or part.startswith("."):
            return True
    # Check filename
    filename = rel_path.name
    if filename in EXCLUDED_DIR_NAMES or filename in EXCLUDED_FILES:
        return True
    if any(filename.endswith(ext) for ext in EXCLUDED_FILE_EXTENSIONS):
        return True
    return False


def create_zip():
    print(f"Packaging {SOURCE_DIR} into {OUTPUT_ZIP}...")
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
        for root, dirs, files in os.walk(SOURCE_DIR):
            # Modify dirs in-place to avoid descending into excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES and not d.startswith(".")]

            for file in files:
                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(SOURCE_DIR)

                if should_exclude(rel_path):
                    continue

                archive_name = Path("hydro_guard_indore") / rel_path
                zip_file.write(abs_path, arcname=str(archive_name))
                file_count += 1
                total_uncompressed_bytes += abs_path.stat().st_size

    zip_size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    raw_size_mb = total_uncompressed_bytes / (1024 * 1024)
    print(f"\nSuccessfully created ZIP file:")
    print(f"- Destination: {OUTPUT_ZIP}")
    print(f"- Total Files Included: {file_count}")
    print(f"- Uncompressed Size: {raw_size_mb:.2f} MB")
    print(f"- Compressed ZIP Size: {zip_size_mb:.2f} MB")


if __name__ == "__main__":
    create_zip()

