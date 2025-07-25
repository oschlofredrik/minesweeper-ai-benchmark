"""Server-Sent Events endpoint for real-time updates."""
from http.server import BaseHTTPRequestHandler
import json
import time
from . import supabase_db as db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/events':
            # Set up SSE headers
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Send initial connection event
            self.send_event('connected', {'status': 'connected'})
            
            # In a real implementation, this would stream updates
            # For Vercel, we'll just send a few demo events
            for i in range(3):
                time.sleep(1)
                self.send_event('update', {
                    'type': 'game_update',
                    'data': {
                        'game_id': f'demo-{i}',
                        'status': 'in_progress',
                        'move': i + 1
                    }
                })
            
            # Send done event
            self.send_event('done', {'status': 'complete'})
            
        else:
            self.send_error(404)
    
    def send_event(self, event_type: str, data: dict):
        """Send an SSE event."""
        event = f"event: {event_type}\n"
        event += f"data: {json.dumps(data)}\n\n"
        self.wfile.write(event.encode())
        self.wfile.flush()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()