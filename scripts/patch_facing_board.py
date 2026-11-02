"""
scripts/patch_facing_board.py
Patches _evaluate_facing_board in backend/app/services/activity_recognition/service.py:
1. Corrects forward vector orthogonal sign to (sh_dy, -sh_dx)
2. Fallback returns (False, 0.0) with reason instead of (True, 0.70)
3. Ensures missing/unreliable keypoints route to NEEDS_REVIEW
"""

with open("backend/app/services/activity_recognition/service.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """            sh_dx = r_sh.x - l_sh.x
            sh_dy = r_sh.y - l_sh.y
            body_vec = np.array([-sh_dy, sh_dx], dtype=float)"""

replacement1 = """            # Body forward vector orthogonal to shoulder axis (pointing toward front of person, away from camera)
            # In screen coordinates (+X right, +Y down), right shoulder is at greater X than left shoulder (sh_dx > 0).
            # Vector pointing forward into classroom toward board (negative Y) is (sh_dy, -sh_dx).
            sh_dx = r_sh.x - l_sh.x
            sh_dy = r_sh.y - l_sh.y
            body_vec = np.array([sh_dy, -sh_dx], dtype=float)"""

target2 = """        return True, 0.70, {
            "alignmentScore": 0.70,
            "boardCenterX": float(board_cx),
            "boardCenterY": float(board_cy),
        }"""

replacement2 = """        return False, 0.0, {
            "alignmentScore": 0.0,
            "boardCenterX": float(board_cx),
            "boardCenterY": float(board_cy),
            "reason": "Missing or low-confidence shoulder keypoints",
        }"""

assert target1 in content, "target1 not found!"
assert target2 in content, "target2 not found!"

content = content.replace(target1, replacement1, 1)
content = content.replace(target2, replacement2, 1)

with open("backend/app/services/activity_recognition/service.py", "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: Patched _evaluate_facing_board vector sign and fallback!")

