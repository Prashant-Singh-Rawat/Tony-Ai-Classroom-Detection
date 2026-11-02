"""
scripts/update_phase_3_frontend.py — Integrates Phase 3 Observable Activity Labels into MonitoringPage.tsx
"""
import re
import sys

target_path = "frontend/src/pages/MonitoringPage.tsx"
with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update lucide-react imports to include Filter, Tag
if "Filter," not in content:
    content = content.replace(
        "  Settings,\n} from 'lucide-react'",
        "  Settings,\n  Filter,\n  Tag,\n} from 'lucide-react'"
    )

# 2. Add ActivityCategory type and update getActivityBoxConfig
old_activity_fn_pattern = re.compile(
    r"  const getActivityBoxConfig = \(det: BoundingBox\) => \{.*?\n  \}",
    re.DOTALL
)

new_activity_fn = '''  export type ActivityCategory =
    | 'facing_board'
    | 'hand_raised'
    | 'phone_visible'
    | 'head_down'
    | 'turned_sideways'
    | 'needs_review'

  export interface ActivityBoxConfig {
    category: ActivityCategory
    colorName: 'GREEN' | 'BLUE' | 'RED' | 'ORANGE' | 'YELLOW'
    border: string
    text: string
    badgeBg: string
    label: string
    isHand: boolean
  }

  const getActivityBoxConfig = (det: BoundingBox): ActivityBoxConfig => {
    const rawLabel = (det.activityLabel || '').trim()

    // 1. RED: Phone visible (COCO class 67 detected overlapping person)
    if (
      rawLabel === 'Phone visible' ||
      rawLabel === 'PHONE_VISIBLE' ||
      det.classId === 67 ||
      rawLabel.toLowerCase().includes('phone')
    ) {
      return {
        category: 'phone_visible',
        colorName: 'RED',
        border: 'border-rose-500 bg-rose-500/15 shadow-rose-500/30',
        text: 'text-rose-400 font-extrabold',
        badgeBg: 'border-rose-500/70 bg-slate-900/90 text-rose-300',
        label: 'Phone visible',
        isHand: false,
      }
    }

    // 2. BLUE: Hand raised (Left / Right / Both)
    if (
      rawLabel.startsWith('Hand raised') ||
      rawLabel.includes('HAND_RAISED') ||
      det.handRaised
    ) {
      let display = 'Hand raised'
      if (rawLabel === 'Hand raised (Left)' || rawLabel === 'LEFT_HAND_RAISED') {
        display = 'Hand raised (Left)'
      } else if (rawLabel === 'Hand raised (Right)' || rawLabel === 'RIGHT_HAND_RAISED') {
        display = 'Hand raised (Right)'
      } else if (rawLabel === 'Hand raised (Both)' || rawLabel === 'BOTH_HANDS_RAISED') {
        display = 'Hand raised (Both)'
      } else if (rawLabel.startsWith('Hand raised (')) {
        display = rawLabel
      }

      return {
        category: 'hand_raised',
        colorName: 'BLUE',
        border: 'border-blue-500 bg-blue-500/15 shadow-blue-500/30',
        text: 'text-blue-400 font-extrabold',
        badgeBg: 'border-blue-500/70 bg-slate-900/90 text-blue-300',
        label: display,
        isHand: true,
      }
    }

    // 3. ORANGE: Head down (N s)
    if (
      rawLabel.startsWith('Head down') ||
      rawLabel === 'HEAD_DOWN_POSTURE' ||
      rawLabel.toLowerCase().includes('head down')
    ) {
      let display = 'Head down'
      if (rawLabel.includes('(') && rawLabel.includes(')')) {
        display = rawLabel
      } else if (det.activityDurationSeconds !== undefined && det.activityDurationSeconds > 0) {
        display = `Head down (${Math.round(det.activityDurationSeconds)}s)`
      }
      return {
        category: 'head_down',
        colorName: 'ORANGE',
        border: 'border-amber-500 bg-amber-500/15 shadow-amber-500/30',
        text: 'text-amber-400 font-bold',
        badgeBg: 'border-amber-500/70 bg-slate-900/90 text-amber-300',
        label: display,
        isHand: false,
      }
    }

    // 4. ORANGE: Turned sideways (possible interaction)
    if (
      rawLabel === 'Turned sideways (possible interaction)' ||
      rawLabel === 'TURNED_SIDEWAYS' ||
      rawLabel === 'POSSIBLE_PEER_INTERACTION' ||
      rawLabel === 'POSSIBLE_SPEAKING' ||
      rawLabel.toLowerCase().includes('turned sideways')
    ) {
      return {
        category: 'turned_sideways',
        colorName: 'ORANGE',
        border: 'border-amber-500 bg-amber-500/15 shadow-amber-500/30',
        text: 'text-amber-400 font-bold',
        badgeBg: 'border-amber-500/70 bg-slate-900/90 text-amber-300',
        label: 'Turned sideways (possible interaction)',
        isHand: false,
      }
    }

    // 5. YELLOW: Needs review
    if (
      rawLabel === 'Needs review' ||
      rawLabel === 'NEEDS_REVIEW' ||
      det.status === 'NEEDS_REVIEW' ||
      det.classId === 2
    ) {
      return {
        category: 'needs_review',
        colorName: 'YELLOW',
        border: 'border-yellow-400 bg-yellow-400/15 shadow-yellow-400/30',
        text: 'text-yellow-300 font-bold',
        badgeBg: 'border-yellow-400/70 bg-slate-900/90 text-yellow-300',
        label: 'Needs review',
        isHand: false,
      }
    }

    // 6. GREEN: Facing board (Default upright posture)
    return {
      category: 'facing_board',
      colorName: 'GREEN',
      border: 'border-emerald-500 bg-emerald-500/15 shadow-emerald-500/20',
      text: 'text-emerald-400 font-semibold',
      badgeBg: 'border-emerald-500/70 bg-slate-900/90 text-emerald-300',
      label: 'Facing board',
      isHand: false,
    }
  }'''

