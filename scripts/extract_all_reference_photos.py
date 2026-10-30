"""
Extract all 8 real drain photographs from the reference screenshot
and save them into data/sample_images/ as clean, high-resolution images.
"""

import cv2
import numpy as np
from pathlib import Path

SRC_IMG = r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810\.user_uploaded\media_1793342534905_fb027599.jpg"
OUT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\sample_images")
OUT_DIR.mkdir(parents=True, exist_ok=True)

img = cv2.imread(SRC_IMG)
if img is None:
    raise RuntimeError(f"Could not load {SRC_IMG}")

h, w = img.shape[:2]
print(f"Loaded reference UI: {w}x{h}")

# In the 1024x935 screenshot:
# Columns for the 4 card columns:
# Card 1 & 5: x ~ [162, 351]
# Card 2 & 6: x ~ [378, 569]
# Card 3 & 7: x ~ [597, 786]
# Card 4 & 8: x ~ [814, 1001]

# Row 1 (Cards 1 to 4):
# y ~ [291, 401]
# Row 2 (Cards 5 to 8):
# Let's find exact row 2 y range

# Let's scan row 2 vertically at x=250 between y=600 and 780
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

cols = [
    (162, 351), # Col 1
    (378, 569), # Col 2
    (597, 786), # Col 3
    (814, 1001), # Col 4
]

# For each column, find exact top and bottom of photo in row 1 and row 2
# Photo pixels are non-white (gray < 245)
# In row 1: between y=285 and y=410
# In row 2: between y=650 and y=780

def find_photo_box(x1, x2, y_search_start, y_search_end):
    # take center slice
    mid_x = (x1 + x2) // 2
    slice_col = gray[y_search_start:y_search_end, mid_x]
    non_white = np.where(slice_col < 240)[0]
    if len(non_white) == 0:
        return y_search_start, y_search_end
    y_top = y_search_start + non_white[0]
    y_bot = y_search_start + non_white[-1] + 1
    return y_top, y_bot

card_names = [
    ("drain_d01_rajwada.jpg", 0, 280, 415),
    ("drain_d02_palasia.jpg", 1, 280, 415),
    ("drain_d03_scheme54.jpg", 2, 280, 415),
    ("drain_d04_vijaynagar.jpg", 3, 280, 415),
    ("drain_d05_mhownaka.jpg", 0, 650, 780),
    ("drain_d06_khandwaroad.jpg", 1, 650, 780),
    ("drain_d07_chappandukan.jpg", 2, 650, 780),
    ("drain_d08_electroniccity.jpg", 3, 650, 780),
]

for filename, col_idx, ys, ye in card_names:
    x1, x2 = cols[col_idx]
    y1, y2 = find_photo_box(x1, x2, ys, ye)
    # Check bounds
    crop = img[y1:y2, x1:x2]
    # Resize slightly to standard 640x360 (16:9) high-quality ratio
    upscaled = cv2.resize(crop, (640, 360), interpolation=cv2.INTER_CUBIC)
    out_path = OUT_DIR / filename
    cv2.imwrite(str(out_path), upscaled, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"Extracted {filename}: [{y1}:{y2}, {x1}:{x2}] -> saved {out_path} ({upscaled.shape})")

print("All 8 drain photographs extracted successfully!")
