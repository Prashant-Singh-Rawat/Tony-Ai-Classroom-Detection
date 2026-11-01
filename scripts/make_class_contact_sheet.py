#!/usr/bin/env python3
"""
scripts/make_class_contact_sheet.py — Deterministic Hand Gesture Contact Sheet Generator.

Features:
- Deterministic, evenly spaced selection of N representative images per class (default N=12).
- In-memory 3x nearest-neighbor upscaling (50x50 -> 150x150) preserving raw pixel fidelity.
- Generates:
    1. Combined contact sheet (Classes 0-19)
    2. Half-sheet 1 (Classes 0-9)
    3. Half-sheet 2 (Classes 10-19)
    4. Markdown visual inspection report (class_visual_inspection.md)
- Zero model training, zero dataset image modification on disk.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DEFAULT_N = 12
UPSCALE_FACTOR = 3  # 50x50 -> 150x150
UPSCALE_METHOD = "3x nearest-neighbor (Image.Resampling.NEAREST)"


def get_sorted_image_files(class_dir: Path) -> list[Path]:
    """Return image files sorted in natural/lexicographic order."""
    if not class_dir.is_dir():
        raise FileNotFoundError(f"Class folder not found: {class_dir}")

    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    files = [p for p in class_dir.iterdir() if p.is_file() and p.suffix.lower() in valid_exts]

    if not files:
        raise ValueError(f"Class folder is empty or has no supported images: {class_dir}")

    # Natural sort: sort numerically by stem if digits, else lexicographically
    def sort_key(p: Path) -> tuple[int, str]:
        stem = p.stem
        if stem.isdigit():
            return (int(stem), p.name)
        return (sys.maxsize, p.name)

    return sorted(files, key=sort_key)


def select_deterministic_indices(total_count: int, n: int = DEFAULT_N) -> list[int]:
    """Pick N evenly spaced integer indices from total_count items."""
    if total_count <= 0:
        return []
    if total_count <= n:
        return list(range(total_count))
    # Evenly spaced integer indices from 0 to total_count - 1
    return [round(i * (total_count - 1) / (n - 1)) for i in range(n)]


def select_representative_files(class_dir: Path, n: int = DEFAULT_N) -> list[Path]:
    """Select exactly N representative files deterministically from class_dir."""
    all_files = get_sorted_image_files(class_dir)
    indices = select_deterministic_indices(len(all_files), n)
    return [all_files[idx] for idx in indices]


def get_font(size: int = 18) -> ImageFont.ImageFont:
    """Attempt to load a clean TTF font; fall back to default PIL font."""
    font_candidates = [
        "arial.ttf",
        "DejaVuSans.ttf",
        "SegoeUI.ttf",
        "tahoma.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segui.ttf",
    ]
    for cand in font_candidates:
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_sheet_image(
    class_data: list[tuple[str, list[Path]]],
    title: str,
    n_per_class: int = DEFAULT_N,
) -> Image.Image:
    """Draw a contact sheet for the given classes and their representative images."""
    thumb_w = 50 * UPSCALE_FACTOR
    thumb_h = 50 * UPSCALE_FACTOR
    label_w = 150
    margin_x = 24
    margin_y = 20
    gap = 8
    header_h = 60

    num_classes = len(class_data)
    row_w = label_w + n_per_class * thumb_w + (n_per_class - 1) * gap
    total_w = row_w + 2 * margin_x
    total_h = header_h + num_classes * (thumb_h + gap) + 2 * margin_y

    # Create canvas (dark slate background)
    canvas = Image.new("RGB", (total_w, total_h), color=(26, 28, 35))
    draw = ImageDraw.Draw(canvas)

    title_font = get_font(22)
    label_font = get_font(18)
    sub_font = get_font(12)

    # Draw header
    draw.text((margin_x, margin_y), title, fill=(240, 240, 245), font=title_font)
    subtitle = f"Visual Inspection Only — {num_classes} Classes | {n_per_class} evenly-spaced samples per class | 3x Nearest-Neighbor Upscale"
    draw.text((margin_x, margin_y + 30), subtitle, fill=(160, 165, 180), font=sub_font)

    current_y = header_h + margin_y

    for class_id, img_paths in class_data:
        # Draw class label block
        label_text = f"Class {class_id}"
        draw.text((margin_x, current_y + thumb_h // 2 - 12), label_text, fill=(255, 215, 0), font=label_font)

        current_x = margin_x + label_w

        for img_path in img_paths:
            try:
                with Image.open(img_path) as raw_img:
                    # In-memory 3x nearest-neighbor upscaling
                    rgb_img = raw_img.convert("RGB")
                    upscaled = rgb_img.resize((thumb_w, thumb_h), Image.Resampling.NEAREST)
            except Exception as e:
                raise RuntimeError(f"Failed to load/decode image {img_path}: {e}")

            canvas.paste(upscaled, (current_x, current_y))
            # Draw subtle cell border
            draw.rectangle(
                [current_x - 1, current_y - 1, current_x + thumb_w, current_y + thumb_h],
                outline=(50, 54, 68),
            )
            current_x += thumb_w + gap

        current_y += thumb_h + gap

    return canvas


def generate_markdown_report(
    class_table_rows: list[dict],
    output_path: Path,
    n_per_class: int,
) -> None:
    """Generate class_visual_inspection.md with required table and human notes section."""
    md = f"""# Hand Gesture Dataset — Class Visual Inspection Report

