with open("frontend/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

def find_section_bounds(section_id):
    start = None
    end = None
    for i, line in enumerate(lines):
        if f'id="{section_id}"' in line:
            start = i
            break
    if start is None:
        return None, None
    # Look for matching </section>
    for j in range(start, len(lines)):
        if '</section>' in lines[j]:
            end = j
            break
    return start + 1, end + 1

for s_id in ["screen-prediction", "screen-simulator", "screen-history"]:
    st, en = find_section_bounds(s_id)
    print(f"Section {s_id}: Lines {st} to {en} (length {en - st + 1 if en else 0} lines)")

