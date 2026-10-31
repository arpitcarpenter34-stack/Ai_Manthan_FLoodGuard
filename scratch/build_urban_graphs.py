import os
import sys
import json
import glob
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

base_urban = r"E:\ai-manthan\hydro_guard_indore\data\urban_drainage_datasets"
out_graph_dir = r"E:\ai-manthan\hydro_guard_indore\data\processed_global\urban_graphs"
os.makedirs(out_graph_dir, exist_ok=True)

print("==================================================================")
print("             TASK 2.4 - STEP 3: BUILD URBAN GRAPH ARTIFACTS       ")
print("==================================================================")

# ==========================================
# 1. BELLINGE GRAPH TOPOLOGY
# ==========================================
print("\n--- 1. BUILDING BELLINGE SWMM GRAPH (1,021 NODES) ---")
bel_swmm = glob.glob(os.path.join(base_urban, "bellinge", "**", "*.inp"), recursive=True)[0]

junctions = {}
outfalls = {}
storage = {}
conduits = []
pumps = []
weirs = []
orifices = []
xsections = {}

current_sec = None
with open(bel_swmm, 'r', encoding='latin1') as f:
    for line in f:
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            current_sec = line
            continue
        if not line or line.startswith(';;') or line.startswith(';'):
            continue
        parts = line.split()
        if not parts or parts[0].lower() in ['name', ';;name', ';name']:
            continue
        try:
            if current_sec == '[JUNCTIONS]':
                junctions[parts[0]] = {
                    'elev': float(parts[1]),
                    'max_depth': float(parts[2]),
                    'init_depth': float(parts[3]) if len(parts) > 3 else 0.0,
                    'sur_depth': float(parts[4]) if len(parts) > 4 else 0.0,
                    'type': 'JUNCTION'
                }
            elif current_sec == '[OUTFALLS]':
                outfalls[parts[0]] = {
                    'elev': float(parts[1]),
                    'max_depth': 0.0,
                    'init_depth': 0.0,
                    'sur_depth': 0.0,
                    'type': 'OUTFALL'
                }
            elif current_sec == '[STORAGE]':
                storage[parts[0]] = {
                    'elev': float(parts[1]),
                    'max_depth': float(parts[2]),
                    'init_depth': float(parts[3]) if len(parts) > 3 else 0.0,
                    'sur_depth': 0.0,
                    'type': 'STORAGE'
                }
            elif current_sec == '[CONDUITS]':
                conduits.append({
                    'name': parts[0],
                    'from': parts[1],
                    'to': parts[2],
                    'length': float(parts[3]),
                    'roughness': float(parts[4]),
                    'type': 'CONDUIT'
                })
            elif current_sec == '[PUMPS]':
                pumps.append({
                    'name': parts[0],
                    'from': parts[1],
                    'to': parts[2],
                    'length': 10.0,
                    'roughness': 0.015,
                    'type': 'PUMP'
                })
            elif current_sec == '[WEIRS]':
                weirs.append({
                    'name': parts[0],
                    'from': parts[1],
                    'to': parts[2],
                    'length': 5.0,
                    'roughness': 0.015,
                    'type': 'WEIR'
                })
            elif current_sec == '[ORIFICES]':
                orifices.append({
                    'name': parts[0],
                    'from': parts[1],
                    'to': parts[2],
                    'length': 5.0,
                    'roughness': 0.015,
                    'type': 'ORIFICE'
                })
            elif current_sec == '[XSECTIONS]':
                xsections[parts[0]] = {
                    'shape': parts[1],
                    'geom1': float(parts[2])
                }
        except Exception:
            continue

all_nodes = list(junctions.keys()) + list(outfalls.keys()) + list(storage.keys())
node_to_idx = {n: i for i, n in enumerate(all_nodes)}
N_bel = len(all_nodes)
print(f"Bellinge Total Nodes: {N_bel} (Junctions: {len(junctions)}, Outfalls: {len(outfalls)}, Storage: {len(storage)})")

A_bel = np.zeros((N_bel, N_bel), dtype=np.float32)
all_edges = conduits + pumps + weirs + orifices
valid_edges = 0
edge_features = []

