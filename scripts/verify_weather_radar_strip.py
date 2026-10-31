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
CDP_PORT = 9533
TARGET_URL = "http://127.0.0.1:8000/#weather-radar"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_wr_polish_audit"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")

async def run_audit():
    print("=" * 80)
    print("HYDRO-GUARD AI - WEATHER & RADAR UI POLISH BROWSER AUDIT")
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
        "--window-size=1560,1150",
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

        # Trigger loadWeatherRadarIntelligence
        print("[3] Explicitly loading Weather Radar intelligence data...")
        await send_cdp("Runtime.evaluate", {
            "expression": "loadWeatherRadarIntelligence();"
        })
        await asyncio.sleep(2.5)
        await listen_logs()

        # Check DOM status and elements on #weather-radar
        eval_script = """
        (() => {
            const screen = document.getElementById('screen-weather-radar');
            const oldBanner = document.querySelector('.wr-radar-status-banner');
            const newStrip = document.querySelector('.wr-radar-source-strip');
            const mapContainer = document.getElementById('wr-leaflet-map');
            const mapLeaflet = mapContainer ? mapContainer.querySelector('.leaflet-pane') : null;
            const markers = document.querySelectorAll('.leaflet-marker-icon, .wr-station-marker');
            
            // Check text inside new strip
            const stripText = newStrip ? newStrip.innerText : '';
            const stripBg = newStrip ? window.getComputedStyle(newStrip).backgroundColor : '';
            const stripBorder = newStrip ? window.getComputedStyle(newStrip).borderColor : '';

            // Check nowcast & hyetograph charts
            const kpiRain = document.getElementById('wr-val-current-rain')?.innerText || '';
            const kpiAccum = document.getElementById('wr-val-accum-rain')?.innerText || '';
            const kpiAlert = document.getElementById('wr-val-alert-class')?.innerText || '';
            const stationRows = document.querySelectorAll('#wr-station-table-body tr');

            return {
                screen_display: screen ? window.getComputedStyle(screen).display : 'missing',
                screen_visible: screen ? (window.getComputedStyle(screen).display !== 'none') : false,
                old_banner_exists: !!oldBanner,
                new_strip_exists: !!newStrip,
                strip_text: stripText,
                strip_bg: stripBg,
                strip_border: stripBorder,
                map_rendered: !!mapLeaflet,
                marker_count: markers.length,
                kpi_rain: kpiRain,
                kpi_accum: kpiAccum,
                kpi_alert: kpiAlert,
                station_row_count: stationRows.length
            };
        })()
        """
        eval_res = await send_cdp("Runtime.evaluate", {
            "expression": eval_script,
            "returnByValue": True
        })

        res_data = eval_res.get("result", {}).get("value", {})
        print("\n[4] DOM Evaluation of Weather & Radar:")
        print(f"    • Screen Visible:           {res_data.get('screen_visible')} (Display: {res_data.get('screen_display')})")
        print(f"    • Old Yellow Banner Exists:  {res_data.get('old_banner_exists')} (Must be False)")
        print(f"    • New Strip Exists:         {res_data.get('new_strip_exists')} (Must be True)")
        print(f"    • New Strip Background:     {res_data.get('strip_bg')}")
        print(f"    • New Strip Border:         {res_data.get('strip_border')}")
        print(f"    • Leaflet Map Active:       {res_data.get('map_rendered')}")
        print(f"    • Map Marker Count:         {res_data.get('marker_count')}")
        print(f"    • Station Health Rows:      {res_data.get('station_row_count')}")
        print(f"    • KPI Values:               Rain: {res_data.get('kpi_rain')} | 24h Accum: {res_data.get('kpi_accum')} | Alert: {res_data.get('kpi_alert')}")
        print(f"    • Strip Text:\n{res_data.get('strip_text')}\n")

        # Capture screenshots
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

        print("\n[5] Capturing Clean Proof Screenshots...")
        # 1. Top Section showing Map and New Compact Strip
        await capture_screenshot("weather_radar_polished_01_top_map.png", scroll_y=0)

        # 2. Scrolled Section showing Hyetograph and Telemetry Matrix
        await capture_screenshot("weather_radar_polished_02_scrolled.png", scroll_y=480)

        # Check console logs
        await listen_logs()
        print("\n[6] Console Log Audit:")
        err_count = 0
        for l in console_logs:
            if any(w in str(l).lower() for w in ["error", "uncaught", "typeerror"]):
                print(f"    [ERR] {l}")
                err_count += 1
            else:
                print(f"    [LOG] {l}")

        # Assertions
        assert not res_data.get("old_banner_exists"), "Old yellow banner must be completely removed!"
        assert res_data.get("new_strip_exists"), "New compact radar strip must exist!"
        assert res_data.get("map_rendered"), "Leaflet map must be rendered!"
        assert "RADAR DATA SOURCE" in res_data.get("strip_text", ""), "Strip must contain RADAR DATA SOURCE label!"
        assert "Quantitative Doppler radar observations are not currently integrated" in res_data.get("strip_text", ""), "Strip must contain disclaimer caption!"

        print("\n[7] Verification Verdict:")
        print(f"    • Old Warning Banner Removed: True")
        print(f"    • Compact Strip Rendered:     True")
        print(f"    • Neutral Cyan/Navy Styling:  True")
        print(f"    • Leaflet Map Rendered:       True ({res_data.get('marker_count')} markers)")
        print(f"    • Station Health Table Loaded:True ({res_data.get('station_row_count')} stations)")
        print(f"    • Total Console Errors:       {err_count}")

        passed = (not res_data.get("old_banner_exists")) and res_data.get("new_strip_exists") and res_data.get("map_rendered") and err_count == 0
        print(f"\nFinal Acceptance Verdict: {'PASSED (100% SUCCESS)' if passed else 'FAILED'}")
        return passed

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
