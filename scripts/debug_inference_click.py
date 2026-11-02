import asyncio
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

CDP_PORT = 9293
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
VIDEO_ABS_PATH = str((Path("data") / "classroom_test" / "ClassVision_Sample_Classroom_Test_Compatible.mp4").resolve())

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
            async def send_cdp(method, params=None):
                msg_id = int(time.time() * 1000) % 1000000
                req = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(req))
                while True:
                    resp = await ws.recv()
                    data = json.loads(resp)
                    if data.get("method") == "Runtime.exceptionThrown":
                        print("EXCEPTION:", json.dumps(data.get("params", {}), indent=2))
                    elif data.get("method") == "Console.messageAdded":
                        print("CONSOLE:", data.get("params", {}).get("message", {}).get("text"))
                    if data.get("id") == msg_id:
                        return data.get("result", {})

            await send_cdp("Page.enable")
            await send_cdp("Runtime.enable")
            await send_cdp("Console.enable")
            await send_cdp("DOM.enable")

            print("Navigating to http://127.0.0.1:5174/live ...")
            await send_cdp("Page.navigate", {"url": "http://127.0.0.1:5174/live"})
            await asyncio.sleep(2.5)

            # Upload video file
            doc = await send_cdp("DOM.getDocument")
            root_node_id = doc["root"]["nodeId"]
            file_input = await send_cdp("DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": "input[type=file]"
            })
            input_node_id = file_input["nodeId"]

            await send_cdp("DOM.setFileInputFiles", {
                "nodeId": input_node_id,
                "files": [VIDEO_ABS_PATH]
            })
            print("Dispatched video file to input. Waiting 2s...")
            await asyncio.sleep(2.0)

            # Click Run File Inference
            await send_cdp("Runtime.evaluate", {
                "expression": """
                    (() => {
                        const btns = Array.from(document.querySelectorAll('button'));
                        const btn = btns.find(b => b.innerText && (b.innerText.includes('Run File Inference') || b.innerText.includes('Run Inference')));
                        if (btn) btn.click();
                    })()
                """
            })

            # Wait 8s and collect logs
            t0 = time.time()
            while time.time() - t0 < 8.0:
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    data = json.loads(resp)
                    if data.get("method") == "Runtime.exceptionThrown":
                        print("EXCEPTION:", json.dumps(data.get("params", {}), indent=2))
                    elif data.get("method") == "Console.messageAdded":
                        print("CONSOLE:", data.get("params", {}).get("message", {}).get("text"))
                except asyncio.TimeoutError:
                    pass

            # Inspect error message or body text
            res = await send_cdp("Runtime.evaluate", {
                "expression": "(() => { const err = document.querySelector('.bg-rose-50') || document.querySelector('.text-rose-600') || document.querySelector('.text-rose-700'); return err ? err.innerText : 'NO_ERROR_TEXT'; })()",
                "returnByValue": True
            })
            print("Error text on screen:", res.get("result", {}).get("value"))

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

