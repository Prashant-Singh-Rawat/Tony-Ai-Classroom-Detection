"""
scripts/capture_screenshots.py
Captures real screenshots of the running ClassVision AI frontend application in Microsoft Edge.
"""

import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("dashboard", "http://127.0.0.1:5174/dashboard"),
    ("monitoring", "http://127.0.0.1:5174/monitoring"),
    ("analytics", "http://127.0.0.1:5174/analytics"),
    ("intelligence", "http://127.0.0.1:5174/intelligence"),
    ("ask_classvision", "http://127.0.0.1:5174/ask"),
    ("reports", "http://127.0.0.1:5174/reports"),
    ("model_status", "http://127.0.0.1:5174/model-status"),
    ("settings", "http://127.0.0.1:5174/settings"),
]

def capture_all():
    results = {}
    for name, url in PAGES:
        out_path = SCREENSHOT_DIR / f"{name}.png"
        cmd = f'start /wait msedge.exe --headless --disable-gpu --screenshot="{out_path}" --window-size=1280,850 "{url}"'
        print(f"Capturing {name} from {url}...")
        try:
            p = subprocess.run(f"cmd.exe /c \"{cmd}\"", shell=True, timeout=20, capture_output=True)
            time.sleep(1)
            if out_path.exists() and out_path.stat().st_size > 0:
                print(f"  [OK] Saved {out_path.name} ({out_path.stat().st_size:,} bytes)")
                results[name] = {
                    "status": "CAPTURED",
                    "path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                    "size_bytes": out_path.stat().st_size,
                    "url": url,
                }
            else:
                print(f"  [FAILED] {name} - file not created")
                results[name] = {"status": "FAILED", "url": url}
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
            results[name] = {"status": "ERROR", "error": str(e), "url": url}
    return results

if __name__ == "__main__":
    res = capture_all()
    print("Done. Results:", res)
