"""Background HTTP service to bridge frontend (index.html) with UrlValidationService.
Listens on 127.0.0.1:8765 to validate candidate URLs with real HTTP requests.
"""
import http.server
import socketserver
import threading
import json
import logging
from typing import Dict, Any
from urllib.parse import urlparse

from services.url_validation_service import UrlValidationService
from services.models import UrlStatus

logger = logging.getLogger(__name__)

PORT = 8765
_SERVER_INSTANCE = None
_SERVER_LOCK = threading.Lock()


class UrlValidationHTTPHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default server access logs to keep terminal clean
        pass

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "service": "UrlValidationService"}).encode('utf-8'))

    def do_POST(self):
        if self.path != '/validate_urls':
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode('utf-8'))
            expected_product = payload.get('expected_product', '')
            candidates = payload.get('candidates', []) # list of {"key": ..., "url": ...}

            results: Dict[str, Any] = {}
            for item in candidates:
                key = item.get('key')
                cand_url = item.get('url', '').strip()
                if not key or not cand_url:
                    continue

                offer = UrlValidationService.validate_product_url(
                    candidate_url=cand_url,
                    expected_product=expected_product,
                    attempt_recovery=True
                )

                results[key] = {
                    "candidate_url": cand_url,
                    "source_url": offer.source_url if offer.url_verified else "",
                    "final_url": offer.final_url,
                    "canonical_url": offer.canonical_url,
                    "url_verified": bool(offer.url_verified),
                    "url_status": offer.url_status.value,
                    "model": offer.model,
                    "match_confidence": offer.match_confidence
                }

            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "results": results}).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling /validate_urls: {e}")
            self.send_response(500)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server():
    global _SERVER_INSTANCE
    with _SERVER_LOCK:
        if _SERVER_INSTANCE is not None:
            return
        try:
            _SERVER_INSTANCE = ThreadingTCPServer(('127.0.0.1', PORT), UrlValidationHTTPHandler)
            thread = threading.Thread(target=_SERVER_INSTANCE.serve_forever, daemon=True, name="UrlValidationServer")
            thread.start()
            logger.info(f"UrlValidationHTTPHandler started on http://127.0.0.1:{PORT}")
        except OSError as e:
            # Address already in use (another process is running it)
            logger.info(f"Port {PORT} already bound: {e}")


def ensure_validation_server_running():
    start_server()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_server()
    print(f"Server running on port {PORT}. Press Ctrl+C to stop.")
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
