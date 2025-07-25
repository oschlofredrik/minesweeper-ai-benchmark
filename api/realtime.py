"""Real-time updates using Server-Sent Events (SSE) as a WebSocket alternative for Vercel."""
from http.server import BaseHTTPRequestHandler
import json
import time
from . import supabase_db as db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path.startswith('/api/sessions/') and path.endswith('/stream'):
            session_id = path.split('/')[-2]
            self.handle_session_stream(session_id)
        else:
            self.send_error(404)
    
    def handle_session_stream(self, session_id):
        """Stream session updates using SSE."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Send initial session state
        session = db.get_session(session_id)
        if session:
            self.send_sse_event('session_update', session)
        
        # Poll for updates (simplified for Vercel's timeout constraints)
        # In production, this would use Supabase Realtime
        last_update = time.time()
        timeout = 25  # Vercel has 30s timeout, leave buffer
        
        while time.time() - last_update < timeout:
            # Check for session updates
            updated_session = db.get_session(session_id)
            if updated_session and updated_session != session:
                self.send_sse_event('session_update', updated_session)
                session = updated_session
            
            # Check for game updates
            if session and session.get('status') == 'in_progress':
                games = db.list_games()
                session_games = [g for g in games if g.get('session_id') == session_id]
                if session_games:
                    self.send_sse_event('games_update', {
                        'session_id': session_id,
                        'games': session_games
                    })
            
            time.sleep(1)  # Poll every second
        
        # Send keepalive before timeout
        self.send_sse_event('keepalive', {'timestamp': time.time()})
    
    def send_sse_event(self, event_type, data):
        """Send an SSE event."""
        message = f"event: {event_type}\n"
        message += f"data: {json.dumps(data, default=str)}\n\n"
        self.wfile.write(message.encode())
        self.wfile.flush()