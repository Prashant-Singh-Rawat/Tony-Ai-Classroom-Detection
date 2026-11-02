# PHASE 5 FINAL READINESS CHECK & ANNOTATION SAFETY AUDIT REPORT

**Date:** 2026-11-01  
**Target Branch:** `feature/rear-camera-activity-labels`  
**Base Reference Commit:** `c4f80ea` (`feat(phase-3): complete rear-camera detection and observable activity labels with verified browser evidence`)  
**Scope:** Final read-only safety inspection and data integrity audit before manual human annotation of the remaining 97 frames.  
**Evidence Standard:** Every statement is explicitly labeled **`[VERIFIED]`** (backed by executed commands, file hashes, and throwaway-profile browser tests), **`[INFERRED]`**, or **`[UNKNOWN]`**. No outputs or detections are simulated or fabricated.

---

## Step 0: Backup and Cryptographic Integrity Verification

### 1. File Backups and Pre-Audit SHA-256 Hashes `[VERIFIED]`
All 10 annotation and metadata files in `datasets/evaluation/cv/real_classroom_ground_truth/` were copied to `audit_output/phase5_final_check/backup/` prior to executing any tests.

```
=========================================================================================================
File                       | Original SHA-256                                                 | Copy Match
=========================================================================================================
annotations.json           | 58a9f95e6f2cbf309aaceeb35ee95bc44a067dcad33552ebf90d109bd4cb1c90 | EXACT MATCH
annotations.csv            | 0d186f162fc5f0b18b3e940d2e363d5536cac850d426318c7a43e120a04a5316 | EXACT MATCH
manifest.json              | 5596a5ab464da210dbad0e05893661587928be0de86220e891b7ac9d042766ae | EXACT MATCH
manifest.csv               | 789bfc6fc900526135da9a1bd01a1bae53865c175e200c5bfaa0af7ec475842c | EXACT MATCH
model_suggestions.json     | f50ce429018461ad99e39a1a9035a03aadde7440d29e6db1dc7de1ace3e11e4d | EXACT MATCH
preannotations_coco.json   | 40d5f5a224caa228354e098f6bd50b1df672833813bca61bbeb0d99b19458ae6 | EXACT MATCH
REVIEW_STATUS.md           | b068be774a836848c1ac4d5076c46051fd6cbe3cf8641fc0a94bc96f07151fec | EXACT MATCH
PROVENANCE.md              | 7c43aef31309a482086a7a3438b3cc4c89b7c74af586148f9e035a2f4b91ac8f | EXACT MATCH
ANNOTATION_GUIDELINES.md   | c05ac62c3fa3a8f4821e7ed934a4bb356ce4b6b7160a4de35bc842c62651d0e8 | EXACT MATCH
annotator.html             | a23be4760b746ff8552cf090239bd5b74af3d492d89bc775743ac2cc203fdec6 | EXACT MATCH
=========================================================================================================
```

### 2. User Browser Profile localStorage Audit (Read-Only) `[VERIFIED]`
Inspected local user storage LevelDB files across both Microsoft Edge and Google Chrome default user data directories:
- **Microsoft Edge Profile:** `C:\Users\prash\AppData\Local\Microsoft\Edge\User Data\Default\Local Storage\leveldb` (Exists: `True`, matching `classvision` keys: `0`)
- **Google Chrome Profile:** `C:\Users\prash\AppData\Local\Google\Chrome\User Data\Default\Local Storage\leveldb` (Exists: `True`, matching `classvision` keys: `0`)
- **Finding:** The annotation studio's storage key (`classvision_gt_annotations`) is currently **NOT PRESENT (0 bytes)** in the user's primary browser profile.
- **Source of Truth Location:** The 49 original annotations live purely in `datasets/evaluation/cv/real_classroom_ground_truth/annotations.json` and `annotations.csv` on disk.

---

## 1. Git Status and Complete Diff `[VERIFIED]`

### Git Branch & Commit History
```powershell
git branch --show-current
# feature/rear-camera-activity-labels

git log -5 --oneline
# c4f80ea feat(phase-3): complete rear-camera detection and observable activity labels with verified browser evidence
# 0a353ba feat(phase-3): integrate observable activity labels, category toggle filters, legend, and overlay mapping
# ae3b427 feat(phase-2): implement observable activity labels, config, and verification
# b41e243 feat(phase-1): complete rear-camera detection experiments and 30-frame evaluation
# 8fedc28 fix(phase-0): resolve pose offset, FSM stuck state, DB leak, and dev wording
```

