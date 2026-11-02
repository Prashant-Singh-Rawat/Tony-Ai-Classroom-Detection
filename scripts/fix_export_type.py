"""
Fix ActivityCategory and ActivityBoxConfig export scope in MonitoringPage.tsx
"""
target_path = "frontend/src/pages/MonitoringPage.tsx"
with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace the inner export type/interface with non-exported inside function or move to top
old_inner = """  export type ActivityCategory =
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
  }"""

new_inner = """  type ActivityCategory =
    | 'facing_board'
    | 'hand_raised'
    | 'phone_visible'
    | 'head_down'
    | 'turned_sideways'
    | 'needs_review'

  interface ActivityBoxConfig {
    category: ActivityCategory
    colorName: 'GREEN' | 'BLUE' | 'RED' | 'ORANGE' | 'YELLOW'
    border: string
    text: string
    badgeBg: string
    label: string
    isHand: boolean
  }"""

if old_inner in content:
    content = content.replace(old_inner, new_inner, 1)
    print("Replaced export type/interface with local type/interface")
else:
    print("Could not find old_inner!")

with open(target_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("Saved")

