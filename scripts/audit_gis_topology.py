import json
import urllib.request
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, r"E:\ai-manthan\hydro_guard_indore")
import config

print("=" * 80)
print(" HYDRO-GUARD AI — SECTION 2: GIS & TOPOLOGY AUDIT")
print("=" * 80)

# 1. Inspect Config Nodes
print("\n[1] 7 INDORE DRAINAGE MONITORING STATIONS (Config & Spatial Invariants):")
nodes = config.DRAINAGE_NODES
for nid, d in nodes.items():
    print(f"  • {nid:20s}: Name='{d['name']}', Lat={d['lat']}, Lon={d['lon']}, AssumedElev={d['elevation_m']}m, River='{d['river']}'")

# 2. Inspect Config Edges
print(f"\n[2] TOPOLOGICAL DRAINAGE EDGES ({len(config.DRAINAGE_EDGES)} configured edges):")
for u, v, attrs in config.DRAINAGE_EDGES:
    u_elev = nodes[u]["elevation_m"]
    v_elev = nodes[v]["elevation_m"]
    drop = u_elev - v_elev
    print(f"  • {u} -> {v}: Length={attrs['length_km']}km, Drop={drop:4.1f}m ({u_elev}m -> {v_elev}m), Roughness n={attrs['roughness_n']}")

# 3. Query /api/v1/flood/topology
print("\n[3] QUERYING BACKEND /api/v1/flood/topology:")
url = "http://127.0.0.1:8000/api/v1/flood/topology"
with urllib.request.urlopen(url) as resp:
    data = json.loads(resp.read().decode("utf-8"))

geojson = data.get("geojson", {})
features = geojson.get("features", [])
print(f"  Total features in combined geojson: {len(features)}")

points = [f for f in features if f.get("geometry", {}).get("type") == "Point"]
lines = [f for f in features if f.get("geometry", {}).get("type") == "LineString"]
print(f"  Point features: {len(points)}")
print(f"  LineString features: {len(lines)}")

# Layer types breakdown
layer_counts = {}
for f in features:
    lt = f.get("properties", {}).get("layer_type", "unknown")
    layer_counts[lt] = layer_counts.get(lt, 0) + 1
print(f"  Breakdown by layer_type: {layer_counts}")

# Real waterways
rw = data.get("real_waterways", {})
rw_features = rw.get("features", [])
print(f"\n[4] REAL OSM WATERWAYS (indore_waterways_osm.geojson):")
print(f"  Features count: {len(rw_features)}")
print(f"  Source metadata: {rw.get('metadata', {})}")
for idx, f in enumerate(rw_features):
    props = f.get("properties", {})
    geom = f.get("geometry", {})
    name = props.get("name", props.get("waterway", "Unnamed waterway"))
    gtype = geom.get("type")
    coords_len = len(geom.get("coordinates", []))
    print(f"  - Real River Reach {idx+1}: '{name}', Type={gtype}, Vertices={coords_len}, OsmID={props.get('osm_id', props.get('@id'))}")

# Copernicus DEM bounds
dem_bounds = data.get("dem_surface_elevation_bounds", {})
print(f"\n[5] COPERNICUS DEM GLO-30 ELEVATION PROFILE:")
print(f"  DEM Available: {data.get('dem_metadata', {}).get('is_dem_available')}")
print(f"  Vertical Datum: {data.get('dem_metadata', {}).get('vertical_datum')}")
print(f"  Surface elevation bounds: {dem_bounds}")

# Check topological flow direction validity (elevation strictly decreasing or gravity-compliant)
print("\n[6] GRAVITY-FLOW VERIFICATION:")
gravity_ok = True
for u, v, attrs in config.DRAINAGE_EDGES:
    u_elev = nodes[u]["elevation_m"]
    v_elev = nodes[v]["elevation_m"]
    if u_elev < v_elev:
        print(f"  [FAIL] Reverse slope detected: {u} ({u_elev}m) -> {v} ({v_elev}m)")
        gravity_ok = False
    else:
        print(f"  [PASS] Gravity flow: {u} ({u_elev}m) -> {v} ({v_elev}m) [Drop: {u_elev - v_elev}m]")
if gravity_ok:
    print("  => ALL DRAINAGE EDGES STRICTLY RESPECT GRAVITY SLOPE!")

