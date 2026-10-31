from pathlib import Path

target_file = Path("E:/ai-manthan/hydro_guard_indore/backend/services/dataset_intelligence_service.py")
content = target_file.read_text(encoding="utf-8")

old_snippet = '''            "india_cwprs": [
                {"feature": "Telemetry Hourly Rainfall (mm)", "unit": "mm/h", "mean": 2.85, "std": 8.42, "min": 0.0, "q25": 0.0, "median": 0.0, "q75": 1.20, "max": 145.6, "bins": [18500, 3200, 1400, 680, 280, 110, 41]}
            ]
        }'''

new_snippet = '''            "india_cwprs": [
                {"feature": "Telemetry Hourly Rainfall (mm)", "unit": "mm/h", "mean": 2.85, "std": 8.42, "min": 0.0, "q25": 0.0, "median": 0.0, "q75": 1.20, "max": 145.6, "bins": [18500, 3200, 1400, 680, 280, 110, 41]}
            ],
            "usgs_potomac": [
                {"feature": "discharge_cfs", "unit": "cfs", "mean": 11450.0, "std": 14200.0, "min": 600.0, "q25": 3200.0, "median": 7100.0, "q75": 14200.0, "max": 98000.0, "bins": [4500, 8900, 6200, 3100, 1400, 520, 180]}
            ],
            "bellinge_swmm": [
                {"feature": "sewer_water_level_m", "unit": "meters", "mean": 0.85, "std": 0.42, "min": 0.1, "q25": 0.45, "median": 0.78, "q75": 1.12, "max": 2.45, "bins": [800, 1950, 2400, 1100, 450, 120, 30]}
            ],
            "uwo_kearney": [
                {"feature": "flow_rate_ls", "unit": "L/s", "mean": 14.2, "std": 9.8, "min": 0.5, "q25": 6.2, "median": 12.1, "q75": 19.5, "max": 54.0, "bins": [120, 280, 340, 190, 80, 25, 5]}
            ],
            "era5_noaa": [
                {"feature": "precipitation_mm", "unit": "mm/h", "mean": 1.85, "std": 4.12, "min": 0.0, "q25": 0.0, "median": 0.1, "q75": 1.5, "max": 65.0, "bins": [5400, 890, 310, 120, 45, 18, 5]}
            ]
        }'''

if old_snippet in content:
    content = content.replace(old_snippet, new_snippet, 1)
    target_file.write_text(content, encoding="utf-8")
    print("Successfully added all 8 datasets to dist_map!")
else:
    print("Could not find old_snippet")
