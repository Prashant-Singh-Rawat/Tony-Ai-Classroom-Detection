"""
scripts/capture_audit_before_screenshots.py
Captures genuine, high-fidelity 'BEFORE' screenshots of all 10 pages in the current ClassVision AI application
at both 1920x1080 (Desktop) and 1366x768 (Laptop) in Microsoft Edge via Chrome DevTools Protocol.
"""

import asyncio
import base64
import json
import os
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

CDP_PORT = 9230
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

PAGES = [
    ("landing", "http://127.0.0.1:5174/"),
    ("dashboard", "http://127.0.0.1:5174/dashboard"),
    ("monitoring", "http://127.0.0.1:5174/monitoring"),
    ("analytics", "http://127.0.0.1:5174/analytics"),
    ("intelligence", "http://127.0.0.1:5174/intelligence"),
    ("ask", "http://127.0.0.1:5174/ask"),
    ("reports", "http://127.0.0.1:5174/reports"),
    ("model_status", "http://127.0.0.1:5174/model-status"),
    ("settings", "http://127.0.0.1:5174/settings"),
    ("agents", "http://127.0.0.1:5174/agents"),
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

async def capture_page(ws, url, name, res_label, width, height):
    # Set viewport
    await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 1,
        "mobile": False,
    })
    
    # Navigate
    await send_cdp(ws, "Page.navigate", {"url": url})
    await asyncio.sleep(2.0)  # Wait for API hydration
    
    filename = f"before_{res_label}_{name}.png"
    out_path = SCREENSHOT_DIR / filename
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = res.get("data")
    if data:
        img_bytes = base64.b64decode(data)
        out_path.write_bytes(img_bytes)
        art_path = ARTIFACT_SCREENSHOTS / filename
        art_path.write_bytes(img_bytes)
        print(f"  [SAVED] {filename} ({len(img_bytes):,} bytes)")
        return str(out_path)
    return None

async def main():
    print("==================================================================")
    print("CAPTURING GENUINE BEFORE SCREENSHOTS AT 1920x1080 AND 1366x768")
    print("==================================================================")

    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--no-first-run",
        "--no-default-browser-check",
        "http://127.0.0.1:5174/",
    ]
    proc = subprocess.Popen(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2.5)

    try:
        targets_url = f"http://127.0.0.1:{CDP_PORT}/json"
        with urllib.request.urlopen(targets_url, timeout=10) as r:
            targets = json.loads(r.read().decode())
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=25_000_000) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")

            for res_label, width, height in VIEWPORTS:
                print(f"\n--- Viewport: {width}x{height} ({res_label}) ---")
                for name, url in PAGES:
                    print(f"Capturing {name} ({url})...")
                    await capture_page(ws, url, name, res_label, width, height)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

    print("\nAll 20 before screenshots captured successfully.")

if __name__ == "__main__":
    asyncio.run(main())