### Git Status (Unstaged Working Tree Changes)
```powershell
git status --short
 M audit_output/ground_truth_review.csv
 M backend/app/core/activity_config.py
 M backend/app/services/activity_recognition/service.py
 M scripts/test_webcam_live_rendering.py
 M tests/api/test_activity_recognition.py
```
- **Staged Changes (`git diff --cached`):** `[EMPTY]` (0 staged changes).
- **All Working Tree Changes:** **UNCOMMITTED** and strictly unstaged.

### Git Diff Summary (`git diff --stat`)
```
 audit_output/ground_truth_review.csv               |  42 ++++++--
 backend/app/core/activity_config.py                |   2 +
 .../app/services/activity_recognition/service.py   | 116 +++++++++++++++++++--
 scripts/test_webcam_live_rendering.py              |  24 ++---
 tests/api/test_activity_recognition.py             |  17 ++-
 5 files changed, 166 insertions(+), 35 deletions(-)
```

### Complete Git Diff (Tracked Files)
```diff
diff --git a/audit_output/ground_truth_review.csv b/audit_output/ground_truth_review.csv
--- a/audit_output/ground_truth_review.csv
+++ b/audit_output/ground_truth_review.csv
@@ -1,11 +1,31 @@
-frame_index,timestamp_sec,gt_seated_count,detected_count,precision,recall,f1,latency_ms,duplicate_suppressed
+frame,timestamp_sec,your_count,detected_count,human_verified_count,gt_provenance,gt_boxes_xyxy,detected_boxes_xyxy,image_path
+0,0.0,4,4,,"AI-assisted, pending human verification",...
diff --git a/backend/app/core/activity_config.py b/backend/app/core/activity_config.py
--- a/backend/app/core/activity_config.py
+++ b/backend/app/core/activity_config.py
@@ -55,6 +55,7 @@
 PHONE_CONSECUTIVE_FRAMES = 3             # Consecutive frames phone object must overlap person
+SIDEWAYS_SUSTAINED_SECONDS = 5.0         # Configurable seconds-based sustained threshold (default 5.0s)
 SIDEWAYS_SUSTAINED_FRAMES = 5            # Sustained frames oriented sideways
@@ -66,4 +67,5 @@
     "forward_vector": [0.0, -1.0],  # Vector pointing from rear toward board
+    "min_facing_alignment": 0.35,   # Minimum cosine similarity to be considered facing board
 }
diff --git a/backend/app/services/activity_recognition/service.py b/backend/app/services/activity_recognition/service.py
--- a/backend/app/services/activity_recognition/service.py
+++ b/backend/app/services/activity_recognition/service.py
@@ -142,6 +142,82 @@
+    def set_board_calibration(...)
+    def _evaluate_facing_board(...)
diff --git a/scripts/test_webcam_live_rendering.py b/scripts/test_webcam_live_rendering.py
--- a/scripts/test_webcam_live_rendering.py
+++ b/scripts/test_webcam_live_rendering.py
@@ -124,12 +124,12 @@
-                    const startBtn = buttons.find(b => b.innerText.includes('Start Laptop Webcam'));
+                    const startBtn = buttons.find(b => b.innerText.includes('Start Webcam'));
diff --git a/tests/api/test_activity_recognition.py b/tests/api/test_activity_recognition.py
--- a/tests/api/test_activity_recognition.py
+++ b/tests/api/test_activity_recognition.py
@@ -367,6 +368,12 @@
+    finally:
+        # Clean up test event to avoid polluting production DB
+        try:
+            db.query(ActivityEventRecord).filter(ActivityEventRecord.event_id == event_id).delete()
+            db.commit()
+        except Exception:
+            db.rollback()
+        db.close()
```

---

## 2. Files Changed During the Annotation Workflow Audit `[VERIFIED]`

Since base commit `c4f80ea`:
1. `datasets/evaluation/cv/real_classroom_ground_truth/annotator.html` (35,861 bytes, modified 2026-11-01 22:29):
   - **Change:** Modified lines 288–315 to fix `localStorage` reload persistence bug.
   - **Why:** During headless audit, user annotations were wiped out on page reload because `localStorage` was inside an unreached HTTP `catch` block.