for e in all_edges:
    u = e['from']
    v = e['to']
    if u in node_to_idx and v in node_to_idx:
        uidx = node_to_idx[u]
        vidx = node_to_idx[v]
        length = e['length']
        roughness = e['roughness']
        geom1 = xsections.get(e['name'], {}).get('geom1', 0.5)
        
        A_pipe = np.pi * (geom1 ** 2) / 4.0
        R_hyd = geom1 / 4.0
        conveyance = (1.0 / max(0.005, roughness)) * A_pipe * (R_hyd ** (2.0 / 3.0))
        weight = float(np.clip(conveyance / max(1.0, length), 0.01, 10.0))
        
        A_bel[uidx, vidx] = weight
        valid_edges += 1
        edge_features.append([uidx, vidx, length, roughness, geom1, weight])

np.fill_diagonal(A_bel, 1.0)
print(f"Bellinge Valid Directed Edges: {valid_edges}")
print(f"Bellinge Adjacency Matrix Shape: {A_bel.shape}, Non-zeros: {np.count_nonzero(A_bel)}")

node_type_map = {'JUNCTION': 0, 'OUTFALL': 1, 'STORAGE': 2}
node_features_bel = np.zeros((N_bel, 4), dtype=np.float32)
for i, n in enumerate(all_nodes):
    info = junctions.get(n) or outfalls.get(n) or storage.get(n)
    node_features_bel[i] = [
        info['elev'],
        info['max_depth'],
        info['init_depth'],
        node_type_map[info['type']]
    ]

np.save(os.path.join(out_graph_dir, "bellinge_adjacency.npy"), A_bel)
np.save(os.path.join(out_graph_dir, "bellinge_node_features.npy"), node_features_bel)
np.save(os.path.join(out_graph_dir, "bellinge_edge_features.npy"), np.array(edge_features, dtype=np.float32))
with open(os.path.join(out_graph_dir, "bellinge_node_ids.json"), "w") as f:
    json.dump({
        'nodes': all_nodes,
        'node_type_counts': {'junctions': len(junctions), 'outfalls': len(outfalls), 'storage': len(storage)},
        'total_nodes': N_bel,
        'total_edges': valid_edges
    }, f, indent=2)

print("Bellinge graph artifacts saved to:", out_graph_dir)

# ==========================================
# 2. UWO GRAPH TOPOLOGY
# ==========================================
print("\n--- 2. BUILDING UWO SWMM GRAPH (444 NODES) ---")
uwo_swmm = glob.glob(os.path.join(base_urban, "uwo", "**", "calibrated_surface_model_original_30min.inp"), recursive=True)[0]

uwo_junc = {}
uwo_outfall = {}
uwo_storage = {}
uwo_conduits = []
uwo_pumps = []
uwo_weirs = []

curr_uwo = None
with open(uwo_swmm, 'r', encoding='latin1') as f:
    for line in f:
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            curr_uwo = line
            continue
        if not line or line.startswith(';;') or line.startswith(';'):
            continue
        parts = line.split()
        if not parts or parts[0].lower() in ['name', ';;name', ';name']:
            continue
        try:
            if curr_uwo == '[JUNCTIONS]':
                uwo_junc[parts[0]] = {'elev': float(parts[1]), 'max_depth': float(parts[2]), 'type': 'JUNCTION'}
            elif curr_uwo == '[OUTFALLS]':
                uwo_outfall[parts[0]] = {'elev': float(parts[1]), 'max_depth': 0.0, 'type': 'OUTFALL'}
            elif curr_uwo == '[STORAGE]':
                uwo_storage[parts[0]] = {'elev': float(parts[1]), 'max_depth': float(parts[2]), 'type': 'STORAGE'}
            elif curr_uwo == '[CONDUITS]':
                uwo_conduits.append({'from': parts[1], 'to': parts[2], 'length': float(parts[3]), 'roughness': float(parts[4])})
            elif curr_uwo == '[PUMPS]':
                uwo_pumps.append({'from': parts[1], 'to': parts[2], 'length': 10.0, 'roughness': 0.015})
            elif curr_uwo == '[WEIRS]':
                uwo_weirs.append({'from': parts[1], 'to': parts[2], 'length': 5.0, 'roughness': 0.015})
        except Exception:
            continue

uwo_nodes = list(uwo_junc.keys()) + list(uwo_outfall.keys()) + list(uwo_storage.keys())
uwo_node_to_idx = {n: i for i, n in enumerate(uwo_nodes)}
N_uwo = len(uwo_nodes)
print(f"UWO Total Nodes: {N_uwo} (Junctions: {len(uwo_junc)}, Outfalls: {len(uwo_outfall)}, Storage: {len(uwo_storage)})")

