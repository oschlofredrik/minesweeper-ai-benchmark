"""Session management endpoints for competitions."""
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse
from . import supabase_db as db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # List all sessions
        if path == '/api/sessions':
            active_only = query_params.get('active', ['false'])[0] == 'true'
            sessions = db.list_sessions(active_only=active_only)
            self.send_json_response(sessions)
            
        # Get specific session
        elif path.startswith('/api/sessions/') and len(path.split('/')) == 4:
            session_id = path.split('/')[-1]
            session = db.get_session(session_id)
            if session:
                self.send_json_response(session)
            else:
                self.send_error(404, "Session not found")
                
        # Get session templates
        elif path == '/api/sessions/templates/quick-match':
            template = {
                "template": {
                    "name": "Quick Match",
                    "description": "Jump into a quick game",
                    "game_type": "minesweeper",
                    "format": "single_round",
                    "max_players": 10,
                    "difficulty": "medium",
                    "time_limit": None,
                    "scoring": "default"
                }
            }
            self.send_json_response(template)
            
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path
        
        # Create new session
        if path == '/api/sessions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            session_data = json.loads(post_data)
            
            # Create session in database
            session_id = db.create_session(session_data)
            session = db.get_session(session_id)
            
            self.send_json_response({
                "success": True,
                "session_id": session_id,
                "join_code": session_id,
                "session": session
            })
            
        # Join session
        elif path.startswith('/api/sessions/') and path.endswith('/join'):
            session_id = path.split('/')[-2]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            join_data = json.loads(post_data)
            
            session = db.get_session(session_id)
            if not session:
                self.send_error(404, "Session not found")
                return
                
            # Add player to session
            player = {
                "id": join_data.get("player_id", "player-" + str(len(session.get("players", [])))),
                "name": join_data.get("name", "Anonymous"),
                "model": join_data.get("model", "gpt-4"),
                "joined_at": db.datetime.utcnow().isoformat()
            }
            
            players = session.get("players", [])
            players.append(player)
            
            db.update_session(session_id, {"players": players})
            
            self.send_json_response({
                "success": True,
                "player": player,
                "session": db.get_session(session_id)
            })
            
        # Start session
        elif path.startswith('/api/sessions/') and path.endswith('/start'):
            session_id = path.split('/')[-2]
            session = db.get_session(session_id)
            
            if not session:
                self.send_error(404, "Session not found")
                return
                
            # Update session status
            db.update_session(session_id, {
                "status": "active",
                "started_at": db.datetime.utcnow().isoformat()
            })
            
            self.send_json_response({
                "success": True,
                "message": "Session started",
                "session": db.get_session(session_id)
            })
            
        # Update session
        elif path.startswith('/api/sessions/') and len(path.split('/')) == 4:
            session_id = path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            updates = json.loads(post_data)
            
            if db.update_session(session_id, updates):
                self.send_json_response({
                    "success": True,
                    "session": db.get_session(session_id)
                })
            else:
                self.send_error(404, "Session not found")
                
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())