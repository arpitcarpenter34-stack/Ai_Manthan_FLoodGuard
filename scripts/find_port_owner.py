import subprocess
import re

res = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
lines = res.stdout.splitlines()
found = [line for line in lines if ":8000" in line]
print(f"Found {len(found)} entries matching :8000:")
for f in found:
    print(f)
    parts = f.split()
    if len(parts) >= 5:
        pid = parts[-1]
        try:
            pinfo = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
            print(pinfo.stdout)
        except Exception as e:
            print(f"Err checking PID {pid}: {e}")

