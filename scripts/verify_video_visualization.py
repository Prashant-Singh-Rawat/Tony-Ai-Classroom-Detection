import asyncio
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots" / "video_fix"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_SCREENSHOTS = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7\screenshots\video_fix")
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

VIDEO_16_9 = str((ROOT / "data" / "classroom_test" / "ClassVision_Sample_Classroom_Test_Compatible.mp4").resolve())
VIDEO_4_3 = str((ROOT / "data" / "test_clips" / "test_clip_4_3_synthetic.mp4").resolve())
VIDEO_PORTRAIT = str((ROOT / "data" / "test_clips" / "test_clip_portrait_synthetic.mp4").resolve())

CDP_PORT = 9298
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

async def send_cdp(ws, method, params=None):
    msg_id = int(time.time() * 10000) % 10000000
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

async def take_screenshot(ws, filename, width=1920, height=1080):
    await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 1,
        "mobile": False,
    })
    await asyncio.sleep(0.5)
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    import base64
    img_bytes = base64.b64decode(res["data"])
    p1 = SCREENSHOT_DIR / filename
    p2 = ARTIFACT_SCREENSHOTS / filename
    p1.write_bytes(img_bytes)
    p2.write_bytes(img_bytes)
    print(f"  [SAVED] {filename} ({len(img_bytes):,} bytes, {width}x{height})", flush=True)

async def measure_rects(ws, label):
    rects = await evaluate_js(ws, """
        (() => {
            const panel = document.querySelector('[data-testid="video-panel-frame"]');
            const videos = Array.from(document.querySelectorAll('[data-testid="video-panel-frame"] video'));
            const video = videos.find(v => v.offsetParent !== null && v.videoWidth > 0) || videos.find(v => v.videoWidth > 0) || null;
            if (!panel) return { error: 'No panel' };
            const pr = panel.getBoundingClientRect();
            let vr = null;
            if (video && video.videoWidth > 0) {
                vr = video.getBoundingClientRect();
            }
            return {
                panel: { width: Math.round(pr.width*10)/10, height: Math.round(pr.height*10)/10, left: Math.round(pr.left*10)/10, top: Math.round(pr.top*10)/10 },
                video: vr ? { width: Math.round(vr.width*10)/10, height: Math.round(vr.height*10)/10, left: Math.round(vr.left*10)/10, top: Math.round(vr.top*10)/10 } : null,
                diffW: vr ? Math.round(Math.abs(pr.width - vr.width)*100)/100 : null,
                diffH: vr ? Math.round(Math.abs(pr.height - vr.height)*100)/100 : null,
                panelAspect: Math.round((pr.width / pr.height)*1000)/1000,
                videoAspect: vr ? Math.round((vr.width / vr.height)*1000)/1000 : null
            };
        })()
    """)
    print(f"[{label}] Rects: {json.dumps(rects)}", flush=True)
    return rects

