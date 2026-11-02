import asyncio
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

CDP_PORT = 9252
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

async def main():
    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--no-first-run",
        "--no-default-browser-check",
        "http://127.0.0.1:5174/live",
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
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:5174/live"})
            await asyncio.sleep(3.0)

            eval_res = await send_cdp(ws, "Runtime.evaluate", {
                "expression": """(() => {
                    const l = document.getElementById("layout-canary");
                    const m = document.getElementById("monitoring-canary");
                    return {
                        layoutCanary: l ? l.innerText : null,
                        monitoringCanary: m ? m.innerText : null
                    };
                })()""",
                "returnByValue": True
            })
            vals = eval_res.get("result", {}).get("value", {})
            print(f"CANARY_EVAL_RESULT: {json.dumps(vals)}")

            # Capture screenshot
            ss = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
            img_bytes = base64.b64decode(ss.get("data", ""))
            out_path = Path("docs/screenshots/canary_live_verification.png")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(img_bytes)
            print(f"Screenshot saved to {out_path} ({len(img_bytes)} bytes)")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

