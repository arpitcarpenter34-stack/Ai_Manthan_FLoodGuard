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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9522
TARGET_URL = "http://127.0.0.1:8000/#weather-radar"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_weather_radar_audit2"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")

async def run_audit():
    print("=" * 80)
    print("HYDRO-GUARD AI - WEATHER & RADAR DASHBOARD DETAILED AUDIT")
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
        "--window-size=1560,1100",
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
            print("ERROR: Failed to connect to headless Chrome CDP!")
            return False

        ws_url = pages[0]["webSocketDebuggerUrl"]
        print(f"[1] Connected to Chrome CDP: {ws_url}")

        ws = await websockets.connect(ws_url, max_size=50 * 1024 * 1024)

        msg_id = 1
        async def send_cdp(method, params=None):
            nonlocal msg_id
            curr_id = msg_id
            msg_id += 1
            payload = {"id": curr_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(payload))
            while True:
                resp = await ws.recv()
                data = json.loads(resp)
                if data.get("id") == curr_id:
                    return data.get("result", {})

        await send_cdp("Page.enable")
        await send_cdp("Runtime.enable")
        await send_cdp("Console.enable")

        console_logs = []
        async def listen_logs():
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=0.1)
                    parsed = json.loads(raw)
                    if parsed.get("method") == "Console.messageAdded":
                        console_logs.append(parsed["params"]["message"])
                    elif parsed.get("method") == "Runtime.consoleAPICalled":
                        args = [str(a.get("value", a.get("description", ""))) for a in parsed["params"].get("args", [])]
                        console_logs.append(" ".join(args))
                except (asyncio.TimeoutError, websockets.ConnectionClosed):
                    break

        print(f"[2] Navigating to {TARGET_URL}...")
        await send_cdp("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(4.0)
        await listen_logs()

        # Check DOM status and rendering with correct element IDs
        eval_script = """
        (() => {
            const screen = document.getElementById('screen-weather-radar');
            const mapEl = document.getElementById('wr-leaflet-map');
            const intensityCanvas = document.getElementById('wr-intensity-canvas');
            const forecastCanvas = document.getElementById('wr-forecast-canvas');
            const hyetoCanvas = document.getElementById('wr-history-hyetograph-canvas');
            
            const currentRain = document.getElementById('wr-val-current-rain')?.innerText;
            const accumRain = document.getElementById('wr-val-accum-rain')?.innerText;
            const fc1h = document.getElementById('wr-val-fc-1h')?.innerText;
            const fc6h = document.getElementById('wr-val-fc-6h')?.innerText;
            const alertLvl = document.getElementById('wr-val-alert-level')?.innerText;
            const alertBadge = document.getElementById('wr-alert-badge')?.innerText;
            const radarAuditTitle = document.querySelector('.wr-radar-stat-title')?.innerText;
            
            const stationRows = document.querySelectorAll('#wr-station-table-body tr')?.length;
            const eventPills = document.querySelectorAll('.wr-ev-pill')?.length;
            const activeEvTitle = document.getElementById('wr-ev-chart-title')?.innerText;

            const nowcastWind = document.getElementById('wr-nowcast-wind')?.innerText;
            const nowcastTemp = document.getElementById('wr-nowcast-temp')?.innerText;
            const nowcastRh = document.getElementById('wr-nowcast-rh')?.innerText;
            const nowcastPressure = document.getElementById('wr-nowcast-pressure')?.innerText;
            const nowcastDrainage = document.getElementById('wr-drainage-status-box')?.innerText;

            return {
                screen_display: screen ? window.getComputedStyle(screen).display : 'missing',
                screen_visible: screen ? (window.getComputedStyle(screen).display !== 'none') : false,
                map_present: !!mapEl,
                map_leaflet_init: mapEl ? mapEl.classList.contains('leaflet-container') : false,
                intensity_canvas: !!intensityCanvas,
                forecast_canvas: !!forecastCanvas,
                hyetograph_canvas: !!hyetoCanvas,
                current_rain: currentRain,
                accum_rain: accumRain,
                fc_1h: fc1h,
                fc_6h: fc6h,
                alert_level: alertLvl,
                alert_badge: alertBadge,
                radar_audit_title: radarAuditTitle,
                station_rows_count: stationRows,
                event_pills_count: eventPills,
                active_event_title: activeEvTitle,
                nowcast_wind: nowcastWind,
                nowcast_temp: nowcastTemp,
                nowcast_rh: nowcastRh,
                nowcast_pressure: nowcastPressure,
                nowcast_drainage: nowcastDrainage
            };
        })()
        """
        eval_res = await send_cdp("Runtime.evaluate", {
            "expression": eval_script,
            "returnByValue": True
        })

        res_data = eval_res.get("result", {}).get("value", {})
        print("\n[3] DOM Evaluation Results:")
        for k, v in res_data.items():
            print(f"    • {k}: {v}")

        # Capture high-resolution full-width views
        async def capture_screenshot(filename, scroll_y=0):
            if scroll_y > 0:
                await send_cdp("Runtime.evaluate", {
                    "expression": f"window.scrollTo(0, {scroll_y});"
                })
                await asyncio.sleep(0.5)
            
            res = await send_cdp("Page.captureScreenshot", {"format": "png"})
            img_b64 = res.get("data")
            if img_b64:
                file_path = SCREENSHOT_DIR / filename
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                shutil.copy(file_path, ARTIFACT_DIR / filename)
                print(f"    ✓ Captured screenshot: {filename} ({os.path.getsize(file_path):,} bytes)")
                return file_path
            return None

        print("\n[4] Capturing Clean Visual Proof Screenshots...")
        await capture_screenshot("wr_01_top_kpis_and_map.png", scroll_y=0)
        await capture_screenshot("wr_02_radar_audit_and_telemetry.png", scroll_y=280)
        await capture_screenshot("wr_03_intensity_forecast_nowcast.png", scroll_y=750)
        await capture_screenshot("wr_04_station_health_matrix.png", scroll_y=1220)
        await capture_screenshot("wr_05_extreme_storm_hyetographs.png", scroll_y=1650)

        # Test Interactivity: Switch Event Pill to Blue Heart
        print("\n[5] Testing Historical Event Selection: Switching to Eastbourne...")
        await send_cdp("Runtime.evaluate", {
            "expression": "document.querySelectorAll('.wr-ev-pill')[1]?.click();"
        })
        await asyncio.sleep(0.8)
        await capture_screenshot("wr_06_event_eastbourne_hyetograph.png", scroll_y=1650)

        # Test Interactivity: Switch Event Pill to CAMELS
        print("\n[6] Testing Historical Event Selection: Switching to CAMELS...")
        await send_cdp("Runtime.evaluate", {
            "expression": "document.querySelectorAll('.wr-ev-pill')[2]?.click();"
        })
        await asyncio.sleep(0.8)
        await capture_screenshot("wr_07_event_camels_hyetograph.png", scroll_y=1650)

        # Test Interactivity: Switch Time Scale to 12h
        print("\n[7] Testing Intensity Time Scale: Switching to 12h...")
        await send_cdp("Runtime.evaluate", {
            "expression": "document.querySelectorAll('.wr-tab-btn')[1]?.click();"
        })
        await asyncio.sleep(0.6)
        await capture_screenshot("wr_08_intensity_12h_view.png", scroll_y=750)

        # Test Interactivity: Switch Region to Pune CWPRS
        print("\n[8] Testing Multi-Region Switching: Switching to Pune CWPRS...")
        await send_cdp("Runtime.evaluate", {
            "expression": """
            (() => {
                const sel = document.getElementById('wr-region-select');
                if (sel) {
                    sel.value = 'pune_cwprs';
                    sel.dispatchEvent(new Event('change'));
                }
            })()
            """
        })
        await asyncio.sleep(3.5)
        await capture_screenshot("wr_09_region_pune_cwprs.png", scroll_y=0)

        # Console inspection
        await listen_logs()
        print("\n[9] JavaScript Console Inspection:")
        errors = [l for l in console_logs if any(err in str(l).lower() for err in ["error", "uncaught", "typeerror"])]
        print(f"    • Total Console Errors: {len(errors)}")
        for e in errors:
            print(f"      [ERR] {e}")

        all_ok = (
            res_data.get("screen_visible") and
            res_data.get("map_present") and
            res_data.get("intensity_canvas") and
            res_data.get("forecast_canvas") and
            res_data.get("hyetograph_canvas") and
            res_data.get("station_rows_count", 0) >= 4 and
            res_data.get("event_pills_count", 0) >= 3 and
            len(errors) == 0
        )
        print(f"\nFinal Audit Verdict: {'ALL CHECKS PASSED (100% SUCCESS)' if all_ok else 'SOME CHECKS REQUIRE ATTENTION'}")
        return all_ok

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()

if __name__ == "__main__":
    success = asyncio.run(run_audit())
    sys.exit(0 if success else 1)
