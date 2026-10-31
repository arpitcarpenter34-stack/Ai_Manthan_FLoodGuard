import asyncio
import base64
import json
import subprocess
import requests
import websockets
from pathlib import Path

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9555
TARGET_URL = "http://127.0.0.1:8000/#home"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_cdp_home_task38"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")

async def check_home():
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,900",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        await asyncio.sleep(1.0)
        r = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=2)
        pages = [p for p in r.json() if p.get("type") == "page"]
        ws = await websockets.connect(pages[0]["webSocketDebuggerUrl"], max_size=50 * 1024 * 1024)
        
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": TARGET_URL}}))
        await asyncio.sleep(3.0)
        
        await ws.send(json.dumps({"id": 3, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 3:
                b64 = msg.get("result", {}).get("data")
                out_p = SCREENSHOT_DIR / "10_homepage_with_model_intel_nav.png"
                out_p.write_bytes(base64.b64decode(b64))
                print(f"[HOMEPAGE] Saved screenshot: {out_p}")
                break
        await ws.close()
    finally:
        chrome_proc.terminate()

if __name__ == "__main__":
    asyncio.run(check_home())
