"""Supabase database module for Vercel deployment."""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

# Supabase configuration from environment
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

# Check if Supabase is configured
HAS_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

if HAS_SUPABASE:
    try:
        # Try to import supabase client
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except ImportError:
        HAS_SUPABASE = False
        supabase = None
else:
    supabase = None

# JSON fallback storage
from pathlib import Path

# Use /tmp directory for Vercel (writable in serverless functions)
DB_PATH = Path("/tmp/tilts_db")
DB_PATH.mkdir(exist_ok=True)

# Database "tables" as JSON files
SESSIONS_FILE = DB_PATH / "sessions.json"
GAMES_FILE = DB_PATH / "games.json"
LEADERBOARD_FILE = DB_PATH / "leaderboard.json"
TASKS_FILE = DB_PATH / "benchmark_tasks.json"

def load_json(file_path: Path, default: Any = None) -> Any:
    """Load JSON file or return default."""
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return default if default is not None else {}

def save_json(file_path: Path, data: Any):
    """Save data to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# Generic data functions for non-table data (like tasks)
def get_data(collection: str, default: Any = None) -> Any:
    """Get data from a collection (uses JSON storage)."""
    file_map = {
        'sessions': SESSIONS_FILE,
        'games': GAMES_FILE,
        'leaderboard': LEADERBOARD_FILE,
        'benchmark_tasks': TASKS_FILE
    }
    
    file_path = file_map.get(collection)
    if file_path:
        return load_json(file_path, default)
    return default if default is not None else []

def save_data(collection: str, data: Any):
    """Save data to a collection (uses JSON storage)."""
    file_map = {
        'sessions': SESSIONS_FILE,
        'games': GAMES_FILE,  
        'leaderboard': LEADERBOARD_FILE,
        'benchmark_tasks': TASKS_FILE
    }
    
    file_path = file_map.get(collection)
    if file_path:
        save_json(file_path, data)

def _ensure_uuid(id_value: str) -> str:
    """Ensure ID is a valid UUID string."""
    if not id_value:
        return str(uuid.uuid4())
    return id_value

# Session Management
def create_session(session_data: Dict[str, Any]) -> str:
    """Create a new session."""
    if not HAS_SUPABASE:
        return json_db.create_session(session_data)
    
    session_id = _ensure_uuid(session_data.get('id', ''))
    join_code = session_data.get('join_code', str(uuid.uuid4())[:8].upper())
    
    data = {
        'id': session_id,
        'join_code': join_code,
        'name': session_data.get('name', 'Untitled Session'),
        'description': session_data.get('description', ''),
        'game_type': session_data.get('game_type', 'minesweeper'),
        'format': session_data.get('format', 'single_round'),
        'max_players': session_data.get('max_players', 10),
        'difficulty': session_data.get('difficulty', 'medium'),
        'config': session_data.get('config', {}),
        'status': 'waiting'
    }
    
    result = supabase.table('sessions').insert(data).execute()
    return result.data[0]['id'] if result.data else session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID or join code."""
    if not HAS_SUPABASE:
        return json_db.get_session(session_id)
    
    # Try by ID first
    result = supabase.table('sessions').select('*').eq('id', session_id).execute()
    if result.data:
        return result.data[0]
    
    # Try by join code
    result = supabase.table('sessions').select('*').eq('join_code', session_id.upper()).execute()
    return result.data[0] if result.data else None

def update_session(session_id: str, updates: Dict[str, Any]) -> bool:
    """Update session data."""
    if not HAS_SUPABASE:
        return json_db.update_session(session_id, updates)
    
    result = supabase.table('sessions').update(updates).eq('id', session_id).execute()
    return bool(result.data)

def list_sessions(active_only: bool = False) -> List[Dict[str, Any]]:
    """List all sessions."""
    if not HAS_SUPABASE:
        return json_db.list_sessions(active_only)
    
    query = supabase.table('sessions').select('*')
    if active_only:
        query = query.in_('status', ['waiting', 'active'])
    
    result = query.order('created_at', desc=True).execute()
    return result.data or []

