"""Vercel AI SDK-style evaluation endpoint for Python."""
print("[EVALUATE_SDK] Module loading...")

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import uuid
from datetime import datetime
import time

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
            
            print(f"[EVALUATE_SDK] Received config: {json.dumps(config)}")
            
            # Extract configuration
            game_type = config.get('gameType', 'minesweeper')
            provider = config.get('provider', 'openai')
            model = config.get('model', 'gpt-4')
            difficulty = config.get('difficulty', 'medium')
            scenario = config.get('scenario')
            num_games = config.get('numGames', 1)
            streaming = config.get('streaming', True)
            temperature = config.get('temperature', 0.7)
            max_steps = config.get('maxSteps', 50)
            
            # Validate inputs
            if game_type not in ['minesweeper', 'risk']:
                self.send_json_response({'error': 'Invalid game type'}, 400)
                return
            
            if provider not in ['openai', 'anthropic']:
                self.send_json_response({'error': 'Invalid provider'}, 400)
                return
            
            # Check API keys
            api_key_env = 'OPENAI_API_KEY' if provider == 'openai' else 'ANTHROPIC_API_KEY'
            if not os.environ.get(api_key_env):
                self.send_json_response({'error': f'{api_key_env} not configured'}, 400)
                return
            
            # For single game with streaming
            if num_games == 1 and streaming:
                self.stream_game_evaluation({
                    'game': game_type,
                    'provider': provider,
                    'model': model,
                    'difficulty': difficulty,
                    'scenario': scenario,
                    'temperature': temperature,
                    'max_steps': max_steps
                })
            else:
                # For multiple games or non-streaming
                result = self.run_batch_evaluation({
                    'game': game_type,
                    'provider': provider,
                    'model': model,
                    'difficulty': difficulty,
                    'scenario': scenario,
                    'num_games': num_games,
                    'temperature': temperature,
                    'max_steps': max_steps
                })
                self.send_json_response(result)
                
        except Exception as e:
            print(f"[EVALUATE_SDK] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def stream_game_evaluation(self, config):
        """Stream a single game evaluation with SDK-style events."""
        print(f"[EVALUATE_SDK] Starting streaming evaluation")
        
        # Set up SSE headers
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # Import required modules
            from ai_models_http import call_ai_model, format_game_messages, extract_function_call
            from game_runner import (
                SimpleMinesweeper, SimpleRisk,
                get_minesweeper_prompt, get_risk_prompt,
                get_function_schema, execute_minesweeper_move, execute_risk_move
            )
            
            # Initialize game
            if config['game'] == 'minesweeper':
                difficulty_configs = {
                    'easy': {'rows': 9, 'cols': 9, 'mines': 10},
                    'medium': {'rows': 16, 'cols': 16, 'mines': 40},
                    'hard': {'rows': 16, 'cols': 30, 'mines': 99}
                }
                cfg = difficulty_configs.get(config['difficulty'], difficulty_configs['medium'])
                game = SimpleMinesweeper(rows=cfg['rows'], cols=cfg['cols'], mines=cfg['mines'])
                get_prompt = get_minesweeper_prompt
                execute_move = execute_minesweeper_move
            else:
                game = SimpleRisk(scenario=config.get('scenario'))
                get_prompt = get_risk_prompt
                execute_move = execute_risk_move
            
            function_schema = get_function_schema(config['game'])
            
            # Send initial status
            self.send_stream_event({
                'type': 'status',
                'message': f'Starting {config["game"]} game with {config["model"]}',
                'gameNumber': 1,
                'totalGames': 1
            })
            
            # Game loop
            move_count = 0
            start_time = time.time()
            
            for step in range(config['max_steps']):
                if game.game_over:
                    break
                
                # Get prompt and call AI
                prompt = get_prompt(game)
                messages = format_game_messages(config['game'], prompt)
                
                response = call_ai_model(
                    provider=config['provider'],
                    model=config['model'],
                    messages=messages,
                    functions=[function_schema],
                    temperature=config['temperature']
                )
                
                # Extract and execute move
                ai_move = extract_function_call(response)
                if not ai_move:
                    self.send_stream_event({
                        'type': 'error',
                        'message': 'Could not extract move from AI response'
                    })
                    break
                
                # Execute move
                valid, message = execute_move(game, ai_move)
                move_count += 1
                
                # Send move event
                move_event = {
                    'type': 'move',
                    'moveNumber': move_count,
                    'action': ai_move.get('action', 'unknown'),
                    'valid': valid,
                    'reasoning': ai_move.get('reasoning', ''),
                    'boardState': game.get_board_state() if hasattr(game, 'get_board_state') else None
                }
                
                # Add position for minesweeper
                if config['game'] == 'minesweeper' and 'row' in ai_move:
                    move_event['position'] = {
                        'row': ai_move['row'],
                        'col': ai_move['col']
                    }
                
                self.send_stream_event(move_event)
            
            # Send completion event
            duration = time.time() - start_time
            completion_event = {
                'type': 'complete',
                'gameId': f'game_{uuid.uuid4().hex[:8]}',
                'won': getattr(game, 'won', False),
                'moves': move_count,
                'duration': duration
            }
            
            if hasattr(game, 'get_coverage'):
                completion_event['coverage'] = game.get_coverage()
            
            self.send_stream_event(completion_event)
            
        except Exception as e:
            print(f"[EVALUATE_SDK] Stream error: {str(e)}")
            self.send_stream_event({
                'type': 'error',
                'message': str(e)
            })
    
    def run_batch_evaluation(self, config):
        """Run multiple games without streaming."""
        results = {
            'success': True,
            'jobId': f'eval_{int(time.time())}',
            'summary': {
                'gamesCompleted': 0,
                'totalGames': config['num_games'],
                'wins': 0,
                'winRate': 0.0,
                'avgMoves': 0.0,
                'duration': 0.0,
                'inProgress': False
            },
            'games': []
        }
        
        # For now, return placeholder
        # In production, this would run actual games
        return results
    
    def send_stream_event(self, event):
        """Send an SSE event."""
        data = json.dumps(event, default=str)
        self.wfile.write(f"data: {data}\n\n".encode())
        self.wfile.flush()
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())