"""Admin endpoints for system management."""
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from . import supabase_db as db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # Get system stats
        if path == '/api/admin/stats':
            stats = {
                "sessions": {
                    "total": len(db.list_sessions()),
                    "active": len(db.list_sessions(active_only=True))
                },
                "games": {
                    "total": len(db.list_games()),
                    "today": sum(1 for g in db.list_games() if g.get("created_at", "").startswith(db.datetime.utcnow().date().isoformat()))
                },
                "leaderboard": {
                    "models": len(db.get_leaderboard()),
                    "total_games": sum(e.get("games_played", 0) for e in db.get_leaderboard())
                },
                "evaluations": {
                    "total": len(db.list_evaluations()),
                    "public": len([e for e in db.list_evaluations() if e.get("is_public", True)])
                },
                "prompts": {
                    "total": len(db.search_prompts())
                }
            }
            self.send_json_response(stats)
            
        # Get all settings
        elif path == '/api/admin/settings':
            settings = db.get_settings()
            self.send_json_response(settings)
            
        # Get feature flags
        elif path == '/api/admin/features':
            settings = db.get_settings()
            self.send_json_response(settings.get("features", {}))
            
        # Get models configuration
        elif path == '/api/admin/models':
            settings = db.get_settings()
            models = settings.get("models", {})
            # Add API key status (without exposing keys)
            api_keys = settings.get("api_keys", {})
            for provider in models:
                models[provider] = {
                    "models": models.get(provider, []),
                    "has_api_key": bool(api_keys.get(f"{provider}_api_key"))
                }
            self.send_json_response(models)
            
        # Database management
        elif path == '/api/admin/database/games':
            limit = int(query_params.get('limit', [100])[0])
            games = db.list_games(limit=limit)
            self.send_json_response({
                "games": games,
                "total": len(games)
            })
            
        elif path == '/api/admin/database/sessions':
            sessions = db.list_sessions()
            self.send_json_response({
                "sessions": sessions,
                "total": len(sessions)
            })
            
        elif path == '/api/admin/database/leaderboard':
            leaderboard = db.get_leaderboard()
            self.send_json_response({
                "entries": leaderboard,
                "total": len(leaderboard)
            })
            
        # Export configuration
        elif path == '/api/admin/export':
            export_data = {
                "settings": db.get_settings(),
                "evaluations": db.list_evaluations(),
                "prompts": db.search_prompts(),
                "exported_at": db.datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            self.send_json_response(export_data)
            
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # Update settings
        if path == '/api/admin/settings':
            db.update_settings(data)
            self.send_json_response({
                "success": True,
                "settings": db.get_settings()
            })
            
        # Update feature flags
        elif path == '/api/admin/features':
            current_settings = db.get_settings()
            current_settings["features"] = data
            db.update_settings(current_settings)
            self.send_json_response({
                "success": True,
                "features": data
            })
            
        # Update API keys
        elif path == '/api/admin/api-keys':
            current_settings = db.get_settings()
            current_settings["api_keys"] = data
            db.update_settings(current_settings)
            # Return without exposing the actual keys
            self.send_json_response({
                "success": True,
                "message": "API keys updated"
            })
            
        # Add/update model
        elif path == '/api/admin/models':
            current_settings = db.get_settings()
            models = current_settings.get("models", {})
            provider = data.get("provider")
            model_name = data.get("model")
            
            if provider and model_name:
                if provider not in models:
                    models[provider] = []
                if model_name not in models[provider]:
                    models[provider].append(model_name)
                current_settings["models"] = models
                db.update_settings(current_settings)
                
            self.send_json_response({
                "success": True,
                "models": models
            })
            
        # Import configuration
        elif path == '/api/admin/import':
            import_data = data
            
            # Validate import data
            if "version" not in import_data:
                self.send_json_response({
                    "success": False,
                    "error": "Invalid import format"
                })
                return
                
            # Import settings (excluding API keys for security)
            if "settings" in import_data:
                settings = import_data["settings"]
                # Preserve existing API keys
                current_settings = db.get_settings()
                settings["api_keys"] = current_settings.get("api_keys", {})
                db.update_settings(settings)
                
            # Import evaluations
            if "evaluations" in import_data:
                for eval_data in import_data["evaluations"]:
                    db.create_evaluation(eval_data)
                    
            # Import prompts
            if "prompts" in import_data:
                for prompt_data in import_data["prompts"]:
                    db.save_prompt(prompt_data)
                    
            self.send_json_response({
                "success": True,
                "message": "Configuration imported successfully"
            })
            
        # Database operations
        elif path == '/api/admin/database/reset-leaderboard':
            # Reset leaderboard
            if hasattr(db, 'supabase') and db.supabase:
                db.supabase.table('leaderboard_entries').delete().execute()
            else:
                db.save_json(db.LEADERBOARD_FILE, {})
            self.send_json_response({
                "success": True,
                "message": "Leaderboard reset"
            })
            
        elif path == '/api/admin/database/cleanup-games':
            # Remove old games (older than 7 days)
            from datetime import datetime, timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('games').delete().lt('created_at', cutoff_date).execute()
                cleaned = len(result.data) if result.data else 0
            else:
                games = db.load_json(db.GAMES_FILE, {})
                cleaned = 0
                for game_id in list(games.keys()):
                    if games[game_id].get("created_at", "") < cutoff_date:
                        del games[game_id]
                        cleaned += 1
                db.save_json(db.GAMES_FILE, games)
            
            self.send_json_response({
                "success": True,
                "cleaned": cleaned,
                "message": f"Removed {cleaned} old games"
            })
            
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        path = self.path
        
        # Delete specific game
        if path.startswith('/api/admin/database/games/'):
            game_id = path.split('/')[-1]
            # Delete game
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('games').delete().eq('id', game_id).execute()
                if result.data:
                    self.send_json_response({
                        "success": True,
                        "message": "Game deleted"
                    })
                else:
                    self.send_error(404, "Game not found")
            else:
                games = db.load_json(db.GAMES_FILE, {})
                if game_id in games:
                    del games[game_id]
                    db.save_json(db.GAMES_FILE, games)
                    self.send_json_response({
                        "success": True,
                        "message": "Game deleted"
                    })
                else:
                    self.send_error(404, "Game not found")
                
        # Delete specific session
        elif path.startswith('/api/admin/database/sessions/'):
            session_id = path.split('/')[-1]
            # Delete session
            if hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('sessions').delete().eq('id', session_id).execute()
                if result.data:
                    self.send_json_response({
                        "success": True,
                        "message": "Session deleted"
                    })
                else:
                    self.send_error(404, "Session not found")
            else:
                sessions = db.load_json(db.SESSIONS_FILE, {})
                if session_id in sessions:
                    del sessions[session_id]
                    db.save_json(db.SESSIONS_FILE, sessions)
                    self.send_json_response({
                        "success": True,
                        "message": "Session deleted"
                    })
                else:
                    self.send_error(404, "Session not found")
                
        # Delete model from configuration
        elif path.startswith('/api/admin/models/'):
            parts = path.split('/')
            if len(parts) >= 6:
                provider = parts[-2]
                model = parts[-1]
                
                settings = db.get_settings()
                models = settings.get("models", {})
                
                if provider in models and model in models[provider]:
                    models[provider].remove(model)
                    settings["models"] = models
                    db.update_settings(settings)
                    
                    self.send_json_response({
                        "success": True,
                        "message": f"Removed {model} from {provider}"
                    })
                else:
                    self.send_error(404, "Model not found")
            else:
                self.send_error(400, "Invalid path")
                
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