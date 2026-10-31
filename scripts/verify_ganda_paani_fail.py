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
CDP_PORT = 9527
TARGET_URL = "http://127.0.0.1:8000/#reports"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_reports_fail_audit"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")

async def run_audit():
    print("=" * 80)
    print("HYDRO-GUARD AI - WATER QUALITY FAIL AUDIT (DIRTY WATER FIX)")
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
        await listen_logs()

        # Check DOM status and rendering of cards
        eval_script = """
        (() => {
            const screen = document.getElementById('screen-reports');
            const cards = document.querySelectorAll('.rm-station-card');
            const cardData = [];

            cards.forEach(c => {
                const title = c.querySelector('.rm-card-title')?.innerText || '';
                const quality = c.querySelector('.rm-status-badge')?.innerText || '';
                const badgeClass = c.querySelector('.rm-status-badge')?.className || '';
                const turbidityEl = c.querySelector('.rm-param-col:nth-child(2) .rm-param-val');
                const turbidity = turbidityEl ? turbidityEl.innerText.trim() : '';
                const turbidityColor = turbidityEl ? turbidityEl.style.color : '';
                const assessment = c.querySelector('.rm-ai-assessment-box')?.innerText || '';
                const indicators = c.querySelectorAll('.rm-status-indicator');
                let mainOutlet = '';
                let treatment = '';
                indicators.forEach(ind => {
                    const txt = ind.innerText || '';
                    if (txt.includes('Main Outlet')) mainOutlet = txt;
                    if (txt.includes('Treatment Route')) treatment = txt;
                });
                cardData.push({ title, quality, badgeClass, turbidity, turbidityColor, assessment, mainOutlet, treatment });
            });

            // Summary metrics
            const passMetric = document.getElementById('rm-stat-pass')?.innerText || '';
            const holdMetric = document.getElementById('rm-stat-hold')?.innerText || '';
            const failMetric = document.getElementById('rm-stat-fail')?.innerText || '';

            return {
                screen_display: screen ? window.getComputedStyle(screen).display : 'missing',
                screen_visible: screen ? (window.getComputedStyle(screen).display !== 'none') : false,
                card_count: cards.length,
                summary_metrics: { pass: passMetric, hold: holdMetric, fail: failMetric },
                cards: cardData
            };
        })()
        """
        eval_res = await send_cdp("Runtime.evaluate", {
            "expression": eval_script,
            "returnByValue": True
        })

        res_data = eval_res.get("result", {}).get("value", {})
        print("\n[3] DOM Evaluation of Water Quality & Drain Cards:")
        print(f"    • Total Cards Rendered: {res_data.get('card_count')}")
        print(f"    • Summary KPI Metrics:  PASS: {res_data.get('summary_metrics', {}).get('pass')} | HOLD: {res_data.get('summary_metrics', {}).get('hold')} | FAIL: {res_data.get('summary_metrics', {}).get('fail')}")
        cards = res_data.get("cards", [])
        for i, c in enumerate(cards):
            print(f"    Card {i+1}: {c['title']}")
            print(f"       Quality:     {c['quality']} (Class: {c['badgeClass']})")
            print(f"       Turbidity:   {c['turbidity']} (Color: {c['turbidityColor']})")
            print(f"       {c['treatment']}")
            print(f"       {c['mainOutlet']}")
            print(f"       AI Verdict:  {c['assessment'][:80]}...")

        # Helper to capture screenshot
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

        print("\n[4] Capturing Clean Proof Screenshots...")
        # 1. Overview of Drain Cards with FAIL badges
        await capture_screenshot("reports_fail_01_cards_overview.png", scroll_y=0)

        # 2. Scrolled View (Cards 4-7: Rambagh, Pardeshipura, Vijay Nagar, Kabithedi)
        await capture_screenshot("reports_fail_02_cards_scrolled.png", scroll_y=460)

        # 3. Open Detail Modal for D-04 Rambagh (Muddy Sludge Culvert)
        print("\n[5] Testing Modal Inspection Certificate for D-04 Rambagh...")
        await send_cdp("Runtime.evaluate", {
            "expression": "openStationModal('NODE_RAMBAGH');"
        })
        await asyncio.sleep(1.0)
        await capture_screenshot("reports_fail_03_modal_rambagh_fail.png", scroll_y=0)

        # Close modal
        await send_cdp("Runtime.evaluate", {
            "expression": "closeStationModal();"
        })
        await asyncio.sleep(0.5)

        # 4. Open Detail Modal for D-07 Kabithedi (Plastic Trash & Municipal Sewage)
        print("\n[6] Testing Modal Inspection Certificate for D-07 Kabithedi...")
        await send_cdp("Runtime.evaluate", {
            "expression": "openStationModal('NODE_KABITHEDI_STP');"
        })
        await asyncio.sleep(1.0)
        await capture_screenshot("reports_fail_04_modal_kabithedi_fail.png", scroll_y=0)

        # Close modal
        await send_cdp("Runtime.evaluate", {
            "expression": "closeStationModal();"
        })
        await asyncio.sleep(0.5)

        # 5. Test Quality Status Filter: Filter by FAIL
        print("\n[7] Testing Quality Status Filter: FAIL...")
        await send_cdp("Runtime.evaluate", {
            "expression": """
            (() => {
                const sel = document.getElementById('rm-filter-quality');
                if (sel) {
                    sel.value = 'FAIL';
                    sel.dispatchEvent(new Event('change'));
                }
            })()
            """
        })
        await asyncio.sleep(1.2)
        await capture_screenshot("reports_fail_05_quality_filter_fail.png", scroll_y=0)

        # Reset Filter
        await send_cdp("Runtime.evaluate", {
            "expression": "resetReportsFilters();"
        })
        await asyncio.sleep(1.0)

        # Check console logs
        await listen_logs()
        print("\n[8] Console Log Audit:")
        err_count = 0
        for l in console_logs:
            if any(w in str(l).lower() for w in ["error", "uncaught", "typeerror"]):
                print(f"    [ERR] {l}")
                err_count += 1
            else:
                print(f"    [LOG] {l}")

        # Assertions
        all_fail = all(c['quality'] == "FAIL" for c in cards)
        all_treatment_req = all("REQUIRED" in c['treatment'] for c in cards)
        fail_metric_7 = res_data.get('summary_metrics', {}).get('fail') == '7'

        print("\n[9] Verification Verdict:")
        print(f"    • Card Count: {len(cards)} (Expected: 7)")
        print(f"    • All 7 Cards Marked FAIL: {all_fail}")
        print(f"    • All 7 Cards Treatment Route REQUIRED: {all_treatment_req}")
        print(f"    • Top KPI FAIL Count is 7: {fail_metric_7}")
        print(f"    • Total Console Errors: {err_count}")

        passed = len(cards) == 7 and all_fail and all_treatment_req and fail_metric_7 and err_count == 0
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

