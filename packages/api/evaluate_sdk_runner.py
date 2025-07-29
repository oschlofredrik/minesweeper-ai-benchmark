"""Runner script to execute SDK evaluations."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from game_runner import SimpleMinesweeper, get_minesweeper_prompt, get_function_schema, execute_minesweeper_move
from db_optimized import update_game, batch_update_leaderboard, HAS_SUPABASE

# This would be called by the TypeScript handler
def run_evaluation(evaluation_id, games, config):
    """Run evaluation using Python game logic but AI calls would go through SDK."""
    results = []
    
    for game_data in games:
        game_id = game_data.get('db_id', game_data['id'])
        
        try:
            # Update status
            if HAS_SUPABASE:
                update_game(game_id, {
                    'status': 'in_progress',
                    'started_at': datetime.utcnow().isoformat()
                })
            
            # Initialize game
            difficulty = config['difficulty']
            difficulties = {
                'easy': {'rows': 9, 'cols': 9, 'mines': 10},
                'medium': {'rows': 16, 'cols': 16, 'mines': 40},
                'hard': {'rows': 16, 'cols': 30, 'mines': 99}
            }
            
            cfg = difficulties.get(difficulty, difficulties['medium'])
            game = SimpleMinesweeper(rows=cfg['rows'], cols=cfg['cols'], mines=cfg['mines'])
            
            # Get initial state for SDK
            initial_state = {
                'rows': game.rows,
                'cols': game.cols,
                'mines': game.num_mines,
                'board': game.get_board_state(),
                'revealed': game.revealed.tolist(),
                'flagged': game.flags.tolist()
            }
            
            results.append({
                'game_id': game_id,
                'initial_state': initial_state,
                'status': 'ready_for_sdk'
            })
            
        except Exception as e:
            if HAS_SUPABASE:
                update_game(game_id, {
                    'status': 'error',
                    'error': str(e)
                })
            results.append({
                'game_id': game_id,
                'error': str(e)
            })
    
    return results

if __name__ == '__main__':
    # This script would be called with evaluation data
    import sys
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        results = run_evaluation(
            data['evaluation_id'],
            data['games'],
            data['config']
        )
        print(json.dumps(results))