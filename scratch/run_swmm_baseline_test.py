import os
import sys
import time
from pyswmm import Simulation, Nodes, Links

sys.stdout.reconfigure(encoding='utf-8')

swmm_dir = r"E:\ai-manthan\hydro_guard_indore\data\urban_drainage_datasets\bellinge\swmm_models\7_SWMM"
inp_path = os.path.join(swmm_dir, "BellingeSWMM_v021_nopervious.inp")
rpt_path = os.path.join(swmm_dir, "BellingeSWMM_v021_nopervious.rpt")
out_path = os.path.join(swmm_dir, "BellingeSWMM_v021_nopervious.out")

# We change working directory to swmm_dir so it resolves relative file "rg_bellinge_Jun2010_Aug2021.dat"
orig_cwd = os.getcwd()
os.chdir(swmm_dir)

print(f"Starting PySWMM simulation on: {inp_path}")
start_time = time.time()

try:
    with Simulation(inp_path, rpt_path, out_path) as sim:
        print(f"Simulation engine initialized: {sim.engine_version}")
        print("Stepping through simulation...")
        steps = 0
        monitored_node = Nodes(sim)['G71F04R'] if 'G71F04R' in [n.nodeid for n in Nodes(sim)] else list(Nodes(sim))[0]
        print(f"Monitoring Node: {monitored_node.nodeid}")
        
        node_depths = []
        timestamps = []
        for step in sim:
            steps += 1
            if steps % 1000 == 0:
                print(f"  Step {steps}: sim time = {sim.current_time}, depth={monitored_node.depth:.3f} m, head={monitored_node.head:.3f} m")
                node_depths.append(monitored_node.depth)
                timestamps.append(sim.current_time)
            # Break after 5000 steps to verify hydraulic execution in real time
            if steps >= 5000:
                print("Successfully executed 5,000 hydrodynamic routing steps!")
                break
                
    elapsed = time.time() - start_time
    print(f"\nPySWMM Simulation executed successfully in {elapsed:.2f} seconds!")
    print(f"Report file created: {os.path.exists(rpt_path)} ({os.path.getsize(rpt_path) if os.path.exists(rpt_path) else 0} bytes)")
    print(f"Output binary created: {os.path.exists(out_path)} ({os.path.getsize(out_path) if os.path.exists(out_path) else 0} bytes)")
except Exception as e:
    print(f"Error executing PySWMM: {e}")
finally:
    os.chdir(orig_cwd)