# Game Management
def create_game(game_data: Dict[str, Any]) -> str:
    """Create a new game record."""
    if not HAS_SUPABASE:
        return json_db.create_game(game_data)
    
    game_id = _ensure_uuid(game_data.get('id', ''))
    
    data = {
        'id': game_id,
        'job_id': game_data.get('job_id'),
        'session_id': game_data.get('session_id'),
        'game_type': game_data.get('game_type', 'minesweeper'),
        'difficulty': game_data.get('difficulty', 'medium'),
        'model_name': game_data.get('model_name'),
        'model_provider': game_data.get('model_provider'),
        'status': 'in_progress',
        'moves': game_data.get('moves', [])
    }
    
    result = supabase.table('games').insert(data).execute()
    return result.data[0]['id'] if result.data else game_id

def get_game(game_id: str) -> Optional[Dict[str, Any]]:
    """Get game by ID."""
    if not HAS_SUPABASE:
        return json_db.get_game(game_id)
    
    result = supabase.table('games').select('*').eq('id', game_id).execute()
    return result.data[0] if result.data else None

def update_game(game_id: str, updates: Dict[str, Any]) -> bool:
    """Update game data."""
    if not HAS_SUPABASE:
        return json_db.update_game(game_id, updates)
    
    result = supabase.table('games').update(updates).eq('id', game_id).execute()
    return bool(result.data)

