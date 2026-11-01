"""
scripts/capture_live_activity_screenshots.py
Captures high-resolution, fully-hydrated screenshots of:
1. /analytics showing the Observable Classroom Activity & Posture Distribution panel
2. /monitoring showing live camera inference with activity labels
"""

import asyncio
import base64
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_SCREENSHOTS = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7\screenshots")
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

CDP_PORT = 9226
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

async def send_cdp(ws, method, params=None):
    msg_id = int(time.time() * 1000) % 1000000
    req = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(req))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})

async def evaluate_js(ws, expr):
    res = await send_cdp(ws, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True,
    })
    return res.get("result", {}).get("value")

async def take_screenshot(ws, filename):
    out_path = SCREENSHOT_DIR / filename
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = res.get("data")
    if data:
        img_bytes = base64.b64decode(data)
        out_path.write_bytes(img_bytes)
        print(f"  [SAVED] {out_path.name} ({len(img_bytes):,} bytes)")
        # Copy to artifact screenshots
        art_path = ARTIFACT_SCREENSHOTS / filename
        art_path.write_bytes(img_bytes)
        return str(out_path)
    return None

async def main():
    print("Launching Edge for activity recognition screenshot capture...")
    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        "--disable-gpu",
        "--window-size=1440,960",
        "--no-first-run",
        "--no-default-browser-check",
        "http://127.0.0.1:5174/monitoring",
    ]
    proc = subprocess.Popen(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2.5)

    try:
        targets_url = f"http://127.0.0.1:{CDP_PORT}/json"
        with urllib.request.urlopen(targets_url, timeout=10) as r:
            targets = json.loads(r.read().decode())
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=20_000_000) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")

            # 1. Monitoring Page - Start Webcam & Live Detection
            print("\n1. Starting Webcam on Monitoring Page...")
            await asyncio.sleep(2.5)
            start_btn = await evaluate_js(ws, """
                (() => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Start Laptop Webcam'));
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
            """)
            print(f"  Start Webcam clicked: {start_btn}")
            print("  Waiting 5s for live inference frames and overlay badges...")
            await asyncio.sleep(5.0)

            # Capture live monitoring with webcam & inference active
            await take_screenshot(ws, "activity_recognition_live.png")

            # 2. Navigate to Analytics Page
            print("\n2. Navigating to Analytics Page...")
            # Click sidebar link for Analytics to trigger client router cleanly
            nav_result = await evaluate_js(ws, """
                (() => {
                    const link = Array.from(document.querySelectorAll('a, button, div')).find(el => el.innerText && el.innerText.trim() === 'Analytics');
                    if (link) { link.click(); return 'clicked_link'; }
                    window.location.href = '/analytics';
                    return 'location_href';
                })()
            """)
            print(f"  Nav result: {nav_result}")
            await asyncio.sleep(3.5)

            # Wait for data table and cards
            for _ in range(10):
                loaded = await evaluate_js(ws, "!!document.querySelector('table')")
                if loaded:
                    break
                await asyncio.sleep(0.5)

            await take_screenshot(ws, "analytics_activity_distribution.png")
            print("Completed screenshot capture successfully.")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())
