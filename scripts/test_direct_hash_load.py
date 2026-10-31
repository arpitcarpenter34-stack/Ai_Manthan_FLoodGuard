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
CDP_PORT = 9470
TARGET_URL = "http://127.0.0.1:8000/#explorer"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_direct_hash"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")

async def test():
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
        await asyncio.sleep(3.0)

        print("\n--- DOM INSPECTION AT http://127.0.0.1:8000/#explorer ---")
        hash_val = await eval_js("window.location.hash")
        vhome_disp = await eval_js("getComputedStyle(document.getElementById('view-home')).display")
        vapp_disp = await eval_js("getComputedStyle(document.getElementById('view-app')).display")
        vapp_cls = await eval_js("document.getElementById('view-app').className")
        scr_disp = await eval_js("getComputedStyle(document.getElementById('screen-explorer')).display")
        scr_height = await eval_js("document.getElementById('screen-explorer').clientHeight")
        scr_bg = await eval_js("getComputedStyle(document.getElementById('screen-explorer')).backgroundColor")
        vapp_bg = await eval_js("getComputedStyle(document.getElementById('view-app')).backgroundColor")
        vapp_bg_img = await eval_js("getComputedStyle(document.getElementById('view-app')).backgroundImage")
        topbar_disp = await eval_js("getComputedStyle(document.querySelector('.page-top-bar')).display")

        print(f"  window.location.hash: {hash_val}")
        print(f"  view-home display: {vhome_disp} (MUST BE none)")
        print(f"  view-app display: {vapp_disp} (MUST BE block or flex)")
        print(f"  view-app class: '{vapp_cls}' (MUST INCLUDE white-theme)")
        print(f"  view-app background-image: {vapp_bg_img} (MUST BE none)")
        print(f"  view-app background-color: {vapp_bg} (MUST BE light/slate)")
        print(f"  page-top-bar display: {topbar_disp} (MUST BE none)")
        print(f"  screen-explorer display: {scr_disp} (MUST BE block)")
        print(f"  screen-explorer clientHeight: {scr_height} px (MUST BE > 500)")
        print(f"  screen-explorer background-color: {scr_bg}")

        # Check rendered content elements
        title = await eval_js("document.querySelector('.wt-title')?.textContent")
        kpi_rec = await eval_js("document.getElementById('de-kpi-records')?.textContent")
        corr_cells = await eval_js("document.querySelectorAll('#de-corr-matrix-container .wt-corr-cell').length")
        missing_cells = await eval_js("document.querySelectorAll('#de-missing-grid-container .wt-mcell').length")
        fi_rows = await eval_js("document.querySelectorAll('#de-fi-list-container .wt-fi-row').length")
        insights = await eval_js("document.querySelectorAll('.wt-insight-item').length")

        print(f"\n--- RENDERED CONTENT ---")
        print(f"  Title: {title}")
        print(f"  Total Records KPI: {kpi_rec}")
        print(f"  Correlation Cells: {corr_cells} (Expected 36)")
        print(f"  Missingness Cells: {missing_cells} (Expected 55)")
        print(f"  Feature Importance Bars: {fi_rows} (Expected 7)")
        print(f"  Key Insights: {insights} (Expected 5)")

        print("\n--- CAPTURING FULL VIEW SCREENSHOT ---")
        await capture_screenshot("task41_fixed_direct_hash_explorer.png")

        print("\n--- CONSOLE ERRORS ---")
        if console_errors:
            print(f"  [ERRORS] {len(console_errors)} found:")
            for e in console_errors:
                print(f"    - {e}")
        else:
            print("  [PASSED] Exactly 0 console errors!")

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
    asyncio.run(test())

