import os
import glob

base_urban = r"E:\ai-manthan\hydro_guard_indore\data\urban_drainage_datasets"
bel_swmm = glob.glob(os.path.join(base_urban, "bellinge", "**", "*.inp"), recursive=True)[0]

print("SWMM file:", bel_swmm)
with open(bel_swmm, 'r', encoding='latin1') as f:
    in_opts = False
    in_rg = False
    for line in f:
        line_s = line.strip()
        if line_s == '[OPTIONS]':
            in_opts = True
            continue
        elif line_s.startswith('['):
            in_opts = False
        if line_s == '[RAINGAGES]':
            in_rg = True
            continue
        elif in_rg and line_s.startswith('['):
            in_rg = False
        
        if in_opts and line_s and not line_s.startswith(';;'):
            print("OPT:", line_s)
        if in_rg and line_s and not line_s.startswith(';;'):
            print("RAINGAGE:", line_s)

