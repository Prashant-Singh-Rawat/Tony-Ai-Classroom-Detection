import asyncio
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots" / "settings_fix"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_SCREENSHOTS = Path(r"C:\Users\prash\.gemini\antigravity\brain\e7cd6bf8-c77c-49e9-a89f-4909ad773aa7\screenshots\settings_fix")
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

VIDEO_SAMPLE = str((ROOT / "data" / "classroom_test" / "ClassVision_Sample_Classroom_Test_Compatible.mp4").resolve())
CDP_PORT = 9299
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
    print(f"=== ClassVision AI: Verifying All 10 Detection Settings ===", flush=True)
    edge_cmd = [
        EDGE_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        f"--user-data-dir={ROOT / 'audit_output' / 'edge_profile_settings'}",
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

    results = {}

    async with websockets.connect(ws_url, max_size=50_000_000) as ws:
        await send_cdp(ws, "Page.enable")
        await send_cdp(ws, "DOM.enable")
        await asyncio.sleep(1.5)

        # Baseline Screenshot
        await take_screenshot(ws, "00_live_initial_state.png")

        # -------------------------------------------------------------
        # 1. CONFIDENCE THRESHOLD SLIDER
        # -------------------------------------------------------------
        print("\n--- Testing 1: Confidence Threshold Slider ---", flush=True)
        conf_info = await evaluate_js(ws, """
            (() => {
                const slider = document.querySelector('input[type="range"][min="0.1"]');
                const label = slider ? slider.closest('div').querySelector('.font-mono')?.textContent : null;
                return { hasSlider: !!slider, currentVal: slider ? slider.value : null, label };
            })()
        """)
        print(f"Initial Confidence: {conf_info}")

        # Update confidence slider to 0.39
        updated_conf = await evaluate_js(ws, """
            (() => {
                const slider = document.querySelector('input[type="range"][min="0.1"]');
                if (!slider) return null;
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                nativeInputValueSetter.call(slider, "0.39");
                slider.dispatchEvent(new Event('input', { bubbles: true }));
                slider.dispatchEvent(new Event('change', { bubbles: true }));
                const label = slider.closest('div').querySelector('.font-mono')?.textContent;
                return { newVal: slider.value, label };
            })()
        """)
        print(f"Updated to 39%: {updated_conf}")
        results["Confidence Threshold"] = updated_conf
        await take_screenshot(ws, "01_confidence_slider_39pct.png")

        # -------------------------------------------------------------
        # 2. BOUNDING BOXES CHECKBOX
        # -------------------------------------------------------------
        print("\n--- Testing 2: Bounding Boxes Checkbox ---", flush=True)
        box_toggle = await evaluate_js(ws, """
            (() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const boxLabel = labels.find(l => l.textContent.includes('Bounding Boxes'));
                const chk = boxLabel ? boxLabel.querySelector('input[type="checkbox"]') : null;
                if (!chk) return { found: false };
                const initialChecked = chk.checked;
                chk.click();
                const afterClick1 = chk.checked;
                chk.click();
                const afterClick2 = chk.checked;
                return { found: true, initialChecked, afterClick1, afterClick2 };
            })()
        """)
        print(f"Bounding Boxes Checkbox Toggle: {box_toggle}")
        results["Bounding Boxes"] = box_toggle

        # -------------------------------------------------------------
        # 3. 17-KEYPOINT SKELETONS CHECKBOX
        # -------------------------------------------------------------
        print("\n--- Testing 3: 17-Keypoint Skeletons Checkbox ---", flush=True)
        skel_toggle = await evaluate_js(ws, """
            (() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const skelLabel = labels.find(l => l.textContent.includes('17-Keypoint Skeletons'));
                const chk = skelLabel ? skelLabel.querySelector('input[type="checkbox"]') : null;
                if (!chk) return { found: false };
                const initialChecked = chk.checked;
                chk.click();
                const afterClick1 = chk.checked;
                return { found: true, initialChecked, afterClick1 };
            })()
        """)
        print(f"17-Keypoint Skeletons Toggle: {skel_toggle}")
        results["17-Keypoint Skeletons"] = skel_toggle
        await take_screenshot(ws, "02_skeletons_toggled.png")

        # -------------------------------------------------------------
        # 4. CLIENT FACE BLUR & 5. SERVER IN-MEMORY BLUR
        # -------------------------------------------------------------
        print("\n--- Testing 4 & 5: Client Face Blur & Server In-Memory Blur ---", flush=True)
        blur_status = await evaluate_js(ws, """
            (() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const clientLabel = labels.find(l => l.textContent.includes('Client Face Blur'));
                const serverLabel = labels.find(l => l.textContent.includes('Server In-Memory Blur'));
                const clientChk = clientLabel ? clientLabel.querySelector('input[type="checkbox"]') : null;
                const serverChk = serverLabel ? serverLabel.querySelector('input[type="checkbox"]') : null;
                return {
                    clientFound: !!clientChk,
                    clientChecked: clientChk ? clientChk.checked : null,
                    clientLabelText: clientLabel ? clientLabel.textContent.trim() : null,
                    serverFound: !!serverChk,
                    serverChecked: serverChk ? serverChk.checked : null,
                    serverLabelText: serverLabel ? serverLabel.textContent.trim() : null,
                };
            })()
        """)
        print(f"Blur settings: {blur_status}")
        results["Client Face Blur"] = blur_status
        results["Server In-Memory Blur"] = blur_status

        # -------------------------------------------------------------
        # 6. TEACHER ZONE OUTLINE CHECKBOX
        # -------------------------------------------------------------
        print("\n--- Testing 6: Teacher Zone Outline Checkbox ---", flush=True)
        zone_toggle = await evaluate_js(ws, """
            (() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const zoneLabel = labels.find(l => l.textContent.includes('Teacher Zone Outline'));
                const chk = zoneLabel ? zoneLabel.querySelector('input[type="checkbox"]') : null;
                if (!chk) return { found: false };
                const initialChecked = chk.checked;
                chk.click();
                const afterClick1 = chk.checked;
                return { found: true, initialChecked, afterClick1 };
            })()
        """)
        print(f"Teacher Zone Outline Toggle: {zone_toggle}")
        results["Teacher Zone Outline"] = zone_toggle

        # -------------------------------------------------------------
        # OPEN ADVANCED PARAMETERS DETAILS
        # -------------------------------------------------------------
        print("\n--- Expanding Advanced Parameters ---", flush=True)
        await evaluate_js(ws, """
            (() => {
                const details = document.querySelector('details');
                if (details) details.open = true;
            })()
        """)
        await asyncio.sleep(0.5)

        # -------------------------------------------------------------
        # 7. FRAME SKIPPING SLIDER
        # -------------------------------------------------------------
        print("\n--- Testing 7: Frame Skipping Slider ---", flush=True)
        frame_skip_info = await evaluate_js(ws, """
            (() => {
                const slider = document.querySelector('input[type="range"][min="1"][max="20"]');
                if (!slider) return null;
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                const initialVal = slider.value;
                const initialLabel = slider.closest('.space-y-1').querySelector('strong')?.textContent;
                nativeInputValueSetter.call(slider, "10");
                slider.dispatchEvent(new Event('input', { bubbles: true }));
                slider.dispatchEvent(new Event('change', { bubbles: true }));
                const newLabel = slider.closest('.space-y-1').querySelector('strong')?.textContent;
                return { initialVal, initialLabel, newVal: slider.value, newLabel };
            })()
        """)
        print(f"Frame Skipping Slider: {frame_skip_info}")
        results["Frame Skipping"] = frame_skip_info

        # -------------------------------------------------------------
        # 8. KEYPOINT THRESHOLD SLIDER
        # -------------------------------------------------------------
        print("\n--- Testing 8: Keypoint Threshold Slider ---", flush=True)
        kp_info = await evaluate_js(ws, """
            (() => {
                const sliders = Array.from(document.querySelectorAll('input[type="range"]'));
                const slider = sliders.find(s => Math.abs(parseFloat(s.min) - 0.1) < 0.01 && Math.abs(parseFloat(s.max) - 0.9) < 0.01);
                if (!slider) return null;
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                const initialVal = slider.value;
                const initialLabel = slider.closest('.space-y-1').querySelector('strong')?.textContent;
                nativeInputValueSetter.call(slider, "0.65");
                slider.dispatchEvent(new Event('input', { bubbles: true }));
                slider.dispatchEvent(new Event('change', { bubbles: true }));
                const newLabel = slider.closest('.space-y-1').querySelector('strong')?.textContent;
                return { initialVal, initialLabel, newVal: slider.value, newLabel };
            })()
        """)
        print(f"Keypoint Threshold Slider: {kp_info}")
        results["Keypoint Threshold"] = kp_info

        # -------------------------------------------------------------
        # 9. ELEVATION MARGIN SLIDER
        # -------------------------------------------------------------
        print("\n--- Testing 9: Elevation Margin Slider ---", flush=True)
        elev_info = await evaluate_js(ws, """
            (() => {
                const sliders = Array.from(document.querySelectorAll('input[type="range"]'));
                const slider = sliders.find(s => s.min === "5" && s.max === "50");
                if (!slider) return null;
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                const initialVal = slider.value;
                const initialLabel = slider.closest('.space-y-1').querySelector('strong')?.textContent;
                nativeInputValueSetter.call(slider, "30");
                slider.dispatchEvent(new Event('input', { bubbles: true }));
                slider.dispatchEvent(new Event('change', { bubbles: true }));
                const newLabel = slider.closest('.space-y-1').querySelector('strong')?.textContent;
                return { initialVal, initialLabel, newVal: slider.value, newLabel };
            })()
        """)
        print(f"Elevation Margin Slider: {elev_info}")
        results["Elevation Margin"] = elev_info

        # -------------------------------------------------------------
        # 10. TEACHER ZONE PRESETS
        # -------------------------------------------------------------
        print("\n--- Testing 10: Teacher Zone Presets ---", flush=True)
        presets_info = await evaluate_js(ws, """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const presetNames = ['left', 'right', 'center', 'full'];
                const presetButtons = {};
                for (const name of presetNames) {
                    const btn = buttons.find(b => b.textContent.trim().toLowerCase() === name);
                    if (btn) {
                        btn.click();
                        presetButtons[name] = {
                            found: true,
                            className: btn.className,
                            isActive: btn.className.includes('bg-blue-50') && btn.className.includes('border-blue-500')
                        };
                    } else {
                        presetButtons[name] = { found: false };
                    }
                }
                return presetButtons;
            })()
        """)
        print(f"Teacher Zone Presets: {presets_info}")
        results["Teacher Zone Presets"] = presets_info

        await take_screenshot(ws, "03_all_settings_configured.png")

        # -------------------------------------------------------------
        # VIDEO UPLOAD & REAL INFERENCE PIPELINE VERIFICATION
        # -------------------------------------------------------------
        print("\n--- Testing Upload and File Inference with Dynamic Settings ---", flush=True)
        # Upload the video file
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
            print("  Video file injected into input#video-upload", flush=True)
            await asyncio.sleep(2.0)

            # Check video element and rects
            vid_status = await evaluate_js(ws, """
                (() => {
                    const video = document.querySelector('video');
                    return {
                        src: video ? video.src : null,
                        videoWidth: video ? video.videoWidth : null,
                        videoHeight: video ? video.videoHeight : null,
                    };
                })()
            """)
            print(f"  Video element loaded: {vid_status}", flush=True)
            await take_screenshot(ws, "04_uploaded_video_before_infer.png")

            # Click Run File Inference
            infer_click = await evaluate_js(ws, """
                (() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const btn = buttons.find(b => b.textContent.includes('Run File Inference'));
                    if (btn) {
                        btn.click();
                        return { clicked: true, text: btn.textContent };
                    }
                    return { clicked: false };
                })()
            """)
            print(f"  Inference clicked: {infer_click}", flush=True)

            # Wait for inference processing
            for wait_sec in range(1, 15):
                await asyncio.sleep(1.0)
                status = await evaluate_js(ws, """
                    (() => {
                        const framesBadge = document.querySelector('[data-testid="inference-frames-badge"]');
                        const boxes = document.querySelectorAll('[data-testid="person-box"]');
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const inferBtn = buttons.find(b => b.textContent.includes('Inference'));
                        return {
                            framesText: framesBadge ? framesBadge.textContent : null,
                            boxCount: boxes.length,
                            inferBtnText: inferBtn ? inferBtn.textContent.trim() : null
                        };
                    })()
                """)
                if status and status.get("boxCount", 0) > 0:
                    print(f"  Inference completed! Status at {wait_sec}s: {status}", flush=True)
                    break

            await take_screenshot(ws, "05_uploaded_video_with_inference_overlays.png")

            # Verify boxes toggle with showBoxes
            boxes_hide = await evaluate_js(ws, """
                (() => {
                    const labels = Array.from(document.querySelectorAll('label'));
                    const boxLabel = labels.find(l => l.textContent.includes('Bounding Boxes'));
                    const chk = boxLabel ? boxLabel.querySelector('input[type="checkbox"]') : null;
                    if (chk && chk.checked) chk.click(); // uncheck
                    const boxesNow = document.querySelectorAll('[data-testid="person-box"]').length;
                    return { uncheckResult: !chk.checked, boxesCountAfterUncheck: boxesNow };
                })()
            """)
            print(f"  Hide bounding boxes test: {boxes_hide}", flush=True)
            await take_screenshot(ws, "06_boxes_hidden_overlays_only.png")

            # Re-check boxes
            await evaluate_js(ws, """
                (() => {
                    const labels = Array.from(document.querySelectorAll('label'));
                    const boxLabel = labels.find(l => l.textContent.includes('Bounding Boxes'));
                    const chk = boxLabel ? boxLabel.querySelector('input[type="checkbox"]') : null;
                    if (chk && !chk.checked) chk.click(); // recheck
                })()
            """)

    proc.kill()
    print("\n=== Verification Finished ===", flush=True)
    with open(ROOT / "audit_output" / "settings_verification_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
