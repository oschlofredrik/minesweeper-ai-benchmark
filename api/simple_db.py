"""Simple database functions for Vercel - no complex imports."""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
HAS_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# Try to import Supabase
supabase = None
if HAS_SUPABASE:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except:
        HAS_SUPABASE = False

# Simple JSON storage for tasks and other data
DATA_STORAGE = {}

def get_data(collection: str, default: Any = None) -> Any:
    """Get data from storage."""
    if collection in DATA_STORAGE:
        return DATA_STORAGE[collection]
    return default if default is not None else []

def save_data(collection: str, data: Any) -> None:
    """Save data to storage."""
    DATA_STORAGE[collection] = data

def list_sessions(active_only: bool = False) -> List[Dict]:
    """List all sessions."""
    if HAS_SUPABASE and supabase:
        try:
            query = supabase.table('sessions').select('*')
            if active_only:
                query = query.eq('status', 'waiting')
            response = query.execute()
            return response.data if response.data else []
        except:
            pass
    # Fallback
    sessions = get_data('sessions', [])
    if active_only:
        return [s for s in sessions if s.get('status') == 'waiting']
    return sessions

def get_leaderboard() -> List[Dict]:
    """Get leaderboard entries."""
    if HAS_SUPABASE and supabase:
        try:
            response = supabase.table('leaderboard_entries').select('*').order('win_rate', desc=True).execute()
            return response.data if response.data else []
        except:
            pass
    # Fallback with demo data
    return [
        {
            "model_name": "gpt-4",
            "total_games": 10,
            "wins": 7,
            "losses": 3,
            "win_rate": 0.7,
            "avg_moves": 45.2,
            "avg_duration": 12.5,
            "ms_s_score": 0.752,
            "ms_i_score": 0.689
        },
        {
            "model_name": "claude-3-opus",
            "total_games": 8,
            "wins": 5,
            "losses": 3,
            "win_rate": 0.625,
            "avg_moves": 52.1,
            "avg_duration": 15.3,
            "ms_s_score": 0.698,
            "ms_i_score": 0.712
        }
    ]

def list_games(limit: int = 100) -> List[Dict]:
    """List games."""
    if HAS_SUPABASE and supabase:
        try:
            response = supabase.table('games').select('*').order('created_at', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except:
            pass
    return get_data('games', [])

def create_game(game_data: Dict) -> str:
    """Create a new game."""
    if 'id' not in game_data:
        game_data['id'] = str(uuid.uuid4())
    if 'created_at' not in game_data:
        game_data['created_at'] = datetime.utcnow().isoformat()
    
    if HAS_SUPABASE and supabase:
        try:
            response = supabase.table('games').insert(game_data).execute()
            if response.data:
                return game_data['id']
        except:
            pass
    
    # Fallback
    games = get_data('games', [])
    games.append(game_data)
    save_data('games', games)
    return game_data['id']

def get_game(game_id: str) -> Optional[Dict]:
    """Get a specific game."""
    if HAS_SUPABASE and supabase:
        try:
            response = supabase.table('games').select('*').eq('id', game_id).single().execute()
            return response.data
        except:
            pass
    
    games = get_data('games', [])
    for game in games:
        if game.get('id') == game_id:
            return game
    return None

def update_game(game_id: str, updates: Dict) -> bool:
    """Update a game."""
    updates['updated_at'] = datetime.utcnow().isoformat()
    
    if HAS_SUPABASE and supabase:
        try:
            response = supabase.table('games').update(updates).eq('id', game_id).execute()
            return bool(response.data)
        except:
            pass
    
    # Fallback
    games = get_data('games', [])
    for i, game in enumerate(games):
        if game.get('id') == game_id:
            games[i].update(updates)
            save_data('games', games)
            return True
    return False