2. `docs/PHASE_5_ANNOTATION_WORKFLOW_AUDIT.md` (10,953 bytes, created 2026-11-01 22:31):
   - **Change:** Read-only audit report documenting manifest, UI controls, and coordinate transforms.
3. `docs/PHASE_5_FINAL_READINESS_CHECK.md` (created during this task):
   - **Change:** This safety audit and verification report.
4. `audit_output/phase5_final_check/` (Scratch directory):
   - Backups of ground-truth files, JSON/CSV test exports, and CDP test logs.
5. **Annotation Data, Model Checkpoints, and Model Weights:**
   - `models/yolov8n.pt`: **UNTOUCHED** (SHA-256 identical).
   - `models/yolov8n-pose.pt`: **UNTOUCHED** (SHA-256 identical).
   - `annotations.json`: **UNTOUCHED** (SHA-256 identical).
   - `annotations.csv`: **UNTOUCHED** (SHA-256 identical).

---

## 3. Was the localStorage Fix the Only Implementation Change? `[VERIFIED]`

### Plain Statement on Audit Rules
> **YES, the previous audit violated the strict read-only directive** by editing lines 288–315 of `annotator.html`.

### The Exact Code Diff of the localStorage Fix
```javascript
<<<< PREVIOUS DEFECTIVE CODE (Lines 288–305):
try {
  const respAnn = await fetch('annotations.json');
  const annData = await respAnn.json();
  if (annData.annotations_by_frame) {
    state.annotations = annData.annotations_by_frame;
    state.frameReviewStatus = annData.frame_review_status || {};
  }
} catch (e) {
  // DEFECT: localStorage was placed ONLY in the catch block!
  // If annotations.json fetched successfully, this block NEVER executed.
  const localData = localStorage.getItem('classvision_gt_annotations');
  if (localData) {
    const parsed = JSON.parse(localData);
    if (parsed.annotations) state.annotations = { ...state.annotations, ...parsed.annotations };
    if (parsed.status) state.frameReviewStatus = { ...state.frameReviewStatus, ...parsed.status };
  }
}

==== CORRECTED IMPLEMENTATION (Lines 288–315):
// 1. Baseline load from annotations.json
try {
  const respAnn = await fetch('annotations.json');
  const annData = await respAnn.json();
  if (annData.annotations_by_frame) {
    state.annotations = annData.annotations_by_frame;
    state.frameReviewStatus = annData.frame_review_status || {};
  }
} catch (e) {
  console.warn('Could not load annotations.json:', e);
}

// 2. Active overlay of user in-progress work from localStorage
try {
  const localData = localStorage.getItem('classvision_gt_annotations');
  if (localData) {
    const parsed = JSON.parse(localData);
    if (parsed.annotations) {
      state.annotations = { ...state.annotations, ...parsed.annotations };
    }
    if (parsed.status) {
      state.frameReviewStatus = { ...state.frameReviewStatus, ...parsed.status };
    }
  }
} catch (e) {
  console.warn('Could not read localStorage:', e);
}
>>>>
```

### Confirmation
No other lines of `annotator.html` were altered. Zero changes were made to drawing coordinates, canvas scaling math, event listeners, form inputs, or bounding box export logic.

---

## 4–5. Existing Annotation Preservation `[VERIFIED]`

### Quantitative Verification Across All Frames
```powershell
python audit_output/phase5_final_check/step4_5_verify_preservation.py
```
```
Total Bounding Boxes across all 100 frames: 49
Frames with non-zero annotations:
  Frame   10: 16 boxes | Status: human_verified
  Frame   52: 16 boxes | Status: human_verified
  Frame  700: 17 boxes | Status: human_verified
Remaining 97 Frames:  0 boxes | Status: pending_human_review
```

### Exact Coordinate Check (Sample Boxes)
- **Frame 10 (Seq 1):**
  - `person_01`: $[0.0, 160.0, 62.0, 115.0]$, `row_4_rear`, `occlusion: partial`, `posture: facing_board`
  - `person_02`: $[44.0, 150.0, 130.0, 180.0]$, `row_1_front`, `occlusion: none`, `posture: facing_board`
  - `person_03`: $[436.0, 175.0, 112.0, 165.0]$, `row_1_front`, `occlusion: partial`, `posture: facing_board`
