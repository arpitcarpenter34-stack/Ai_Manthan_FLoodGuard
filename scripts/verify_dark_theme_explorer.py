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
CDP_PORT = 9488
TARGET_URL = "http://127.0.0.1:8000/#explorer"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_dark_explorer_audit"
SCREENSHOT_DIR = Path(r"E:\ai-manthan\hydro_guard_indore\data\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Arpit\.gemini\antigravity\brain\4b346643-0a90-4b44-a46e-95be0cc73810")

async def run_audit():
    print("=" * 80)
    print(" HYDRO-GUARD AI - TASK 4.1-THEME: DARK GLASSMORPHISM & HEATMAP AUDIT")
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
        "--window-size=1500,980",
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
            print("[FAIL] Could not connect to Chrome CDP.")
            return

        ws = await websockets.connect(pages[0]["webSocketDebuggerUrl"], max_size=100 * 1024 * 1024)

        msg_id = 0
        pending = {}
        console_logs = []
        console_errors = []

        async def reader():
            try:
                async for raw in ws:
                    data = json.loads(raw)
                    mid = data.get("id")
                    if mid is not None and mid in pending:
                        fut = pending.pop(mid)
                        if not fut.done():
                            fut.set_result(data.get("result", {}))
                    else:
                        method = data.get("method")
                        params = data.get("params", {})
                        if method == "Runtime.consoleAPICalled":
                            msg_type = params.get("type")
                            args = [str(a.get("value", a.get("description", ""))) for a in params.get("args", [])]
                            text = " ".join(args)
                            console_logs.append(f"[{msg_type}] {text}")
                            if msg_type in ["error", "assert"]:
                                console_errors.append(text)
                        elif method == "Runtime.exceptionThrown":
                            details = params.get("exceptionDetails", {})
                            text = details.get("text", "") + ": " + str(details.get("exception", {}).get("description", ""))
                            console_errors.append(text)
            except Exception:
                pass

        reader_task = asyncio.create_task(reader())

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            cur_id = msg_id
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            pending[cur_id] = fut
            await ws.send(json.dumps({"id": cur_id, "method": method, "params": params or {}}))
            return await asyncio.wait_for(fut, timeout=15)

        async def eval_js(expr):
            res = await send_cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            return res.get("result", {}).get("value")

        async def snap(filename):
            res = await send_cmd("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(res.get("data", ""))
            out_path = SCREENSHOT_DIR / filename
            out_path.write_bytes(data)
            # Copy to artifact dir
            art_path = ARTIFACT_DIR / filename
            art_path.write_bytes(data)
            print(f"  [SCREENSHOT] Saved: {filename} ({len(data):,} bytes)")

        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("Network.enable")
        # Clear cache to guarantee fresh CSS/JS
        await send_cmd("Network.clearBrowserCache")

        print(f"\n[STEP 1] Navigating to {TARGET_URL}...")
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(2.5)

        # Audit Screen Visibility & Theme
        print("\n[STEP 2] Auditing Theme & Screen Elements...")
        screen_visible = await eval_js("""
            (() => {
                const s = document.getElementById("screen-explorer");
                return !!(s && s.classList.contains("active") && s.offsetParent !== null && getComputedStyle(s).display !== "none");
            })()
        """)
        print(f"  -> screen-explorer visible: {screen_visible}")

        white_theme_active = await eval_js("""
            (() => {
                const v = document.getElementById("view-app");
                return v ? v.classList.contains("white-theme") : null;
            })()
        """)
        print(f"  -> view-app has white-theme class: {white_theme_active} (Expected: False)")

        theme_styles = await eval_js("""
            (() => {
                const vApp = document.getElementById("view-app");
                const header = document.querySelector(".app-header");
                const sidebar = document.querySelector(".app-sidebar");
                const firstCard = document.querySelector(".wt-card");
                const summaryCard = document.querySelector(".wt-summary-card");
                const pageTitle = document.querySelector(".wt-title");
                return {
                    vAppBg: vApp ? getComputedStyle(vApp).backgroundColor : null,
                    headerBg: header ? getComputedStyle(header).backgroundColor : null,
                    sidebarBg: sidebar ? getComputedStyle(sidebar).backgroundColor : null,
                    firstCardBg: firstCard ? getComputedStyle(firstCard).backgroundColor : null,
                    summaryCardBg: summaryCard ? getComputedStyle(summaryCard).backgroundColor : null,
                    pageTitleCol: pageTitle ? getComputedStyle(pageTitle).color : null
                };
            })()
        """)
        print(f"  -> Header bg: {theme_styles.get('headerBg')}")
        print(f"  -> Sidebar bg: {theme_styles.get('sidebarBg')}")
        print(f"  -> Summary Card bg: {theme_styles.get('summaryCardBg')}")
        print(f"  -> Content Card bg: {theme_styles.get('firstCardBg')}")
        print(f"  -> Page Title Color: {theme_styles.get('pageTitleCol')}")

        # Audit Feature Correlation Heatmap
        print("\n[STEP 3] Auditing Feature Correlation Heatmap...")
        heatmap_audit = await eval_js("""
            (() => {
                const container = document.getElementById("de-corr-matrix-container");
                if (!container) return { error: "Container not found" };

                const headerRow = container.querySelector(".wt-corr-header-row");
                const topLabels = Array.from(container.querySelectorAll(".wt-corr-top-lbl")).map(el => el.textContent.trim());
                const leftLabels = Array.from(container.querySelectorAll(".wt-corr-lbl")).map(el => el.textContent.trim());
                const cells = Array.from(container.querySelectorAll(".wt-corr-cell")).map(el => ({
                    val: el.textContent.trim(),
                    bg: getComputedStyle(el).backgroundColor,
                    col: getComputedStyle(el).color
                }));

                const rows = container.querySelectorAll(".wt-corr-row");

                return {
                    hasHeaderRow: !!headerRow,
                    topLabelCount: topLabels.length,
                    topLabels: topLabels,
                    leftLabelCount: leftLabels.length,
                    leftLabels: leftLabels,
                    rowCount: rows.length,
                    totalCells: cells.length,
                    cellSample: cells.slice(0, 6),
                    firstCellColor: cells[0] ? cells[0].col : null,
                    firstCellBg: cells[0] ? cells[0].bg : null
                };
            })()
        """)
        print(f"  -> Heatmap has Top Header Row: {heatmap_audit.get('hasHeaderRow')}")
        print(f"  -> Top X-axis labels ({heatmap_audit.get('topLabelCount')}): {heatmap_audit.get('topLabels')}")
        print(f"  -> Left Y-axis labels ({heatmap_audit.get('leftLabelCount')}): {heatmap_audit.get('leftLabels')}")
        print(f"  -> Total cells: {heatmap_audit.get('totalCells')}")
        print(f"  -> Sample cell values: {[c.get('val') for c in heatmap_audit.get('cellSample', [])]}")
        print(f"  -> Sample cell text color: {heatmap_audit.get('firstCellColor')}")
        print(f"  -> Sample cell background: {heatmap_audit.get('firstCellBg')}")

        # Capture Dark Theme Overview Screenshot
        await snap("task41_dark_theme_explorer_overview.png")

        # Test switching to Spearman correlation method
        print("\n[STEP 4] Testing Correlation Method Switch to Spearman...")
        await eval_js("""
            (() => {
                const sel = document.getElementById("de-corr-method-select");
                if (sel) {
                    sel.value = "spearman";
                    onDeCorrMethodChange("spearman");
                }
            })()
        """)
        await asyncio.sleep(0.5)

        spearman_cells = await eval_js("""
            (() => {
                const cells = Array.from(document.querySelectorAll("#de-corr-matrix-container .wt-corr-cell")).map(el => el.textContent.trim());
                return cells.slice(0, 6);
            })()
        """)
        print(f"  -> Spearman Row 1 cells: {spearman_cells}")
        await snap("task41_dark_theme_explorer_spearman.png")

        # Test other sub-tabs to ensure dark theme applies everywhere
        tabs_to_test = [
            ("features", "Feature Engineering Lab", "task41_dark_theme_tab2_features.png"),
            ("relationships", "Hydrological Relationships", "task41_dark_theme_tab3_relationships.png"),
            ("fingerprint", "Flood Fingerprint", "task41_dark_theme_tab4_fingerprint.png"),
            ("spatial", "Spatio-Temporal Analysis", "task41_dark_theme_tab5_spatial.png"),
            ("model", "Model & Prediction Insights", "task41_dark_theme_tab6_model.png"),
        ]

        for tab_id, tab_name, snap_file in tabs_to_test:
            print(f"\n[STEP 5] Testing Sub-tab: {tab_name} ({tab_id})...")
            await eval_js(f"switchDeTab('{tab_id}')")
            await asyncio.sleep(0.5)
            await snap(snap_file)

        # Switch back to Overview
        await eval_js("switchDeTab('overview')")
        await asyncio.sleep(0.3)

        # Test switching datasets
        print("\n[STEP 6] Testing Dataset Switching to CAMELS...")
        await eval_js("onDeDatasetPillClick('camels_hourly')")
        await asyncio.sleep(1.0)
        camels_top_labels = await eval_js("""
            Array.from(document.querySelectorAll("#de-corr-matrix-container .wt-corr-top-lbl")).map(el => el.textContent.trim())
        """)
        print(f"  -> CAMELS Top X-axis labels: {camels_top_labels}")
        await snap("task41_dark_theme_camels.png")

        # Switch back to Blue Heart
        await eval_js("onDeDatasetPillClick('blue_heart')")
        await asyncio.sleep(0.8)

        # Console Errors Audit
        print(f"\n[STEP 7] Console Errors Audit...")
        print(f"  -> Total Console Errors: {len(console_errors)}")
        for err in console_errors:
            print(f"     [ERROR] {err}")

        # Verification Verdict
        assert screen_visible, "Screen explorer must be visible"
        assert white_theme_active is False, "White theme must NOT be active on view-app"
        assert heatmap_audit.get("hasHeaderRow") is True, "Heatmap must have top header row"
        assert heatmap_audit.get("topLabelCount") == 6, f"Expected 6 top labels, got {heatmap_audit.get('topLabelCount')}"
        assert heatmap_audit.get("leftLabelCount") == 6, f"Expected 6 left labels, got {heatmap_audit.get('leftLabelCount')}"
        assert heatmap_audit.get("totalCells") == 36, f"Expected 36 cells (6x6), got {heatmap_audit.get('totalCells')}"
        assert len(console_errors) == 0, f"Expected 0 console errors, got {len(console_errors)}"

        print("\n" + "=" * 80)
        print("ALL ACCEPTANCE TESTS PASSED WITH 100% SUCCESS!")
        print("=" * 80)

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=2)
        except Exception:
            chrome_proc.kill()

if __name__ == "__main__":
    asyncio.run(run_audit())

