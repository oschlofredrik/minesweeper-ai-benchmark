"""Task management for benchmark scenarios."""
from http.server import BaseHTTPRequestHandler
import json
import random
import uuid
from pathlib import Path
from typing import Dict, List, Any
from .lib import supabase_db as db

class TaskGenerator:
    """Generate benchmark tasks for games."""
    
    @staticmethod
    def generate_minesweeper_task(difficulty: str = "medium") -> Dict[str, Any]:
        """Generate a Minesweeper task with a specific board configuration."""
        configs = {
            "easy": {"rows": 9, "cols": 9, "mines": 10},
            "medium": {"rows": 16, "cols": 16, "mines": 40},
            "hard": {"rows": 16, "cols": 30, "mines": 99},
            "expert": {"rows": 20, "cols": 30, "mines": 145}
        }
        
        config = configs.get(difficulty, configs["medium"])
        
        # Generate mine positions
        total_cells = config["rows"] * config["cols"]
        mine_positions = random.sample(range(total_cells), config["mines"])
        mines = [(pos // config["cols"], pos % config["cols"]) for pos in mine_positions]
        
        # Generate a guaranteed safe starting position
        safe_start = None
        for r in range(config["rows"]):
            for c in range(config["cols"]):
                if (r, c) not in mines:
                    # Check if this position has no adjacent mines
                    adjacent_mines = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < config["rows"] and 0 <= nc < config["cols"]:
                                if (nr, nc) in mines:
                                    adjacent_mines += 1
                    if adjacent_mines == 0:
                        safe_start = (r, c)
                        break
            if safe_start:
                break
        
        return {
            "id": str(uuid.uuid4()),
            "game_type": "minesweeper",
            "difficulty": difficulty,
            "config": config,
            "board": {
                "mines": mines,
                "safe_start": safe_start or (0, 0)
            },
            "metadata": {
                "density": config["mines"] / total_cells,
                "board_size": f"{config['rows']}x{config['cols']}",
                "total_mines": config["mines"]
            }
        }
    
    @staticmethod
    def generate_risk_task(scenario: str = "balanced") -> Dict[str, Any]:
        """Generate a Risk task with specific starting positions."""
        scenarios = {
            "balanced": {
                "description": "Balanced starting positions",
                "player_territories": ["North America", "South America"],
                "ai_territories": ["Europe", "Africa"],
                "neutral_territories": ["Asia", "Australia"]
            },
            "defensive": {
                "description": "Defend Australia",
                "player_territories": ["Australia"],
                "ai_territories": ["Asia", "Africa"],
                "neutral_territories": ["Europe", "North America", "South America"]
            },
            "aggressive": {
                "description": "Control two continents",
                "player_territories": ["North America", "Europe"],
                "ai_territories": ["Asia"],
                "neutral_territories": ["South America", "Africa", "Australia"]
            }
        }
        
        scenario_config = scenarios.get(scenario, scenarios["balanced"])
        
        return {
            "id": str(uuid.uuid4()),
            "game_type": "risk",
            "difficulty": scenario,
            "config": scenario_config,
            "metadata": {
                "scenario": scenario,
                "player_advantage": len(scenario_config["player_territories"]) / 6
            }
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/tasks':
            self.handle_list_tasks()
        elif path.startswith('/api/tasks/generate'):
            self.handle_generate_tasks()
        elif path.startswith('/api/tasks/') and len(path.split('/')) == 4:
            task_id = path.split('/')[-1]
            self.handle_get_task(task_id)
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        if path == '/api/tasks/batch':
            self.handle_batch_generate()
        else:
            self.send_error(404)
    
    def handle_list_tasks(self):
        """List available tasks."""
        # Check for query parameters
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = {}
        if query:
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        
        # Get tasks from storage
        tasks = db.get_data('benchmark_tasks', [])
        
        # Filter by game type if specified
        if 'game_type' in params:
            tasks = [t for t in tasks if t.get('game_type') == params['game_type']]
        
        # Filter by difficulty if specified
        if 'difficulty' in params:
            tasks = [t for t in tasks if t.get('difficulty') == params['difficulty']]
        
        self.send_json_response({'tasks': tasks})
    
    def handle_generate_tasks(self):
        """Generate new tasks on demand."""
        # Parse query parameters
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = {}
        if query:
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        
        game_type = params.get('game_type', 'minesweeper')
        count = int(params.get('count', '1'))
        difficulty = params.get('difficulty', 'medium')
        
        tasks = []
        generator = TaskGenerator()
        
        for _ in range(count):
            if game_type == 'minesweeper':
                task = generator.generate_minesweeper_task(difficulty)
            elif game_type == 'risk':
                task = generator.generate_risk_task(difficulty)
            else:
                continue
            
            tasks.append(task)
        
        # Store tasks
        existing_tasks = db.get_data('benchmark_tasks', [])
        existing_tasks.extend(tasks)
        db.save_data('benchmark_tasks', existing_tasks)
        
        self.send_json_response({
            'tasks': tasks,
            'count': len(tasks)
        })
    
    def handle_get_task(self, task_id):
        """Get a specific task."""
        tasks = db.get_data('benchmark_tasks', [])
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if task:
            self.send_json_response(task)
        else:
            self.send_error(404, "Task not found")
    
    def handle_batch_generate(self):
        """Generate a batch of tasks."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        
        tasks = []
        generator = TaskGenerator()
        
        # Generate tasks for each configuration
        for config in body.get('configurations', []):
            game_type = config.get('game_type', 'minesweeper')
            count = config.get('count', 10)
            
            if game_type == 'minesweeper':
                for difficulty in config.get('difficulties', ['easy', 'medium', 'hard']):
                    for _ in range(count):
                        task = generator.generate_minesweeper_task(difficulty)
                        tasks.append(task)
                        
            elif game_type == 'risk':
                for scenario in config.get('scenarios', ['balanced', 'defensive', 'aggressive']):
                    for _ in range(count):
                        task = generator.generate_risk_task(scenario)
                        tasks.append(task)
        
        # Store tasks
        existing_tasks = db.get_data('benchmark_tasks', [])
        existing_tasks.extend(tasks)
        db.save_data('benchmark_tasks', existing_tasks)
        
        self.send_json_response({
            'tasks_created': len(tasks),
            'total_tasks': len(existing_tasks)
        })
    
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