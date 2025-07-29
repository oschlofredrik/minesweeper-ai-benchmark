"""Status endpoint for SDK evaluations."""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get evaluation status."""
        try:
            # Extract evaluation ID from path
            path_parts = self.path.strip('/').split('/')
            if len(path_parts) < 3:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid path"}).encode())
                return
            
            evaluation_id = path_parts[2]  # /api/evaluation/{id}/status
            
            # For now, return a mock response
            # In a real implementation, this would query the database
            response = {
                "evaluation_id": evaluation_id,
                "status": "completed",
                "progress": 1.0,
                "games_total": 1,
                "games_completed": 1,
                "message": "This is a simplified status endpoint",
                "games": [{
                    "id": "mock-game-1",
                    "status": "completed",
                    "won": True,
                    "moves": 42,
                    "duration": 15.3
                }]
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": f"Error in evaluation_status: {str(e)}",
                "type": type(e).__name__
            }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()