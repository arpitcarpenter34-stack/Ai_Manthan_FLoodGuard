import glob
import os

print("Searching for blue_heart files:")
for f in glob.glob("**/*blue_heart*.*", recursive=True):
    print(f"  {f} ({os.path.getsize(f):,} bytes)")

print("\nSearching for cwprs files:")
for f in glob.glob("**/*cwprs*.*", recursive=True):
    print(f"  {f} ({os.path.getsize(f):,} bytes)")

