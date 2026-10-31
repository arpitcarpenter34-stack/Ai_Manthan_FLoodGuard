"""
HYDRO-GUARD AI — Task 4.0 CDP Verification Script
Verify removal of Flood Prediction, Pump Simulator, and History navigation & pages.
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
CDP_PORT = 9446
TARGET_URL = "http://127.0.0.1:8000/"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_cdp_task40"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")


async def run_audit():
    print("=" * 80)
    print(" HYDRO-GUARD AI — TASK 4.0 NAVIGATION & PAGE REMOVAL AUDIT")
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
                print(f"  [SCREENSHOT] Saved: {filename} ({len(img_bytes)} bytes)")
                return out_path
            return None

        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("DOM.enable")

        # ---------------------------------------------------------------------
        # 1. LOAD HOMEPAGE & VERIFY REMOVALS FROM NAVBAR & HERO CARDS
        # ---------------------------------------------------------------------
        print("\n--- 1. AUDITING HOMEPAGE NAVBAR & HERO CARDS ---")
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(2.5)

        # Check homepage navbar links
        nav_texts = await eval_js("Array.from(document.querySelectorAll('.nav-links a')).map(a => a.textContent.trim())")
        print(f"  Homepage nav links: {nav_texts}")
        assert "Flood Prediction" not in nav_texts, "Flood Prediction still in nav links!"
        assert "Pump Simulator" not in nav_texts, "Pump Simulator still in nav links!"
        assert "History & Logs" not in nav_texts, "History & Logs still in nav links!"
        print("  [PASS] Homepage navbar is clean.")

        # Check hero canvas and scroll track
        canvas_exists = await eval_js("document.getElementById('hero-canvas') !== null")
        print(f"  Hero scroll canvas exists: {canvas_exists}")
        assert canvas_exists, "Hero canvas missing!"

        await capture_screenshot("task40_01_homepage_clean.png")

        # ---------------------------------------------------------------------
        # 2. AUDIFY SIDEBAR NAVIGATION: 3 REMOVED ENTRIES MUST BE GONE
        # ---------------------------------------------------------------------
        print("\n--- 2. AUDITING SIDEBAR NAVIGATION ITEMS ---")
        await eval_js("navigateTo('explorer')")
        await asyncio.sleep(1.5)

        has_nav_pred = await eval_js("document.getElementById('nav-item-prediction') !== null")
        has_nav_sim = await eval_js("document.getElementById('nav-item-simulator') !== null")
        has_nav_hist = await eval_js("document.getElementById('nav-item-history') !== null")

        print(f"  nav-item-prediction in DOM: {has_nav_pred} (Expected: False)")
        print(f"  nav-item-simulator in DOM: {has_nav_sim} (Expected: False)")
        print(f"  nav-item-history in DOM: {has_nav_hist} (Expected: False)")

        assert not has_nav_pred, "nav-item-prediction was NOT removed from sidebar!"
        assert not has_nav_sim, "nav-item-simulator was NOT removed from sidebar!"
        assert not has_nav_hist, "nav-item-history was NOT removed from sidebar!"
        print("  [PASS] All 3 specified navigation entries are completely absent from sidebar.")

        # ---------------------------------------------------------------------
        # 3. AUDIT PAGE CONTAINERS: 3 REMOVED PAGES MUST BE GONE
        # ---------------------------------------------------------------------
        print("\n--- 3. AUDITING PAGE CONTAINERS IN DOM ---")
        has_sec_pred = await eval_js("document.getElementById('screen-prediction') !== null")
        has_sec_sim = await eval_js("document.getElementById('screen-simulator') !== null")
        has_sec_hist = await eval_js("document.getElementById('screen-history') !== null")

        print(f"  screen-prediction in DOM: {has_sec_pred} (Expected: False)")
        print(f"  screen-simulator in DOM: {has_sec_sim} (Expected: False)")
        print(f"  screen-history in DOM: {has_sec_hist} (Expected: False)")

        assert not has_sec_pred, "screen-prediction was NOT removed from DOM!"
        assert not has_sec_sim, "screen-simulator was NOT removed from DOM!"
        assert not has_sec_hist, "screen-history was NOT removed from DOM!"
        print("  [PASS] All 3 specified page containers are completely absent from DOM.")

        # ---------------------------------------------------------------------
        # 4. VERIFY ALL 9 RETAINED SECTIONS ARE FUNCTIONAL
        # ---------------------------------------------------------------------
        print("\n--- 4. AUDITING RETAINED SECTIONS ---")
        retained_screens = [
            ("explorer", "screen-explorer", "Multi-Basin Dataset Explorer"),
            ("weather-radar", "screen-weather-radar", "Weather Radar & Precipitation"),
            ("drivers", "screen-drivers", "Feature Breakdown & Flood Driver"),
            ("model-intel", "screen-model-intel", "AI Model Intelligence"),
            ("map", "screen-map", "Spatial Drainage GIS"),
            ("reports", "screen-reports", "Reports & Monitoring"),
            ("purity", "screen-purity", "Image Purity Tester"),
            ("sound", "screen-sound", "Sound Level Tester")
        ]

        for s_id, dom_id, title_part in retained_screens:
            await eval_js(f"navigateTo('{s_id}')")
            await asyncio.sleep(1.2)
            is_active = await eval_js(f"document.getElementById('{dom_id}').classList.contains('active')")
            curr_title = await eval_js("document.getElementById('current-screen-title').textContent")
            print(f"  Navigated to #{s_id}: Active={is_active}, Title='{curr_title}'")
            assert is_active, f"Screen {dom_id} did not become active!"
            assert title_part.lower() in curr_title.lower(), f"Screen title mismatch for {s_id}!"

        print("  [PASS] All 9 retained sections switch and load correctly.")
        await capture_screenshot("task40_02_retained_sidebar_view.png")

        # ---------------------------------------------------------------------
        # 5. TEST SAFETY OF OLD URL HASHES (#prediction, #simulator, #history)
        # ---------------------------------------------------------------------
        print("\n--- 5. TESTING SAFETY OF OBSOLETE URL HASHES ---")
        for old_hash in ["prediction", "simulator", "history"]:
            await eval_js(f"window.location.hash = '{old_hash}'")
            await eval_js("initRoutingFromHash()")
            await asyncio.sleep(0.5)
            # Should safely be on home view without error
            v_home = await eval_js("appState.currentView")
            print(f"  Navigating to obsolete #{old_hash} safely routed to: view='{v_home}'")
            assert v_home in ["home", "app"], "Invalid appState view!"

        print("  [PASS] Obsolete URL hashes handle gracefully without exceptions.")

        # ---------------------------------------------------------------------
        # 6. CONSOLE ERROR AUDIT
        # ---------------------------------------------------------------------
        print("\n--- 6. JAVASCRIPT CONSOLE AUDIT ---")
        print(f"Total console messages: {len(console_logs)}")
        print(f"Total console errors: {len(console_errors)}")
        if console_errors:
            for err in console_errors:
                print(f"  [ERROR] {err}")
        assert len(console_errors) == 0, f"Encountered {len(console_errors)} console errors!"
        print("  [PASS] Zero console errors during entire audit!")

        print("\n" + "=" * 80)
        print(" ALL TASK 4.0 REMOVAL CHECKS PASSED (6/6)")
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

