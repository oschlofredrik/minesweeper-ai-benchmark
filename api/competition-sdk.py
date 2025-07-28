"""Competition endpoint using Vercel AI SDK workflows."""
print("[COMPETITION_SDK] Module loading...")

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import uuid
from datetime import datetime
import asyncio

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config = json.loads(post_data)
            
            print(f"[COMPETITION_SDK] Received config: {json.dumps(config)}")
            
            # Extract configuration
            competition_type = config.get('type', 'tournament')  # tournament, team, league
            
            if competition_type == 'tournament':
                self.handle_tournament(config)
            elif competition_type == 'team':
                self.handle_team_game(config)
            elif competition_type == 'league':
                self.handle_league(config)
            else:
                self.send_error(400, f"Unknown competition type: {competition_type}")
                
        except Exception as e:
            print(f"[COMPETITION_SDK] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_tournament(self, config):
        """Handle elimination tournament request."""
        tournament_id = f"tournament_{uuid.uuid4().hex[:8]}"
        
        # For now, return a mock response showing the tournament structure
        # In production, this would call the TypeScript SDK via subprocess or API
        
        participants = config.get('participants', [])
        bracket_size = 1
        while bracket_size < len(participants):
            bracket_size *= 2
        
        response = {
            'id': tournament_id,
            'type': 'elimination',
            'name': config.get('name', 'AI Tournament'),
            'status': 'created',
            'participants': participants,
            'bracket': {
                'size': bracket_size,
                'rounds': int(bracket_size ** 0.5)
            },
            'rules': {
                'gameType': config.get('gameType', 'minesweeper'),
                'roundFormat': config.get('roundFormat', 'best-of-3'),
                'difficulty': config.get('difficulty', 'medium')
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.send_json_response(response)
    
    def handle_team_game(self, config):
        """Handle team-based game request."""
        team_game_id = f"team_{uuid.uuid4().hex[:8]}"
        
        # Extract team configuration
        team = config.get('team', {})
        members = team.get('members', [])
        
        # Validate team composition
        roles = [m.get('role') for m in members]
        if 'strategist' not in roles:
            self.send_error(400, "Team must have at least one strategist")
            return
        
        response = {
            'id': team_game_id,
            'type': 'team',
            'status': 'created',
            'team': {
                'name': team.get('name', 'AI Team'),
                'members': members,
                'communicationStyle': team.get('communicationStyle', 'sequential')
            },
            'game': {
                'type': config.get('gameType', 'minesweeper'),
                'difficulty': config.get('difficulty', 'medium')
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.send_json_response(response)
    
    def handle_league(self, config):
        """Handle league/round-robin competition."""
        league_id = f"league_{uuid.uuid4().hex[:8]}"
        
        participants = config.get('participants', [])
        rounds = config.get('rounds', 1)
        
        # Calculate total games (each participant plays each other)
        total_games = len(participants) * (len(participants) - 1) * rounds // 2
        
        response = {
            'id': league_id,
            'type': 'league',
            'name': config.get('name', 'AI League'),
            'status': 'created',
            'participants': participants,
            'format': {
                'rounds': rounds,
                'totalGames': total_games,
                'pointSystem': config.get('pointSystem', {
                    'win': 3,
                    'draw': 1,
                    'loss': 0
                })
            },
            'schedule': self.generate_league_schedule(participants, rounds),
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.send_json_response(response)
    
    def generate_league_schedule(self, participants, rounds):
        """Generate round-robin schedule."""
        schedule = []
        n = len(participants)
        
        for round_num in range(rounds):
            round_games = []
            
            # Simple round-robin algorithm
            for i in range(n):
                for j in range(i + 1, n):
                    round_games.append({
                        'home': participants[i]['name'] if 'name' in participants[i] else f"{participants[i]['provider']}-{participants[i]['model']}",
                        'away': participants[j]['name'] if 'name' in participants[j] else f"{participants[j]['provider']}-{participants[j]['model']}",
                        'round': round_num + 1
                    })
            
            schedule.extend(round_games)
        
        return schedule
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())