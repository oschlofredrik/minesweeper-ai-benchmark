"""Games configuration endpoint for Vercel."""
from http.server import BaseHTTPRequestHandler
import json

# Game configuration data embedded in the endpoint
GAME_CONFIGS = {
    "minesweeper": {
        "name": "Minesweeper",
        "description": "Classic mine detection game",
        "difficulties": {
            "easy": {
                "display": "Easy (9x9, 10 mines)",
                "config": {"rows": 9, "cols": 9, "mines": 10}
            },
            "medium": {
                "display": "Medium (16x16, 40 mines)",
                "config": {"rows": 16, "cols": 16, "mines": 40}
            },
            "hard": {
                "display": "Hard (16x30, 99 mines)",
                "config": {"rows": 16, "cols": 30, "mines": 99}
            },
            "expert": {
                "display": "Expert (20x40, 160 mines)",
                "config": {"rows": 20, "cols": 40, "mines": 160}
            }
        },
        "scenarios": []
    },
    "risk": {
        "name": "Risk",
        "description": "Strategic territory conquest game",
        "difficulties": {
            "easy": {
                "display": "Easy - Quick game",
                "config": {"ai_difficulty": "easy", "starting_armies": 40}
            },
            "medium": {
                "display": "Medium - Standard game", 
                "config": {"ai_difficulty": "medium", "starting_armies": 35}
            },
            "hard": {
                "display": "Hard - Challenging game",
                "config": {"ai_difficulty": "hard", "starting_armies": 30}
            }
        },
        "scenarios": [
            {
                "id": "north_america_conquest",
                "name": "North America Conquest",
                "description": "You control most of North America. Complete the conquest!",
                "objectives": [
                    "Conquer all of North America",
                    "Minimize army losses",
                    "Complete within 5 turns"
                ],
                "turn_limit": 5
            },
            {
                "id": "defend_australia",
                "name": "Defend Australia",
                "description": "You control Australia but enemies are massing in Asia. Defend your continent!",
                "objectives": [
                    "Maintain control of Australia",
                    "Survive 10 turns",
                    "Optional: Expand into Asia"
                ],
                "turn_limit": 10
            },
            {
                "id": "europe_vs_asia",
                "name": "Europe vs Asia",
                "description": "A classic continent showdown. You control Europe, opponent controls Asia.",
                "objectives": [
                    "Break into Asia",
                    "Maintain Europe control", 
                    "Achieve territorial advantage"
                ],
                "turn_limit": 15
            },
            {
                "id": "blitzkrieg",
                "name": "Blitzkrieg Challenge",
                "description": "You have overwhelming force. Conquer as much as possible in 3 turns!",
                "objectives": [
                    "Conquer at least 8 territories",
                    "Complete conquest of Africa",
                    "Do it in 3 turns"
                ],
                "turn_limit": 3
            },
            {
                "id": "last_stand",
                "name": "Last Stand",
                "description": "You're down to your last few territories. Can you turn it around?",
                "objectives": [
                    "Survive 15 turns",
                    "Control at least 6 territories",
                    "Optional: Conquer a continent"
                ],
                "turn_limit": 15
            }
        ]
    }
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path_parts = self.path.split('/')
        
        if len(path_parts) >= 3 and path_parts[2] == 'games':
            if len(path_parts) == 3:
                # List all games
                games = []
                for game_id, config in GAME_CONFIGS.items():
                    games.append({
                        "id": game_id,
                        "name": config["name"],
                        "description": config["description"],
                        "has_scenarios": len(config.get("scenarios", [])) > 0,
                        "difficulties": list(config["difficulties"].keys())
                    })
                self.send_json_response({"games": games})
                
            elif len(path_parts) == 4:
                # Get specific game config
                game_id = path_parts[3]
                if game_id in GAME_CONFIGS:
                    self.send_json_response(GAME_CONFIGS[game_id])
                else:
                    self.send_error(404, "Game not found")
                    
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())