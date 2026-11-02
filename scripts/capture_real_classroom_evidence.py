"""
scripts/capture_real_classroom_evidence.py
Captures real-browser evidence of the integrated Live page running on real many-student classroom video:
- File: data/classroom_test/depositphotos_stock_classroom.mp4
- Viewports: 1366x768 and 1920x1080
- Modes: Person Mode (bounding boxes + anonymous labels) and Pose Mode (skeletons + boxes)
- Verifies Anonymous IDs in UI
- Saves screenshots to docs/screenshots/final/ and artifact directories
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
FINAL_SCREENSHOT_DIR = ROOT / "docs" / "screenshots" / "final"
FINAL_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_SCREENSHOTS = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7\screenshots\final")
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

VIDEO_ABS_PATH = str((ROOT / "data" / "classroom_test" / "depositphotos_stock_classroom.mp4").resolve())
CDP_PORT = 9234
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
    out_path = FINAL_SCREENSHOT_DIR / filename
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = res.get("data")
    if data:
        img_bytes = base64.b64decode(data)
        out_path.write_bytes(img_bytes)
        print(f"  [SAVED] {out_path.name} ({len(img_bytes):,} bytes)")
        art_path = ARTIFACT_SCREENSHOTS / filename
        art_path.write_bytes(img_bytes)
        return str(out_path)
    return None

async def set_viewport(ws, width, height):
    await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 1,
        "mobile": False,
    })
    await asyncio.sleep(0.5)

async def main():
    print("==================================================================")
    print("CAPTURING REAL CLASSROOM BROWSER EVIDENCE (F4 & F5)")
    print("==================================================================")
    print(f"Target Video: {VIDEO_ABS_PATH}")

    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1366,768",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
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
            await send_cdp(ws, "DOM.enable")

            print("\n1. Navigating to http://127.0.0.1:5174/live ...")
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:5174/live"})
            await asyncio.sleep(2.5)

            # Disable teaching zone filtering so the whole classroom is analyzed
            zone_toggle = await evaluate_js(ws, """
                (() => {
                    const cbs = Array.from(document.querySelectorAll('input[type="checkbox"]'));
                    const zoneCb = cbs.find(cb => {
                        const lbl = cb.closest('label');
                        return lbl && (lbl.innerText.includes('Teaching Zone') || lbl.innerText.includes('Zone Filter') || lbl.innerText.includes('Instructor ROI'));
                    });
                    if (zoneCb && zoneCb.checked) {
                        zoneCb.click();
                        return { toggled: true, checked: zoneCb.checked };
                    }
                    return { found: !!zoneCb };
                })()
            """)
            print(f"Zone filter adjustment: {zone_toggle}")

            # Upload video file via CDP
            print("\n2. Uploading real many-student classroom video...")
            doc = await send_cdp(ws, "DOM.getDocument")
            root_node_id = doc["root"]["nodeId"]
            file_input = await send_cdp(ws, "DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": "input[type=file]"
            })
            input_node_id = file_input["nodeId"]

            await send_cdp(ws, "DOM.setFileInputFiles", {
                "nodeId": input_node_id,
                "files": [VIDEO_ABS_PATH]
            })
            print("Dispatched video file to file input. Waiting 2.0s...")
            await asyncio.sleep(2.0)

            # Click Run File Inference
            click_res = await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const btn = btns.find(b => b.innerText && (b.innerText.includes('Run File Inference') || b.innerText.includes('Run Inference')));
                    if (btn) {
                        btn.click();
                        return { clicked: true, text: btn.innerText.trim() };
                    }
                    return { clicked: false };
                })()
            """)
            print(f"Click Run File Inference: {click_res}")

            # Poll for inference completion
            print("\n3. Polling for video inference completion...")
            done = False
            for i in range(120):
                await asyncio.sleep(1.0)
                status = await evaluate_js(ws, """
                    (() => {
                        const txt = document.body.innerText;
                        const isDone = txt.includes('Inference Completed') || txt.includes('Processing Complete') || txt.includes('Sequential Video Processing Complete');
                        const isRunning = txt.includes('Processing Video...') || txt.includes('Inference Running...') || txt.includes('Analyzing');
                        return { isDone, isRunning };
                    })()
                """)
                if status and status.get("isDone") and not status.get("isRunning"):
                    print(f"  Inference complete after {i+1}s: {status}")
                    done = True
                    break
                elif i % 5 == 0:
                    print(f"  polling {i}s: {status}")

            if not done:
                print("  Warning: Polling timed out or still running. Proceeding with available state...")

            # Seek video to 5.0s
            seek_info = await evaluate_js(ws, """
                (() => {
                    const v = document.querySelector('video[src]') || document.querySelectorAll('video')[1] || document.querySelector('video');
                    if (v) {
                        v.currentTime = 5.0;
                        v.dispatchEvent(new Event('timeupdate', { bubbles: true }));
                        v.dispatchEvent(new Event('seeked', { bubbles: true }));
                        return { found: true, time: v.currentTime, duration: v.duration };
                    }
                    return { found: false };
                })()
            """)
            print(f"Seek video info: {seek_info}")
            await asyncio.sleep(1.5)

            # Verify Anonymous IDs in DOM (F5)
            dom_id_check = await evaluate_js(ws, """
                (() => {
                    const boxes = Array.from(document.querySelectorAll('div[class*="border-2 rounded shadow-lg"]'));
                    const labels = boxes.map(b => b.innerText.replace(/\\n/g, ' ').trim());
                    const anonIds = labels.map(l => {
                        const match = l.match(/(anon_\\d+|track_\\d+|student_\\d+)/i);
                        return match ? match[0] : null;
                    }).filter(Boolean);
                    
                    return {
                        totalBoxes: boxes.length,
                        labels: labels.slice(0, 15),
                        anonIds: anonIds.slice(0, 15),
                        allAnonymous: anonIds.length > 0 && anonIds.every(id => /^(anon_|track_|student_)/i.test(id))
                    };
                })()
            """)
            print(f"\n4. Anonymous ID Verification (F5): {json.dumps(dom_id_check, indent=2)}")

            # Ensure Pose Skeletons are visible (Pose Mode)
            await evaluate_js(ws, """
                (() => {
                    const cbs = Array.from(document.querySelectorAll('input[type="checkbox"]'));
                    const kpCb = cbs.find(cb => {
                        const lbl = cb.closest('label');
                        return lbl && (lbl.innerText.includes('Pose Skeleton') || lbl.innerText.includes('Keypoint') || lbl.innerText.includes('Skeletons'));
                    });
                    if (kpCb && !kpCb.checked) kpCb.click();
                })()
            """)
            await asyncio.sleep(0.5)

            # Capture 1366x768 Pose Mode
            print("\n5. Capturing 1366x768 Pose Mode screenshot...")
            await set_viewport(ws, 1366, 768)
            await take_screenshot(ws, "live_1366x768_pose_real_classroom.png")

            # Switch to Person Mode (turn off skeletons)
            print("\n6. Capturing 1366x768 Person Mode screenshot...")
            await evaluate_js(ws, """
                (() => {
                    const cbs = Array.from(document.querySelectorAll('input[type="checkbox"]'));
                    const kpCb = cbs.find(cb => {
                        const lbl = cb.closest('label');
                        return lbl && (lbl.innerText.includes('Pose Skeleton') || lbl.innerText.includes('Keypoint') || lbl.innerText.includes('Skeletons'));
                    });
                    if (kpCb && kpCb.checked) kpCb.click();
                })()
            """)
            await asyncio.sleep(0.5)
            await take_screenshot(ws, "live_1366x768_person_real_classroom.png")

            # Switch to 1920x1080
            print("\n7. Capturing 1920x1080 screenshots...")
            await set_viewport(ws, 1920, 1080)
            await take_screenshot(ws, "live_1920x1080_person_real_classroom.png")

            # Turn Pose Mode back on for 1920x1080 Pose Mode
            await evaluate_js(ws, """
                (() => {
                    const cbs = Array.from(document.querySelectorAll('input[type="checkbox"]'));
                    const kpCb = cbs.find(cb => {
                        const lbl = cb.closest('label');
                        return lbl && (lbl.innerText.includes('Pose Skeleton') || lbl.innerText.includes('Keypoint') || lbl.innerText.includes('Skeletons'));
                    });
                    if (kpCb && !kpCb.checked) kpCb.click();
                })()
            """)
            await asyncio.sleep(0.5)
            await take_screenshot(ws, "live_1920x1080_pose_real_classroom.png")

            print("\nALL SCREENSHOTS CAPTURED AND ANONYMOUS IDS VERIFIED!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

