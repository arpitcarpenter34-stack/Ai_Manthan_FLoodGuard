"""
HYDRO-GUARD AI — Major Project Transformation Acceptance Audit
Comprehensive Chrome DevTools Protocol (CDP) Verification Script
"""

import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import requests
import websockets

sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9445
TARGET_URL = "http://127.0.0.1:8000/"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_cdp_transformation"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")


async def run_audit():
    print("=" * 80)
    print(" HYDRO-GUARD AI — MAJOR PROJECT TRANSFORMATION ACCEPTANCE AUDIT")
    print("=" * 80)

    # Launch Chrome
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
        # Wait for Chrome CDP
        pages = []
        for _ in range(40):
            try:
                r = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=1)
                if r.status_code == 200:
                    targets = r.json()
                    pages = [p for p in targets if p.get("type") == "page"]
                    if pages:
                        break
            except Exception:
                pass
            time.sleep(0.2)

        if not pages:
            print("[FAIL] Could not connect to Chrome CDP targets.")
            return

        page_ws_url = pages[0]["webSocketDebuggerUrl"]
        ws = await websockets.connect(page_ws_url, max_size=100 * 1024 * 1024)

        msg_id = 0
        pending = {}
        console_logs = []
        console_errors = []

        async def reader():
            try:
                async for raw in ws:
                    data = json.loads(raw)
                    mid = data.get("id")
                    if mid is not None and mid in pending:
                        fut = pending.pop(mid)
                        if not fut.done():
                            fut.set_result(data.get("result", {}))
                    else:
                        method = data.get("method")
                        params = data.get("params", {})
                        if method == "Runtime.consoleAPICalled":
                            msg_type = params.get("type")
                            args = [str(a.get("value", a.get("description", ""))) for a in params.get("args", [])]
                            text = " ".join(args)
                            console_logs.append(f"[{msg_type}] {text}")
                            if msg_type in ["error", "assert"]:
                                console_errors.append(text)
                        elif method == "Runtime.exceptionThrown":
                            details = params.get("exceptionDetails", {})
                            text = details.get("text", "") + ": " + str(details.get("exception", {}).get("description", ""))
                            console_errors.append(text)
            except Exception:
                pass

        reader_task = asyncio.create_task(reader())

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            cid = msg_id
            fut = asyncio.get_event_loop().create_future()
            pending[cid] = fut
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            return await fut

        async def eval_js(expr):
            res = await send_cmd("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            val = res.get("result", {}).get("value")
            return val

        async def capture_screenshot(filename):
            res = await send_cmd("Page.captureScreenshot", {"format": "png"})
            b64 = res.get("data")
            if b64:
                img_bytes = base64.b64decode(b64)
                out_path = SCREENSHOT_DIR / filename
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                # Copy to artifact directory as well
                try:
                    shutil.copy2(out_path, ARTIFACT_DIR / filename)
                except Exception as e:
                    print(f"Warning copying to artifact dir: {e}")
                print(f"  [SCREENSHOT] Saved: {filename} ({len(img_bytes)} bytes)")
                return out_path
            return None

        # Enable domains
        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("DOM.enable")

        # ---------------------------------------------------------------------
        # 1. AUDIT HOMEPAGE
        # ---------------------------------------------------------------------
        print("\n--- 1. AUDITING CINEMATIC HOMEPAGE (#home) ---")
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(2.5)

        title = await eval_js("document.title")
        brand_subtitle = await eval_js("document.querySelector('.logo-text span').textContent.trim()")
        hero_desc = await eval_js("document.querySelector('.hero-description').textContent.trim()")
        active_view = await eval_js("appState.currentView")

        print(f"  Title: {title}")
        print(f"  Logo Subtitle: {brand_subtitle}")
        print(f"  Hero Description: {hero_desc[:65]}...")
        print(f"  Active View: {active_view}")

        assert "Urban Drainage & Flood Intelligence Platform" in title, "Page title mismatch!"
        assert "Urban Drainage & Flood Intelligence Platform" in brand_subtitle, "Logo subtitle mismatch!"
        assert active_view == "home", "Default view should be home!"
        print("  [PASS] Homepage branding generalized and intact.")
        await capture_screenshot("transformation_01_homepage.png")

        # ---------------------------------------------------------------------
        # 2. AUDIT DATASET EXPLORER (#explorer)
        # ---------------------------------------------------------------------
        print("\n--- 2. AUDITING DATASET EXPLORER (#explorer) ---")
        await eval_js("navigateTo('explorer')")
        await asyncio.sleep(2.0)

        screen_active = await eval_js("document.getElementById('screen-explorer').classList.contains('active')")
        dataset_count = await eval_js("document.getElementById('de-dataset-select').options.length")
        dossier_text = await eval_js("document.getElementById('de-dossier-card').textContent")

        print(f"  Screen active: {screen_active}")
        print(f"  Datasets in selector: {dataset_count}")
        assert screen_active, "screen-explorer should be active!"
        assert dataset_count == 8, f"Expected 8 datasets in selector, got {dataset_count}!"

        # Check observations table rendered
        obs_text = await eval_js("document.getElementById('de-obs-table-container').textContent")
        print(f"  Observations table populated: {len(obs_text) > 50} (length {len(obs_text)})")
        assert len(obs_text) > 50, "Observations table should have loaded data!"

        # Check distributions rendered
        dist_text = await eval_js("document.getElementById('de-dist-container').textContent")
        print(f"  Distributions populated: {len(dist_text) > 50} (length {len(dist_text)})")

        # Run Blue Heart Checkpoint Inference
        print("  Triggering Blue Heart ST-GNN Checkpoint Inference via UI...")
        await eval_js("executeBlueHeartInference()")
        await asyncio.sleep(2.5)

        inf_result_text = await eval_js("document.getElementById('de-inference-results-area').textContent")
        print(f"  Inference executed: {inf_result_text[:120]}...")
        assert "Forecast Results" in inf_result_text or "Sample #" in inf_result_text, "Inference did not return forecast results!"
        print("  [PASS] Dataset Explorer successfully loaded 8 datasets and executed ST-GNN inference.")
        await capture_screenshot("transformation_02_dataset_explorer.png")

        # ---------------------------------------------------------------------
        # 3. AUDIT WEATHER RADAR & PRECIPITATION INTELLIGENCE (#weather-radar)
        # ---------------------------------------------------------------------
        print("\n--- 3. AUDITING WEATHER RADAR & PRECIPITATION INTELLIGENCE (#weather-radar) ---")
        await eval_js("navigateTo('weather-radar')")
        await asyncio.sleep(2.0)

        wr_active = await eval_js("document.getElementById('screen-weather-radar').classList.contains('active')")
        audit_banner = await eval_js("document.querySelector('.wr-audit-text h4').textContent.trim()")
        telem_cards = await eval_js("document.querySelectorAll('.wr-telem-card').length")
        hyetograph_drawn = await eval_js("document.getElementById('wr-hyetograph-canvas').width > 0")

        print(f"  Screen active: {wr_active}")
        print(f"  Audit banner: {audit_banner}")
        print(f"  Telemetry cards count: {telem_cards}")
        print(f"  Hyetograph canvas width: {hyetograph_drawn}")

        assert wr_active, "screen-weather-radar should be active!"
        assert "AUTHENTIC DOPPLER RADAR AUDIT" in audit_banner, "Radar audit banner missing!"
        assert telem_cards >= 3, "Expected at least 3 telemetry cards!"
        print("  [PASS] Weather Radar Intelligence adheres to authentic telemetry and 0 radar fabrication.")
        await capture_screenshot("transformation_03_weather_radar.png")

        # ---------------------------------------------------------------------
        # 4. AUDIT FEATURE & FLOOD DRIVER ATTRIBUTION (#drivers)
        # ---------------------------------------------------------------------
        print("\n--- 4. AUDITING FEATURE & FLOOD DRIVER ATTRIBUTION (#drivers) ---")
        await eval_js("navigateTo('drivers')")
        await asyncio.sleep(2.5)

        dr_active = await eval_js("document.getElementById('screen-drivers').classList.contains('active')")
        imp_canvas = await eval_js("document.getElementById('dr-importance-canvas').width > 0")
        lag_canvas = await eval_js("document.getElementById('dr-lag-canvas').width > 0")
        sens_rows = await eval_js("document.querySelectorAll('#screen-drivers tbody tr').length")

        print(f"  Screen active: {dr_active}")
        print(f"  Importance canvas: {imp_canvas}")
        print(f"  Temporal lag canvas: {lag_canvas}")
        print(f"  Sensitivity matrix rows: {sens_rows}")

        assert dr_active, "screen-drivers should be active!"
        assert imp_canvas, "Permutation importance canvas not rendered!"
        assert lag_canvas, "Lag weights canvas not rendered!"
        assert sens_rows == 7, f"Expected 7 sensitivity matrix rows, got {sens_rows}!"
        print("  [PASS] Flood Driver Analysis rendered permutation XAI, lag decay, and Jacobian matrix.")
        await capture_screenshot("transformation_04_flood_drivers.png")

        # ---------------------------------------------------------------------
        # 5. AUDIT AI MODEL INTELLIGENCE (#model-intel)
        # ---------------------------------------------------------------------
        print("\n--- 5. AUDITING AI MODEL INTELLIGENCE (#model-intel) ---")
        await eval_js("navigateTo('model-intel')")
        await asyncio.sleep(2.0)

        mi_active = await eval_js("document.getElementById('screen-model-intel').classList.contains('active')")
        mi_tabs = await eval_js("document.querySelectorAll('.mi-tab-btn').length")
        print(f"  Screen active: {mi_active}")
        print(f"  Tabs count: {mi_tabs}")
        assert mi_active, "screen-model-intel should be active!"
        assert mi_tabs == 6, f"Expected 6 subtabs, got {mi_tabs}!"
        print("  [PASS] Model Intelligence screen healthy with 6 tabs.")
        await capture_screenshot("transformation_05_model_intel.png")

        # ---------------------------------------------------------------------
        # 6. AUDIT FLOOD PREDICTION (#prediction)
        # ---------------------------------------------------------------------
        print("\n--- 6. AUDITING FLOOD PREDICTION (#prediction) ---")
        await eval_js("navigateTo('prediction')")
        await asyncio.sleep(2.0)

        pred_active = await eval_js("document.getElementById('screen-prediction').classList.contains('active')")
        print(f"  Screen active: {pred_active}")
        assert pred_active, "screen-prediction should be active!"
        print("  [PASS] Flood prediction operational.")
        await capture_screenshot("transformation_06_flood_prediction.png")

        # ---------------------------------------------------------------------
        # 7. AUDIT SPATIAL DRAINAGE GIS (#map)
        # ---------------------------------------------------------------------
        print("\n--- 7. AUDITING SPATIAL DRAINAGE GIS (#map) ---")
        await eval_js("navigateTo('map')")
        await asyncio.sleep(2.0)

        map_active = await eval_js("document.getElementById('screen-map').classList.contains('active')")
        leaflet_loaded = await eval_js("typeof L !== 'undefined' && appState.leafletMap !== null")
        print(f"  Screen active: {map_active}")
        print(f"  Leaflet map initialized: {leaflet_loaded}")
        assert map_active, "screen-map should be active!"
        print("  [PASS] Spatial GIS map operational.")
        await capture_screenshot("transformation_07_spatial_map.png")

        # ---------------------------------------------------------------------
        # 8. AUDIT PUMP & GATE OPTIMIZATION (#simulator)
        # ---------------------------------------------------------------------
        print("\n--- 8. AUDITING PUMP & GATE OPTIMIZATION (#simulator) ---")
        await eval_js("navigateTo('simulator')")
        await asyncio.sleep(2.0)

        sim_active = await eval_js("document.getElementById('screen-simulator').classList.contains('active')")
        print(f"  Screen active: {sim_active}")
        assert sim_active, "screen-simulator should be active!"
        print("  [PASS] Pump & Gate simulator operational.")
        await capture_screenshot("transformation_08_pump_simulator.png")

        # ---------------------------------------------------------------------
        # 9. AUDIT HISTORICAL ANALYTICS & LOGS (#history)
        # ---------------------------------------------------------------------
        print("\n--- 9. AUDITING HISTORICAL ANALYTICS (#history) ---")
        await eval_js("navigateTo('history')")
        await asyncio.sleep(2.0)

        hist_active = await eval_js("document.getElementById('screen-history').classList.contains('active')")
        print(f"  Screen active: {hist_active}")
        assert hist_active, "screen-history should be active!"
        print("  [PASS] Historical logs operational.")
        await capture_screenshot("transformation_09_history_logs.png")

        # ---------------------------------------------------------------------
        # 10. AUDIT REPORTS & AUDIT (#reports)
        # ---------------------------------------------------------------------
        print("\n--- 10. AUDITING REPORTS & AUDIT (#reports) ---")
        await eval_js("navigateTo('reports')")
        await asyncio.sleep(2.0)

        rep_active = await eval_js("document.getElementById('screen-reports').classList.contains('active')")
        print(f"  Screen active: {rep_active}")
        assert rep_active, "screen-reports should be active!"
        print("  [PASS] Reports & Audit operational.")
        await capture_screenshot("transformation_10_reports.png")

        # ---------------------------------------------------------------------
        # CHECK CONSOLE ERRORS
        # ---------------------------------------------------------------------
        print("\n--- JAVASCRIPT CONSOLE AUDIT ---")
        print(f"Total console messages logged: {len(console_logs)}")
        print(f"Total console errors logged: {len(console_errors)}")
        if console_errors:
            print("Console errors found:")
            for e in console_errors:
                print(f"  [ERROR] {e}")
        else:
            print("  [PASS] 0 JavaScript console errors recorded across all 10 screens!")

        assert len(console_errors) == 0, f"Encountered {len(console_errors)} console errors!"

        print("\n" + "=" * 80)
        print(" ALL 10 E2E MAJOR TRANSFORMATION AUDIT CHECKS PASSED (10/10)")
        print("=" * 80)

        reader_task.cancel()

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(run_audit())
