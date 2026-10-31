import asyncio
import json
import subprocess
import time
import requests
import websockets

async def inspect():
    proc = subprocess.Popen([
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--remote-debugging-port=9460",
        "--headless=new",
        "--user-data-dir=C:/Users/Arpit/AppData/Local/Temp/chrome_diag2",
        "--window-size=1440,960",
        "http://127.0.0.1:8000/#explorer"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(3.0)
    try:
        r = requests.get("http://127.0.0.1:9460/json").json()
        ws = await websockets.connect(r[0]["webSocketDebuggerUrl"])
        
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
        
        print("--- INSPECTING http://127.0.0.1:8000/#explorer ---")
        print("1. window.location.hash:", await eval_js("window.location.hash"))
        print("2. appState:", await eval_js("JSON.stringify(window.appState)"))
        print("3. view-home display:", await eval_js("getComputedStyle(document.getElementById('view-home')).display"))
        print("4. view-home class:", await eval_js("document.getElementById('view-home').className"))
        print("5. view-app display:", await eval_js("getComputedStyle(document.getElementById('view-app')).display"))
        print("6. view-app class:", await eval_js("document.getElementById('view-app').className"))
        print("7. screen-explorer display:", await eval_js("getComputedStyle(document.getElementById('screen-explorer')).display"))
        print("8. screen-explorer class:", await eval_js("document.getElementById('screen-explorer').className"))
        print("9. screen-explorer style attr:", await eval_js("document.getElementById('screen-explorer').getAttribute('style')"))
        print("10. deState:", await eval_js("JSON.stringify(window.deState)"))
        print("11. #screen-explorer clientHeight:", await eval_js("document.getElementById('screen-explorer').clientHeight"))
        print("12. document.body background:", await eval_js("getComputedStyle(document.body).background"))
        print("13. view-app background:", await eval_js("getComputedStyle(document.getElementById('view-app')).background"))
        print("14. #screen-explorer background:", await eval_js("getComputedStyle(document.getElementById('screen-explorer')).background"))
        print("15. page-top-bar display:", await eval_js("getComputedStyle(document.querySelector('.page-top-bar')).display"))
        print("16. current-screen-title text:", await eval_js("document.getElementById('current-screen-title')?.textContent"))
        print("17. hero-scroll-container display:", await eval_js("document.querySelector('.hero-scroll-container') ? getComputedStyle(document.querySelector('.hero-scroll-container')).display : 'NO HERO'"))
        
        # Take a screenshot to see what is visible right now!
        msg_id += 1
        await ws.send(json.dumps({"id": msg_id, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
        while True:
            resp = json.loads(await ws.recv())
            if resp.get("id") == msg_id:
                b64 = resp.get("result", {}).get("data")
                import base64
                with open("data/screenshots/inspect_explorer_view.png", "wb") as f:
                    f.write(base64.b64decode(b64))
                with open(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810\inspect_explorer_view.png", "wb") as f:
                    f.write(base64.b64decode(b64))
                print("Captured screenshot to inspect_explorer_view.png")
                break
                
        await ws.close()
    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(inspect())

