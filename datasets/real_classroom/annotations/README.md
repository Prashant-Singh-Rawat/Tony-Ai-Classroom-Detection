# Classroom Hand-Raise Annotation Protocol

## Overview & Scope
Annotations in ClassVision AI are defined **per individual person** within each frame, NOT per whole frame.
Every visible student in an extracted frame must be enclosed in a bounding box with an assigned class.

---

## 1. Annotation Format (YOLO)
Each annotated frame corresponds to a text file with the identical base name:
`<session_id>/<video_stem>_t<timestamp_ms>.txt`

Each line contains space-separated values:
```text
<class_id> <x_center> <y_center> <width> <height>
```
- `<class_id>`: Integer in `{0, 1, 2}`
  - `0`: `hand_raised` — Hand raised to participate or ask a question.
  - `1`: `hand_not_raised` — Resting, writing, typing, resting head on arm, touching chin/glasses.
  - `2`: `ambiguous` — Occluded hand, stretching, partial raise below shoulder, or uncertain gesture.
- `<x_center> <y_center> <width> <height>`: Bounding box coordinates normalized to `[0.0, 1.0]`.

---

## 2. Ambiguous Box Policy
- **Excluded from Training**: Ambiguous boxes are omitted when constructing model training batches.
- **Excluded from Accuracy Metrics**: Performance metrics (Precision, Recall, mAP) evaluate only `hand_raised` (0) and `hand_not_raised` (1).
- **Quality Assurance**: Ambiguous labels are counted and logged to track boundary ambiguity and provide test cases for `NEEDS_REVIEW` escalation.

---

## 3. Two-Pass Verification Workflow
1. `annotations/raw/`: First-pass annotations produced by primary annotator.
2. `annotations/reviewed/`: Second-pass verification by an independent reviewer.
   - **MANDATORY**: Only annotations present in `annotations/reviewed/` can be used by `scripts/split_classroom_dataset.py` for train/val/test splits or model training.
3. `annotations/annotation_index.csv`:
   Header: `frame_id,annotator,reviewed,review_date`
   Tracks the review state and timestamp for each labeled frame.

---

## 4. Local-Only Annotation Tools
To prevent unauthorized cloud synchronization of student footage, use **strictly local tools**:
- **CVAT Local**: Run CVAT on local Docker (`localhost:8080`).
- **Label Studio**: Run `label-studio start` locally.
- **LabelImg**: Lightweight desktop application for YOLO bounding boxes.

> **DO NOT** use public or SaaS cloud annotation tools (Roboflow Cloud, CVAT Cloud, Labelbox) for student footage.
