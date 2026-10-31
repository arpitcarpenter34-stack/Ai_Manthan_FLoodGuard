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
CDP_PORT = 9474
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_home_test"

async def test_home():
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,960",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        pages = []
        for _ in range(40):
            try:
                r = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=1)
                if r.status_code == 200:
                    pages = [p for p in r.json() if p.get("type") == "page"]
                    if pages: break
            except Exception: pass
            time.sleep(0.2)

        ws = await websockets.connect(pages[0]["webSocketDebuggerUrl"])
        msg_id = 0
        async def eval_js(expr):
            nonlocal msg_id
            msg_id += 1
            cid = msg_id
            await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True}}))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {}).get("value")

        await ws.send(json.dumps({"id": 100, "method": "Page.navigate", "params": {"url": "http://127.0.0.1:8000/#explorer"}}))
        await asyncio.sleep(2.0)
        print("At #explorer:")
        print("  view-app display:", await eval_js("getComputedStyle(document.getElementById('view-app')).display"))
        print("  view-home display:", await eval_js("getComputedStyle(document.getElementById('view-home')).display"))

        # Click Home button
        await eval_js("navigateToHome();")
        await asyncio.sleep(1.0)
        print("After navigateToHome():")
        print("  view-app display:", await eval_js("getComputedStyle(document.getElementById('view-app')).display"))
        print("  view-home display:", await eval_js("getComputedStyle(document.getElementById('view-home')).display"))
        print("  canvas present:", await eval_js("Boolean(document.getElementById('hero-canvas'))"))

        # Click Dataset Explorer link on homepage
        await eval_js("navigateTo('explorer');")
        await asyncio.sleep(1.0)
        print("After navigateTo('explorer') from homepage:")
        print("  view-app display:", await eval_js("getComputedStyle(document.getElementById('view-app')).display"))
        print("  view-home display:", await eval_js("getComputedStyle(document.getElementById('view-home')).display"))
        print("  screen-explorer display:", await eval_js("getComputedStyle(document.getElementById('screen-explorer')).display"))

        await ws.close()
    finally:
        chrome_proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_home())

