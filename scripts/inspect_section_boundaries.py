with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- SCREEN-PREDICTION SURROUNDINGS ---")
for i in range(2148, 2156):
    print(f"{i+1}: {lines[i]}", end="")
print("...")
for i in range(2294, 2305):
    print(f"{i+1}: {lines[i]}", end="")

print("\n--- SCREEN-SIMULATOR SURROUNDINGS ---")
for i in range(2556, 2564):
    print(f"{i+1}: {lines[i]}", end="")
print("...")
for i in range(2678, 2688):
    print(f"{i+1}: {lines[i]}", end="")

print("\n--- SCREEN-HISTORY SURROUNDINGS ---")
for i in range(2940, 2948):
    print(f"{i+1}: {lines[i]}", end="")
print("...")
for i in range(2994, 3004):
    print(f"{i+1}: {lines[i]}", end="")

