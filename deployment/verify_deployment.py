#!/usr/bin/env python3
"""
verify_deployment.py
--------------------
Automated end-to-end integration and smoke verification test suite
for the AI-Powered Mobile Urban Intelligence backend.

Usage:
    python verify_deployment.py [--url http://127.0.0.1:8000] [--insecure]
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


class DeploymentVerifier:
    def __init__(self, base_url: str, insecure: bool = False):
        self.base_url = base_url.rstrip('/')
        self.insecure = insecure
        self.passes = []
        self.failures = []

        # Configure TLS context: strict default verification; opt-in insecure bypass
        if self.insecure:
            self.ssl_ctx = ssl.create_default_context()
            self.ssl_ctx.check_hostname = False
            self.ssl_ctx.verify_mode = ssl.CERT_NONE
        else:
            self.ssl_ctx = ssl.create_default_context()

    def test_http_endpoint(
        self,
        name: str,
        path_or_url: str,
        method: str = 'GET',
        expected_status: int = 200,
        headers: dict = None,
        data: bytes = None,
        required: bool = True
    ):
        url = path_or_url if path_or_url.startswith('http') else f'{self.base_url}{path_or_url}'
        headers = headers or {}
        req = urllib.request.Request(url, headers=headers, data=data, method=method)
        t0 = time.perf_counter()

        try:
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=10) as resp:
                body = resp.read()
                lat = (time.perf_counter() - t0) * 1000
                status = resp.status
                content_type = resp.headers.get('content-type', '')
                content_range = resp.headers.get('content-range', '')

                if status == expected_status:
                    msg = f"[PASS] {name} ({method} {url}) -> HTTP {status} ({lat:.1f}ms)"
                    print(f"  {msg}")
                    self.passes.append({'name': name, 'url': url, 'status': status, 'latency_ms': lat})
                    return {
                        'status': status,
                        'body': body,
                        'content_type': content_type,
                        'content_range': content_range,
                        'headers': resp.headers
                    }
                else:
                    err_msg = f"[FAIL] {name} ({method} {url}) -> Unexpected HTTP {status} (Expected {expected_status})"
                    print(f"  {err_msg}")
                    if required:
                        self.failures.append({'name': name, 'url': url, 'error': err_msg})
                    return None
        except urllib.error.HTTPError as e:
            lat = (time.perf_counter() - t0) * 1000
            if e.code == expected_status:
                msg = f"[PASS] {name} ({method} {url}) -> Expected HTTP {e.code} ({lat:.1f}ms)"
                print(f"  {msg}")
                self.passes.append({'name': name, 'url': url, 'status': e.code, 'latency_ms': lat})
                return {'status': e.code, 'body': e.read(), 'headers': e.headers}
            else:
                err_msg = f"[FAIL] {name} ({method} {url}) -> HTTP Error {e.code} (Expected {expected_status})"
                print(f"  {err_msg}")
                if required:
                    self.failures.append({'name': name, 'url': url, 'error': err_msg})
                return None
        except Exception as exc:
            lat = (time.perf_counter() - t0) * 1000
            err_msg = f"[FAIL] {name} ({method} {url}) -> Exception: {exc} ({lat:.1f}ms)"
            print(f"  {err_msg}")
            if required:
                self.failures.append({'name': name, 'url': url, 'error': err_msg})
            return None

    async def test_websocket_camera(self, required: bool = True):
        import websockets
        ws_base = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
        uri = f"{ws_base}/api/ws/camera/BUS_021?mode=pothole&lat=28.6139&lng=77.2090"
        print(f"  Testing Camera WebSocket: {uri}")
        t0 = time.perf_counter()

        try:
            ws_ssl = self.ssl_ctx if uri.startswith('wss://') else None
            async with websockets.connect(uri, ssl=ws_ssl) as ws:
                frame_id = 106
                header = struct.pack('<I', frame_id)
                # Minimal 1x1 white JPEG binary payload
                min_jpeg = bytes.fromhex(
                    'ffd8ffe000104a46494600010101006000600000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffd9'
                )
                payload = header + min_jpeg

                await ws.send(payload)
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                lat = (time.perf_counter() - t0) * 1000
                data = json.loads(msg)
                status = data.get('status')
                resp_frame_id = data.get('frame_id')

                if status in ['no_detection', 'streaming', 'new', 'frame_rejected', 'frame_skipped']:
                    msg = f"[PASS] Camera WS Ingestion -> status={status} frame_id={resp_frame_id} ({lat:.1f}ms)"
                    print(f"  {msg}")
                    self.passes.append({'name': 'Camera WebSocket', 'url': uri, 'status': status, 'latency_ms': lat})
                    return True
                else:
                    err_msg = f"[FAIL] Camera WS Ingestion -> unexpected response status: {status}"
                    print(f"  {err_msg}")
                    if required:
                        self.failures.append({'name': 'Camera WebSocket', 'url': uri, 'error': err_msg})
                    return False
        except Exception as exc:
            lat = (time.perf_counter() - t0) * 1000
            err_msg = f"[FAIL] Camera WebSocket -> Exception: {exc} ({lat:.1f}ms)"
            print(f"  {err_msg}")
            if required:
                self.failures.append({'name': 'Camera WebSocket', 'url': uri, 'error': err_msg})
            return False

    def run_all(self) -> bool:
        print("==============================================================================")
        print(f" Running Automated Deployment Verification against: {self.base_url}")
        print(f" TLS Certificate Verification: {'INSECURE (Disabled)' if self.insecure else 'SECURE (Enabled)'}")
        print("==============================================================================\n")

        print("1. System Health & Docs:")
        self.test_http_endpoint("Root Endpoint", "/")
        self.test_http_endpoint("Health Check", "/health")
        self.test_http_endpoint("API Health Check", "/api/health")
        self.test_http_endpoint("Swagger Docs", "/docs")

        print("\n2. Telemetry & Analytics:")
        self.test_http_endpoint("List Buses", "/api/buses")
        self.test_http_endpoint("List Events", "/api/events?limit=5")
        self.test_http_endpoint("List Hotspots", "/api/hotspots")
        self.test_http_endpoint("Analytics Summary", "/api/analytics/summary")

        print("\n3. Video Feeds & HTTP Range Streaming:")
        self.test_http_endpoint("Sample Videos List", "/api/videos/samples")
        self.test_http_endpoint("Full Video Stream (200 OK)", "/api/videos/stream/cityRoad_potHoles.mp4")
        self.test_http_endpoint(
            "Range Video Stream (206 Partial)",
            "/api/videos/stream/cityRoad_potHoles.mp4",
            headers={"Range": "bytes=0-1023"},
            expected_status=206
        )

        print("\n4. CORS Preflight & Production Origin:")
        cors_resp = self.test_http_endpoint(
            "CORS Preflight (Vercel Origin)",
            "/api/events",
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
        try:
            asyncio.run(self.test_websocket_camera())
        except Exception as exc:
            self.failures.append({'name': 'Camera WebSocket Async Runner', 'url': self.base_url, 'error': str(exc)})

        print("\n==============================================================================")
        print(" Verification Summary:")
        print(f" Passed: {len(self.passes)} / {len(self.passes) + len(self.failures)}")
        print(f" Failed: {len(self.failures)} / {len(self.passes) + len(self.failures)}")

        if self.failures:
            print("\n❌ FAILED TESTS:")
            for f in self.failures:
                print(f"  - {f['name']}: {f.get('error', 'Failed')}")
            print("\nVERDICT: FAIL — Fix required before production use.")
            print("==============================================================================")
            return False
        else:
            print("\n✅ ALL TESTS PASSED SUCCESSFULLY!")
            print("VERDICT: PASS — Backend is ready for live integration.")
            print("==============================================================================")
            return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Automated Deployment Smoke Test Suite")
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='Base URL to test (default: http://127.0.0.1:8000)')
    parser.add_argument('--insecure', action='store_true', help='Disable TLS certificate verification (opt-in for self-signed or local dev certs)')
    args = parser.parse_args()

    verifier = DeploymentVerifier(base_url=args.url, insecure=args.insecure)
    success = verifier.run_all()
    sys.exit(0 if success else 1)