A_uwo = np.zeros((N_uwo, N_uwo), dtype=np.float32)
uwo_edges_total = uwo_conduits + uwo_pumps + uwo_weirs
valid_uwo_edges = 0
for e in uwo_edges_total:
    u = e['from']
    v = e['to']
    if u in uwo_node_to_idx and v in uwo_node_to_idx:
        uidx = uwo_node_to_idx[u]
        vidx = uwo_node_to_idx[v]
        A_uwo[uidx, vidx] = float(np.clip(100.0 / max(1.0, e['length']), 0.01, 10.0))
        valid_uwo_edges += 1

np.fill_diagonal(A_uwo, 1.0)
print(f"UWO Valid Directed Edges: {valid_uwo_edges}")
print(f"UWO Adjacency Matrix Shape: {A_uwo.shape}, Non-zeros: {np.count_nonzero(A_uwo)}")

node_features_uwo = np.zeros((N_uwo, 3), dtype=np.float32)
for i, n in enumerate(uwo_nodes):
    info = uwo_junc.get(n) or uwo_outfall.get(n) or uwo_storage.get(n)
    node_features_uwo[i] = [info['elev'], info['max_depth'], node_type_map[info['type']]]

np.save(os.path.join(out_graph_dir, "uwo_adjacency.npy"), A_uwo)
np.save(os.path.join(out_graph_dir, "uwo_node_features.npy"), node_features_uwo)
with open(os.path.join(out_graph_dir, "uwo_node_ids.json"), "w") as f:
    json.dump({
        'nodes': uwo_nodes,
        'node_type_counts': {'junctions': len(uwo_junc), 'outfalls': len(uwo_outfall), 'storage': len(uwo_storage)},
        'total_nodes': N_uwo,
        'total_edges': valid_uwo_edges
    }, f, indent=2)

print("UWO graph artifacts saved to:", out_graph_dir)

# ==========================================
# 3. BLUE HEART ROAD GULLY SUBGRAPH (15 GULLIES)
# ==========================================
print("\n--- 3. BUILDING BLUE HEART ROAD GULLY SUBGRAPH (15 SENSORS) ---")
bh_gully_dir = os.path.join(base_urban, "blue_heart", "highway_gully_telemetry")
bh_gully_files = sorted([f for f in glob.glob(os.path.join(bh_gully_dir, "*.csv")) if "quality" not in f])
gully_names = [os.path.basename(f).replace(".csv", "") for f in bh_gully_files]
N_gully = len(gully_names)
print(f"Blue Heart Monitored Gullies: {N_gully}")

bh_idx_csv = os.path.join(base_urban, "blue_heart", "index_telemetry_data.csv")
df_idx = pd.read_csv(bh_idx_csv)
gully_coords = {}
for _, row in df_idx.iterrows():
    loc = str(row['locationName'])
    for gn in gully_names:
        if gn.split('_')[0] in loc or gn in loc:
            gully_coords[gn] = (float(row['locationLatitude']), float(row['locationLongitude']))

print(f"Matched Gully Coordinates: {len(gully_coords)} of {N_gully}")

A_gully = np.zeros((N_gully, N_gully), dtype=np.float32)
sigma = 2000.0

for i, g1 in enumerate(gully_names):
    c1 = gully_coords.get(g1, (50.77, 0.28))
    for j, g2 in enumerate(gully_names):
        if i == j:
            A_gully[i, j] = 1.0
        else:
            c2 = gully_coords.get(g2, (50.77, 0.28))
            d_lat = (c1[0] - c2[0]) * 111000.0
            d_lon = (c1[1] - c2[1]) * 111000.0 * np.cos(np.radians(c1[0]))
            dist = np.sqrt(d_lat**2 + d_lon**2)
            if dist < 5000.0:
                A_gully[i, j] = float(np.exp(-(dist**2) / (sigma**2)))

print(f"Blue Heart Gully Adjacency Shape: {A_gully.shape}, Non-zeros: {np.count_nonzero(A_gully)}")

np.save(os.path.join(out_graph_dir, "blue_heart_gully_adjacency.npy"), A_gully)
with open(os.path.join(out_graph_dir, "blue_heart_gully_node_ids.json"), "w") as f:
    json.dump({
        'sensors': gully_names,
        'total_sensors': N_gully,
        'coordinates': gully_coords
    }, f, indent=2)

print("Blue Heart gully graph artifacts saved to:", out_graph_dir)
print("\nAll Urban Graph Artifacts successfully constructed.")