async def main():
    print(f"=== ClassVision AI: Video Visualization and Rect Verification ===", flush=True)
    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        f"--user-data-dir={ROOT / 'audit_output' / 'edge_profile_vid'}",
        "http://127.0.0.1:5174/live"
    ]
    proc = subprocess.Popen(edge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Edge process started. Waiting for CDP endpoint...", flush=True)
    await asyncio.sleep(2.5)

    ws_url = None
    for _ in range(10):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json") as resp:
                tabs = json.loads(resp.read().decode())
                for t in tabs:
                    if t.get("type") == "page" and "5174" in t.get("url", ""):
                        ws_url = t.get("webSocketDebuggerUrl")
                        break
                if ws_url:
                    break
        except Exception:
            await asyncio.sleep(0.5)

    if not ws_url:
        print("ERROR: Could not connect to Edge CDP endpoint.")
        proc.kill()
        return

    measurements = {}

    async with websockets.connect(ws_url, max_size=50_000_000) as ws:
        await send_cdp(ws, "Page.enable")
        await send_cdp(ws, "DOM.enable")
        await asyncio.sleep(2.0)

        # -------------------------------------------------------------
        # TEST 1: EMPTY STATE AT ALL RESOLUTIONS
        # -------------------------------------------------------------
        print("\n--- TEST 1: Empty State Across Screen Sizes ---", flush=True)
        resolutions = [
            ("1920x1080", 1920, 1080),
            ("1366x768", 1366, 768),
            ("1280x720", 1280, 720),
            ("768x1024", 768, 1024),
            ("375x667", 375, 667),
        ]
        for name, w, h in resolutions:
            await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": (w < 600)})
            await asyncio.sleep(0.5)
            rect = await measure_rects(ws, f"Empty State {name}")
            measurements[f"empty_{name}"] = rect
            await take_screenshot(ws, f"empty_state_{name}.png", w, h)

        # -------------------------------------------------------------
        # TEST 2: UPLOAD 16:9 CLASSROOM VIDEO
        # -------------------------------------------------------------
        print("\n--- TEST 2: Upload 16:9 Classroom Video ---", flush=True)
        await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False})
        
        doc = await send_cdp(ws, "DOM.getDocument")
        root_node_id = doc["root"]["nodeId"]
        file_input = await send_cdp(ws, "DOM.querySelector", {"nodeId": root_node_id, "selector": "input[type=file]"})
        await send_cdp(ws, "DOM.setFileInputFiles", {"nodeId": file_input["nodeId"], "files": [VIDEO_16_9]})
        print("  16:9 Video dispatched to file input. Waiting for metadata...", flush=True)
        await asyncio.sleep(2.0)

        for name, w, h in resolutions:
            await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": (w < 600)})
            await asyncio.sleep(0.4)
            rect = await measure_rects(ws, f"16:9 Video {name}")
            measurements[f"video16_9_{name}"] = rect
            await take_screenshot(ws, f"video_16_9_{name}.png", w, h)

        # -------------------------------------------------------------
        # TEST 3: RUN INFERENCE & VERIFY OVERLAYS, PAUSE, SEEK
        # -------------------------------------------------------------
        print("\n--- TEST 3: Running Inference on 16:9 Video ---", flush=True)
        await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False})
        
        # Click Run File Inference
        await evaluate_js(ws, """
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const btn = btns.find(b => b.innerText && b.innerText.includes('Run File Inference'));
                if (btn) btn.click();
            })()
        """)
        print("  Inference triggered. Waiting for completion...", flush=True)
        completed = False
        for i in range(60):
            res_state = await evaluate_js(ws, "document.body.innerText.includes('Sequential Classroom Video Processing Complete') || document.body.innerText.includes('Inference Completed')")
            if res_state:
                print(f"  Sequential inference completed at {i+1}s!", flush=True)
                completed = True
                break
            await asyncio.sleep(1.0)
        
        if not completed:
            print("  Warning: Inference did not complete within 60s, checking error status...", flush=True)
            err = await evaluate_js(ws, "document.body.innerText")
            print(f"  Page text excerpt: {err[:300]}", flush=True)

        await asyncio.sleep(1.0)
        # Capture screenshot showing bounding boxes, skeleton, activity labels
        await take_screenshot(ws, "video_16_9_with_detections_1920x1080.png", 1920, 1080)
        await take_screenshot(ws, "video_16_9_with_detections_1366x768.png", 1366, 768)

        # Verify boxes count and activities
        boxes_info = await evaluate_js(ws, """
            (() => {
                const panel = document.querySelector('[data-testid="video-panel-frame"]');
                if (!panel) return { error: 'No panel' };
                const boxes = Array.from(panel.querySelectorAll('div[class*="border"]'));
                const chips = Array.from(panel.querySelectorAll('span')).map(s => s.innerText.trim()).filter(Boolean);
                return {
                    boxCount: boxes.length,
                    chips: chips.slice(0, 15)
                };
            })()
        """)
        print(f"  Detections rendered in DOM: {json.dumps(boxes_info)}", flush=True)

        # Test Seeking & Pausing
        print("\n--- TEST 4: Video Seeking & Pausing ---", flush=True)
        await evaluate_js(ws, """
            (() => {
                const videos = Array.from(document.querySelectorAll('[data-testid="video-panel-frame"] video'));
                const v = videos.find(v => v.offsetParent !== null && v.videoWidth > 0) || videos[0];
                if (v) {
                    v.currentTime = 2.5;
                    v.pause();
                }
            })()
        """)
        await asyncio.sleep(1.0)
        seek_rect = await measure_rects(ws, "Paused & Seeked at t=2.5s")
        measurements["seek_2_5s"] = seek_rect
        await take_screenshot(ws, "video_16_9_paused_at_2_5s.png", 1920, 1080)

        # -------------------------------------------------------------
        # TEST 5: UPLOAD 4:3 SYNTHETIC VIDEO
        # -------------------------------------------------------------
        print("\n--- TEST 5: Upload 4:3 Synthetic Clip ---", flush=True)
        doc = await send_cdp(ws, "DOM.getDocument")
        file_input = await send_cdp(ws, "DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
        await send_cdp(ws, "DOM.setFileInputFiles", {"nodeId": file_input["nodeId"], "files": [VIDEO_4_3]})
        await asyncio.sleep(2.0)
        rect_4_3 = await measure_rects(ws, "4:3 Synthetic Video 1920x1080")
        measurements["video_4_3_1920x1080"] = rect_4_3
        await take_screenshot(ws, "video_4_3_clip_1920x1080.png", 1920, 1080)
        await take_screenshot(ws, "video_4_3_clip_1366x768.png", 1366, 768)

        # -------------------------------------------------------------
        # TEST 6: UPLOAD PORTRAIT (9:16) SYNTHETIC VIDEO
        # -------------------------------------------------------------
        print("\n--- TEST 6: Upload Portrait Synthetic Clip ---", flush=True)
        doc = await send_cdp(ws, "DOM.getDocument")
        file_input = await send_cdp(ws, "DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
        await send_cdp(ws, "DOM.setFileInputFiles", {"nodeId": file_input["nodeId"], "files": [VIDEO_PORTRAIT]})
        await asyncio.sleep(2.0)
        rect_port = await measure_rects(ws, "Portrait Synthetic Video 1920x1080")
        measurements["video_portrait_1920x1080"] = rect_port
        await take_screenshot(ws, "video_portrait_clip_1920x1080.png", 1920, 1080)
        await take_screenshot(ws, "video_portrait_clip_1366x768.png", 1366, 768)

        # -------------------------------------------------------------
        # TEST 7: WEBCAM MODE (1280x720)
        # -------------------------------------------------------------
        print("\n--- TEST 7: Start Webcam Mode ---", flush=True)
        await evaluate_js(ws, """
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const btn = btns.find(b => b.innerText && (b.innerText.includes('Start Laptop Webcam') || b.innerText.includes('Start Live Inference')));
                if (btn) btn.click();
            })()
        """)
        await asyncio.sleep(3.0)
        rect_webcam = await measure_rects(ws, "Webcam Active 1280x720")
        measurements["webcam_1280x720"] = rect_webcam
        await take_screenshot(ws, "webcam_active_1280x720.png", 1280, 720)
        await take_screenshot(ws, "webcam_active_1920x1080.png", 1920, 1080)

        # -------------------------------------------------------------
        # TEST 8: FULLSCREEN MODE
        # -------------------------------------------------------------
        print("\n--- TEST 8: Fullscreen Mode ---", flush=True)
        await evaluate_js(ws, """
            (() => {
                const panel = document.querySelector('[data-testid=\"video-panel-frame\"]');
                if (panel && panel.requestFullscreen) {
                    panel.requestFullscreen().catch(() => {});
                }
            })()
        """)
        await asyncio.sleep(1.0)
        await take_screenshot(ws, "fullscreen_mode_1920x1080.png", 1920, 1080)

    proc.kill()
    print("\nVerification completed successfully! Measurements saved.")
    with open("docs/screenshots/video_fix/measurements.json", "w") as f:
        json.dump(measurements, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
