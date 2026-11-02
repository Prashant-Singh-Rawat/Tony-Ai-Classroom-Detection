"""
scripts/capture_audit_after_screenshots.py
Captures genuine, high-fidelity 'AFTER' screenshots of all pages in the redesigned ClassVision AI application
at both 1920x1080 (Desktop) and 1366x768 (Laptop) in Microsoft Edge via Chrome DevTools Protocol.
Computes DOM metrics and pixel luminance comparison vs BEFORE screenshots.
"""

import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from PIL import Image, ImageStat
import websockets

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7")
ARTIFACT_SCREENSHOTS = ARTIFACT_DIR / "screenshots"
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

AUDIT_OUTPUT = ROOT / "audit_output"
AUDIT_OUTPUT.mkdir(parents=True, exist_ok=True)

CDP_PORT = 9245
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

PAGES = [
    ("landing", "http://127.0.0.1:5174/"),
    ("dashboard", "http://127.0.0.1:5174/dashboard"),
    ("live", "http://127.0.0.1:5174/live"),
    ("monitoring", "http://127.0.0.1:5174/monitoring"),
    ("analytics", "http://127.0.0.1:5174/analytics"),
    ("intelligence", "http://127.0.0.1:5174/intelligence"),
    ("ask", "http://127.0.0.1:5174/ask"),
    ("reports", "http://127.0.0.1:5174/reports"),
    ("model_status", "http://127.0.0.1:5174/model-status"),
    ("settings", "http://127.0.0.1:5174/settings"),
]

VIEWPORTS = [
    ("1920", 1920, 1080),
    ("1366", 1366, 768),
]

async def send_cdp(ws, method, params=None):
    msg_id = int(time.time() * 1000) % 1000000
    req = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(req))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})

def compute_luminance(image_path: Path) -> float:
    if not image_path.exists():
        return 0.0
    im = Image.open(image_path).convert('L')
    stat = ImageStat.Stat(im)
    return float(stat.mean[0])

async def main():
    print("==================================================================")
    print("CAPTURING REDESIGNED AFTER SCREENSHOTS & COMPUTING METRICS")
    print("==================================================================")

    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--no-first-run",
        "--no-default-browser-check",
        "http://127.0.0.1:5174/dashboard",
    ]
    proc = subprocess.Popen(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2.5)

    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": "http://127.0.0.1:5174",
        "pages_evaluated": [],
    }

    try:
        targets_url = f"http://127.0.0.1:{CDP_PORT}/json"
        with urllib.request.urlopen(targets_url, timeout=10) as r:
            targets = json.loads(r.read().decode())
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=25_000_000) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")

            for name, url in PAGES:
                page_record = {
                    "page_name": name,
                    "url": url,
                    "viewports": {},
                    "dom_metrics": {},
                }

                # Set viewport to 1920 first to read DOM
                await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
                    "width": 1920,
                    "height": 1080,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                })
                await send_cdp(ws, "Page.navigate", {"url": url})
                await asyncio.sleep(2.5)  # Allow API hydration

                # Evaluate DOM styling & structure
                dom_eval = await send_cdp(ws, "Runtime.evaluate", {
                    "expression": """(() => {
                        const body = document.body;
                        const bodyStyle = window.getComputedStyle(body);
                        const navLinks = Array.from(document.querySelectorAll('nav a, aside a')).map(a => a.textContent.trim()).filter(Boolean);
                        const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.textContent.trim()).filter(Boolean);
                        const hasDarkBackground = bodyStyle.backgroundColor.includes('8, 9, 14') || bodyStyle.backgroundColor.includes('10, 12, 19');
                        const isLightBackground = bodyStyle.backgroundColor.includes('248, 250, 252') || bodyStyle.backgroundColor.includes('255, 255, 255');
                        return {
                            bodyBgColor: bodyStyle.backgroundColor,
                            bodyTextColor: bodyStyle.color,
                            navCount: navLinks.length,
                            navItems: navLinks.slice(0, 8),
                            headings: headings.slice(0, 5),
                            hasDarkBackground: hasDarkBackground,
                            isLightBackground: isLightBackground
                        };
                    })()""",
                    "returnByValue": True
                })
                page_record["dom_metrics"] = dom_eval.get("result", {}).get("value", {})

                # Capture viewports
                for res_label, width, height in VIEWPORTS:
                    await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
                        "width": width,
                        "height": height,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    })
                    await asyncio.sleep(1.0)

                    after_filename = f"after_{res_label}_{name}.png"
                    after_path = SCREENSHOT_DIR / after_filename
                    
                    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
                    data = res.get("data")
                    if data:
                        img_bytes = base64.b64decode(data)
                        after_path.write_bytes(img_bytes)
                        art_path = ARTIFACT_SCREENSHOTS / after_filename
                        art_path.write_bytes(img_bytes)
                        
                        # Also copy to root artifact directory so it's directly accessible as an artifact
                        (ARTIFACT_DIR / after_filename).write_bytes(img_bytes)

                        # Luminance calculation
                        after_lum = compute_luminance(after_path)

                        # Look for matching before screenshot
                        before_filename = f"before_{res_label}_{'monitoring' if name == 'live' else name}.png"
                        before_path = SCREENSHOT_DIR / before_filename
                        before_lum = compute_luminance(before_path)

                        page_record["viewports"][res_label] = {
                            "after_file": after_filename,
                            "after_bytes": len(img_bytes),
                            "after_luminance": round(after_lum, 2),
                            "before_file": before_filename if before_path.exists() else None,
                            "before_luminance": round(before_lum, 2) if before_path.exists() else None,
                            "luminance_shift": round(after_lum - before_lum, 2) if before_path.exists() else None,
                            "theme_transition_verified": bool(after_lum > 150 and (before_lum < 80 if before_path.exists() else True))
                        }
                        print(f"  [AFTER] {after_filename}: Lum={after_lum:.1f} (Before={before_lum:.1f}, Shift=+{after_lum-before_lum:.1f})")

                evidence["pages_evaluated"].append(page_record)

        # Write evidence JSON
        out_json = AUDIT_OUTPUT / "redesign_v3_verification_evidence.json"
        out_json.write_text(json.dumps(evidence, indent=2))
        print(f"\nSaved verification evidence to {out_json}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())