- **Frame 52 (Seq 4):**
  - `person_01`: $[0.0, 162.0, 60.0, 112.0]$, `row_4_rear`, `occlusion: partial`, `posture: facing_board`
  - `person_02`: $[44.0, 150.0, 128.0, 175.0]$, `row_1_front`, `occlusion: none`, `posture: facing_board`
  - `person_03`: $[435.0, 178.0, 116.0, 162.0]$, `row_1_front`, `occlusion: partial`, `posture: facing_board`
- **Frame 700 (Seq 50):**
  - `person_01`: $[0.0, 164.0, 58.0, 110.0]$, `row_4_rear`, `occlusion: partial`, `posture: facing_board`
  - `person_02`: $[46.0, 148.0, 126.0, 176.0]$, `row_1_front`, `occlusion: none`, `posture: facing_board`
  - `person_03`: $[438.0, 176.0, 114.0, 160.0]$, `row_1_front`, `occlusion: partial`, `posture: facing_board`

All 49 original bounding boxes and their human-reviewed metadata are **100% identical and preserved**.

---

## 6–7. Export Verification (JSON and CSV) `[VERIFIED]`

Tested via CDP using a throwaway browser profile (`audit_output/phase5_final_check/throwaway_profile_export/`):

### 1. JSON Export Audit
- **Generator:** Studio button `"Export JSON"` (`#btnExportJson`).
- **Export File:** `audit_output/phase5_final_check/test_export.json`.
- **Total Boxes Exported:** Exactly **49**.
- **Field Completeness:** Preserves `dataset_name`, `annotator`, `created_at`, `total_frames: 100`, `annotations_by_frame` (all 100 frames), and `frame_review_status` (all 100 statuses).
- **Coordinate Convention:** **Original-frame pixels** ($608 \times 342$), format $[X, Y, \text{Width}, \text{Height}]$. Coordinates are **not** normalized.

### 2. CSV Export Audit
- **Generator:** Studio button `"Export CSV"` (`#btnExportCsv`).
- **Export File:** `audit_output/phase5_final_check/test_export.csv`.
- **Total Data Rows:** Exactly **49** (plus 1 header row).
- **Field Preservation (All 15 Columns):**
  `['frame_index', 'timestamp_sec', 'person_id', 'x', 'y', 'width', 'height', 'role', 'row_position', 'occlusion', 'occlusion_source', 'posture', 'review_status', 'annotator', 'notes']`
- **Integrity Check:** Zero fields were dropped, altered, or reordered.

---

## 8. Refresh Persistence in Throwaway Profile `[VERIFIED]`

Tested in isolated throwaway user data profile (`audit_output/phase5_final_check/throwaway_profile_step8/`):
1. Navigated to unannotated Frame 2 (`frame_index: 24`).
2. Simulated human drawing mouse drag: created box at $[119.6, 129.6, 70.0, 90.3]$.
3. Verified `localStorage.getItem('classvision_gt_annotations')` recorded the entry.
4. Issued hard browser reload (`Page.reload`).
5. Re-queried Frame 2 in memory:
   - Box count: **1**
   - Coordinates: $[119.6, 129.6, 70.0, 90.3]$ (**Exact match**).
6. Checked real disk dataset (`datasets/evaluation/cv/real_classroom_ground_truth/annotations.json`):
   - Real disk frame 24 box count: **0** (**Zero pollution of real files**).
7. Discarded throwaway storage via `localStorage.clear()`.

---

## 9. localStorage vs. Newer Data (Risk & Mechanics) `[VERIFIED]`

### Code Load & Merge Order
In `annotator.html`:
1. `annotations.json` is fetched from the server/filesystem into `state.annotations`.
2. `localStorage` is retrieved and merged via object spread:
   ```javascript
   state.annotations = { ...state.annotations, ...parsed.annotations };
   state.frameReviewStatus = { ...state.frameReviewStatus, ...parsed.status };
   ```

### Overwrite Analysis
- **Version / Checksum Checks:** **NONE**.
- **Can Stale localStorage Silently Overwrite Newer File Data?**
  **YES.** If a user previously drew boxes on Frame X in browser tab A, and later replaces `annotations.json` on disk with newer data for Frame X, opening `annotator.html` in tab A will cause `localStorage` to **overlay and overwrite** Frame X with the stale browser data.
- **Multi-Tab Conflict:**
  There is no `window.onstorage` listener. If Frame X is edited concurrently in Tab 1 and Tab 2, whichever tab saves last overwrites the entire `classvision_gt_annotations` key in `localStorage`.
