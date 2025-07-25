"""Session management with proper Supabase integration."""
from http.server import BaseHTTPRequestHandler
import json
import random
import string
from datetime import datetime, timedelta
from . import supabase_db as db

def generate_join_code():
    """Generate a unique 6-character join code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class handler(BaseHTTPRequestHandler):
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
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/sessions':
            self.handle_list_sessions()
        elif path.startswith('/api/sessions/') and not path.endswith('/'):
            session_id = path.split('/')[-1]
            self.handle_get_session(session_id)
        else:
            self.send_error(404)
    
    def handle_create_session(self):
        """Create a new session with join code."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        
        # Generate unique join code
        join_code = generate_join_code()
        
        # Create session
        session_data = {
            'name': body.get('name', 'Unnamed Session'),
            'join_code': join_code,
            'host_id': body.get('creator_id'),
            'game_type': body.get('game_type', 'minesweeper'),
            'max_players': body.get('max_players', 20),
            'status': 'waiting',
            'config': body.get('config', {}),
            'players': [{
                'id': body.get('creator_id'),
                'name': body.get('creator_name', 'Host'),
                'is_host': True,
                'model': body.get('model', 'gpt-4'),
                'ready': False
            }],
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        session_id = db.create_session(session_data)
        
        self.send_json_response({
            'session_id': session_id,
            'join_code': join_code,
            'status': 'created'
        })
    
    def handle_join_session(self):
        """Join an existing session with join code."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        
        join_code = body.get('join_code', '').upper()
        
        # Find session by join code
        sessions = db.list_sessions()
        session = None
        for s in sessions:
            if s.get('join_code') == join_code and s.get('status') == 'waiting':
                session = s
                break
        
        if not session:
            self.send_error(404, "Session not found or already started")
            return
        
        # Add player to session
        new_player = {
            'id': body.get('player_id'),
            'name': body.get('player_name', 'Player'),
            'is_host': False,
            'model': body.get('ai_model', 'gpt-4'),
            'ready': False
        }
        
        # Update players list
        players = session.get('players', [])
        # Remove if already exists
        players = [p for p in players if p['id'] != new_player['id']]
        players.append(new_player)
        
        # Update session
        db.update_session(session['id'], {'players': players})
        
        self.send_json_response({
            'session_id': session['id'],
            'join_code': join_code,
            'status': 'joined'
        })
    
    def handle_start_session(self, session_id):
        """Start a competition session."""
        session = db.get_session(session_id)
        if not session:
            self.send_error(404, "Session not found")
            return
        
        # Update session status
        db.update_session(session_id, {
            'status': 'in_progress',
            'started_at': datetime.utcnow().isoformat()
        })
        
        # Create games for all players
        games_created = []
        for player in session.get('players', []):
            game_data = {
                'session_id': session_id,
                'player_id': player['id'],
                'player_name': player['name'],
                'model_name': player['model'],
                'model_provider': 'openai' if 'gpt' in player['model'] else 'anthropic',
                'game_type': session['game_type'],
                'status': 'queued',
                'config': session.get('config', {})
            }
            game_id = db.create_game(game_data)
            games_created.append(game_id)
        
        self.send_json_response({
            'status': 'started',
            'games_created': len(games_created)
        })
    
    def handle_list_sessions(self):
        """List all sessions."""
        active_only = self.path.endswith('?active=true')
        sessions = db.list_sessions(active_only=active_only)
        self.send_json_response({'sessions': sessions})
    
    def handle_get_session(self, session_id):
        """Get a specific session."""
        session = db.get_session(session_id)
        if session:
            self.send_json_response(session)
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