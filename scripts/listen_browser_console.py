import asyncio
import json
import subprocess
import time
import urllib.request
import websockets

CDP_PORT = 9288
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

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
                    elif data.get("method") == "Log.entryAdded":
                        print("LOG:", data.get("params", {}).get("entry", {}).get("text"))
                    if data.get("id") == msg_id:
                        return data.get("result", {})

            await send_cdp("Page.enable")
            await send_cdp("Runtime.enable")
            await send_cdp("Console.enable")
            await send_cdp("Log.enable")

            print("Navigating to http://127.0.0.1:5174/live ...")
            await send_cdp("Page.navigate", {"url": "http://127.0.0.1:5174/live"})
            
            # Read incoming messages for 4 seconds
            t0 = time.time()
            while time.time() - t0 < 4.0:
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    data = json.loads(resp)
                    if data.get("method") == "Runtime.exceptionThrown":
                        print("EXCEPTION:", json.dumps(data.get("params", {}), indent=2))
                    elif data.get("method") == "Console.messageAdded":
                        print("CONSOLE:", data.get("params", {}).get("message", {}).get("text"))
                    elif data.get("method") == "Log.entryAdded":
                        print("LOG:", data.get("params", {}).get("entry", {}).get("text"))
                except asyncio.TimeoutError:
                    pass

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

