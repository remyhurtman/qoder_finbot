from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "message": "Service is up and running",
            "timestamp": "2025-08-31"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return