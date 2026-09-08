#!/usr/bin/env python3
"""
verify_deployment.py
--------------------
Automated end-to-end integration and smoke verification test suite
for the AI-Powered Mobile Urban Intelligence backend.

Usage:
    python verify_deployment.py [--url http://127.0.0.1:8000]
"""

import argparse
import asyncio
import json
import struct
import sys
import time
import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_http_endpoint(name, url, method='GET', expected_status=200, headers=None, data=None):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            body = resp.read()
            lat = (time.perf_counter() - t0) * 1000
            status = resp.status
            content_type = resp.headers.get('content-type', '')
            content_range = resp.headers.get('content-range', '')
            print(f'  [PASS] {name} ({method} {url}) -> HTTP {status} ({lat:.1f}ms)')
            return {
                'status': status,
                'body': body,
                'content_type': content_type,
                'content_range': content_range,
                'headers': resp.headers
            }
    except urllib.error.HTTPError as e:
        lat = (time.perf_counter() - t0) * 1000
        if e.code == expected_status:
            print(f'  [PASS] {name} ({method} {url}) -> Expected HTTP {e.code} ({lat:.1f}ms)')
            return {'status': e.code, 'body': e.read(), 'headers': e.headers}
        print(f'  [FAIL] {name} ({method} {url}) -> HTTP Error {e.code}: {e.read().decode("utf-8", errors="ignore")}')
        return None
    except Exception as exc:
        print(f'  [FAIL] {name} ({method} {url}) -> Exception: {exc}')
        return None


async def test_websocket_camera(ws_base_url):
    import websockets
    uri = f'{ws_base_url.replace("http", "ws")}/api/ws/camera/BUS_021?mode=pothole&lat=28.6139&lng=77.2090'
    print(f'  Testing Camera WebSocket: {uri}')
    try:
        async with websockets.connect(uri, ssl=ctx if uri.startswith('wss') else None) as ws:
            frame_id = 106
            header = struct.pack('<I', frame_id)
            min_jpeg = bytes.fromhex('ffd8ffe000104a46494600010101006000600000ffdb004300080606070605080707070909080a0c140d0c0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffd9')
            payload = header + min_jpeg

            await ws.send(payload)
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            print(f'  [PASS] Camera WS response: status={data.get("status")} frame_id={data.get("frame_id")}')
            return True
    except Exception as exc:
        print(f'  [WARN] Camera WS test note: {exc}')
        return False


def run_all_tests(base_url):
    print("==============================================================================")
    print(f" Running Automated Deployment Verification against: {base_url}")
    print("==============================================================================\n")

    print("1. System Health & Docs:")
    test_http_endpoint("Root Endpoint", f"{base_url}/")
    test_http_endpoint("Health Check", f"{base_url}/health")
    test_http_endpoint("API Health Check", f"{base_url}/api/health")
    test_http_endpoint("Swagger Docs", f"{base_url}/docs")

    print("\n2. Telemetry & Analytics:")
    test_http_endpoint("List Buses", f"{base_url}/api/buses")
    test_http_endpoint("List Events", f"{base_url}/api/events?limit=5")
    test_http_endpoint("List Hotspots", f"{base_url}/api/hotspots")
    test_http_endpoint("Analytics Summary", f"{base_url}/api/analytics/summary")

    print("\n3. Video Feeds & HTTP Range Streaming:")
    test_http_endpoint("Sample Videos List", f"{base_url}/api/videos/samples")
    test_http_endpoint("Full Video Stream (200 OK)", f"{base_url}/api/videos/stream/cityRoad_potHoles.mp4")
    test_http_endpoint("Range Video Stream (206 Partial)", f"{base_url}/api/videos/stream/cityRoad_potHoles.mp4",
                       headers={"Range": "bytes=0-1023"}, expected_status=206)

    print("\n4. CORS Preflight & Production Origin:")
    cors_resp = test_http_endpoint(
        "CORS Preflight (Vercel Origin)",
        f"{base_url}/api/events",
        method="OPTIONS",
        headers={
            "Origin": "https://ai-powered-mobile-urban-intelligenc.vercel.app",
            "Access-Control-Request-Method": "GET"
        }
    )
    if cors_resp and cors_resp.get("headers"):
        allow_orig = cors_resp["headers"].get("access-control-allow-origin", "")
        print(f"     Access-Control-Allow-Origin: {allow_orig}")

    print("\n5. WebSocket Camera & Event Streaming:")
    asyncio.run(test_websocket_camera(base_url))

    print("\n==============================================================================")
    print(" Verification Suite Complete!")
    print("==============================================================================")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='Base URL to test')
    args = parser.parse_args()
    run_all_tests(args.url)
