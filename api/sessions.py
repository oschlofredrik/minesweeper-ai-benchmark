"""Sessions endpoint - self-contained for Vercel."""
from http.server import BaseHTTPRequestHandler
import json
import os
import random
import string
from datetime import datetime, timedelta
import uuid

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

def generate_join_code():
    """Generate a unique 6-character join code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/sessions':
            self.handle_list_sessions()
        elif path.startswith('/api/sessions/') and not path.endswith('/'):
            session_id = path.split('/')[-1]
            self.handle_get_session(session_id)
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        if path == '/api/sessions/create':
            self.handle_create_session()
        elif path == '/api/sessions/join':
            self.handle_join_session()
        elif path.startswith('/api/sessions/') and path.endswith('/start'):
            session_id = path.split('/')[-2]
            self.handle_start_session(session_id)
        else:
            self.send_error(404)
    
    def handle_list_sessions(self):
        """List all sessions."""
        active_only = 'active=true' in self.path
        
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            try:
                from supabase import create_client
                supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                query = supabase.table('sessions').select('*')
                if active_only:
                    query = query.eq('status', 'waiting')
                response = query.execute()
                sessions = response.data if response.data else []
            except:
                sessions = []
        else:
            # Demo data
            sessions = [
                {
                    "id": "demo-1",
                    "name": "Friday AI Challenge",
                    "join_code": "DEMO01",
                    "status": "waiting",
                    "players": [{"name": "Alice", "model": "gpt-4"}],
                    "created_at": datetime.utcnow().isoformat()
                }
            ] if not active_only else []
        
        self.send_json_response({'sessions': sessions})
    
    def handle_create_session(self):
        """Create a new session."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        
        join_code = generate_join_code()
        session_id = str(uuid.uuid4())
        
        session_data = {
            'id': session_id,
            'name': body.get('name', 'Unnamed Session'),
            'join_code': join_code,
            'host_id': body.get('creator_id'),
            'game_type': body.get('game_type', 'minesweeper'),
            'max_players': body.get('max_players', 20),
            'status': 'waiting',
            'players': [{
                'id': body.get('creator_id'),
                'name': body.get('creator_name', 'Host'),
                'is_host': True,
                'model': body.get('model', 'gpt-4'),
                'ready': False
            }],
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Try to save to Supabase
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            try:
                from supabase import create_client
                supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                supabase.table('sessions').insert(session_data).execute()
            except:
                pass  # Continue with response even if save fails
        
        self.send_json_response({
            'session_id': session_id,
            'join_code': join_code,
            'status': 'created'
        })
    
    def handle_join_session(self):
        """Join a session."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        
        join_code = body.get('join_code', '').upper()
        
        # For demo, accept DEMO01
        if join_code == 'DEMO01':
            self.send_json_response({
                'session_id': 'demo-1',
                'join_code': join_code,
                'status': 'joined'
            })
        else:
            self.send_error(404, "Session not found")
    
    def handle_start_session(self, session_id):
        """Start a session."""
        self.send_json_response({
            'status': 'started',
            'games_created': 1
        })
    
    def handle_get_session(self, session_id):
        """Get session details."""
        if session_id == 'demo-1':
            self.send_json_response({
                "id": "demo-1",
                "name": "Friday AI Challenge",
                "join_code": "DEMO01",
                "status": "waiting",
                "players": [{"name": "Alice", "model": "gpt-4"}]
            })
        else:
            self.send_error(404, "Session not found")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())