if old_activity_fn_pattern.search(content):
    content = old_activity_fn_pattern.sub(new_activity_fn, content)
    print("Updated getActivityBoxConfig")
else:
    print("Could not find old getActivityBoxConfig pattern!")
    sys.exit(1)

# 3. Add activeCategoryFilter and activeDetections state
state_anchor = "  const [serverSideBlurApplied, setServerSideBlurApplied] = useState(true)"
new_state = '''  const [serverSideBlurApplied, setServerSideBlurApplied] = useState(true)
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<ActivityCategory | null>(null)

  const activeDetections: BoundingBox[] = useMemo(() => {
    if (isWebcamActive) {
      return detectionResult?.boxes || []
    }
    if (selectedFile?.type.startsWith('video/')) {
      if (activeVideoFrame?.boxes) return activeVideoFrame.boxes
      if (videoResult?.timeline && videoResult.timeline.length > 0) {
        return videoResult.timeline[0].boxes || []
      }
      return []
    }
    if (detectionResult?.boxes) {
      return detectionResult.boxes
    }
    return []
  }, [isWebcamActive, selectedFile, activeVideoFrame, videoResult, detectionResult])

  const categoryCounts = useMemo(() => {
    const counts: Record<ActivityCategory, number> = {
      facing_board: 0,
      hand_raised: 0,
      phone_visible: 0,
      head_down: 0,
      turned_sideways: 0,
      needs_review: 0,
    }
    activeDetections.forEach((det) => {
      const cfg = getActivityBoxConfig(det)
      counts[cfg.category] = (counts[cfg.category] || 0) + 1
    })
    return counts
  }, [activeDetections])

  const lowConfidenceCount = useMemo(() => {
    return activeDetections.filter(
      (det) => det.confidence >= 0.15 && det.confidence <= 0.30
    ).length
  }, [activeDetections])'''

if state_anchor in content:
    content = content.replace(state_anchor, new_state, 1)
    print("Added category filter state and computed counts")
else:
    print("Could not find state_anchor")
    sys.exit(1)

with open(target_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("Step 1 done")

