"""
Clean, Reliable CDP Screenshot Capture for Reports & Monitoring Screen
with Genuine Drain Photographs.
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
CDP_PORT = 9933
TARGET_URL = "http://127.0.0.1:8000/#reports"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_cdp_reports_clean_run"
ARTIFACT_DIR = r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810"
OUTPUT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data")


async def run():
    if os.path.exists(USER_DATA_DIR):
        try:
            shutil.rmtree(USER_DATA_DIR, ignore_errors=True)
        except Exception:
            pass
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[CDP] Launching Chrome on port {CDP_PORT}...")
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--disable-extensions",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        TARGET_URL
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
        for _ in range(30):
            try:
                r = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=1)
                if r.status_code == 200:
                    pages = [p for p in r.json() if p.get("type") == "page"]
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
                    try:
                        msg = json.loads(raw_msg)
                        mid = msg.get("id")
                        if mid is not None and mid in pending_futures:
                            fut = pending_futures.pop(mid)
                            if not fut.done():
                                fut.set_result(msg.get("result", {}))
                    except Exception:
                        pass
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

        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")

        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 1600,
            "height": 1150,
            "deviceScaleFactor": 1,
            "mobile": False
        })

        await asyncio.sleep(2.0)

        # Trigger navigation to reports screen if not active
        eval_res = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                if (typeof navigateTo === 'function') navigateTo('reports', false);
                const cards = document.querySelectorAll('.rm-station-card');
                const cardDetails = Array.from(cards).map(c => ({
                    title: c.querySelector('.rm-card-title')?.innerText,
                    status: c.querySelector('.rm-status-badge')?.innerText,
                    imgSrc: c.querySelector('.rm-card-img')?.src
                }));
                return {
                    reportsActive: document.getElementById('screen-reports')?.classList.contains('active'),
                    cardCount: cards.length,
                    cards: cardDetails
                };
            })()
            """,
            "returnByValue": True
        })
        info = eval_res.get("result", {}).get("value", {})
        print(f"Reports Active: {info.get('reportsActive')}")
        print(f"Card Count: {info.get('cardCount')}")
        for c in info.get("cards", []):
            print(f"  * {c.get('title')} [{c.get('status')}] -> {c.get('imgSrc')}")

        # Wait a moment for images to paint
        await asyncio.sleep(2.5)
        await capture_screen("reports_monitoring_main.png")
        print("\n[SUCCESS] Reports & Monitoring screenshot captured cleanly!")

        reader_task.cancel()

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()
        chrome_proc.wait()


if __name__ == "__main__":
    asyncio.run(run())
