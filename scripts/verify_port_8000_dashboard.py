import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import urllib.request
import requests
import websockets

sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9876
BASE_URL = "http://127.0.0.1:8000"
USER_DATA_DIR = tempfile.mkdtemp(prefix="chrome_cdp_port8000_")

print("=" * 80)
print(" HYDRO-GUARD AI — PORT 8000 PRIMARY DASHBOARD BROWSER AUDIT")
print("=" * 80)

async def run_audit():
    print(f"\n[1] Launching Headless Chrome on CDP port {CDP_PORT}...")
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
        # Wait for CDP HTTP interface
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

        async def reader_loop():
            try:
                async for raw_msg in ws:
                    msg = json.loads(raw_msg)
                    mid = msg.get("id")
                    if mid is not None and mid in pending_futures:
                        fut = pending_futures.pop(mid)
                        if not fut.done():
                            fut.set_result(msg)
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

        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("Network.enable")

        # ---------------------------------------------------------------
        # 1. SECTION 1: HOME / HERO
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 1: HOME / HERO VIEW (#home)")
        print("-" * 60)
        await send_cmd("Page.navigate", {"url": f"{BASE_URL}/#home"})
        await asyncio.sleep(2.0)

        title = await eval_js("document.title")
        hero_visible = await eval_js("Boolean(document.getElementById('view-home') && document.getElementById('view-home').style.display !== 'none')")
        canvas_exists = await eval_js("Boolean(document.getElementById('hero-canvas'))")
        nav_links_count = await eval_js("document.querySelectorAll('.nav-links li').length")
        hero_h1 = await eval_js("document.querySelector('.hero-title')?.innerText?.replace(/\\n/g, ' ')")

        print(f"  Page Title: '{title}'")
        print(f"  Hero View Active: {hero_visible}")
        print(f"  Hero Canvas Animation Mounted: {canvas_exists}")
        print(f"  Navbar Links Count: {nav_links_count}")
        print(f"  Hero Headline: '{hero_h1}'")
        assert hero_visible and canvas_exists and nav_links_count >= 7

        # ---------------------------------------------------------------
        # 2. SECTION 2: FLOOD MAP (#map)
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 2: FLOOD MAP (#map)")
        print("-" * 60)
        await eval_js("navigateTo('map')")
        await asyncio.sleep(1.0)

        map_screen_active = await eval_js("document.getElementById('screen-map')?.classList.contains('active')")
        leaflet_initialized = await eval_js("Boolean(appState.leafletMap)")
        markers_count = await eval_js("appState.mapMarkers.length")
        map_bounds = await eval_js("appState.leafletMap ? appState.leafletMap.getCenter() : null")

        print(f"  Map Screen Active: {map_screen_active}")
        print(f"  Leaflet Engine Initialized: {leaflet_initialized}")
        print(f"  Station Markers Rendered: {markers_count} (Expected: 7 Indore stations)")
        print(f"  Map Center Coordinate: {map_bounds}")
        assert map_screen_active and leaflet_initialized and markers_count == 7

        # ---------------------------------------------------------------
        # 3. SECTION 3: AI FLOOD PREDICTION (#prediction)
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 3: AI FLOOD PREDICTION (#prediction)")
        print("-" * 60)
        await eval_js("navigateTo('prediction')")
        await asyncio.sleep(0.5)

        # Test A: Dry Weather (0.0 mm/h)
        await eval_js("""
            document.getElementById('input-rain-slider').value = '0.0';
            document.getElementById('input-surge-slider').value = '1.0';
            document.getElementById('input-pumps-count').value = '2';
            runDualPrediction();
        """)
        await asyncio.sleep(0.8)
        dry_prob = await eval_js("document.getElementById('ml-prob-val')?.innerText")
        dry_tier = await eval_js("document.getElementById('ml-tier-val')?.innerText")
        dry_arrival = await eval_js("document.getElementById('phys-arrival-val')?.innerText")

        # Test B: Moderate Rain (15.0 mm/h)
        await eval_js("""
            document.getElementById('input-rain-slider').value = '15.0';
            document.getElementById('input-surge-slider').value = '1.0';
            document.getElementById('input-pumps-count').value = '2';
            runDualPrediction();
        """)
        await asyncio.sleep(0.8)
        mod_prob = await eval_js("document.getElementById('ml-prob-val')?.innerText")
        mod_tier = await eval_js("document.getElementById('ml-tier-val')?.innerText")
        mod_arrival = await eval_js("document.getElementById('phys-arrival-val')?.innerText")

        # Test C: Heavy Rain (65.0 mm/h, 1.5x surge)
        await eval_js("""
            document.getElementById('input-rain-slider').value = '65.0';
            document.getElementById('input-surge-slider').value = '1.5';
            document.getElementById('input-pumps-count').value = '2';
            runDualPrediction();
        """)
        await asyncio.sleep(0.8)
        heavy_prob = await eval_js("document.getElementById('ml-prob-val')?.innerText")
        heavy_tier = await eval_js("document.getElementById('ml-tier-val')?.innerText")
        heavy_arrival = await eval_js("document.getElementById('phys-arrival-val')?.innerText")
        heavy_choke = await eval_js("document.getElementById('phys-choke-val')?.innerText")
        nodes_rows = await eval_js("document.querySelectorAll('#pred-nodes-tbody tr').length")

        print(f"  [Scenario A: 0 mm/h]   -> Risk: {dry_tier} | Prob: {dry_prob} | Arrival: {dry_arrival}")
        print(f"  [Scenario B: 15 mm/h]  -> Risk: {mod_tier} | Prob: {mod_prob} | Arrival: {mod_arrival}")
        print(f"  [Scenario C: 65 mm/h]  -> Risk: {heavy_tier} | Prob: {heavy_prob} | Arrival: {heavy_arrival} | Choke: {heavy_choke}")
        print(f"  Node Inundation Rows: {nodes_rows}")
        assert nodes_rows == 7

        # ---------------------------------------------------------------
        # 4. SECTION 4: WATER PURITY (#purity)
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 4: WATER PURITY ANALYSIS (#purity)")
        print("-" * 60)
        await eval_js("navigateTo('purity')")
        await asyncio.sleep(0.5)

        # Clean Sample Test
        await eval_js("runImageAnalysisWithSample('clean_rainwater', 'clean_rainwater.jpg')")
        await asyncio.sleep(0.6)
        clean_purity = await eval_js("document.getElementById('gauge-purity-text')?.innerText")
        clean_verdict = await eval_js("document.getElementById('purity-alert-headline')?.innerText")
        clean_gate = await eval_js("document.getElementById('purity-gate-action')?.innerText")

        # Sludge Sample Test
        await eval_js("runImageAnalysisWithSample('polluted_sludge', 'polluted_sludge.jpg')")
        await asyncio.sleep(0.6)
        sludge_purity = await eval_js("document.getElementById('gauge-purity-text')?.innerText")
        sludge_verdict = await eval_js("document.getElementById('purity-alert-headline')?.innerText")
        sludge_gate = await eval_js("document.getElementById('purity-gate-action')?.innerText")

        print(f"  [Clean Rainwater]  -> Score: {clean_purity} | Verdict: '{clean_verdict}' | Action: '{clean_gate}'")
        print(f"  [Polluted Sludge]  -> Score: {sludge_purity} | Verdict: '{sludge_verdict}' | Action: '{sludge_gate}'")
        assert "PASS" in clean_verdict or "80" in clean_verdict
        assert "FAIL" in sludge_verdict or "STP" in sludge_gate

        # ---------------------------------------------------------------
        # 5. SECTION 5: ACOUSTIC LEVEL AI (#sound)
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 5: ACOUSTIC DRAIN MONITORING (#sound)")
        print("-" * 60)
        await eval_js("navigateTo('sound')")
        await asyncio.sleep(0.5)

        # Run with moderate surge audio
        await eval_js("runAcousticAnalysisWithLevel(60.0, 'moderate_surge_60pct.wav')")
        await asyncio.sleep(0.6)
        sound_level = await eval_js("document.getElementById('gauge-sound-text')?.innerText")
        sound_db = await eval_js("document.getElementById('sound-db-text')?.innerText")
        sound_alert = await eval_js("document.getElementById('sound-alert-headline')?.innerText")
        sound_spec_file = await eval_js("document.getElementById('spec-sound-filename')?.innerText")

        print(f"  Acoustic Level: {sound_level} | SPL Decibels: {sound_db}")
        print(f"  Alert Headline: '{sound_alert}' | Target Sample File: '{sound_spec_file}'")
        print("  Provenance: Calibrated underground sewer hydrophone audio (prerecorded/synthesized WAV, not live mic)")
        assert len(sound_level) > 0 and len(sound_db) > 0

        # ---------------------------------------------------------------
        # 6. SECTION 6: PUMP & GATE SIMULATOR (#simulator)
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 6: PUMP & GATE SIMULATOR (#simulator)")
        print("-" * 60)
        await eval_js("navigateTo('simulator')")
        await asyncio.sleep(0.5)

        sim_active = await eval_js("document.getElementById('screen-simulator')?.classList.contains('active')")
        sim_slider_val = await eval_js("document.getElementById('sim-surge-slider')?.value")
        print(f"  Simulator Screen Active: {sim_active}")
        print(f"  Surge Multiplier Control: {sim_slider_val}x")
        print("  Provenance: Dynamic hydraulic simulation model (no physical municipal hardware actuators claimed)")
        assert sim_active

        # ---------------------------------------------------------------
        # 7. SECTION 7: REPORTS & MONITORING (#reports)
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 7: REPORTS & MONITORING (#reports)")
        print("-" * 60)
        await eval_js("navigateTo('reports')")
        await asyncio.sleep(1.0)

        reports_active = await eval_js("document.getElementById('screen-reports')?.classList.contains('active')")
        station_cards = await eval_js("document.querySelectorAll('#rm-stations-grid .rm-station-card').length")
        stat_stations_val = await eval_js("document.getElementById('rm-stat-stations')?.innerText")
        clock_txt = await eval_js("document.getElementById('rm-clock-txt')?.innerText")

        print(f"  Reports Screen Active: {reports_active}")
        print(f"  Station Grid Cards Rendered: {station_cards} (Expected: 7 Indore stations)")
        print(f"  Reports Header Stat Stations: {stat_stations_val}")
        print(f"  Reports Clock / Weather: '{clock_txt}'")

        # Verify actual CSV and PDF download contents
        with urllib.request.urlopen(f"{BASE_URL}/api/v1/reports/export/csv") as r:
            csv_content = r.read().decode("utf-8")
        with urllib.request.urlopen(f"{BASE_URL}/api/v1/reports/export-all-pdf") as r:
            pdf_bytes = r.read()

        csv_lines = csv_content.strip().split("\n")
        print(f"  Exported CSV: {len(csv_lines)} lines, Header: '{csv_lines[0]}'")
        print(f"  Exported PDF: {len(pdf_bytes)} bytes, Magic Header: {pdf_bytes[:4]}")
        assert len(csv_lines) >= 8 and b"%PDF" in pdf_bytes

        # ---------------------------------------------------------------
        # 8. SECTION 8: HISTORY & AUDIT LOGS (#history)
        # ---------------------------------------------------------------
        print("\n" + "-" * 60)
        print(" SECTION 8: HISTORY & AUDIT LOGS (#history)")
        print("-" * 60)
        await eval_js("navigateTo('history')")
        await asyncio.sleep(0.5)

        # Insert a real audit record via db_manager to verify live persistence
        sys.path.insert(0, r"E:\ai-manthan\hydro_guard_indore")
        from backend.services.db_manager import db_manager
        test_rec_id = db_manager.log_image_analysis(
            input_source="acceptance_audit_test.jpg",
            purity_score=94.5,
            is_clean=True,
            gate_action="GATE OPEN TO KHAN RIVER",
            turbidity_estimate=9.2,
            debris_count=0,
            details={"audit_tag": "TASK_3_4_FINAL_AUDIT"}
        )
        print(f"  Inserted live SQLite audit record: ID #{test_rec_id}")

        # Fetch history logs in browser
        await eval_js("fetchHistoryLogs()")
        await asyncio.sleep(0.6)

        history_rows = await eval_js("document.querySelectorAll('#history-logs-tbody tr').length")
        first_row_text = await eval_js("document.querySelector('#history-logs-tbody tr')?.innerText?.replace(/\\t/g, ' | ')")
        print(f"  History Table Rows in Browser: {history_rows}")
        print(f"  Latest Persistent Record in UI: {first_row_text}")
        assert history_rows >= 1 and "acceptance_audit_test" in first_row_text

        # Clean up test record from SQLite
        try:
            import sqlite3
            conn = sqlite3.connect(r"E:\ai-manthan\hydro_guard_indore\data\hydro_guard.db")
            conn.execute("DELETE FROM image_analysis_logs WHERE id = ?", (test_rec_id,))
            conn.commit()
            conn.close()
            print(f"  Safely purged temporary audit record ID #{test_rec_id} from SQLite.")
        except Exception as e:
            print(f"  Note on purge: {e}")

        print("\n" + "=" * 80)
        print(" ALL 8 PORT 8000 DASHBOARD SECTIONS VERIFIED LIVE IN CHROME BROWSER!")
        print("=" * 80)

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()

if __name__ == "__main__":
    asyncio.run(run_audit())
