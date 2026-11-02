import asyncio
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

CDP_PORT = 9285
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

            # Check title / text
            body_text = await evaluate_js(ws, "document.body.innerText.slice(0, 100)")
            print(f"Body text preview: {body_text!r}")

            # Take screenshot of empty state
            ss = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
            img_bytes = base64.b64decode(ss.get("data", ""))
            print(f"Empty state screenshot size: {len(img_bytes)} bytes")
            Path("audit_output/test_empty.png").write_bytes(img_bytes)

            # Upload video file
            doc = await send_cdp(ws, "DOM.getDocument")
            root_node_id = doc["root"]["nodeId"]
            file_input = await send_cdp(ws, "DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": "input[type=file]"
            })
            input_node_id = file_input["nodeId"]
            print(f"File input nodeId: {input_node_id}")

            await send_cdp(ws, "DOM.setFileInputFiles", {
                "nodeId": input_node_id,
                "files": [VIDEO_ABS_PATH]
            })
            print("Dispatched video file to input. Waiting 2s...")
            await asyncio.sleep(2.0)

            # Check buttons
            buttons = await evaluate_js(ws, "Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim())")
            print(f"Buttons after file input: {buttons}")

            # Check preview element
            preview = await evaluate_js(ws, "(() => { const v = document.querySelector('video'); return v ? { src: v.src ? 'has_src' : 'no_src', readyState: v.readyState } : null; })()")
            print(f"Video element: {preview}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