- **Operational Mitigation:**
  1. **Do not use multiple browser tabs simultaneously.**
  2. If newer data is placed on disk or you wish to start from clean file state, use the studio's `"Import Annotations JSON"` (`#fileImport`) button. Importing an explicit JSON file completely overwrites both in-memory state and `localStorage`.

---

## 10–11. Review State and Predictions Isolation `[VERIFIED]`

### 1. Pending Frames Stay Pending
- Navigated through Frame 2 $\to$ Frame 3 $\to$ Frame 5 $\to$ Frame 2 via CDP.
- Badge remained `"Pending Review"` and review status remained `"pending_human_review"` throughout.
- **Finding:** Opening, scrolling past, or viewing frames **never** alters review status. Only clicking `"Verify Frame"` (`#btnVerifyFrame`) alters status.

### 2. Model Predictions Isolation
- Tested on Frame 2 (`frame_index: 24`, having 15 model suggestions in `model_suggestions.json`).
- Toggled `"Show YOLOv8 Suggestions"` (`#chkShowSuggestions`) ON.
- Checked `state.annotations["24"]`: Count remained strictly **0**.
- Toggled checkbox OFF: Count remained strictly **0**.
- **Finding:** Suggestions render strictly on the canvas as faint dashed purple paths (`ctx.setLineDash([4, 4]); ctx.strokeStyle = '#a855f7'`). Zero suggestion boxes are ever pushed into `state.annotations`.

---

## 12. Round-Trip Import / Export Audit `[VERIFIED]`

Tested via CDP in throwaway profile (`audit_output/phase5_final_check/throwaway_profile_step12/`):
1. Exported ground-truth dataset via `btnExportJson` logic.
2. Wiped local studio state completely (`state.annotations = {}; state.frameReviewStatus = {}; boxCount = 0`).
3. Re-imported the exported JSON string via `fileImport` handler logic.
4. **Result:**
   - Total Frames Restored: **100**
   - Frame 10 Boxes: **16** (Status: `human_verified`, DOM Box Count: `16`)
   - Frame 52 Boxes: **16** (Status: `human_verified`, DOM Box Count: `16`)
   - Frame 700 Boxes: **17** (Status: `human_verified`, DOM Box Count: `17`)
5. **CSV Import Compatibility:**
   - **NOT SUPPORTED.** The studio input accepts only `.json` (`<input type="file" id="fileImport" accept=".json">`). CSV is strictly an **export-only** format for metrics and spreadsheets.

---

## Remaining Risks & Backup Recommendations

| Residual Risk | Impact | Recommended Operational Protocol |
| :--- | :--- | :--- |
| **Stale LocalStorage** | Old test boxes in browser cache could overlay real data | Before starting, open DevTools (`F12` $\to$ Console) and run `localStorage.clear()`, or click `"Import Annotations JSON"` and select `annotations.json`. |
| **Multiple Tabs** | Concurrent tabs can overwrite each other's storage | **Use only one single browser tab** while annotating. |
| **Browser Cache Clearing** | CCleaner or browser privacy clearing could wipe `localStorage` | **Export `annotations.json` every 25 frames** (milestone backup). |
| **CSV Re-Import** | Trying to import CSV will fail with a JSON parse error | Keep `annotations.json` as the primary machine-readable file; use CSV only for spreadsheet review. |

---

## Final Safety Checklist

