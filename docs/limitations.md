# ClassVision AI — Limitations & Ethical Safeguards

**ClassVision AI:** Real-Time Multimodal Classroom Intelligence System  
**Document Purpose:** Clear and honest disclosure of system boundaries, assumptions, and hardware constraints.

---

## 1. Computer Vision & Hand-Raise Detection Limitations

1. **Geometric Rule Sensitivity:**
   - Hand-raise detection relies on 2D vertical comparisons between wrist ($y$) and shoulder ($y$).
   - In steep camera angles, side-profile seating, or when students rest their heads on their hands, false positives or false negatives may occur.
   - Ambiguous detections are explicitly classified as `NEEDS_REVIEW` rather than claiming 100% certainty.

2. **No Facial Recognition or Biometric Profiling:**
   - By design, ClassVision AI assigns transient anonymous IDs (`anon_001`, `anon_002`...).
   - The system does not recognize student identities, perform automated attendance by face, or track individual students between sessions.

3. **No Mental State or Emotion Inference:**
   - The system does not claim to infer student confusion, boredom, depression, or cognitive attention from facial expressions or body posture. Only observable physical actions (e.g., hand raised) are monitored.

---

## 2. Speech & Audio Transcription Limitations

1. **Classroom Acoustic Noise:**
   - Faster-Whisper `tiny` is optimized for resource efficiency on consumer hardware (HP Victus 4GB VRAM / CPU int8).
   - Heavy classroom background chatter, HVAC noise, or overlapping speech can degrade word error rate (WER).

2. **Microphone Placement:**
   - Far-field student questions may be transcribed with lower accuracy than instructor speech captured through a dedicated microphone.

---

## 3. Whiteboard & OCR Limitations

1. **Handwritten Mathematical Notation:**
   - EasyOCR achieves high accuracy on printed text, slides, and clear capital letters.
   - Rapid cursive handwriting or non-standard complex fractional/integral notation on dirty whiteboards may produce low-confidence extractions.
   - Every OCR block outputs its confidence score ($0.0 - 1.0$) so downstream consumers can filter low-confidence terms.

---

## 4. Hardware Constraints (HP Victus / GTX 1650 4GB)

1. **VRAM Conservation:**
   - Models run sequentially using CPU int8 execution or lightweight GPU allocations to stay safely within the 4 GB VRAM ceiling.
   - Lazy loading is employed so only currently active modules occupy memory.

