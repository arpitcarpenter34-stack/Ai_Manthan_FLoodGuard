import subprocess
import os

res = subprocess.run(["git", "status", "--porcelain"], cwd="E:/ai-manthan/hydro_guard_indore", capture_output=True, text=True)
lines = res.stdout.splitlines()

large_files = []
for line in lines:
    status = line[:2]
    fname = line[3:].strip()
    fpath = os.path.join("E:/ai-manthan/hydro_guard_indore", fname)
    if os.path.isfile(fpath):
        sz_mb = os.path.getsize(fpath) / (1024 * 1024)
        if sz_mb > 10:
            large_files.append((fname, sz_mb))

large_files.sort(key=lambda x: x[1], reverse=True)
print(f"Total files > 10MB: {len(large_files)}")
for fname, sz in large_files[:20]:
    print(f"  {sz:.2f} MB : {fname}")
