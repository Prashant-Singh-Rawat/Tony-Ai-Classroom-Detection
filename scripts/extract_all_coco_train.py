"""
scripts/extract_all_coco_train.py — Extract complete COCO train2017 images
========================================================================
Extracts all remaining training images from C:\\Users\\prash\\Downloads\\COCO_Keypoints.zip
into datasets/kaggle/human_pose/coco_keypoints/train2017/
Non-destructive: skips files that already exist.
"""

import sys
import time
import zipfile
from pathlib import Path

ZIP_PATH = Path(r"C:\Users\prash\Downloads\COCO_Keypoints.zip")
TARGET_DIR = Path("datasets/kaggle/human_pose/coco_keypoints/train2017")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

if not ZIP_PATH.is_file():
    print(f"Error: Archive not found at {ZIP_PATH}", file=sys.stderr)
    sys.exit(1)

t0 = time.time()
print(f"Opening {ZIP_PATH}...")
with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    train_members = [
        m for m in zf.namelist() if m.startswith("coco2017/train2017/") and m.endswith(".jpg")
    ]
    total = len(train_members)
    print(f"Found {total} train images in archive.")

    extracted = 0
    skipped = 0

    for idx, member in enumerate(train_members, 1):
        filename = member.split("/")[-1]
        out_file = TARGET_DIR / filename
        if out_file.exists():
            skipped += 1
            continue

        with zf.open(member) as src_f, open(out_file, "wb") as dst_f:
            dst_f.write(src_f.read())
        extracted += 1

        if idx % 5000 == 0 or idx == total:
            elapsed = time.time() - t0
            rate = idx / elapsed if elapsed > 0 else 0
            print(f"Progress: {idx}/{total} ({idx/total*100:.1f}%) | {rate:.1f} img/s | Extracted: {extracted}, Skipped: {skipped}")

print(f"Completed! Total: {total}, Extracted: {extracted}, Skipped: {skipped} in {time.time()-t0:.2f}s")

