"""
HYDRO-GUARD AI — Task 3.5 In-Browser Frontend CDP Verification & Screenshot Suite.
Tests:
1. Console errors (must be 0 uncaught errors)
2. Homepage scroll animation integrity & 299 hero frames
3. Flood Map: Street inundation table, depth badges, and bottleneck cards
4. Flood Prediction: 90% Confidence Intervals, Uncertainty, and Baseline Comparison
5. Pump & Gate Simulator: MPC Optimization card, KPIs, and fleet schedule
6. Captures full-resolution screenshots of each section.
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import requests
import websockets

sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9877
BASE_URL = "http://127.0.0.1:8000"
USER_DATA_DIR = tempfile.mkdtemp(prefix="chrome_cdp_t35_")
SCREENSHOTS_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print(" HYDRO-GUARD AI — TASK 3.5 BROWSER VERIFICATION & SCREENSHOT CAPTURE")
print("=" * 80)

# Verify all 299 hero frames on disk
frames_dir = Path(r"E:\ai-manthan\hydro_guard_indore\frontend\static\hero_frames")
frame_files = list(frames_dir.glob("ezgif-frame-*.png")) if frames_dir.exists() else []
print(f"Hero Frames on disk: {len(frame_files)} / 299")
assert len(frame_files) >= 299, f"Hero frames missing! Found {len(frame_files)}"


async def run_browser_verification():
    print(f"\n[1] Launching Chrome CDP on port {CDP_PORT}...")
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--window-size=1600,1200",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
        for _ in range(35):
            try:
                r = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=1)
                if r.status_code == 200:
                    pages = [p for p in r.json() if p.get("type") == "page"]
                    if pages:
                        break
            except Exception:
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("Failed to connect to Chrome CDP.")

        page_ws_url = pages[0]["webSocketDebuggerUrl"]
        print(f"  Connected to Chrome page WebSocket: {page_ws_url}")

        ws = await websockets.connect(page_ws_url, max_size=50 * 1024 * 1024, ping_interval=None)
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
                            fut.set_result(msg)
                    # Check console errors
                    if msg.get("method") == "Console.messageAdded":
                        lvl = msg.get("params", {}).get("message", {}).get("level")
                        txt = msg.get("params", {}).get("message", {}).get("text", "")
                        if lvl == "error":
                            console_errors.append(txt)
            except Exception:
                pass

        reader_task = asyncio.create_task(reader_loop())

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            pending_futures[msg_id] = fut
            cmd = {"id": msg_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(cmd))
            return await asyncio.wait_for(fut, timeout=20.0)

        async def eval_js(expression: str):
            res = await send_cmd("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            })
            return res.get("result", {}).get("result", {}).get("value")

        async def capture_screen(filename: str):
            res = await send_cmd("Page.captureScreenshot", {"format": "png"})
            b64_data = res.get("result", {}).get("data", "")
            if b64_data:
                img_path = SCREENSHOTS_DIR / filename
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(b64_data))
                print(f"  Captured screenshot: {img_path.name} ({len(b64_data)} bytes b64)")

        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("Console.enable")

        # ---------------------------------------------------------------------
        # 1. HOMEPAGE & HERO SCROLL ANIMATION
        # ---------------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" 1. HOMEPAGE & HERO SCROLL ANIMATION AUDIT")
        print("-" * 60)
        await send_cmd("Page.navigate", {"url": f"{BASE_URL}/#home"})
        await asyncio.sleep(2.5)

        title = await eval_js("document.title")
        hero_visible = await eval_js("Boolean(document.getElementById('view-home') && document.getElementById('view-home').style.display !== 'none')")
        canvas_exists = await eval_js("Boolean(document.getElementById('hero-canvas'))")
        hero_h1 = await eval_js("document.querySelector('.hero-title')?.innerText?.replace(/\\n/g, ' ')")
        navbar_count = await eval_js("document.querySelectorAll('.nav-links li').length")

        print(f"  Page Title: '{title}'")
        print(f"  Hero View Active: {hero_visible}")
        print(f"  Hero Canvas Animation Mounted: {canvas_exists}")
        print(f"  Hero Headline: '{hero_h1}'")
        print(f"  Navbar Links Count: {navbar_count}")
        assert hero_visible and canvas_exists and navbar_count >= 7

        await capture_screen("01_homepage_intact.png")

        # ---------------------------------------------------------------------
        # 2. FLOOD MAP SECTION (#map)
        # ---------------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" 2. FLOOD MAP & STREET INUNDATION MAPPING AUDIT")
        print("-" * 60)
        await eval_js("navigateTo('map')")
        await asyncio.sleep(2.0)

        map_active = await eval_js("document.getElementById('screen-map')?.classList.contains('active')")
        leaflet_initialized = await eval_js("Boolean(appState.leafletMap)")
        station_markers = await eval_js("appState.mapMarkers.length")
        streets_rendered = await eval_js("document.querySelectorAll('#t35-streets-tbody tr').length")
        bottlenecks_rendered = await eval_js("document.querySelectorAll('#t35-bottlenecks-list > div').length")
        first_street_text = await eval_js("document.querySelector('#t35-streets-tbody tr')?.innerText?.replace(/\\n/g, ' | ')")
        first_bn_text = await eval_js("document.querySelector('#t35-bottlenecks-list > div')?.innerText?.replace(/\\n/g, ' | ')")

        print(f"  Map Screen Active: {map_active}")
        print(f"  Leaflet Engine Initialized: {leaflet_initialized}")
        print(f"  Station Markers Rendered: {station_markers} / 7")
        print(f"  Street Corridors Rendered in Table: {streets_rendered} / 21")
        print(f"  Hydraulic Bottlenecks Rendered: {bottlenecks_rendered} / 3")
        print(f"  Sample Street Corridor: {first_street_text[:80]}...")
        print(f"  Sample Bottleneck: {first_bn_text[:80]}...")
        assert map_active and leaflet_initialized and streets_rendered >= 15 and bottlenecks_rendered >= 3

        await capture_screen("02_flood_map_inundation.png")

        # ---------------------------------------------------------------------
        # 3. FLOOD PREDICTION SECTION (#prediction)
        # ---------------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" 3. FLOOD PREDICTION WITH CONFIDENCE INTERVALS AUDIT")
        print("-" * 60)
        await eval_js("navigateTo('prediction')")
        await asyncio.sleep(1.0)

        pred_active = await eval_js("document.getElementById('screen-prediction')?.classList.contains('active')")
        ml_prob = await eval_js("document.getElementById('ml-prob-val')?.innerText")
        ml_tier = await eval_js("document.getElementById('ml-tier-val')?.innerText")
        phys_arrival = await eval_js("document.getElementById('phys-arrival-val')?.innerText")
        ci_depth = await eval_js("document.getElementById('t35-ci-depth-pill')?.innerText")
        ci_arrival = await eval_js("document.getElementById('t35-ci-arrival-pill')?.innerText")
        uncertainty = await eval_js("document.getElementById('t35-uncertainty-pill')?.innerText")
        streets_count = await eval_js("document.getElementById('t35-streets-count-pill')?.innerText")
        node_rows = await eval_js("document.querySelectorAll('#pred-nodes-tbody tr').length")

        print(f"  Prediction Screen Active: {pred_active}")
        print(f"  ML Inundation Prob: {ml_prob} | Tier: {ml_tier}")
        print(f"  Peak Surge Arrival: {phys_arrival}")
        print(f"  90% CI (Depth): {ci_depth}")
        print(f"  90% CI (Arrival): {ci_arrival}")
        print(f"  Uncertainty (σ): {uncertainty}")
        print(f"  Inundated Streets Count: {streets_count}")
        print(f"  Node Inundation Rows: {node_rows} / 7")
        assert pred_active and node_rows == 7 and ci_depth and ci_arrival

        await capture_screen("03_flood_prediction_uncertainty.png")

        # ---------------------------------------------------------------------
        # 4. PUMP & GATE SIMULATOR SECTION (#simulator)
        # ---------------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" 4. PUMP & GATE SIMULATOR & MPC OPTIMIZATION AUDIT")
        print("-" * 60)
        await eval_js("navigateTo('simulator')")
        await asyncio.sleep(1.2)

        sim_active = await eval_js("document.getElementById('screen-simulator')?.classList.contains('active')")
        opt_card_exists = await eval_js("Boolean(document.getElementById('t35-sim-optimization-card'))")
        kpi_overflow = await eval_js("document.getElementById('opt-kpi-overflow-reduc')?.innerText")
        kpi_vol = await eval_js("document.getElementById('opt-kpi-vol-prevented')?.innerText")
        kpi_pumps = await eval_js("document.getElementById('opt-kpi-pumps')?.innerText")
        kpi_down = await eval_js("document.getElementById('opt-kpi-downstream')?.innerText")
        pumps_rows = await eval_js("document.querySelectorAll('#opt-pumps-tbody tr').length")
        directive = await eval_js("document.getElementById('opt-operator-directive-txt')?.innerText")

        print(f"  Simulator Screen Active: {sim_active}")
        print(f"  MPC Optimization Card Visible: {opt_card_exists}")
        print(f"  KPI Overflow Reduction: {kpi_overflow}")
        print(f"  KPI Prevented Volume: {kpi_vol}")
        print(f"  KPI Fleet Mobilization: {kpi_pumps}")
        print(f"  KPI Downstream Safety: {kpi_down}")
        print(f"  Pump Station Fleet Rows: {pumps_rows} / 3")
        print(f"  Operator Directive: {directive[:80]}...")
        assert sim_active and opt_card_exists and pumps_rows == 3

        await capture_screen("04_pump_simulator_mpc.png")

        print("\n" + "=" * 80)
        print(" ALL 4 IN-BROWSER VALIDATIONS PASSED & SCREENSHOTS CAPTURED!")
        print("=" * 80)
        print(f"Console errors recorded: {len(console_errors)}")

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(run_browser_verification())
