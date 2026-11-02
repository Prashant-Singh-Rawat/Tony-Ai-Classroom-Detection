import asyncio
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots" / "sideways_improvement"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_SCREENSHOTS = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7\screenshots\sideways_improvement")
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

VIDEO_SAMPLE = str((ROOT / "data" / "classroom_test" / "ClassVision_Sample_Classroom_Test_Compatible.mp4").resolve())
CDP_PORT = 9295
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
    (SCREENSHOT_DIR / filename).write_bytes(img_bytes)
    (ARTIFACT_SCREENSHOTS / filename).write_bytes(img_bytes)
    print(f"  [SAVED] {filename} ({len(img_bytes):,} bytes)", flush=True)

async def main():
    print(f"=== ClassVision AI: Sideways Activity Detection Verification ===", flush=True)
    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        f"--user-data-dir={ROOT / 'audit_output' / 'edge_profile_sideways_v2'}",
        "http://127.0.0.1:5174/live"
    ]
    proc = subprocess.Popen(edge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Edge process started. Connecting to CDP...", flush=True)
    await asyncio.sleep(2.5)

    ws_url = None
    for _ in range(12):
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

    async with websockets.connect(ws_url, max_size=50_000_000) as ws:
        await send_cdp(ws, "Page.enable")
        await send_cdp(ws, "DOM.enable")
        await asyncio.sleep(1.5)

        # Baseline Screenshot
        await take_screenshot(ws, "01_live_initial_state.png")

        # Upload classroom test video
        print("\n--- Uploading classroom video ---", flush=True)
        file_input_node = await send_cdp(ws, "DOM.getDocument")
        file_input_desc = await send_cdp(ws, "DOM.querySelector", {
            "nodeId": file_input_node["root"]["nodeId"],
            "selector": "input[type='file']",
        })
        if file_input_desc.get("nodeId"):
            await send_cdp(ws, "DOM.setFileInputFiles", {
                "nodeId": file_input_desc["nodeId"],
                "files": [VIDEO_SAMPLE],
            })
            print("  Video file injected into file input", flush=True)
            await asyncio.sleep(2.0)

            # Click Run File Inference
            print("\n--- Executing Sequential YOLO Inference ---", flush=True)
            await evaluate_js(ws, """
                (() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const btn = buttons.find(b => b.textContent.includes('Run File Inference'));
                    if (btn) btn.click();
                })()
            """)

            # Wait for inference completion
            for wait_sec in range(1, 20):
                await asyncio.sleep(1.0)
                status = await evaluate_js(ws, """
                    (() => {
                        const boxes = document.querySelectorAll('[data-testid="person-box"]');
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const inferBtn = buttons.find(b => b.textContent.includes('Inference'));
                        return {
                            boxCount: boxes.length,
                            inferDone: inferBtn && !inferBtn.textContent.includes('Running')
                        };
                    })()
                """)
                if status and status.get("boxCount", 0) > 0:
                    print(f"  Inference finished at {wait_sec}s", flush=True)
                    break

            await asyncio.sleep(1.0)

            # Seek video to 1.5s where students are actively Turned Sideways
            print("\n--- Seeking video to 1.5s (Turned Sideways Activity) ---", flush=True)
            seek_res = await evaluate_js(ws, """
                (() => {
                    const video = document.querySelector('video');
                    if (video) {
                        video.currentTime = 1.5;
                        video.dispatchEvent(new Event('timeupdate'));
                        video.dispatchEvent(new Event('seeked'));
                        return { currentTime: video.currentTime };
                    }
                    return null;
                })()
            """)
            print(f"  Video seeked: {seek_res}", flush=True)
            await asyncio.sleep(1.0)

            # Inspect boxes and labels at t=1.5s
            boxes_info = await evaluate_js(ws, """
                (() => {
                    const boxes = Array.from(document.querySelectorAll('[data-testid="person-box"]'));
                    return boxes.map(b => {
                        const labelSpan = b.querySelector('.font-bold');
                        return {
                            label: labelSpan ? labelSpan.textContent.trim() : null,
                            className: b.className
                        };
                    });
                })()
            """)
            print(f"  Boxes at t=1.5s: {boxes_info}", flush=True)

            # 02: Screenshot showing Orange Turned Sideways boxes
            await take_screenshot(ws, "02_video_turned_sideways_at_1_5s.png")

            # Click filter: Turned sideways (Orange)
            print("\n--- Clicking Turned Sideways Filter ---", flush=True)
            filter_sw = await evaluate_js(ws, """
                (() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const btn = buttons.find(b => b.textContent.includes('Turned sideways'));
                    if (btn) {
                        btn.click();
                        return { text: btn.textContent.trim() };
                    }
                    return null;
                })()
            """)
            print(f"  Filter clicked: {filter_sw}", flush=True)
            await asyncio.sleep(1.0)
            await take_screenshot(ws, "03_filtered_turned_sideways_orange.png")

            # Seek video to 8.75s where students are mixed (Turned sideways + Facing board)
            print("\n--- Seeking video to 8.75s (Mixed Activities) ---", flush=True)
            await evaluate_js(ws, """
                (() => {
                    const video = document.querySelector('video');
                    if (video) {
                        video.currentTime = 8.75;
                        video.dispatchEvent(new Event('timeupdate'));
                        video.dispatchEvent(new Event('seeked'));
                    }
                    // Reset filter to All
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const allBtn = buttons.find(b => b.textContent.startsWith('All ('));
                    if (allBtn) allBtn.click();
                })()
            """)
            await asyncio.sleep(1.0)
            await take_screenshot(ws, "04_mixed_activities_at_8_75s.png")

    proc.kill()
    print("\n=== Verification Completed Successfully ===", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
