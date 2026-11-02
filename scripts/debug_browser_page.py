import asyncio
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

CDP_PORT = 9287
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

            # Navigate to /live
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:5174/live"})
            await asyncio.sleep(3.0)

            res = await send_cdp(ws, "Runtime.evaluate", {
                "expression": "document.documentElement.outerHTML"
            })
            html = res.get("result", {}).get("value", "")
            Path("audit_output/debug_page.html").write_text(html, encoding="utf-8")
            print("Wrote audit_output/debug_page.html, len =", len(html))

            # Check for error elements
            err_el = await send_cdp(ws, "Runtime.evaluate", {
                "expression": "document.querySelector('vite-error-overlay')?.shadowRoot?.innerHTML || 'NO_OVERLAY'"
            })
            print("Vite error overlay:", err_el.get("result", {}).get("value")[:500] if err_el.get("result", {}).get("value") else "None")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())
