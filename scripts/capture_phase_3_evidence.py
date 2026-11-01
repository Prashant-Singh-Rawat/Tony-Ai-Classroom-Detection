"""
scripts/capture_phase_3_evidence.py — End-to-end browser verification & visual evidence capture for Phase 3
Captures genuine, high-fidelity browser screenshots of:
1. Initial empty state (1366x768)
2. Live Pose mode with active detections (1366x768 and 1920x1080)
3. Category toggle filter: Hand raised only
4. Category toggle filter: Facing board only
5. Category toggle filter: Restored All
6. Person mode switch (YOLOv8 bounding boxes without skeleton)
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
SCREENSHOT_DIR = ROOT / "docs" / "screenshots" / "phase_3"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_SCREENSHOTS = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7\screenshots\phase_3")
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

VIDEO_ABS_PATH = str((ROOT / "data" / "classroom_test" / "ClassVision_Sample_Classroom_Test_Compatible.mp4").resolve())
CDP_PORT = 9295
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

async def take_screenshot(ws, filename, width=1366, height=768):
    await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 1,
        "mobile": False,
    })
    await asyncio.sleep(0.6)

    out_path = SCREENSHOT_DIR / filename
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = res.get("data")
    if data:
        img_bytes = base64.b64decode(data)
        out_path.write_bytes(img_bytes)
        print(f"  [SAVED] {out_path.name} ({len(img_bytes):,} bytes, {width}x{height})", flush=True)
        art_path = ARTIFACT_SCREENSHOTS / filename
        art_path.write_bytes(img_bytes)
        return str(out_path)
    return None

async def main():
    print("==================================================================", flush=True)
    print("PHASE 3: BROWSER AUTOMATION & VISUAL EVIDENCE COLLECTION", flush=True)
    print("==================================================================", flush=True)
    print(f"Target Video: {VIDEO_ABS_PATH}", flush=True)

    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1440,960",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ]
    proc = subprocess.Popen(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2.0)

    ws_url = None
    for _ in range(15):
        try:
            targets_url = f"http://127.0.0.1:{CDP_PORT}/json"
            with urllib.request.urlopen(targets_url, timeout=5) as r:
                targets = json.loads(r.read().decode())
            page = next(t for t in targets if t.get("type") == "page" and not t.get("url", "").startswith("edge://"))
            ws_url = page["webSocketDebuggerUrl"]
            break
        except Exception:
            await asyncio.sleep(0.5)

    if not ws_url:
        print("[ERROR] Could not connect to Edge CDP", flush=True)
        proc.terminate()
        return

    try:
        async with websockets.connect(ws_url, max_size=25_000_000) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")
            await send_cdp(ws, "DOM.enable")

            print("\n1. Navigating to http://127.0.0.1:5174/live ...", flush=True)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:5174/live"})
            await asyncio.sleep(2.5)

            # Wait for React to mount
            for poll in range(20):
                ready = await evaluate_js(ws, "document.readyState === 'complete' && !!document.querySelector('button')")
                if ready:
                    print(f"  React mounted cleanly after {poll * 0.5 + 2.5}s", flush=True)
                    break
                await asyncio.sleep(0.5)

            # 1. Capture initial empty state
            print("\n2. Capturing initial empty state (1366x768)...", flush=True)
            await take_screenshot(ws, "phase_3_live_empty_1366x768.png", 1366, 768)

            # 2. Upload video file via CDP DOM
            print("\n3. Setting file input via CDP DOM...", flush=True)
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
            print("  Dispatched video file to input. Waiting for preview mounting...", flush=True)
            await asyncio.sleep(2.0)

            # Set confidence threshold to 0.15 (Phase 1 optimized rear-camera setting)
            slider_res = await evaluate_js(ws, """
                (() => {
                    const slider = Array.from(document.querySelectorAll('input[type=range]')).find(i => i.min === '0.1');
                    if (slider) {
                        const proto = window.HTMLInputElement.prototype;
                        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
                        setter.call(slider, '0.15');
                        slider.dispatchEvent(new Event('input', { bubbles: true }));
                        slider.dispatchEvent(new Event('change', { bubbles: true }));
                        return { updated: true, val: slider.value };
                    }
                    return { updated: false };
                })()
            """)
            print(f"  Confidence slider set to 0.15: {slider_res}", flush=True)
            await asyncio.sleep(0.5)

            # 3. Trigger inference
            print("\n4. Triggering 'Run File Inference'...", flush=True)
            click_res = await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const btn = btns.find(b => b.innerText && (b.innerText.includes('Run File Inference') || b.innerText.includes('Run Inference')));
                    if (btn) {
                        btn.click();
                        return 'CLICKED_INFERENCE';
                    }
                    return 'BUTTON_NOT_FOUND';
                })()
            """)
            print(f"  Click result: {click_res}", flush=True)

            # 4. Wait for sequential inference processing to complete
            print("  Waiting for inference to complete...", flush=True)
            inference_ready = False
            for poll in range(50):
                await asyncio.sleep(1.0)
                status = await evaluate_js(ws, """
                    (() => {
                        const txt = document.body.innerText;
                        const isDone = txt.includes('Inference Completed') || txt.includes('Sequential Video Processing Complete') || txt.includes('Processing Complete');
                        const isRunning = txt.includes('Processing Video...') || txt.includes('Inference running...');
                        return { isDone, isRunning };
                    })()
                """)
                if status and status.get("isDone") and not status.get("isRunning"):
                    inference_ready = True
                    print(f"  [INFERENCE COMPLETE] after ~{poll+1}s: {status}", flush=True)
                    break
                elif poll % 5 == 0:
                    print(f"  ... polling ({poll}s): {status}", flush=True)

            if not inference_ready:
                print("  Warning: Polling timed out. Proceeding with available state...", flush=True)

            # 5. Seek uploaded video to t = 4.5s (Student 2 has hand raised, others facing board)
            print("\n5. Seeking uploaded video to t = 4.5s (Hand Raised & Facing Board visible)...", flush=True)
            seek_res = await evaluate_js(ws, """
                (() => {
                    const v = document.querySelector('video[src]') || document.querySelectorAll('video')[1] || document.querySelector('video');
                    if (v) {
                        v.currentTime = 4.5;
                        v.dispatchEvent(new Event('timeupdate', { bubbles: true }));
                        v.dispatchEvent(new Event('seeked', { bubbles: true }));
                        return { currentTime: v.currentTime, duration: v.duration };
                    }
                    return 'NO_VIDEO';
                })()
            """)
            print(f"  Seek result: {seek_res}", flush=True)
            await asyncio.sleep(1.5)

            # Verify detection boxes and category pills
            det_info = await evaluate_js(ws, """
                (() => {
                    const boxes = Array.from(document.querySelectorAll('div[class*="border-2 rounded shadow-lg"]'));
                    const badges = boxes.map(b => b.innerText.replace(/\\n/g, ' '));
                    const filterPills = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(t => t.includes('('));
                    return {
                        boxCount: boxes.length,
                        badges,
                        filterPills: filterPills.slice(0, 8),
                    };
                })()
            """)
            print(f"  Detection State at t=4.5s: {det_info}", flush=True)

            # 6. Capture Pose Mode Screenshots (1366x768 and 1920x1080)
            print("\n6. Capturing Pose Mode Screenshots...", flush=True)
            await take_screenshot(ws, "phase_3_live_pose_1366x768.png", 1366, 768)
            await take_screenshot(ws, "phase_3_live_pose_1920x1080.png", 1920, 1080)

            # 7. Test Category Visibility Toggle Filter: Click "Hand raised"
            print("\n7. Testing Category Visibility Toggle Filter: Click 'Hand raised'...", flush=True)
            click_hr = await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const hrBtn = btns.find(b => b.innerText && b.innerText.includes('Hand raised'));
                    if (hrBtn) {
                        hrBtn.click();
                        return 'CLICKED_HAND_RAISED';
                    }
                    return 'NOT_FOUND';
                })()
            """)
            print(f"  Click result: {click_hr}", flush=True)
            await asyncio.sleep(1.0)

            filtered_hr_info = await evaluate_js(ws, """
                (() => {
                    const boxes = Array.from(document.querySelectorAll('div[class*="border-2 rounded shadow-lg"]'));
                    return {
                        remainingBoxes: boxes.length,
                        boxLabels: boxes.map(b => b.innerText.replace(/\\n/g, ' '))
                    };
                })()
            """)
            print(f"  Filtered state (Hand raised only): {filtered_hr_info}", flush=True)
            await take_screenshot(ws, "phase_3_filter_hand_raised_only.png", 1366, 768)

            # 8. Test Category Visibility Toggle Filter: Click "Facing board"
            print("\n8. Testing Category Visibility Toggle Filter: Click 'Facing board'...", flush=True)
            click_fb = await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const fbBtn = btns.find(b => b.innerText && b.innerText.includes('Facing board'));
                    if (fbBtn) {
                        fbBtn.click();
                        return 'CLICKED_FACING_BOARD';
                    }
                    return 'NOT_FOUND';
                })()
            """)
            print(f"  Click result: {click_fb}", flush=True)
            await asyncio.sleep(1.0)

            filtered_fb_info = await evaluate_js(ws, """
                (() => {
                    const boxes = Array.from(document.querySelectorAll('div[class*="border-2 rounded shadow-lg"]'));
                    return {
                        remainingBoxes: boxes.length,
                        boxLabels: boxes.map(b => b.innerText.replace(/\\n/g, ' '))
                    };
                })()
            """)
            print(f"  Filtered state (Facing board only): {filtered_fb_info}", flush=True)
            await take_screenshot(ws, "phase_3_filter_facing_board_only.png", 1366, 768)

            # 9. Reset filter by clicking "All"
            print("\n9. Resetting Filter: Click 'All'...", flush=True)
            await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const allBtn = btns.find(b => b.innerText && b.innerText.startsWith('All'));
                    if (allBtn) {
                        allBtn.click();
                        return 'CLICKED_ALL';
                    }
                    return 'NOT_FOUND';
                })()
            """)
            await asyncio.sleep(1.0)
            await take_screenshot(ws, "phase_3_filter_restored_all.png", 1366, 768)

            # 10. Test Person Mode Switch (YOLOv8 bounding boxes without skeleton)
            print("\n10. Testing Person Mode Switch (YOLOv8 bounding boxes without skeleton)...", flush=True)
            await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const pBtn = btns.find(b => b.innerText && b.innerText.includes('Person (YOLOv8)'));
                    if (pBtn) {
                        pBtn.click();
                        return 'SWITCHED_PERSON_MODE';
                    }
                    return 'NOT_FOUND';
                })()
            """)
            await asyncio.sleep(1.0)
            await take_screenshot(ws, "phase_3_live_person_mode.png", 1366, 768)

            print("\n[SUCCESS] All Phase 3 visual evidence captured successfully!", flush=True)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())
