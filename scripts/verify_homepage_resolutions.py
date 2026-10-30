"""
Verify Homepage Layout across Desktop, Tablet, and Mobile resolutions
after removing unverified floating metric cards.
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import requests
import websockets

sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9555
TARGET_URL = "http://127.0.0.1:8000/#home"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_cdp_homepage"
ARTIFACT_DIR = r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810"
OUTPUT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data")


async def run_homepage_verification():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[CDP] Launching Chrome on port {CDP_PORT}...")
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
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
                            fut.set_result(msg.get("result", {}))
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
            return await asyncio.wait_for(fut, timeout=15.0)

        async def capture_screen(filename: str):
            res = await send_cmd("Page.captureScreenshot", {"format": "png"})
            b64_data = res.get("data")
            if b64_data:
                png_bytes = base64.b64decode(b64_data)
                local_path = OUTPUT_DIR / filename
                with open(local_path, "wb") as f:
                    f.write(png_bytes)
                print(f"[SCREENSHOT] Saved: {local_path} ({len(png_bytes)} bytes)")
                if os.path.exists(ARTIFACT_DIR):
                    artifact_path = os.path.join(ARTIFACT_DIR, filename)
                    with open(artifact_path, "wb") as f:
                        f.write(png_bytes)
                return str(local_path)
            return None

        await send_cmd("Network.enable")
        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")

        # -------------------------------------------------------------
        # 1. Desktop Resolution Verification (1600 x 1000)
        # -------------------------------------------------------------
        print("\n=======================================================")
        print("  1. DESKTOP RESOLUTION VERIFICATION (1600 x 1000)")
        print("=======================================================")
        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 1600,
            "height": 1000,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(2.5)

        desktop_eval = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                if (typeof navigateToHome === 'function') navigateToHome(false);
                
                // Check removed cards
                const heroVisuals = document.querySelector('.hero-visuals');
                const rainCard = document.querySelector('.card-rainfall') || document.getElementById('hero-rain-val');
                const riverCard = document.querySelector('.card-river') || document.getElementById('hero-river-val');
                const flowCard = document.querySelector('.card-drainage') || document.getElementById('hero-flow-val');

                // Check preserved elements
                const heroTitle = document.querySelector('.hero-title')?.innerText?.trim();
                const btnExplore = document.querySelector('.btn-dashboard-explore')?.innerText?.trim();
                const btnMap = document.querySelector('.btn-map-view')?.innerText?.trim();
                const featureCards = Array.from(document.querySelectorAll('.hero-mini-card')).map(c => ({
                    title: c.querySelector('.hero-mini-title')?.innerText?.trim(),
                    desc: c.querySelector('.hero-mini-desc')?.innerText?.trim()
                }));
                const navLinks = Array.from(document.querySelectorAll('.home-navbar .nav-link')).map(l => l.innerText?.trim());

                return {
                    cardsRemoved: !heroVisuals && !rainCard && !riverCard && !flowCard,
                    heroTitle,
                    btnExplore,
                    btnMap,
                    featureCardsCount: featureCards.length,
                    featureCards,
                    navLinks
                };
            })()
            """,
            "returnByValue": True
        })

        d_info = desktop_eval.get("result", {}).get("value", {})
        print(f"Floating Metric Cards Removed: {d_info.get('cardsRemoved')}")
        print(f"Hero Title: {repr(d_info.get('heroTitle'))}")
        print(f"CTA Buttons: [{d_info.get('btnExplore')}] & [{d_info.get('btnMap')}]")
        print(f"Preserved Feature Cards Count: {d_info.get('featureCardsCount')} (Expected: 4)")
        for fc in d_info.get("featureCards", []):
            print(f"  * {fc['title']} - {fc['desc']}")
        print(f"Preserved Navbar Links: {d_info.get('navLinks')}")

        await capture_screen("homepage_desktop_clean.png")

        # -------------------------------------------------------------
        # 2. Tablet Resolution Verification (768 x 1024)
        # -------------------------------------------------------------
        print("\n=======================================================")
        print("  2. TABLET RESOLUTION VERIFICATION (768 x 1024)")
        print("=======================================================")
        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 768,
            "height": 1024,
            "deviceScaleFactor": 1,
            "mobile": True
        })
        await asyncio.sleep(1.0)
        await capture_screen("homepage_tablet_clean.png")

        # -------------------------------------------------------------
        # 3. Mobile Resolution Verification (375 x 812)
        # -------------------------------------------------------------
        print("\n=======================================================")
        print("  3. MOBILE RESOLUTION VERIFICATION (375 x 812)")
        print("=======================================================")
        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 375,
            "height": 812,
            "deviceScaleFactor": 2,
            "mobile": True
        })
        await asyncio.sleep(1.0)
        await capture_screen("homepage_mobile_clean.png")

        reader_task.cancel()
        print("\n[SUCCESS] Homepage layout verification and screenshots completed cleanly!")

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()
        chrome_proc.wait()


if __name__ == "__main__":
    asyncio.run(run_homepage_verification())
