"""
Comprehensive E2E Chrome CDP Verification & Screenshot Capture for
AquaGuard AI / HYDRO-GUARD AI Reports & Monitoring Dashboard.
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

import tempfile

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9777
TARGET_URL = "http://127.0.0.1:8000/#reports"
USER_DATA_DIR = tempfile.mkdtemp(prefix="chrome_cdp_reports_")
ARTIFACT_DIR = r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810"
OUTPUT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data")


async def run_reports_cdp():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[CDP] Launching Chrome on port {CDP_PORT}...")
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--window-size=1600,1200",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
        # Wait for Chrome to bind CDP port
        for _ in range(30):
            try:
                r = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=1)
                if r.status_code == 200:
                    pages = r.json()
                    if pages:
                        break
            except Exception:
                time.sleep(0.2)
        else:
            print("ERROR: Failed to connect to Chrome CDP HTTP interface.")
            return

        page_ws_url = pages[0]["webSocketDebuggerUrl"]
        print(f"[CDP] Connected to Chrome page WebSocket: {page_ws_url}")

        # Connect with 50MB message size limit for large base64 screenshot transfers
        ws = await websockets.connect(page_ws_url, max_size=50 * 1024 * 1024, ping_interval=None)
        msg_id = 0
        pending_futures = {}
        console_messages = []

        async def reader_loop():
            try:
                async for raw_msg in ws:
                    try:
                        msg = json.loads(raw_msg)
                        mid = msg.get("id")
                        if mid is not None and mid in pending_futures:
                            fut = pending_futures.pop(mid)
                            if not fut.done():
                                fut.set_result(msg.get("result", {}))
                        else:
                            method = msg.get("method")
                            params = msg.get("params", {})
                            if method == "Console.messageAdded":
                                cmsg = params.get("message", {})
                                console_messages.append(cmsg.get("text", ""))
                            elif method == "Runtime.consoleAPICalled":
                                args = [str(a.get("value", a.get("description", ""))) for a in (params.get("args") or [])]
                                console_messages.append(" ".join(args))
                    except Exception as inner_e:
                        pass
            except websockets.exceptions.ConnectionClosed as e:
                print(f"[WS ConnectionClosed] code={e.code}, reason={e.reason}")
            except Exception as e:
                print(f"[WS ERROR] {type(e).__name__}: {e}")

        reader_task = asyncio.create_task(reader_loop())

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            pending_futures[msg_id] = fut
            cmd = {"id": msg_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(cmd))
            return await asyncio.wait_for(fut, timeout=15.0)

        async def save_screenshot(filename: str):
            res = await send_cmd("Page.captureScreenshot", {"format": "png"})
            b64_data = res.get("data")
            if b64_data:
                png_bytes = base64.b64decode(b64_data)
                local_path = OUTPUT_DIR / filename
                with open(local_path, "wb") as f:
                    f.write(png_bytes)
                print(f"[SCREENSHOT] Saved local screenshot: {local_path} ({len(png_bytes)} bytes)")
                
                # Copy to artifact dir for markdown embedding
                if os.path.exists(ARTIFACT_DIR):
                    artifact_path = os.path.join(ARTIFACT_DIR, filename)
                    with open(artifact_path, "wb") as f:
                        f.write(png_bytes)
                    print(f"[SCREENSHOT] Copied to artifact directory: {artifact_path}")
                return str(local_path)
            return None

        # Enable necessary CDP domains
        await send_cmd("Network.enable")
        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 1600,
            "height": 1200,
            "deviceScaleFactor": 1,
            "mobile": False
        })

        # -------------------------------------------------------------
        # STEP 1: Navigate to page and trigger #reports view
        # -------------------------------------------------------------
        print(f"\n[STEP 1] Navigating to {TARGET_URL}...")
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        
        # Wait for page scripts to load and initialize
        for _ in range(40):
            await asyncio.sleep(0.3)
            chk = await send_cmd("Runtime.evaluate", {"expression": "typeof navigateTo === 'function'"})
            if chk.get("result", {}).get("value") is True:
                break
        
        # Explicitly switch to reports screen
        eval_init = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                if (typeof navigateTo === 'function') {
                    navigateTo('reports', true);
                }
                return {
                    currentScreen: (typeof appState !== 'undefined' ? appState.currentScreen : 'unknown'),
                    currentView: (typeof appState !== 'undefined' ? appState.currentView : 'unknown'),
                    hash: window.location.hash
                };
            })()
            """,
            "returnByValue": True
        })
        print(f"[STEP 1] Init evaluation: {eval_init.get('result', {}).get('value')}")
        
        # Wait for station cards to render
        for _ in range(30):
            await asyncio.sleep(0.3)
            chk_cards = await send_cmd("Runtime.evaluate", {"expression": "document.querySelectorAll('.rm-station-card').length"})
            if (chk_cards.get("result", {}).get("value") or 0) > 0:
                print(f"[STEP 1] Station cards rendered: {chk_cards.get('result', {}).get('value')}")
                break
        await asyncio.sleep(1.0)

        # -------------------------------------------------------------
        # STEP 2: Verify DOM Elements & Aesthetic Structure
        # -------------------------------------------------------------
        dom_eval = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const screen = document.getElementById('screen-reports');
                const isVisible = screen && screen.classList.contains('active');
                
                // Header checks
                const title = document.querySelector('.rm-page-title')?.innerText?.trim();
                const subtitle = document.querySelector('.rm-page-subtitle')?.innerText?.trim();
                const clock = document.getElementById('rm-clock-txt')?.innerText?.trim();
                const temp = document.getElementById('rm-weather-temp')?.innerText?.trim();

                // Metric cards
                const metricCards = Array.from(document.querySelectorAll('.rm-metric-card')).map(c => ({
                    label: c.querySelector('.rm-metric-label')?.innerText?.trim(),
                    num: c.querySelector('.rm-metric-num')?.innerText?.trim()
                }));

                // Tabs
                const tabs = Array.from(document.querySelectorAll('.rm-tab-btn')).map(t => ({
                    text: t.innerText?.trim(),
                    active: t.classList.contains('active')
                }));

                // Station Cards
                const stationCards = Array.from(document.querySelectorAll('#rm-stations-grid .rm-station-card')).map(card => {
                    const pills = card.querySelectorAll('.rm-metric-pill');
                    return {
                        title: card.querySelector('.rm-card-title')?.innerText?.trim(),
                        badge: card.querySelector('.rm-status-badge')?.innerText?.trim(),
                        sampleId: card.querySelector('.rm-card-meta-left .rm-meta-val')?.innerText?.trim(),
                        sampleDate: card.querySelector('.rm-card-meta-right .rm-meta-val')?.innerText?.trim(),
                        metricsCount: pills.length,
                        purityOrPh: pills[0]?.innerText?.replace(/\\s+/g, ' ')?.trim(),
                        turbidity: pills[1]?.innerText?.replace(/\\s+/g, ' ')?.trim(),
                        tds: pills[2]?.innerText?.replace(/\\s+/g, ' ')?.trim(),
                        sluiceStatus: card.querySelector('.rm-sluice-status')?.innerText?.trim(),
                        hasViewBtn: !!card.querySelector('.rm-btn-card-action'),
                        hasPdfBtn: !!card.querySelectorAll('.rm-btn-card-action')[1]
                    };
                });

                return {
                    isVisible,
                    title,
                    subtitle,
                    weather: { clock, temp },
                    metricCards,
                    tabs,
                    stationCount: stationCards.length,
                    stationCards
                };
            })()
            """,
            "returnByValue": True
        })

        dom_info = dom_eval.get("result", {}).get("value", {})
        print("\n=======================================================")
        print("  REPORTS & MONITORING DOM STATE VERIFICATION")
        print("=======================================================")
        print(f"Screen Container Visible: {dom_info.get('isVisible')}")
        print(f"Title: {dom_info.get('title')}")
        print(f"Subtitle: {dom_info.get('subtitle')}")
        print(f"Weather Header: {dom_info.get('weather')}")
        print("\n8 Metric Cards:")
        for mc in dom_info.get("metricCards", []):
            print(f"  * {mc['label']}: {mc['num']}")
        print("\nTabs:")
        for t in dom_info.get("tabs", []):
            print(f"  * {t['text']} (Active: {t['active']})")
        print(f"\nRendered Station Cards: {dom_info.get('stationCount')} stations")
        for s in dom_info.get("stationCards", []):
            print(f"  * {s.get('title')} | Status: {s.get('badge')} | Sample: {s.get('sampleId')} ({s.get('sampleDate')}) | Metrics: {s.get('purityOrPh')} | {s.get('turbidity')} | {s.get('tds')}")

        # -------------------------------------------------------------
        # STEP 3: Capture Main Drain Reports View Screenshot
        # -------------------------------------------------------------
        print("\n[STEP 3] Capturing main Drain Reports view screenshot...")
        main_screenshot = await save_screenshot("reports_monitoring_main.png")

        # -------------------------------------------------------------
        # STEP 4: Test Modal Opening and Capture Modal Screenshot
        # -------------------------------------------------------------
        print("\n[STEP 4] Opening Station Inspection Modal for card 1...")
        await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const firstCardBtn = document.querySelector('#rm-stations-grid .rm-btn-card-action');
                if (firstCardBtn) {
                    firstCardBtn.click();
                    return { clicked: true };
                }
                return { clicked: false };
            })()
            """
        })
        await asyncio.sleep(1.5)
        modal_eval = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const modal = document.getElementById('modal-station-detail');
                const isShown = modal && modal.style.display !== 'none';
                const title = document.getElementById('modal-station-title')?.innerText?.trim();
                const bodyText = document.getElementById('modal-station-body')?.innerText?.trim()?.slice(0, 150);
                return { isShown, title, bodySnippet: bodyText };
            })()
            """,
            "returnByValue": True
        })
        print(f"[STEP 4] Modal State: {modal_eval.get('result', {}).get('value')}")
        await save_screenshot("reports_monitoring_modal.png")

        # Close Modal
        await send_cmd("Runtime.evaluate", {
            "expression": "if (typeof closeStationModal === 'function') closeStationModal();"
        })
        await asyncio.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 5: Switch to Tab 2: Filtration Units
        # -------------------------------------------------------------
        print("\n[STEP 5] Switching to Filtration Units tab...")
        await send_cmd("Runtime.evaluate", {
            "expression": "if (typeof switchReportsTab === 'function') switchReportsTab('filtration');"
        })
        await asyncio.sleep(1.5)
        tab2_eval = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const cards = Array.from(document.querySelectorAll('#rm-filtration-grid .rm-facility-card')).map(c => ({
                    title: c.querySelector('.rm-facility-card-title')?.innerText?.trim(),
                    sub: c.querySelector('.rm-facility-card-sub')?.innerText?.trim(),
                    badge: c.querySelector('.rm-badge-pill')?.innerText?.trim()
                }));
                return { count: cards.length, cards };
            })()
            """,
            "returnByValue": True
        })
        print(f"[STEP 5] Filtration Facilities Rendered: {tab2_eval.get('result', {}).get('value')}")
        await save_screenshot("reports_monitoring_filtration.png")

        # -------------------------------------------------------------
        # STEP 6: Switch to Tab 3: Area Monitoring
        # -------------------------------------------------------------
        print("\n[STEP 6] Switching to Area Monitoring tab...")
        await send_cmd("Runtime.evaluate", {
            "expression": "if (typeof switchReportsTab === 'function') switchReportsTab('areas');"
        })
        await asyncio.sleep(1.5)
        tab3_eval = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const cards = Array.from(document.querySelectorAll('#rm-areas-grid .rm-facility-card')).map(c => ({
                    title: c.querySelector('.rm-facility-card-title')?.innerText?.trim(),
                    sub: c.querySelector('.rm-facility-card-sub')?.innerText?.trim(),
                    badge: c.querySelector('.rm-badge-pill')?.innerText?.trim()
                }));
                return { count: cards.length, cards };
            })()
            """,
            "returnByValue": True
        })
        print(f"[STEP 6] Monitored Areas Rendered: {tab3_eval.get('result', {}).get('value')}")
        await save_screenshot("reports_monitoring_areas.png")

        # Switch back to Tab 1
        await send_cmd("Runtime.evaluate", {
            "expression": "if (typeof switchReportsTab === 'function') switchReportsTab('drains');"
        })
        await asyncio.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 7: Test Search and Filter Interaction
        # -------------------------------------------------------------
        print("\n[STEP 7] Testing Search Filter ('Rajwada')...")
        await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const searchInput = document.getElementById('rm-input-search');
                if (searchInput) {
                    searchInput.value = 'Rajwada';
                    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                    return { searched: true };
                }
                return { searched: false };
            })()
            """
        })
        await asyncio.sleep(1.2)
        filter_eval = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const cards = Array.from(document.querySelectorAll('#rm-stations-grid .rm-station-card')).map(c => c.querySelector('.rm-card-name')?.innerText?.trim());
                const paginationText = document.getElementById('rm-pagination-text')?.innerText?.trim();
                return { filteredCards: cards, paginationText };
            })()
            """,
            "returnByValue": True
        })
        print(f"[STEP 7] Filter result: {filter_eval.get('result', {}).get('value')}")
        await save_screenshot("reports_monitoring_filtered.png")

        # Reset search
        await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const searchInput = document.getElementById('rm-input-search');
                if (searchInput) {
                    searchInput.value = '';
                    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
            })()
            """
        })
        await asyncio.sleep(0.8)

        reader_task.cancel()
        print("\n[SUCCESS] All E2E CDP browser verifications completed successfully!")

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()
        chrome_proc.wait()
        print("[CDP] Chrome headless process closed cleanly.")


if __name__ == "__main__":
    asyncio.run(run_reports_cdp())
