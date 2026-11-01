# ClassVision AI — Real Classroom Data Collection Protocol

## 1. Core Ethics and Privacy Mandate

ClassVision AI is strictly designed as an environmental and pedagogical analysis platform, **not** a surveillance or biometric monitoring system.

All data collection activities adhere to the following non-negotiable architectural constraints:
1. **Absolute Prohibition of Facial Recognition**: No face identification, biometric embeddings, facial database matching, or identity verification algorithms are permitted.
2. **Anonymous Identification Only**: Every tracked individual is assigned an ephemeral or session-scoped anonymous identifier (e.g. `PERSON_01`, `TRACK_104`, `STUDENT_A1`). No personal identifiers (names, roll numbers, student IDs) are ever recorded or linked.
3. **Face Blurring on Ingestion**: All real classroom video footage and still photographs pass through an automated privacy-preserving face obfuscation filter (Gaussian blur / solid masking) prior to long-term storage or human annotation.
4. **Local Data Residency**: Raw footage is stored on secured local storage volumes. No unblurred video or biometric artifacts are transmitted to public cloud services.
5. **Informed Consent**: All participating instructors and students (or legal guardians for minors) must complete written consent forms acknowledging recording parameters and privacy protocols before collection commences.

---

## 2. Modality Collection Plans

### 2.1 Classroom Images (`datasets/real_classroom/images/`)
- **Objective**: Capture representative single-frame snapshots for training posture detection, seating arrangement analysis, and static hand-raise recognition across varied illumination and seating geometries.
- **Collection Setup**:
  - Minimum 1080p resolution (1920x1080) at standard classroom aspect ratios (16:9).
  - Multiple perspective angles: front-facing wide angle, elevated corner mount, and rear perspective.
  - Variable environmental conditions: daylight natural light, fluorescent artificial light, dim lighting during projector presentations.
- **Workflow & Anonymization**:
  1. Capture raw images to `raw/`.
  2. Execute automatic face detection and apply irreversible Gaussian blur to all detected facial regions.
  3. Save sanitized images to `labeled/` directory.
  4. Annotate bounding boxes for body pose, hand gestures, and desk boundaries using anonymous IDs.
  5. Store annotation JSONs and collection parameters in `metadata/`.

### 2.2 Classroom Videos (`datasets/real_classroom/videos/`)
- **Objective**: Capture temporal sequences to evaluate student engagement dynamics, action transitions (e.g., transition from note-taking to raising hand), teacher mobility, and multi-student interaction.
- **Collection Setup**:
  - Frame rate: 30 FPS at 1080p resolution.
  - Recording duration: 15–45 minute standard lecture sessions.
  - Frame striding during processing: 2 FPS for action recognition; 5 FPS for hand-raise verification.
- **Workflow & Tracking**:
  1. Ingest raw recording into `raw/`.
  2. Apply automated face blurring across all video frames using detected bounding coordinates with temporal smoothing.
  3. Assign anonymous Kalman filter or ByteTrack track identifiers (`TRACK_001` through `TRACK_NNN`).
  4. Save processed, blurred footage into `processed/`.
  5. Generate temporal activity interval labels in `metadata/`.

### 2.3 Lecture Audio (`datasets/real_classroom/audio/`)
- **Objective**: Transcribe spoken pedagogical content for topic modeling, automated lecture summarization, slide alignment, and RAG knowledge indexing.
- **Collection Setup**:
  - Primary Channel: Wireless lapel microphone worn by the lecturer (16 kHz, 16-bit PCM mono WAV format).
  - Secondary Channel (Optional): Boundary room microphone for classroom acoustic context and student questions.
- **Privacy Protections**:
  - No voice biometric analysis, speaker identification, or voiceprint extraction.
  - Automated redaction of casual off-topic conversations or incidental mentions of student names prior to NLP pipeline entry.
- **Workflow**:
  1. Raw uncompressed audio saved to `raw/`.
  2. Band-pass filtering (80 Hz to 8000 Hz) and background noise suppression applied.
  3. Export normalized audio to `processed/`.
  4. Generate Whisper-compatible timestamped transcripts in `metadata/`.

### 2.4 Board Images (`datasets/real_classroom/board/`)
- **Objective**: Digitize handwritten notes, mathematical derivations, chemical diagrams, and projected lecture slides from instructional boards.
- **Collection Setup**:
  - Target Surfaces: Traditional chalkboards (green/black), dry-erase whiteboards, and digital interactive flat panels.
  - Angle: Perpendicular or semi-oblique perspectives with four-corner reference markers for perspective transformation.
  - Frequency: Captured at discrete intervals (e.g. every 2 minutes or upon major board state modification).
- **Workflow**:
  1. Capture high-resolution board photos to `raw/`.
  2. Apply 4-point perspective warp and homography correction to rectify the writing plane.
  3. Normalize illumination and apply adaptive thresholding for ink/chalk contrast enhancement.
  4. Store rectified, sanitized images in `labeled/`.
  5. Generate OCR ground truth transcriptions (character-level and block-level bounding boxes) in `metadata/`.

---

## 3. Data Governance and Lifecycle

- **Raw Data Quarantine**: Raw recordings are accessible only by the primary project investigator for quality verification and face-blur validation.
- **Retention Period**: Raw unblurred footage must be permanently deleted within 14 days of successful sanitization and labeling.
- **Sanitized Long-Term Storage**: Only anonymized, face-blurred, and normalized artifacts reside permanently in `datasets/real_classroom/`.
- **Review Fallback**: Any frame or audio segment where anonymization fails (e.g. face blur fails due to extreme angle) is immediately discarded from the corpus.
