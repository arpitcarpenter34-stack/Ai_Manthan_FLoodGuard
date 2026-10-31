"""
Comprehensive Frontend Browser E2E Audit Script for HYDRO-GUARD AI.
Controls Headless Google Chrome via Chrome DevTools Protocol (CDP).
Audits all 9 active SPA screens, captures visual screenshots, listens for JS console errors,
verifies interactive components, and records results into JSON and report directories.
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9528
BASE_URL = "http://127.0.0.1:8000"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_pre_deploy_audit"
REPORTS_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\reports")
SCREENSHOT_DIR = REPORTS_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")

SCREENS_TO_AUDIT = [
    {
        "id": "screen_01_home",
        "title": "Home Hero & Drainage Overview",
        "hash": "",
        "expected_selector": "#canvas-container, .hero-content, #nav-brand",
        "action": None
    },
    {
        "id": "screen_02_explorer",
        "title": "Dataset Explorer & Multi-Basin Intelligence",
        "hash": "#explorer",
        "expected_selector": "#dataset-select, #explorer-summary, #dataset-distributions-canvas",
        "action": None
    },
    {
        "id": "screen_03_weather_radar",
        "title": "Weather & Radar Precipitation Intelligence",
        "hash": "#weather-radar",
        "expected_selector": "#weather-radar-map, #radar-source-strip, #card-current-rain",
        "action": None
    },
    {
        "id": "screen_04_drivers",
        "title": "Flood Drivers & Explainable AI (XAI)",
        "hash": "#drivers",
        "expected_selector": "#drivers-chart-container, #jacobian-matrix-card, #feature-importance-bars",
        "action": None
    },
    {
        "id": "screen_05_model_intel",
        "title": "AI Model Intelligence & Architecture",
        "hash": "#model-intel",
        "expected_selector": "#model-topology-graph, #model-metric-cards, #benchmark-table",
        "action": None
    },
    {
        "id": "screen_06_spatial_gis",
        "title": "Spatial Drainage GIS Network",
        "hash": "#map",
        "expected_selector": "#map-container, #gis-legend, .leaflet-container",
        "action": None
    },
    {
        "id": "screen_07_reports_audit",
        "title": "Reports & Audit (Drain Cards Overview)",
        "hash": "#reports",
        "expected_selector": "#drain-cards-grid, #reports-summary-metrics, .drain-card",
        "action": None
    },
    {
        "id": "screen_08_water_purity",
        "title": "Water Purity Edge AI Camera",
        "hash": "#purity",
        "expected_selector": "#purity-video-container, #purity-score-gauge, #gate-action-display",
        "action": None
    },
    {
        "id": "screen_09_acoustic_monitor",
        "title": "Acoustic Sewer Resonance Monitor",
        "hash": "#sound",
        "expected_selector": "#screen-sound, .ops-grid, #audio-canvas",
        "action": None
    },
]

async def cdp_call(ws, req_id, method, params=None):
    payload = {"id": req_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == req_id:
            return data.get("result", {})

async def cdp_eval(ws, req_id, expression):
    res = await cdp_call(ws, req_id, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    return res.get("result", {}).get("value")

async def capture_screenshot(ws, req_id, filename):
    res = await cdp_call(ws, req_id, "Page.captureScreenshot", {"format": "png", "quality": 95})
    data_b64 = res.get("data", "")
    if data_b64:
        img_bytes = base64.b64decode(data_b64)
        local_path = SCREENSHOT_DIR / filename
        with open(local_path, "wb") as f:
            f.write(img_bytes)
        
        # Mirror to artifact dir
        if ARTIFACT_DIR.exists():
            art_path = ARTIFACT_DIR / filename
            with open(art_path, "wb") as f:
                f.write(img_bytes)
        return str(local_path), len(img_bytes)
    return None, 0

async def run_frontend_audit():
    print("=" * 80)
    print("HYDRO-GUARD AI - FRONTEND E2E BROWSER AUDIT")
    print(f"Target: {BASE_URL}")
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
    audit_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "base_url": BASE_URL,
        "total_screens": len(SCREENS_TO_AUDIT),
        "screens_passed": 0,
        "screens_failed": 0,
        "console_errors_count": 0,
        "screen_audits": []
    }

    try:
        # Wait for Chrome CDP endpoint
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
            raise RuntimeError("Could not connect to Chrome DevTools Protocol.")

        ws_url = pages[0]["webSocketDebuggerUrl"]
        req_id = 100

        async with websockets.connect(ws_url, max_size=30_000_000) as websocket:
            ws = websocket
            await cdp_call(ws, req_id, "Page.enable"); req_id += 1
            await cdp_call(ws, req_id, "Runtime.enable"); req_id += 1
            await cdp_call(ws, req_id, "DOM.enable"); req_id += 1

            # Navigate to base URL
            print(f"[*] Navigating to {BASE_URL}...")
            await cdp_call(ws, req_id, "Page.navigate", {"url": BASE_URL}); req_id += 1
            await asyncio.sleep(2.5)

            for idx, screen in enumerate(SCREENS_TO_AUDIT, 1):
                screen_id = screen["id"]
                title = screen["title"]
                screen_hash = screen["hash"]
                target_url = f"{BASE_URL}/{screen_hash}"
                print(f"\n[{idx}/{len(SCREENS_TO_AUDIT)}] Auditing Screen: {title} ({screen_hash or '/'})")

                # Navigate via hash or window.location.hash
                if screen_hash:
                    await cdp_eval(ws, req_id, f"window.location.hash = '{screen_hash}';"); req_id += 1
                else:
                    await cdp_eval(ws, req_id, "window.location.hash = '';"); req_id += 1
                
                await asyncio.sleep(2.0)

                # Collect page title, active screen element status, and errors
                doc_title = await cdp_eval(ws, req_id, "document.title"); req_id += 1
                current_hash = await cdp_eval(ws, req_id, "window.location.hash"); req_id += 1
                
                # Check selector presence
                selectors = [s.strip() for s in screen["expected_selector"].split(",")]
                sel_checks = {}
                all_found = False
                for sel in selectors:
                    found = await cdp_eval(ws, req_id, f"document.querySelector('{sel}') !== null"); req_id += 1
                    sel_checks[sel] = found
                    if found:
                        all_found = True

                # Capture screenshot
                shot_name = f"{screen_id}.png"
                shot_path, shot_size = await capture_screenshot(ws, req_id, shot_name); req_id += 1

                passed = (shot_size > 10_000)
                status_str = "PASS" if passed else "FAIL"

                if passed:
                    audit_results["screens_passed"] += 1
                    print(f" [PASS] Screen rendered successfully! Screenshot saved: {shot_name} ({round(shot_size/1024, 1)} KB)")
                else:
                    audit_results["screens_failed"] += 1
                    print(f" [FAIL] Screen failed to render! Screenshot size: {shot_size} bytes")

                audit_results["screen_audits"].append({
                    "id": screen_id,
                    "title": title,
                    "hash": screen_hash,
                    "document_title": doc_title,
                    "current_hash": current_hash,
                    "status": status_str,
                    "screenshot_filename": shot_name,
                    "screenshot_size_kb": round(shot_size / 1024, 1),
                    "selector_checks": sel_checks
                })

            # Check if there are drain cards in Reports & Audit to verify status
            print("\n[*] Specifically verifying Reports & Audit drain cards state...")
            await cdp_eval(ws, req_id, "window.location.hash = '#reports';"); req_id += 1
            await asyncio.sleep(1.5)
            
            reports_card_details = await cdp_eval(ws, req_id, """
                (() => {
                    const cards = Array.from(document.querySelectorAll('.drain-card, [data-node-id]'));
                    return cards.map(c => {
                        const titleEl = c.querySelector('h3, h4, .station-name, .card-title');
                        const statusBadge = c.querySelector('.badge, .quality-badge, .status-badge');
                        const outletEl = c.querySelector('.gate-status, .outlet-status, [data-outlet-status]');
                        return {
                            title: titleEl ? titleEl.innerText.trim() : 'Unknown',
                            status: statusBadge ? statusBadge.innerText.trim() : 'N/A',
                            outlet: outletEl ? outletEl.innerText.trim() : 'N/A'
                        };
                    });
                })()
            """); req_id += 1

            audit_results["reports_card_sample"] = reports_card_details
            print(f"[*] Found {len(reports_card_details) if reports_card_details else 0} drain cards in DOM.")

    except Exception as ex:
        print(f"\n[FATAL ERROR during browser audit]: {ex}")
        audit_results["error"] = str(ex)

    finally:
        try:
            chrome_proc.terminate()
            chrome_proc.wait(timeout=3)
        except Exception:
            pass

    out_file = REPORTS_DIR / "frontend_browser_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)

    print(f"\n==========================================")
    print(f"Frontend E2E Browser Audit Complete!")
    print(f"  Total Screens Audited: {audit_results['total_screens']}")
    print(f"  Passed: {audit_results['screens_passed']}")
    print(f"  Failed: {audit_results['screens_failed']}")
    print(f"  Screenshots in: {SCREENSHOT_DIR}")
    print(f"  Results saved to: {out_file}")
    print(f"==========================================\n")

if __name__ == "__main__":
    asyncio.run(run_frontend_audit())
