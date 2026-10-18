"""
Local Web Server for Project Atlas Portal.
Allows testing the CodeIgniter 3 Portal UI locally on Windows without installing PHP!
Serves the chat portal on http://localhost:8080 and proxies requests to the FastAPI backend.
"""

import os
import re
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

PORT = 8080
API_URL = os.getenv("ATLAS_API_URL", "http://127.0.0.1:8000")
VIEW_PATH = os.path.join(os.path.dirname(__file__), "application", "views", "chat_view.php")

class PortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        client_id = query.get("client_id", ["C-01"])[0]

        with open(VIEW_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        # Simple template evaluation for local preview
        html = template
        html = html.replace("<?php echo ($current_client === 'C-01' ? 'selected' : ''); ?>", "selected" if client_id == "C-01" else "")
        html = html.replace("<?php echo ($current_client === 'C-02' ? 'selected' : ''); ?>", "selected" if client_id == "C-02" else "")
        html = html.replace("<?php echo ($current_client === 'C-01' ? 'Northwind Utilities (C-01)' : 'Blue Delta Infra (C-02)'); ?>", 
                            "Northwind Utilities (C-01)" if client_id == "C-01" else "Blue Delta Infra (C-02)")
        html = html.replace("<?php echo $current_client; ?>", client_id)
        html = html.replace("<?php echo site_url('chat/send'); ?>", "/chat/send")
        html = html.replace("<?php echo $this->security->get_csrf_token_name(); ?>", "csrf_test")
        html = html.replace("<?php echo $this->security->get_csrf_hash(); ?>", "dummy_token_123")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        if self.path == "/chat/send":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = parse_qs(body)
            client_id = data.get("client_id", ["C-01"])[0]
            message = data.get("message", [""])[0]

            # Forward to FastAPI backend
            try:
                res = requests.post(
                    f"{API_URL}/chat",
                    json={"client_id": client_id, "message": message},
                    headers={"X-API-Key": "atlas_secret_key_12345"},
                    timeout=30
                )
                res_data = res.json()
                res_data["answer_escaped"] = res_data.get("answer", "").replace("\n", "<br>")
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(requests.models.complexjson.dumps(res_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                err_payload = {
                    "answer": f"Connection Error: Unable to reach FastAPI backend on {API_URL}. Ensure it is running.",
                    "citations": [],
                    "confidence": 0.0,
                    "conflicts": [],
                    "derived_values": [],
                    "escalated": True
                }
                self.wfile.write(requests.models.complexjson.dumps(err_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PortalHandler)
    print("=" * 70)
    print(f"Project Atlas Web Portal running on: http://localhost:{PORT}")
    print(f"Proxying queries to FastAPI backend at: {API_URL}")
    print("Press CTRL+C to stop.")
    print("=" * 70)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping portal server...")
        server.server_close()
