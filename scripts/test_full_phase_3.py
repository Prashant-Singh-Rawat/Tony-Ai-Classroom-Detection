import asyncio
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

CDP_PORT = 9292
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
VIDEO_ABS_PATH = str((Path("data") / "classroom_test" / "ClassVision_Sample_Classroom_Test_Compatible.mp4").resolve())

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

async def main():
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

    try:
        targets_url = f"http://127.0.0.1:{CDP_PORT}/json"
        with urllib.request.urlopen(targets_url, timeout=5) as r:
            targets = json.loads(r.read().decode())
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=25_000_000) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")
            await send_cdp(ws, "DOM.enable")

            print("Navigating to http://127.0.0.1:5174/live ...")
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:5174/live"})
            await asyncio.sleep(2.5)

            # Upload video file
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
            print("Dispatched video file to input. Waiting 2s...")
            await asyncio.sleep(2.0)

            # Click Run File Inference
            click_res = await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const btn = btns.find(b => b.innerText && (b.innerText.includes('Run File Inference') || b.innerText.includes('Run Inference')));
                    if (btn) {
                        btn.click();
                        return 'CLICKED';
                    }
                    return 'NOT_FOUND';
                })()
            """)
            print(f"Click Run File Inference: {click_res}")

            # Wait for inference completion
            print("Polling for inference completion...")
            done = False
            for i in range(40):
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
                    print(f"Inference complete after {i+1}s: {status}")
                    done = True
                    break
                elif i % 5 == 0:
                    print(f"  polling {i}s: {status}")

            if not done:
                print("Polling timed out!")

            # Seek uploaded video to 4.5s
            seek_info = await evaluate_js(ws, """
                (() => {
                    const v = document.querySelector('video[src]') || document.querySelectorAll('video')[1] || document.querySelector('video');
                    if (v) {
                        v.currentTime = 4.5;
                        v.dispatchEvent(new Event('timeupdate', { bubbles: true }));
                        v.dispatchEvent(new Event('seeked', { bubbles: true }));
                        return { found: true, src: v.src ? 'has_src' : 'no_src', time: v.currentTime, dur: v.duration };
                    }
                    return { found: false };
                })()
            """)
            print(f"Seek info: {seek_info}")
            await asyncio.sleep(1.5)

            # Check detection boxes
            box_info = await evaluate_js(ws, """
                (() => {
                    const boxes = Array.from(document.querySelectorAll('div[class*="border-2 rounded shadow-lg"]'));
                    const badges = boxes.map(b => b.innerText.replace(/\\n/g, ' '));
                    const pillTexts = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(t => t.includes('('));
                    return {
                        boxCount: boxes.length,
                        badges,
                        pillTexts: pillTexts.slice(0, 8),
                    };
                })()
            """)
            print(f"Box Info at 4.5s: {box_info}")

            # Capture screenshot
            ss = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
            img_bytes = base64.b64decode(ss.get("data", ""))
            Path("audit_output/test_full_capture.png").write_bytes(img_bytes)
            print(f"Screenshot saved: {len(img_bytes)} bytes")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