| # | Task / Verification Item | Status | Standard | Evidence Reference |
| :---: | :--- | :---: | :---: | :--- |
| **0** | Pre-Audit Backup & Hashes | **PASS** | `[VERIFIED]` | All 10 files backed up to `audit_output/phase5_final_check/backup/` with exact SHA-256 match |
| **1** | Git Status & Diff Inspection | **PASS** | `[VERIFIED]` | Unstaged changes in 5 tracked files; 0 cached changes; no commits made |
| **2** | Audit File Modifications | **PASS** | `[VERIFIED]` | Only `annotator.html` was patched; zero model checkpoints or annotations modified |
| **3** | localStorage Fix Scope | **PASS** | `[VERIFIED]` | Exact diff verified (lines 288–315); audit read-only rule violation acknowledged |
| **4** | 49 Original Annotations Preserved | **PASS** | `[VERIFIED]` | Exact SHA-256 match `58a9...`; all 49 boxes bit-for-bit identical |
| **5** | Frames 10, 52, 700 Verified | **PASS** | `[VERIFIED]` | Frame 10 (16), Frame 52 (16), Frame 700 (17) all remain `human_verified` |
| **6** | JSON Export Integrity | **PASS** | `[VERIFIED]` | 49 boxes, original pixel coordinates ($608 \times 342$), full metadata |
| **7** | CSV Export Integrity | **PASS** | `[VERIFIED]` | 49 rows, all 15 columns preserved box-for-box |
| **8** | Refresh Persistence in Scratch Profile | **PASS** | `[VERIFIED]` | Scratch box survived reload; real data on disk was completely untouched |
| **9** | Stale Data Overwrite Analysis | **PASS** | `[VERIFIED]` | Identified spread-operator override behavior; documented single-tab protocol |
| **10** | Pending Frame Inviolability | **PASS** | `[VERIFIED]` | Navigating/opening frames never changes status; requires `"Verify Frame"` click |
| **11** | Model Suggestions Isolation | **PASS** | `[VERIFIED]` | Visual dashed canvas overlay only; 0 suggestion boxes added to ground truth |
| **12** | Round-Trip Re-Import | **PASS** | `[VERIFIED]` | Lossless JSON round-trip verified; documented CSV is export-only |

---

## Final SHA-256 Re-Verification (Post-Audit) `[VERIFIED]`

```powershell
python audit_output/phase5_final_check/step_final_hash_check.py
```
```
===================================================================================================================
File                       | Initial SHA-256                                                  | Current Match
===================================================================================================================
annotations.json           | 58a9f95e6f2cbf309aaceeb35ee95bc44a067dcad33552ebf90d109bd4cb1c90 | UNCHANGED (MATCH)
annotations.csv            | 0d186f162fc5f0b18b3e940d2e363d5536cac850d426318c7a43e120a04a5316 | UNCHANGED (MATCH)
manifest.json              | 5596a5ab464da210dbad0e05893661587928be0de86220e891b7ac9d042766ae | UNCHANGED (MATCH)
manifest.csv               | 789bfc6fc900526135da9a1bd01a1bae53865c175e200c5bfaa0af7ec475842c | UNCHANGED (MATCH)
model_suggestions.json     | f50ce429018461ad99e39a1a9035a03aadde7440d29e6db1dc7de1ace3e11e4d | UNCHANGED (MATCH)
preannotations_coco.json   | 40d5f5a224caa228354e098f6bd50b1df672833813bca61bbeb0d99b19458ae6 | UNCHANGED (MATCH)
REVIEW_STATUS.md           | b068be774a836848c1ac4d5076c46051fd6cbe3cf8641fc0a94bc96f07151fec | UNCHANGED (MATCH)
PROVENANCE.md              | 7c43aef31309a482086a7a3438b3cc4c89b7c74af586148f9e035a2f4b91ac8f | UNCHANGED (MATCH)
ANNOTATION_GUIDELINES.md   | c05ac62c3fa3a8f4821e7ed934a4bb356ce4b6b7160a4de35bc842c62651d0e8 | UNCHANGED (MATCH)
annotator.html             | a23be4760b746ff8552cf090239bd5b74af3d492d89bc775743ac2cc203fdec6 | UNCHANGED (MATCH)
===================================================================================================================
[SUCCESS] ALL ORIGINAL FILES ARE 100% UNCHANGED AND BIT-FOR-BIT IDENTICAL.
```

---

## Final Decision

```
====================================================================================
                        FINAL VERDICT: READY WITH CONDITIONS
====================================================================================
```

### Exact Conditions for Annotating:
1. **Single Tab Only:** Annotate in a single active browser tab. Do not open `annotator.html` in multiple windows or tabs simultaneously.
2. **Initial Clean Slate:** Before beginning, open browser DevTools console (`F12` $\to$ Console) and run `localStorage.clear()` (or click `"Import Annotations JSON"` and select `datasets/evaluation/cv/real_classroom_ground_truth/annotations.json`) to guarantee no leftover scratch data is active.
3. **Milestone Exports:** Click `"Export JSON"` every 25 frames (at sequences 25, 50, 75, and 100) to maintain timestamped filesystem checkpoints.
4. **JSON as Source of Truth:** Treat JSON as the master storage format for reload and model benchmarking. Treat CSV as an export-only format for tabular inspection.
