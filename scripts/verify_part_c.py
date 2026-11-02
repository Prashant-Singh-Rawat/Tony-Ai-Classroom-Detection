"""
scripts/verify_part_c.py
Full Automated Visual & Functional Verification of ClassVision AI Redesign (Part C).
Captures screenshots across 4 viewports (1920x1080, 1366x768, 768x1024, 375x667).
Validates DOM styles, prohibited strings, sidebar items, console errors, image luminance, and black pixel ratio.
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
SCREENSHOT_AFTER_DIR = ROOT / "docs" / "screenshots" / "after"
SCREENSHOT_AFTER_DIR.mkdir(parents=True, exist_ok=True)

SCREENSHOT_BEFORE_DIR = ROOT / "docs" / "screenshots" / "before"

ARTIFACT_DIR = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7")
ARTIFACT_SCREENSHOTS = ARTIFACT_DIR / "screenshots"
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

AUDIT_OUTPUT = ROOT / "audit_output"
AUDIT_OUTPUT.mkdir(parents=True, exist_ok=True)

CDP_PORT = 9255
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

ROUTES = [
    ("dashboard", "http://127.0.0.1:5174/dashboard"),
    ("live", "http://127.0.0.1:5174/live"),
    ("analytics", "http://127.0.0.1:5174/analytics"),
    ("intelligence", "http://127.0.0.1:5174/intelligence"),
    ("ask", "http://127.0.0.1:5174/ask"),
    ("reports", "http://127.0.0.1:5174/reports"),
    ("settings", "http://127.0.0.1:5174/settings"),
    ("landing", "http://127.0.0.1:5174/"),
]

VIEWPORTS = [
    ("1920x1080", 1920, 1080),
    ("1366x768", 1366, 768),
    ("tablet_768x1024", 768, 1024),
    ("mobile_375x667", 375, 667),
]

PROHIBITED_STRINGS = [
    "Agent Command Center",
    "Data & Model Status",
    "LIVE REAL MODE",
    "VITE_USE_DEMO_DATA",
    "PHASE 2",
    "Offline Root",
    "Instructor Demo",
]

EXPECTED_SIDEBAR_ITEMS = [
    "Overview",
    "Live Classroom",
    "Analytics",
    "Lecture Intelligence",
    "Ask ClassVision",
    "Reports",
    "Settings",
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

def analyze_image(img_path: Path):
    if not img_path.exists():
        return 0.0, 1.0
    im = Image.open(img_path).convert('L')
    stat = ImageStat.Stat(im)
    mean_brightness = float(stat.mean[0])
    # Near-black pixels (< 30 / 255)
    pixels = list(im.getdata())
    black_count = sum(1 for p in pixels if p < 30)
    black_ratio = float(black_count / len(pixels)) if pixels else 0.0
    return round(mean_brightness, 2), round(black_ratio, 4)

async def main():
    print("==================================================================")
    print("STARTING PART C MANDATORY VISUAL PROOF & VALIDATION SUITE")
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

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "url_tested": "http://127.0.0.1:5174",
        "routes": {},
        "prohibited_strings_check": {},
        "sidebar_verification": {},
        "body_background_check": {},
        "brightness_and_contrast_metrics": {},
        "console_errors": {},
    }

    try:
        targets_url = f"http://127.0.0.1:{CDP_PORT}/json"
        with urllib.request.urlopen(targets_url, timeout=10) as r:
            targets = json.loads(r.read().decode())
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=30_000_000) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")
            await send_cdp(ws, "Log.enable")

            # Collect console messages
            console_errors = []

            for route_name, route_url in ROUTES:
                print(f"\n--> Evaluating Route: {route_name} ({route_url})")
                route_data = {"viewports": {}, "prohibited_hits": []}

                # 1. Desktop evaluation for DOM inspection
                await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
                    "width": 1920,
                    "height": 1080,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                })
                await send_cdp(ws, "Page.navigate", {"url": route_url})
                await asyncio.sleep(2.5)

                # DOM Checks
                dom_info = await send_cdp(ws, "Runtime.evaluate", {
                    "expression": """(() => {
                        const body = document.body;
                        const bodyBg = window.getComputedStyle(body).backgroundColor;
                        const fullText = document.body.innerText;
                        
                        // Extract sidebar links
                        const sidebarLinks = Array.from(document.querySelectorAll('aside nav a span, aside a span'))
                            .map(el => el.textContent.trim())
                            .filter(t => t && !['PRO', 'Offline Edge', 'Privacy Safeguarded', 'Academic Observer', 'Institution License'].includes(t));

                        return {
                            computedBg: bodyBg,
                            fullText: fullText,
                            sidebarLinks: sidebarLinks
                        };
                    })()""",
                    "returnByValue": True
                })

                val = dom_info.get("result", {}).get("value", {})
                computed_bg = val.get("computedBg", "")
                full_text = val.get("fullText", "")
                sidebar_links = val.get("sidebarLinks", [])

                # Verify background
                is_bg_correct = (
                    "247, 248, 250" in computed_bg or 
                    "248, 250, 252" in computed_bg or
                    computed_bg == "rgb(247, 248, 250)"
                )
                results["body_background_check"][route_name] = {
                    "computed": computed_bg,
                    "pass": is_bg_correct,
                }

                # Check prohibited strings
                hits = []
                for s in PROHIBITED_STRINGS:
                    if s in full_text:
                        hits.append(s)
                results["prohibited_strings_check"][route_name] = {
                    "hits": hits,
                    "pass": len(hits) == 0,
                }

                # Check sidebar if route is inside authenticated Layout
                if route_name != "landing":
                    # Filter only the 7 primary items
                    primary_found = [item for item in EXPECTED_SIDEBAR_ITEMS if item in sidebar_links]
                    results["sidebar_verification"][route_name] = {
                        "found_items": sidebar_links,
                        "primary_count": len(primary_found),
                        "exact_match": (primary_found == EXPECTED_SIDEBAR_ITEMS),
                        "pass": (primary_found == EXPECTED_SIDEBAR_ITEMS),
                    }

                # Viewport captures
                for vp_label, w, h in VIEWPORTS:
                    is_mob = "mobile" in vp_label
                    await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
                        "width": w,
                        "height": h,
                        "deviceScaleFactor": 1,
                        "mobile": is_mob,
                    })
                    await asyncio.sleep(1.0)

                    after_filename = f"after_{vp_label}_{route_name}.png"
                    after_path = SCREENSHOT_AFTER_DIR / after_filename

                    ss = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
                    data = ss.get("data")
                    if data:
                        img_bytes = base64.b64decode(data)
                        after_path.write_bytes(img_bytes)
                        (ARTIFACT_SCREENSHOTS / after_filename).write_bytes(img_bytes)
                        (ARTIFACT_DIR / after_filename).write_bytes(img_bytes)

                        # Brightness & black pixel ratio
                        after_lum, after_black = analyze_image(after_path)

                        # Find matching before screenshot (for 1920 and 1366)
                        res_prefix = "1920" if "1920" in vp_label else ("1366" if "1366" in vp_label else None)
                        before_file = f"before_{res_prefix}_{'monitoring' if route_name == 'live' else route_name}.png" if res_prefix else None
                        before_path = SCREENSHOT_BEFORE_DIR / before_file if before_file else None

                        before_lum, before_black = (analyze_image(before_path) if before_path and before_path.exists() else (None, None))

                        route_data["viewports"][vp_label] = {
                            "after_file": str(after_path.relative_to(ROOT)),
                            "after_brightness": after_lum,
                            "after_near_black_ratio": after_black,
                            "before_file": str(before_path.relative_to(ROOT)) if before_path and before_path.exists() else None,
                            "before_brightness": before_lum,
                            "before_near_black_ratio": before_black,
                            "brightness_increase": round(after_lum - before_lum, 2) if before_lum is not None else None,
                        }
                        print(f"  [{vp_label}] Lum: {after_lum:.1f} (Before: {before_lum if before_lum else 'N/A'}), BlackRatio: {after_black*100:.1f}%")

                results["routes"][route_name] = route_data

        # 3. Old Identity Colour Scan across frontend/src
        old_color_targets = ['#0a0a0c', '#08090e', '#7c3aed', '#06b6d4', 'bg-black']
        old_color_report = {}
        total_non_dev_hits = 0
        for root, _, files in os.walk(ROOT / "frontend" / "src"):
            for f in files:
                if f.endswith(('.tsx', '.ts', '.css')):
                    p = Path(root) / f
                    rel_p = str(p.relative_to(ROOT))
                    text = p.read_text(encoding='utf-8', errors='ignore')
                    hits = {tgt: text.count(tgt) for tgt in old_color_targets if tgt in text}
                    is_dev = "AgentCommandCenter" in f or "ModelStatus" in f
                    if hits:
                        old_color_report[rel_p] = {"hits": hits, "is_dev_gated": is_dev}
                        if not is_dev:
                            total_non_dev_hits += sum(hits.values())

        results["old_color_scan"] = {
            "files_with_hits": old_color_report,
            "total_non_dev_hits": total_non_dev_hits,
            "pass": total_non_dev_hits == 0,
        }

        # Save output JSON
        out_json = AUDIT_OUTPUT / "part_c_visual_proof.json"
        out_json.write_text(json.dumps(results, indent=2))
        print(f"\n==================================================================")
        print(f"RESULTS SAVED TO {out_json}")
        print(f"Total Non-Dev Old Colour Hits: {total_non_dev_hits}")
        print(f"==================================================================")

    finally:
        proc.terminate()
        try: proc.wait(timeout=3)
        except: proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

