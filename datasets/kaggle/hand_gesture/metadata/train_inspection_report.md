# Hand Gesture Dataset — Training Partition Inspection Report (Phase 0.4)

## 1. Overview
- **Dataset Name**: Kaggle Hand Gesture Recognition Dataset (User-Provided)
- **Training Archive**: `datasets/kaggle/hand_gesture/raw/train.zip`
- **Archive Size**: 28,591,574 bytes (27.27 MB)
- **Archive SHA-256**: `f14185c413f165952f932f0b8d8ab7188a8b004524b5f9b511cdb031b85dac12`
- **Extraction Directory**: `datasets/kaggle/hand_gesture/extracted/train/`
- **Date Inspected**: 2026-09-30
- **Total Training Images**: **18,000**
- **Total Classes**: **20** (`0` through `19`)

---

## 2. Training Partition Metrics

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Total Images** | **18,000** | 100% verified decoded |
| **Total Classes** | **20** | `0` through `19` |
| **Images Per Class** | Exactly **900** per class | Perfectly balanced (std = 0.0) |
| **Image Dimensions** | **50 × 50 pixels** | 100% of images (18,000/18,000) |
| **File Formats** | **JPEG (`.jpg`)** | Standard JPEG 3-channel RGB |
| **Corrupted Files** | **0** | Verified via PIL integrity check |
| **Zero-Byte Files** | **0** | All image files contain non-zero byte payloads |
| **Empty Folders** | **0** | Every class folder contains exactly 900 files |
| **Class Semantics** | **NOT VERIFIED** | Numerical folders 0–19; no meanings assumed |
| **License Status** | **NOT YET VERIFIED** | Source license unbundled in local archive |

---

## 3. Class Distribution & Comparison with Test Set

| Class ID | Train Image Count | Test Image Count | Ratio (Train : Test) | Verified Semantic Meaning |
| :---: | :---: | :---: | :---: | :--- |
| `0` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `1` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `2` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `3` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `4` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `5` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `6` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `7` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `8` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `9` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `10` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `11` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `12` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `13` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `14` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `15` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `16` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `17` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `18` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| `19` | 900 | 300 | 3 : 1 (75% / 25%) | CLASS SEMANTICS NOT YET VERIFIED |
| **Total** | **18,000** | **6,000** | **3 : 1 (75% / 25%)** | **Balanced across 20 numerical classes** |

---

## 4. Train vs Test Comparison & Leakage Analysis

### 4.1 Class Compatibility
- **Train Class IDs**: `['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']`
- **Test Class IDs**: `['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']`
- **Train / Test Class IDs Match Exactly**: **YES** (100% identical 20 classes `0` through `19`)
- **Train-Only Classes**: None
- **Test-Only Classes**: None

### 4.2 Dimension & Format Consistency
- Both partitions feature exclusively **50 × 50 pixel** resolution images.
- Both partitions use standard **JPEG (`.jpg`)** encoding.

### 4.3 Overlap / Data Leakage Check
- **Methodology**: SHA-256 cryptographic hashes computed for all 18,000 training images and matched against the 6,000 test hashes.
- **Exact Duplicate Overlap Count**: **0**
- **Conclusion**: There are **zero exact-duplicate images** shared between the training set and the test set. The dataset partitions are completely disjoint at the cryptographic level.

---

## 5. Non-Destructive Invariant Compliance
- **Models Trained**: NONE
- **Augmentation**: NONE
- **Preprocessing / Resizing**: NONE
- **Class Renaming**: NONE (classes kept strictly as `0` through `19`)
- **Image Deletions / Modifications**: 0