def list_games(session_id: Optional[str] = None, job_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """List games with optional filters."""
    if not HAS_SUPABASE:
        return json_db.list_games(session_id, limit)
    
    query = supabase.table('games').select('*')
    
    if session_id:
        query = query.eq('session_id', session_id)
    if job_id:
        query = query.eq('job_id', job_id)
    
    result = query.order('created_at', desc=True).limit(limit).execute()
    return result.data or []

# Leaderboard Management
def update_leaderboard(model_name: str, game_result: Dict[str, Any]):
    """Update leaderboard with game results."""
    if not HAS_SUPABASE:
        return json_db.update_leaderboard(model_name, game_result)
    
    # Check if entry exists
    result = supabase.table('leaderboard_entries').select('*').eq('model_name', model_name).execute()
    
    if result.data:
        # Update existing entry
        entry = result.data[0]
        entry['games_played'] += 1
        
        if game_result.get('won'):
            entry['wins'] += 1
        else:
            entry['losses'] += 1
        
        entry['total_moves'] += game_result.get('total_moves', 0)
        entry['valid_moves'] += game_result.get('valid_moves', 0)
        entry['mines_identified'] += game_result.get('mines_identified', 0)
        entry['mines_total'] += game_result.get('mines_total', 0)
        
        # Calculate rates
        if entry['games_played'] > 0:
            entry['win_rate'] = entry['wins'] / entry['games_played']
        if entry['total_moves'] > 0:
            entry['valid_move_rate'] = entry['valid_moves'] / entry['total_moves']
        if entry['mines_total'] > 0:
            entry['mine_identification_precision'] = entry['mines_identified'] / entry['mines_total']
        
        supabase.table('leaderboard_entries').update(entry).eq('model_name', model_name).execute()
    else:
        # Create new entry
        entry = {
            'model_name': model_name,
            'games_played': 1,
            'wins': 1 if game_result.get('won') else 0,
            'losses': 0 if game_result.get('won') else 1,
            'total_moves': game_result.get('total_moves', 0),
            'valid_moves': game_result.get('valid_moves', 0),
            'mines_identified': game_result.get('mines_identified', 0),
            'mines_total': game_result.get('mines_total', 0),
            'win_rate': 1.0 if game_result.get('won') else 0.0
        }
        
        supabase.table('leaderboard_entries').insert(entry).execute()

def get_leaderboard() -> List[Dict[str, Any]]:
    """Get leaderboard entries sorted by win rate."""
    if not HAS_SUPABASE:
        return json_db.get_leaderboard()
    
    result = supabase.table('leaderboard_entries').select('*').order('win_rate', desc=True).execute()
    return result.data or []

# Evaluation Management
def create_evaluation(eval_data: Dict[str, Any]) -> str:
    """Create a new evaluation."""
    if not HAS_SUPABASE:
        return json_db.create_evaluation(eval_data)
    
    eval_id = _ensure_uuid(eval_data.get('id', ''))
    
    data = {
        'id': eval_id,
        'name': eval_data.get('name', 'Untitled Evaluation'),
        'description': eval_data.get('description', ''),
        'game_type': eval_data.get('game_type', 'minesweeper'),
        'author': eval_data.get('author', 'anonymous'),
        'metrics': eval_data.get('metrics', []),
        'weights': eval_data.get('weights', {}),
        'tags': eval_data.get('tags', []),
        'is_public': eval_data.get('is_public', True)
    }
    
    result = supabase.table('evaluations').insert(data).execute()
    return result.data[0]['id'] if result.data else eval_id

def get_evaluation(eval_id: str) -> Optional[Dict[str, Any]]:
    """Get evaluation by ID."""
    if not HAS_SUPABASE:
        return json_db.get_evaluation(eval_id)
    
    result = supabase.table('evaluations').select('*').eq('id', eval_id).execute()
    return result.data[0] if result.data else None

def list_evaluations(game_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List evaluations with optional game type filter."""
    if not HAS_SUPABASE:
        return json_db.list_evaluations(game_type)
    
    query = supabase.table('evaluations').select('*')
    
    if game_type:
        query = query.eq('game_type', game_type)
    
    result = query.order('usage_count', desc=True).execute()
    return result.data or []

# Prompt Management
def save_prompt(prompt_data: Dict[str, Any]) -> str:
    """Save a prompt."""
    if not HAS_SUPABASE:
        return json_db.save_prompt(prompt_data)
    
    prompt_id = _ensure_uuid(prompt_data.get('id', ''))
    
    data = {
        'id': prompt_id,
        'name': prompt_data.get('name', 'Untitled Prompt'),
        'description': prompt_data.get('description', ''),
        'content': prompt_data.get('content', ''),
        'game_type': prompt_data.get('game_type', 'minesweeper'),
        'author': prompt_data.get('author', 'anonymous'),
        'tags': prompt_data.get('tags', []),
        'variables': prompt_data.get('variables', {}),
        'example_output': prompt_data.get('example_output', ''),
        'is_public': prompt_data.get('is_public', True)
    }
    
    result = supabase.table('prompts').insert(data).execute()
    return result.data[0]['id'] if result.data else prompt_id

def search_prompts(query: str = "", game_type: Optional[str] = None, 
                  tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search prompts."""
    if not HAS_SUPABASE:
        return json_db.search_prompts(query, game_type, tags)
    
    # Start with all prompts
    result = supabase.table('prompts').select('*').execute()
    prompts = result.data or []
    
    # Filter by query (client-side for now)
    if query:
        query_lower = query.lower()
        prompts = [p for p in prompts if 
                   query_lower in p.get('name', '').lower() or
                   query_lower in p.get('description', '').lower() or
                   query_lower in p.get('content', '').lower()]
    
    # Filter by game type
    if game_type:
        prompts = [p for p in prompts if p.get('game_type') == game_type]
    
    # Filter by tags
    if tags:
        prompts = [p for p in prompts if 
                   any(tag in p.get('tags', []) for tag in tags)]
    
    # Sort by likes
    return sorted(prompts, key=lambda x: x.get('likes', 0), reverse=True)

# Settings Management
def get_settings() -> Dict[str, Any]:
    """Get all settings."""
    if not HAS_SUPABASE:
        return json_db.get_settings()
    
    result = supabase.table('settings').select('*').execute()
    
    settings = {}
    for row in (result.data or []):
        settings[row['key']] = row['value']
    
    # Return with defaults if empty
    return {
        'api_keys': settings.get('api_keys', {}),
        'features': settings.get('features', {
            'competitions': True,
            'evaluations': True,
            'marketplace': True,
            'admin': True
        }),
        'models': settings.get('models', {
            'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku']
        })
    }

def update_settings(updates: Dict[str, Any]):
    """Update settings."""
    if not HAS_SUPABASE:
        return json_db.update_settings(updates)
    
    for key, value in updates.items():
        supabase.table('settings').upsert({
            'key': key,
            'value': value
        }).execute()

# Export all functions for compatibility
__all__ = [
    'HAS_SUPABASE',
    'create_session',
    'get_session',
    'update_session',
    'list_sessions',
    'create_game',
    'get_game',
    'update_game',
    'list_games',
    'update_leaderboard',
    'get_leaderboard',
    'create_evaluation',
    'get_evaluation',
    'list_evaluations',
    'save_prompt',
    'search_prompts',
    'get_settings',
    'update_settings'
]