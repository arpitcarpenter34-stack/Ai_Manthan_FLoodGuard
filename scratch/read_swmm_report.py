import os

rpt_path = r"E:\ai-manthan\hydro_guard_indore\data\urban_drainage_datasets\bellinge\swmm_models\7_SWMM\BellingeSWMM_v021_nopervious.rpt"

with open(rpt_path, 'r', encoding='latin1') as f:
    lines = f.readlines()

print(f"Total report lines: {len(lines)}")
# Print summary sections
capture = False
for line in lines:
    if "Routing Continuity" in line or "Highest Flow" in line or "Node Inundation" in line or "Highest Surcharge" in line or "Continuity Error" in line or "WARNING" in line:
        capture = True
    if capture:
        print(line.strip())
        if line.strip() == "" and "Continuity" not in line:
            capture = False

