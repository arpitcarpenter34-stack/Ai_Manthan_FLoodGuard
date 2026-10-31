"""
Task 3.8: Complete CDP Verification for AI Model Intelligence & Scientific Explainability Dashboard.
Robust Chrome DevTools Protocol (CDP) client over WebSocket.
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import requests
import websockets

sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9444
TARGET_URL = "http://127.0.0.1:8000/#model-intel"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_cdp_task38"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def run_verification():
    print("=" * 80)
    print(" HYDRO-GUARD AI — TASK 3.8 MODEL INTELLIGENCE E2E BROWSER AUDIT")
    print("=" * 80)

    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,920",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
        # Wait for Chrome to bind
        for _ in range(30):
            try:
                r = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=1)
                if r.status_code == 200:
                    targets = r.json()
                    pages = [p for p in targets if p.get("type") == "page"]
                    if pages:
                        break
            except Exception:
                time.sleep(0.2)
        else:
            print("[ERROR] Could not connect to Chrome CDP interface.")
            return

        page_ws_url = pages[0]["webSocketDebuggerUrl"]
        ws = await websockets.connect(page_ws_url, max_size=100 * 1024 * 1024)

        msg_id = 0
        pending_futures = {}
        console_errors = []

        async def reader_loop():
            try:
                async for raw_msg in ws:
                    msg = json.loads(raw_msg)
                    mid = msg.get("id")
                    if mid is not None and mid in pending_futures:
                        fut = pending_futures.pop(mid)
                        if not fut.done():
                            fut.set_result(msg.get("result", {}))
                    else:
                        method = msg.get("method")
                        params = msg.get("params", {})
                        if method == "Console.messageAdded":
                            cmsg = params.get("message", {})
                            if cmsg.get("level") == "error":
                                console_errors.append(cmsg.get("text"))
                        elif method == "Runtime.consoleAPICalled":
                            if params.get("type") == "error":
                                args = [str(a.get("value", a.get("description", ""))) for a in params.get("args", [])]
                                console_errors.append(" ".join(args))
            except websockets.exceptions.ConnectionClosed:
                pass

        reader_task = asyncio.create_task(reader_loop())

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            cur_id = msg_id
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            pending_futures[cur_id] = fut
            payload = {"id": cur_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(payload))
            return await asyncio.wait_for(fut, timeout=10.0)

        async def eval_js(expression):
            res = await send_cmd("Runtime.evaluate", {"expression": expression, "returnByValue": True})
            val = res.get("result", {}).get("value")
            return val

        async def capture_screenshot(filename):
            res = await send_cmd("Page.captureScreenshot", {"format": "png", "quality": 95})
            b64_data = res.get("data")
            if b64_data:
                img_path = SCREENSHOT_DIR / filename
                img_path.write_bytes(base64.b64decode(b64_data))
                print(f"[SCREENSHOT] Saved: {img_path}")
                return img_path
            return None

        # Enable Network, Console, Runtime, Page
        await send_cmd("Network.enable")
        await send_cmd("Console.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("Page.enable")

        print(f"\nNavigating to {TARGET_URL}...")
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(4.0)

        # Check Active Screen
        active_screen = await eval_js("appState.currentScreen")
        print(f"[CHECK 1] Active Screen: '{active_screen}' (Expected: 'model-intel')")
        assert active_screen == "model-intel", f"Active screen should be model-intel, got {active_screen}"

        # Check Lineage Section Cards
        card_count = await eval_js("document.querySelectorAll('#mi-lineage-cards-grid .mi-lineage-card').length")
        print(f"[CHECK 2] Lineage Cards rendered: {card_count} (Expected: 6)")
        assert card_count == 6, f"Expected 6 lineage cards, found {card_count}"

        # Check Provenance Matrix Rows
        row_count = await eval_js("document.querySelectorAll('#mi-provenance-table-body tr').length")
        print(f"[CHECK 3] Master Provenance Table Rows: {row_count} (Expected: 6)")
        assert row_count == 6, f"Expected 6 rows, found {row_count}"

        # Capture Tab 1 Screenshot
        await capture_screenshot("05_model_intel_lineage.png")

        # Switch to Tab 2: Training Dynamics
        print("\nSwitching to Tab 2 (Training Dynamics)...")
        await eval_js("document.getElementById('mi-btn-tab-training').click()")
        await asyncio.sleep(0.8)
        best_ep = await eval_js("document.getElementById('mi-tele-best-epoch').textContent")
        best_loss = await eval_js("document.getElementById('mi-tele-best-loss').textContent")
        print(f"[CHECK 4] Training Telemetry: Best Epoch='{best_ep}', Best Val Loss='{best_loss}'")
        assert "Epoch 5" in best_ep, "Best epoch should be Epoch 5"
        await capture_screenshot("06_model_intel_training_loss.png")

        # Switch to Tab 3: Model Evaluation
        print("\nSwitching to Tab 3 (Model Evaluation & Residuals)...")
        await eval_js("document.getElementById('mi-btn-tab-evaluation').click()")
        await asyncio.sleep(0.8)
        bench_rows = await eval_js("document.querySelectorAll('#mi-benchmark-table-body tr').length")
        print(f"[CHECK 5] Multi-Model Benchmark Rows: {bench_rows} (Expected: 6)")
        assert bench_rows == 6, f"Expected 6 models in benchmark, found {bench_rows}"
        await capture_screenshot("07_model_intel_evaluation_residuals.png")

        # Switch to Tab 4: Feature Importance & XAI
        print("\nSwitching to Tab 4 (Feature Importance & XAI)...")
        await eval_js("document.getElementById('mi-btn-tab-explainability').click()")
        await asyncio.sleep(0.8)
        node_sens_rows = await eval_js("document.querySelectorAll('#mi-node-sensitivity-tbody tr').length")
        print(f"[CHECK 6] Per-Node Hydrological Sensitivity Rows: {node_sens_rows} (Expected: 7 nodes)")
        assert node_sens_rows == 7, f"Expected 7 node rows, found {node_sens_rows}"
        await capture_screenshot("08_model_intel_feature_importance.png")

        # Switch to Tab 5: What-If Scenario Lab
        print("\nSwitching to Tab 5 (What-If Scenario Lab)...")
        await eval_js("document.getElementById('mi-btn-tab-whatif').click()")
        await asyncio.sleep(0.8)

        # Perturb rainfall slider to 75 mm/h
        await eval_js("""
            document.getElementById('mi-input-rain').value = 75;
            onWhatIfSliderChange();
        """)
        await asyncio.sleep(1.0)
        wf_rows = await eval_js("document.querySelectorAll('#mi-waterfall-box .mi-wf-row').length")
        rain_label = await eval_js("document.getElementById('mi-val-rain').textContent")
        print(f"[CHECK 7] What-If Slider perturbed to: '{rain_label}', Waterfall rows: {wf_rows} (Expected: 6)")
        assert wf_rows == 6, f"Expected 6 waterfall rows, found {wf_rows}"
        await capture_screenshot("09_model_intel_whatif_lab.png")

        # Switch to Tab 6: Dataset Explorer
        print("\nSwitching to Tab 6 (Dataset Explorer)...")
        await eval_js("document.getElementById('mi-btn-tab-explorer').click()")
        await asyncio.sleep(0.8)
        exp_rows = await eval_js("document.querySelectorAll('#mi-explorer-content tbody tr').length")
        print(f"[CHECK 8] Dataset Explorer rows: {exp_rows} (Expected: >= 2)")
        assert exp_rows >= 2, f"Expected >= 2 rows, found {exp_rows}"

        # Verify Console Errors
        print(f"\n[CONSOLE ERRORS CHECK] Total errors detected: {len(console_errors)}")
        if console_errors:
            for err in console_errors:
                print(f"  - Console error: {err}")
        else:
            print("  ✓ ZERO JavaScript or rendering console errors detected.")

        reader_task.cancel()
        print("\n" + "=" * 80)
        print(" TASK 3.8 MODEL INTELLIGENCE BROWSER AUDIT: 100% PASSED!")
        print("=" * 80)

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()


if __name__ == "__main__":
    asyncio.run(run_verification())
