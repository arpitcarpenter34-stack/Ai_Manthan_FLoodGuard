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
CDP_PORT = 9472
TARGET_URL = "http://127.0.0.1:8000/#explorer"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_full_audit"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")

async def run_audit():
    print("=" * 80)
    print(" HYDRO-GUARD AI — TASK 4.1-FIX COMPREHENSIVE BROWSER AUDIT")
    print("=" * 80)

    if os.path.exists(USER_DATA_DIR):
        try:
            shutil.rmtree(USER_DATA_DIR, ignore_errors=True)
        except Exception:
            pass

    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,960",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
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
            print("[FAIL] Could not connect to Chrome CDP.")
            return

        ws = await websockets.connect(pages[0]["webSocketDebuggerUrl"], max_size=100 * 1024 * 1024)

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
                try:
                    shutil.copy2(out_path, ARTIFACT_DIR / filename)
                except Exception as e:
                    print(f"Warning copying to artifact dir: {e}")
                print(f"  [SCREENSHOT] Saved: {filename} ({len(img_bytes)/1024:.1f} KB)")
                return out_path
            return None

        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("DOM.enable")

        print(f"[NAVIGATE] Directly loading {TARGET_URL}...")
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(2.5)

        # ---------------------------------------------------------------------
        # AUDIT 1: Tab 1 — Data Overview (Fresh screenshot)
        # ---------------------------------------------------------------------
        print("\n--- 1. AUDITING TAB 1: DATA OVERVIEW ---")
        title = await eval_js("document.querySelector('.wt-title')?.textContent")
        kpi_rec = await eval_js("document.getElementById('de-kpi-records')?.textContent")
        kpi_feat = await eval_js("document.getElementById('de-kpi-features')?.textContent")
        kpi_nodes = await eval_js("document.getElementById('de-kpi-nodes')?.textContent")
        mean_val = await eval_js("document.getElementById('de-stat-mean')?.textContent")
        corr_count = await eval_js("document.querySelectorAll('#de-corr-matrix-container .wt-corr-cell').length")
        miss_count = await eval_js("document.querySelectorAll('#de-missing-grid-container .wt-mcell').length")
        fi_count = await eval_js("document.querySelectorAll('#de-fi-list-container .wt-fi-row').length")
        ins_count = await eval_js("document.querySelectorAll('.wt-insight-item').length")

        print(f"  Title: {title}")
        print(f"  KPIs: Records={kpi_rec}, Features={kpi_feat}, Nodes={kpi_nodes}")
        print(f"  Feature Distribution Mean: {mean_val}")
        print(f"  Correlation Cells: {corr_count}")
        print(f"  Missing Data Cells: {miss_count}")
        print(f"  Feature Importance Bars: {fi_count}")
        print(f"  Key Insights Pills: {ins_count}")

        await capture_screenshot("task41_fixed_01_overview.png")

        # ---------------------------------------------------------------------
        # AUDIT 2: Tab 2 — Feature Engineering Lab
        # ---------------------------------------------------------------------
        print("\n--- 2. AUDITING TAB 2: FEATURE ENGINEERING LAB ---")
        await eval_js("switchDeTab('features');")
        await asyncio.sleep(0.8)
        fe_rows = await eval_js("document.querySelectorAll('#de-fe-tbody tr').length")
        await eval_js("document.getElementById('de-sb-r').value = 45; runFeatureSandbox();")
        dhdt = await eval_js("document.getElementById('de-sb-dhdt')?.textContent")
        print(f"  Recipe Rows: {fe_rows}")
        print(f"  Sandbox Output (dh/dt): {dhdt}")
        await capture_screenshot("task41_fixed_02_features.png")

        # ---------------------------------------------------------------------
        # AUDIT 3: Tab 3 — Hydrological Relationships
        # ---------------------------------------------------------------------
        print("\n--- 3. AUDITING TAB 3: HYDROLOGICAL RELATIONSHIPS ---")
        await eval_js("switchDeTab('relationships');")
        await asyncio.sleep(0.8)
        rel_delay = await eval_js("document.getElementById('de-rel-delay')?.textContent")
        print(f"  Flow Propagation Delay: {rel_delay}")
        await capture_screenshot("task41_fixed_03_relationships.png")

        # ---------------------------------------------------------------------
        # AUDIT 4: Tab 4 — Flood Fingerprint
        # ---------------------------------------------------------------------
        print("\n--- 4. AUDITING TAB 4: FLOOD FINGERPRINT ---")
        await eval_js("switchDeTab('fingerprint');")
        await asyncio.sleep(0.8)
        ev_count = await eval_js("document.querySelectorAll('#de-events-grid .wt-event-card').length")
        print(f"  Historical Events Loaded: {ev_count}")
        await capture_screenshot("task41_fixed_04_fingerprint.png")

        # ---------------------------------------------------------------------
        # AUDIT 5: Tab 5 — Spatio-Temporal Analysis
        # ---------------------------------------------------------------------
        print("\n--- 5. AUDITING TAB 5: SPATIO-TEMPORAL ANALYSIS ---")
        await eval_js("switchDeTab('spatial');")
        await asyncio.sleep(0.8)
        nodes_rows = await eval_js("document.querySelectorAll('#de-spatial-tbody tr').length")
        heatmap_rows = await eval_js("document.querySelectorAll('#de-spatial-heatmap-grid > div').length")
        print(f"  Sensor Rows: {nodes_rows}, Heatmap Rows: {heatmap_rows}")
        await capture_screenshot("task41_fixed_05_spatial.png")

        # ---------------------------------------------------------------------
        # AUDIT 6: Tab 6 — Model & Prediction Insights
        # ---------------------------------------------------------------------
        print("\n--- 6. AUDITING TAB 6: MODEL & PREDICTION INSIGHTS ---")
        await eval_js("switchDeTab('model');")
        await asyncio.sleep(0.8)
        m_arch = await eval_js("document.getElementById('de-m-arch')?.textContent")
        m_mae = await eval_js("document.getElementById('de-m-mae')?.textContent")
        print(f"  ST-GNN Checkpoint Architecture: {m_arch}")
        print(f"  Evaluation MAE: {m_mae}")
        print("  [ACTION] Executing Checkpoint Inference...")
        await eval_js("runLiveCheckpointInference();")
        await asyncio.sleep(1.8)
        inf_nodes = await eval_js("document.querySelectorAll('.wt-node-card').length")
        print(f"  Inference Generated Nodes: {inf_nodes}")
        await capture_screenshot("task41_fixed_06_model.png")

        # ---------------------------------------------------------------------
        # AUDIT 7: Quick-Switch Pill Interactivity
        # ---------------------------------------------------------------------
        print("\n--- 7. TESTING QUICK-SWITCH PILLS ---")
        print("  [ACTION] Switching to CAMELS (Aroostook, US)...")
        await eval_js("onDeDatasetPillClick('camels_hourly'); switchDeTab('overview');")
        await asyncio.sleep(1.0)
        c_title = await eval_js("document.getElementById('de-summary-title')?.textContent")
        c_rec = await eval_js("document.getElementById('de-kpi-records')?.textContent")
        print(f"  Result: {c_title} | Records: {c_rec}")
        await capture_screenshot("task41_fixed_07_camels.png")

        print("  [ACTION] Switching to CWPRS (India)...")
        await eval_js("onDeDatasetPillClick('india_cwprs');")
        await asyncio.sleep(1.0)
        cw_title = await eval_js("document.getElementById('de-summary-title')?.textContent")
        cw_rec = await eval_js("document.getElementById('de-kpi-records')?.textContent")
        print(f"  Result: {cw_title} | Records: {cw_rec}")
        await capture_screenshot("task41_fixed_08_cwprs.png")

        print("  [ACTION] Switching back to Blue Heart (UK)...")
        await eval_js("onDeDatasetPillClick('blue_heart');")
        await asyncio.sleep(0.8)

        # ---------------------------------------------------------------------
        # CONSOLE ERROR CHECK
        # ---------------------------------------------------------------------
        print("\n" + "=" * 80)
        print(" CONSOLE ERROR AUDIT")
        print("=" * 80)
        if console_errors:
            print(f"  [WARNING] {len(console_errors)} errors detected:")
            for err in console_errors:
                print(f"    - {err}")
        else:
            print("  [PASSED] Exactly 0 console errors detected across all tabs!")

        print("\n[COMPLETE] Task 4.1-FIX Verification finished successfully!")
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

