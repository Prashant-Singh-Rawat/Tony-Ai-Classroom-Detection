# Kaggle English Character Recognition Dataset — Information Report

**Dataset ID**: `ds_kaggle_english_character_recognition_v1`  
**Location**: `datasets/kaggle/handwriting/english_character_recognition/`  
**Origin**: `KAGGLE DATA`  
**License**: `UNKNOWN` (Sourced from Kaggle archive without explicit license file included)  
**Source URL**: `UNKNOWN` (Downloaded from Kaggle user archive)  
**Acquisition Date**: 2026-10-31  
**Integrity**: Verified (0 corrupted files across 210,227 total images)  

---

## 1. Dataset Overview

The dataset consists of handwritten and printed alphanumeric characters partitioned into 62 distinct class folders:
- **Digits (0-9)**: 10 classes (`0` through `9`), 3,473 images each (34,730 total).
- **Uppercase Letters (A-Z)**: 26 classes (`A_U` through `Z_U`), 3,473 images each (90,298 total).
- **Lowercase Letters (a-z)**: 26 classes (`a_L` through `z_L`), between 3,274 and 3,284 images each (85,199 total).

**Total Images**: 210,227  
**Total Classes**: 62  

---

## 2. Image Specifications

- **Format**: PNG (`image/png`)
- **Dimensions**: 40 pixels (width) x 60 pixels (height)
- **Color Mode**: RGB (3 channels, 8-bit unsigned integer per channel)
- **Orientation**: Upright centered character glyphs on light background with dark stroke pixels.

---

## 3. Class Inventory & Counts

| Category | Folder Name | Character Represented | Sample Count |
| :--- | :--- | :---: | :---: |
| Digits | `0` to `9` | `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9` | 3,473 each (34,730) |
| Uppercase Letters | `A_U` to `Z_U` | `A` through `Z` | 3,473 each (90,298) |
| Lowercase Letters | `a_L` to `z_L` | `a` through `z` | 3,274 to 3,284 each (85,199) |

---

## 4. Privacy & Compliance

- **No Real Classroom Video**: The dataset consists solely of isolated character glyph crops.
- **No Student Identity / Biometrics**: No faces, names, voices, or identifiable individual student attributes are present.
- **Local Storage Only**: All dataset storage and training computations remain 100% on local host storage.