## Notice to Human Reviewer
> **IMPORTANT**: This document and the associated contact sheets are prepared exclusively for **HUMAN VISUAL INSPECTION**.
> No class meanings or gesture labels are assumed by the system.
> The determination of what gesture each class index (0–19) represents must be made and verified by a human expert.

---

## 1. Inspection Parameters & Reproducibility
- **Selection Method**: Deterministic evenly spaced sampling over naturally sorted filenames.
- **Images Per Class Displayed (N)**: {n_per_class}
- **Upscaling Method**: {UPSCALE_METHOD} (in-memory only; 0 dataset files modified)
- **Primary Contact Sheet**: [`hand_gesture_class_contact_sheet.png`](hand_gesture_class_contact_sheet.png)
- **Half Sheets**: [`hand_gesture_class_contact_sheet_0_9.png`](hand_gesture_class_contact_sheet_0_9.png), [`hand_gesture_class_contact_sheet_10_19.png`](hand_gesture_class_contact_sheet_10_19.png)

---

## 2. Class Overview Table

| Class ID | Training images | Test images | Representative image filenames (train) | Semantic meaning |
| :---: | :---: | :---: | :--- | :---: |
"""

    for row in class_table_rows:
        samples_str = ", ".join(f"`{name}`" for name in row["sample_filenames"])
        md += f"| `{row['class_id']}` | {row['train_count']} | {row['test_count']} | {samples_str} | **{row['semantic_meaning']}** |\n"

    md += """
---

## 3. Human Visual Notes
*(To be completed by a human reviewer after viewing the contact sheets. Do not automate.)*

"""
    for row in class_table_rows:
        md += f"- **Class {row['class_id']}**: (to be filled in by a human after viewing the contact sheet)\n"

    md += """
---

## 4. Policy Compliance
- **Model Training**: NONE (no model loaded, trained, or evaluated)
- **Dataset Modification**: NONE (0 images resized or altered on disk)
- **Automatic Class Labeling**: PROHIBITED (all semantic meanings stay strictly `NOT VERIFIED`)
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Saved visual inspection markdown report to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic hand gesture class contact sheet.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(r"c:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection"),
        help="Project root directory",
    )
    parser.add_argument(
        "-n",
        "--num-samples",
        type=int,
        default=DEFAULT_N,
        help="Number of representative samples per class (default 12)",
    )
    args = parser.parse_args()

    hg_root = args.root / "datasets" / "kaggle" / "hand_gesture"
    train_dir = hg_root / "extracted" / "train"
    test_dir = hg_root / "extracted" / "test"
    metadata_dir = hg_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    if not train_dir.exists():
        print(f"ERROR: Train directory missing: {train_dir}", file=sys.stderr)
        return 1

    classes = sorted(
        [d.name for d in train_dir.iterdir() if d.is_dir()],
        key=lambda x: int(x) if x.isdigit() else x,
    )

    if not classes:
        print(f"ERROR: No class directories found in {train_dir}", file=sys.stderr)
        return 1

    print(f"Processing {len(classes)} classes with N={args.num_samples}...")

    class_data: list[tuple[str, list[Path]]] = []
    class_table_rows: list[dict] = []

    for c in classes:
        c_train_folder = train_dir / c
        rep_files = select_representative_files(c_train_folder, args.num_samples)
        class_data.append((c, rep_files))

        # Test count
        c_test_folder = test_dir / c
        test_count = len(list(c_test_folder.glob("*.jpg"))) if c_test_folder.exists() else 0
        train_count = len(list(c_train_folder.glob("*.jpg")))

        class_table_rows.append(
            {
                "class_id": c,
                "train_count": train_count,
                "test_count": test_count,
                "sample_filenames": [p.name for p in rep_files],
                "semantic_meaning": "NOT VERIFIED",
            }
        )

    # 1. Full combined sheet (all 20 classes)
    combined_img = create_sheet_image(
        class_data,
        "ClassVision AI — Hand Gesture Dataset: Classes 0 to 19",
        args.num_samples,
    )
    combined_path = metadata_dir / "hand_gesture_class_contact_sheet.png"
    combined_img.save(combined_path)
    print(f"Saved combined contact sheet ({combined_img.size[0]}x{combined_img.size[1]}) to {combined_path}")

    # 2. Half-sheet 0-9
    half1_data = class_data[:10]
    half1_img = create_sheet_image(
        half1_data,
        "ClassVision AI — Hand Gesture Dataset: Classes 0 to 9",
        args.num_samples,
    )
    half1_path = metadata_dir / "hand_gesture_class_contact_sheet_0_9.png"
    half1_img.save(half1_path)
    print(f"Saved half-sheet 0-9 ({half1_img.size[0]}x{half1_img.size[1]}) to {half1_path}")

    # 3. Half-sheet 10-19
    half2_data = class_data[10:]
    half2_img = create_sheet_image(
        half2_data,
        "ClassVision AI — Hand Gesture Dataset: Classes 10 to 19",
        args.num_samples,
    )
    half2_path = metadata_dir / "hand_gesture_class_contact_sheet_10_19.png"
    half2_img.save(half2_path)
    print(f"Saved half-sheet 10-19 ({half2_img.size[0]}x{half2_img.size[1]}) to {half2_path}")

    # 4. Generate markdown report
    md_path = metadata_dir / "class_visual_inspection.md"
    generate_markdown_report(class_table_rows, md_path, args.num_samples)

    return 0


if __name__ == "__main__":
    sys.exit(main())
