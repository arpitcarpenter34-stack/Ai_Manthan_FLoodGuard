from pathlib import Path

target_file = Path("E:/ai-manthan/hydro_guard_indore/backend/services/dataset_intelligence_service.py")
content = target_file.read_text(encoding="utf-8")

old_code = '''        return {
            "dataset_id": dataset_id,
            "distributions": dist_map.get(dataset_id)
        }'''

new_code = '''        normalized = dataset_id.lower().strip()
        alias_map = {
            "cwprs_pune": "india_cwprs",
            "pune_cwprs": "india_cwprs",
            "cwprs": "india_cwprs",
            "usgs": "usgs_potomac",
            "bellinge": "bellinge_swmm",
            "uwo": "uwo_kearney",
            "era5": "era5_noaa",
            "noaa": "era5_noaa",
        }
        canonical_id = alias_map.get(normalized, normalized)
        if canonical_id not in dist_map:
            return None

        return {
            "dataset_id": dataset_id,
            "distributions": dist_map[canonical_id]
        }'''

# Replace regardless of line endings
old_code_crlf = old_code.replace("\n", "\r\n")
new_code_crlf = new_code.replace("\n", "\r\n")

if old_code_crlf in content:
    content = content.replace(old_code_crlf, new_code_crlf, 1)
    target_file.write_text(content, encoding="utf-8")
    print("Successfully patched dataset_intelligence_service.py (CRLF)")
elif old_code in content:
    content = content.replace(old_code, new_code, 1)
    target_file.write_text(content, encoding="utf-8")
    print("Successfully patched dataset_intelligence_service.py (LF)")
else:
    print("Could not find old_code in dataset_intelligence_service.py")
