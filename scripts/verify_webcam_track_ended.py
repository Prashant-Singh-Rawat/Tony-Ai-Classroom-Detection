"""
scripts/verify_webcam_track_ended.py
Verifies that stopping the webcam explicitly causes every MediaStreamTrack's
readyState to transition to 'ended', releasing the camera hardware.
"""

import asyncio
import json
import subprocess
import time
import urllib.request
import websockets

CDP_PORT = 9244
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FRONTEND_URL = "http://127.0.0.1:5174/live"

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
    print("==================================================================")
    print("VERIFYING WEBCAM TRACK RELEASE: readyState === 'ended'")
    print("==================================================================")

    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        "--disable-gpu",
        "--window-size=1280,800",
        "--no-first-run",
        "--no-default-browser-check",
        FRONTEND_URL,
    ]
    proc = subprocess.Popen(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2.5)

    try:
        targets_url = f"http://127.0.0.1:{CDP_PORT}/json"
        with urllib.request.urlopen(targets_url, timeout=10) as r:
            targets = json.loads(r.read().decode())
        page = next(t for t in targets if t.get("type") == "page")
        ws_url = page["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=20_000_000) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")
            await asyncio.sleep(2.0)

            # 1. Start Webcam
            print("1. Triggering 'Start Webcam'...")
            start_res = await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const btn = btns.find(b => b.innerText.includes('Start Webcam'));
                    if (btn) {
                        btn.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                })()
            """)
            print(f"  Start click: {start_res}")
            await asyncio.sleep(3.5)

            # 2. Inspect active tracks and attach window reference
            track_active_info = await evaluate_js(ws, """
                (() => {
                    const video = document.querySelector('video');
                    if (video && video.srcObject) {
                        const stream = video.srcObject;
                        const tracks = stream.getTracks();
                        window.__testTracks = tracks; // hold global reference
                        return {
                            hasStream: true,
                            trackCount: tracks.length,
                            tracks: tracks.map(t => ({
                                id: t.id,
                                kind: t.kind,
                                label: t.label,
                                readyState: t.readyState,
                                enabled: t.enabled,
                                muted: t.muted
                            }))
                        };
                    }
                    return { hasStream: false };
                })()
            """)
            print(f"2. Active stream and track states:\n{json.dumps(track_active_info, indent=2)}")

            # 3. Stop Webcam
            print("\n3. Triggering 'Stop Webcam'...")
            stop_res = await evaluate_js(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const btn = btns.find(b => b.innerText.includes('Stop Webcam'));
                    if (btn) {
                        btn.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                })()
            """)
            print(f"  Stop click: {stop_res}")
            await asyncio.sleep(1.5)

            # 4. Check readyState on the stored track reference
            track_stopped_info = await evaluate_js(ws, """
                (() => {
                    const tracks = window.__testTracks || [];
                    const video = document.querySelector('video');
                    return {
                        srcObjectIsNull: video ? (video.srcObject === null) : true,
                        videoIsPaused: video ? video.paused : true,
                        evaluatedTrackCount: tracks.length,
                        trackStates: tracks.map(t => ({
                            id: t.id,
                            kind: t.kind,
                            readyState: t.readyState,
                            isEnded: (t.readyState === 'ended')
                        }))
                    };
                })()
            """)
            print(f"4. Post-stop track status (hardware release check):\n{json.dumps(track_stopped_info, indent=2)}")

            # Validation assertions
            assert track_stopped_info["srcObjectIsNull"] is True
            assert track_stopped_info["evaluatedTrackCount"] > 0
            all_ended = all(t["isEnded"] for t in track_stopped_info["trackStates"])
            print(f"\nAll MediaStreamTracks have readyState === 'ended': {all_ended}")
            assert all_ended is True, "Every MediaStreamTrack must be ended!"
            print("\n[VERIFIED] Hardware camera stream cleanly stopped and released!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())

