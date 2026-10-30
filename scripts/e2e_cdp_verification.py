"""
Robust Chrome DevTools Protocol (CDP) client over WebSocket.
Single reader loop with Future dispatch by message ID.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
import requests
import websockets

sys.stdout.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9333
TARGET_URL = "http://127.0.0.1:8000/#map"
USER_DATA_DIR = r"C:\Users\Arpit\AppData\Local\Temp\chrome_cdp_verify"


async def run_cdp():
    print(f"Launching Chrome on port {CDP_PORT}...")
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
        # Wait for Chrome to bind CDP port
        for _ in range(25):
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
        print(f"Connected to Chrome page WebSocket: {page_ws_url}")

        ws = await websockets.connect(page_ws_url)
        msg_id = 0
        pending_futures = {}

        network_requests = {}
        console_messages = []
        network_errors = []

        async def reader_loop():
            try:
                async for raw_msg in ws:
                    msg = json.loads(raw_msg)
                    mid = msg.get("id")
                    if mid is not None and mid in pending_futures:
                        fut = pending_futures.pop(mid)
                        if not fut.done():
                            fut.set_result(msg.get("result", {}))
                    else:
                        method = msg.get("method")
                        params = msg.get("params", {})
                        if method == "Network.requestWillBeSent":
                            req_id = params.get("requestId")
                            network_requests[req_id] = {
                                "url": params.get("request", {}).get("url"),
                                "method": params.get("request", {}).get("method"),
                                "status": None
                            }
                        elif method == "Network.responseReceived":
                            req_id = params.get("requestId")
                            if req_id in network_requests:
                                network_requests[req_id]["status"] = params.get("response", {}).get("status")
                                network_requests[req_id]["mimeType"] = params.get("response", {}).get("mimeType")
                        elif method == "Network.loadingFailed":
                            req_id = params.get("requestId")
                            url = network_requests.get(req_id, {}).get("url", "unknown")
                            network_errors.append({
                                "url": url,
                                "errorText": params.get("errorText")
                            })
                        elif method == "Console.messageAdded":
                            cmsg = params.get("message", {})
                            console_messages.append({
                                "level": cmsg.get("level"),
                                "text": cmsg.get("text")
                            })
                        elif method == "Runtime.consoleAPICalled":
                            args = [str(a.get("value", a.get("description", ""))) for a in params.get("args", [])]
                            console_messages.append({
                                "level": params.get("type"),
                                "text": " ".join(args)
                            })
            except websockets.exceptions.ConnectionClosed:
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
            return await asyncio.wait_for(fut, timeout=10.0)

        # Enable Network, Console, Page, Runtime
        await send_cmd("Network.enable")
        await send_cmd("Console.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("Page.enable")

        # -------------------------------------------------------------
        # CHECK 1: Navigate to Map & Verify Topology API & OSM Features
        # -------------------------------------------------------------
        print(f"\n=======================================================")
        print(f"  CHECK 1: Opening {TARGET_URL} & Verifying Waterways")
        print(f"=======================================================")
        await send_cmd("Page.navigate", {"url": TARGET_URL})
        await asyncio.sleep(4.0)  # Wait for map tiles, fetch, and rendering

        res = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const state = (typeof appState !== 'undefined') ? appState : (window.appState || {});
                const mapReady = !!state.leafletMap;
                const waterwayLayerReady = !!state.waterwayLayer;
                let layersCount = 0;
                let featuresSummary = [];

                if (waterwayLayerReady) {
                    const layers = state.waterwayLayer.getLayers();
                    layersCount = layers.length;
                    featuresSummary = layers.map((layer, idx) => {
                        const p = (layer.feature && layer.feature.properties) || {};
                        return {
                            osm_id: p.osm_id,
                            name: p.english_name || p.name,
                            system: p.river_system,
                            waterway_type: p.waterway_type,
                            length_km: p.length_km,
                            node_count: p.node_count,
                            is_real_gis_data: p.is_real_gis_data,
                            has_popup: !!layer.getPopup()
                        };
                    });
                }

                const markersCount = state.mapMarkers ? state.mapMarkers.length : 0;
                const hasPolyline = !!state.mapPolyline;

                return {
                    mapReady,
                    waterwayLayerReady,
                    layersCount,
                    markersCount,
                    hasPolyline,
                    featuresSummary
                };
            })()
            """,
            "returnByValue": True
        })

        chk1 = res.get("result", {}).get("value", {})
        print(f"Leaflet Map Instantiated: {chk1.get('mapReady')}")
        print(f"Waterway Layer Instantiated: {chk1.get('waterwayLayerReady')}")
        print(f"Rendered Waterway Features Count: {chk1.get('layersCount')} (Expected: 7)")
        print(f"Municipal Monitoring Markers Count: {chk1.get('markersCount')} (Expected: 7)")
        print(f"Schematic Flow Polyline Ready: {chk1.get('hasPolyline')}")

        features = chk1.get("featuresSummary", [])
        for idx, f in enumerate(features):
            print(f"  [{idx+1}] {f['name']} ({f['system']}) | Type: {f['waterway_type']} | Nodes: {f['node_count']} | Length: {f['length_km']} km | Real GIS: {f['is_real_gis_data']} | Popup: {f['has_popup']}")

        # -------------------------------------------------------------
        # CHECK 2: Browser Console and Network Errors
        # -------------------------------------------------------------
        print(f"\n=======================================================")
        print(f"  CHECK 2: Browser Console and Network Error Inspection")
        print(f"=======================================================")
        topo_reqs = [r for r in network_requests.values() if r.get("url") and "/api/v1/flood/topology" in r["url"]]
        print(f"GET /api/v1/flood/topology requests observed: {len(topo_reqs)}")
        for tr in topo_reqs:
            print(f"  * URL: {tr['url']} | Status: {tr['status']} | MIME: {tr.get('mimeType')}")

        tile_reqs = [r for r in network_requests.values() if r.get("url") and "tile.openstreetmap.org" in r["url"]]
        print(f"OpenStreetMap tile requests observed: {len(tile_reqs)}")
        failed_tiles = [r for r in tile_reqs if r.get("status") not in [200, 304, None]]
        print(f"Failed OSM tiles: {len(failed_tiles)}")

        print(f"Network loading failures: {len(network_errors)}")
        for ne in network_errors:
            print(f"  * Failed URL: {ne['url']} -> {ne['errorText']}")

        err_console = [c for c in console_messages if c["level"] in ["error", "assert"]]
        print(f"Browser console error count: {len(err_console)}")
        for ec in err_console:
            print(f"  * Console Error: {ec['text']}")

        # -------------------------------------------------------------
        # CHECK 3: Confirm OSM Attribution and Feature Popups
        # -------------------------------------------------------------
        print(f"\n=======================================================")
        print(f"  CHECK 3: OSM Attribution and Feature Popups")
        print(f"=======================================================")
        res_attr = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const attrEl = document.querySelector('.leaflet-control-attribution');
                const legendEl = document.querySelector('.gis-map-legend');
                const statCard = document.getElementById('map-stat-waterway-len');

                let samplePopup = "";
                let samplePopupEnglish = "";
                if (window.appState && window.appState.waterwayLayer) {
                    const layers = window.appState.waterwayLayer.getLayers();
                    if (layers.length > 0 && layers[0].getPopup()) {
                        samplePopup = layers[0].getPopup().getContent();
                    }
                }

                let polylinePopup = "";
                if (window.appState && window.appState.mapPolyline && window.appState.mapPolyline.getPopup()) {
                    polylinePopup = window.appState.mapPolyline.getPopup().getContent();
                }

                return {
                    attributionText: attrEl ? attrEl.innerText.trim() : null,
                    hasLegend: !!legendEl,
                    legendText: legendEl ? legendEl.innerText.trim() : null,
                    statCardText: statCard ? statCard.innerText.trim() : null,
                    samplePopup,
                    polylinePopup
                };
            })()
            """,
            "returnByValue": True
        })

        chk3 = res_attr.get("result", {}).get("value", {})
        print(f"Map Attribution: \"{chk3.get('attributionText')}\"")
        print(f"Waterway Stat Card: \"{chk3.get('statCardText')}\"")
        print(f"Interactive GIS Legend Present: {chk3.get('hasLegend')}")
        if chk3.get("legendText"):
            print("Legend Text Preview:\n" + "\n".join("  " + line for line in chk3["legendText"].split("\n")[:6]))
        print(f"\nRiver Feature Popup HTML Snippet:\n  {chk3.get('samplePopup')[:240]}...")
        print(f"\nSchematic Flow Polyline Popup Snippet:\n  {chk3.get('polylinePopup')[:180]}...")

        # -------------------------------------------------------------
        # CHECK 4: Reload Map & Confirm Resilience
        # -------------------------------------------------------------
        print(f"\n=======================================================")
        print(f"  CHECK 4: Page Reload & State Resilience")
        print(f"=======================================================")
        await send_cmd("Page.reload")
        await asyncio.sleep(4.0)

        res_reload = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const mapReady = !!window.appState && !!window.appState.leafletMap;
                const layers = (window.appState && window.appState.waterwayLayer) ? window.appState.waterwayLayer.getLayers() : [];
                const markers = (window.appState && window.appState.mapMarkers) ? window.appState.mapMarkers.length : 0;
                const statCard = document.getElementById('map-stat-waterway-len');
                return {
                    mapReady,
                    layerCountAfterReload: layers.length,
                    markersCountAfterReload: markers,
                    statCardText: statCard ? statCard.innerText.trim() : null
                };
            })()
            """,
            "returnByValue": True
        })

        chk4 = res_reload.get("result", {}).get("value", {})
        print(f"Map Re-initialized after reload: {chk4.get('mapReady')}")
        print(f"Waterway Layers count after reload: {chk4.get('layerCountAfterReload')} (Expected: 7)")
        print(f"Monitoring Markers count after reload: {chk4.get('markersCountAfterReload')} (Expected: 7)")
        print(f"Stat Card after reload: {chk4.get('statCardText')}")

        # -------------------------------------------------------------
        # CHECK 5: Distinguishing Synthetic vs Real GIS Data
        # -------------------------------------------------------------
        print(f"\n=======================================================")
        print(f"  CHECK 5: Synthetic vs Real GIS Data Separation")
        print(f"=======================================================")
        res_dist = await send_cmd("Runtime.evaluate", {
            "expression": """
            (() => {
                const realFeatures = window.appState.waterwayLayer ? window.appState.waterwayLayer.getLayers().map(l => ({
                    id: l.feature.id,
                    name: l.feature.properties.english_name,
                    is_real_gis_data: l.feature.properties.is_real_gis_data,
                    provenance: l.feature.properties.provenance,
                    layer_type: l.feature.properties.layer_type
                })) : [];

                const schematicEdge = window.appState.mapPolyline ? {
                    dashArray: window.appState.mapPolyline.options.dashArray,
                    color: window.appState.mapPolyline.options.color
                } : null;

                return {
                    realFeatures,
                    schematicEdge
                };
            })()
            """,
            "returnByValue": True
        })

        chk5 = res_dist.get("result", {}).get("value", {})
        print("Real GIS Waterways Layer (OpenStreetMap Verified):")
        for rf in chk5.get("realFeatures", []):
            print(f"  * {rf['name']} ({rf['id']}) -> is_real_gis_data: {rf['is_real_gis_data']} | provenance: {rf['provenance']}")

        se = chk5.get("schematicEdge", {})
        print(f"\nSchematic Edge Layer: Color={se.get('color')} | DashArray={se.get('dashArray')} (Dashed line distinguishing it from continuous real river vectors)")

        reader_task.cancel()

    finally:
        if ws:
            await ws.close()
        chrome_proc.terminate()
        chrome_proc.wait()
        print("\nChrome instance terminated cleanly.")


if __name__ == "__main__":
    asyncio.run(run_cdp())
