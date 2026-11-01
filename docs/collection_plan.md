# Real Classroom Data Collection Plan & Privacy Architecture

## 1. OneDrive Privacy Warning & Storage Configuration

> [!CAUTION]
> **CRITICAL PRIVACY WARNING: ONEDRIVE SYNC RISK**
> The project codebase resides inside a OneDrive-synchronized folder path (`.../OneDrive/...`).
> Classroom footage contains identifiable images, video, and audio of students and instructors.
> **DO NOT** store raw classroom videos, extracted frames, audio recordings, or student annotations inside a folder synced to Microsoft OneDrive or any third-party cloud storage service, unless institutional ethics clearance explicitly authorizes cloud processing.

### Configuring Non-Synced Storage via `CLASSVISION_REAL_DATA_ROOT`
All data ingestion and processing scripts resolve the data directory in the following priority order:
1. `--root <PATH>` command-line argument
2. `CLASSVISION_REAL_DATA_ROOT` environment variable
3. Default path: `datasets/real_classroom` (relative to repository root)

#### Windows Setup Instructions

##### Option A: User Environment Variable (Permanent)
Run in PowerShell:
```powershell
[Environment]::SetEnvironmentVariable("CLASSVISION_REAL_DATA_ROOT", "D:\ClassVisionData\real_classroom", "User")
```
Or in Windows Command Prompt:
```cmd
setx CLASSVISION_REAL_DATA_ROOT "D:\ClassVisionData\real_classroom"
```

##### Option B: Current Terminal Session (Temporary)
In PowerShell:
```powershell
$env:CLASSVISION_REAL_DATA_ROOT = "D:\ClassVisionData\real_classroom"
```
In Command Prompt:
```cmd
set CLASSVISION_REAL_DATA_ROOT=D:\ClassVisionData\real_classroom
```

##### Option C: Explicit CLI Argument
Pass `--root` directly when invoking any script:
```bash
python scripts/extract_classroom_frames.py --root "D:\ClassVisionData\real_classroom"
```

### Zero Cloud Transmission Guarantee
- All frame extraction, perceptual hashing, quality analysis, annotation verification, and dataset splitting execute **100% offline**.
- No script transmits data over the network or connects to cloud endpoints.

---

## 2. Collection Guidance & Positive-Class Strategy

### The Hand-Raise Imbalance Problem
In natural classroom footage, students spend 95%+ of class time with hands not raised. Spontaneous hand raises are brief (2–10 seconds) and infrequent. Training solely on unscripted classroom video leads to severe class imbalance.

### Dual-Source Protocol
To construct a balanced and representative benchmark:
1. **Consented Scripted Segments**:
   - Organise structured sessions with consented student volunteers.
   - Prompt participants to raise hands in varied styles (left hand, right hand, high raise, elbow-on-desk raise, waving).
   - Vary body postures, attire, and seat locations.
2. **Natural Classroom Sessions**:
   - Record authentic lectures and discussion seminars with full institutional consent.
   - Capture real-world noise: fidgeting, scratching head, resting chin on hand, typing on laptops, writing notes.
3. **Transparent Metric Reporting**:
   - All reports must explicitly distinguish and display the ratio of `hand_raised` to `hand_not_raised`.

### Definition of the 1,000 Target
The target figure of **1,000 instances** refers strictly to **reviewed images with verified bounding box annotations**, NOT raw video frames.

---

## 3. Session Metadata & Diversity Checklist

A `session_id` designates a continuous recording block (e.g. one class period or one camera placement). Multiple video camera angles from the same lecture belong to the same session.

For each session, record the following environmental parameters in `datasets/real_classroom/metadata/sessions.csv` without recording any student names or personal identifiers:

| Diversity Dimension | Target Variations |
| :--- | :--- |
| **Camera Angle & Position** | Front-of-room (teacher view), rear-of-room, side-angle, elevated corner |
| **Lighting Conditions** | Daylight/windows, fluorescent tubes, dim projector lighting, backlit |
| **Classroom Scale** | Small seminar (5–15 students), medium hall (20–40), auditorium (50+) |
| **Distance to Subject** | Near field (1–3 m), mid field (3–7 m), far field (7–15 m) |
| **Occlusion Scenarios** | Partial desk occlusion, laptop screens, student in front blocking view |
| **Time of Day** | Morning (8–11 AM), Midday (11 AM–2 PM), Evening (4–7 PM) |

---

## 4. Local-Only Annotation Protocol

### Strictly Local Tools
Classroom recordings must never be uploaded to cloud labeling services (e.g. public CVAT cloud, Roboflow, Labelbox).
Recommended offline-only tools:
- **CVAT Local**: Run CVAT on `localhost` via Docker.
- **Label Studio Local**: Run `pip install label-studio && label-studio start` locally.
- **LabelImg**: Standalone offline desktop utility for bounding boxes.

### Person-Level Annotation Schema
Labels apply to **individual people**, not entire frames:
- Bounding boxes encompass the student (torso + arms + head).
- Classes:
  - `0`: `hand_raised` (hand raised above shoulder/desk to get attention)
  - `1`: `hand_not_raised` (resting, writing, typing, head scratch, fidgeting)
  - `2`: `ambiguous` (occluded, stretching, borderline posture)

> **Ambiguous Policy**: Ambiguous boxes are flagged and **excluded** from training loss and benchmark accuracy metrics. They are tracked for future `NEEDS_REVIEW` escalation.
