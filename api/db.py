"""Database module for Vercel deployment using JSON files as a simple database."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

# Use /tmp directory for Vercel (writable in serverless functions)
DB_PATH = Path("/tmp/tilts_db")
DB_PATH.mkdir(exist_ok=True)

# Database "tables" as JSON files
SESSIONS_FILE = DB_PATH / "sessions.json"
GAMES_FILE = DB_PATH / "games.json"
LEADERBOARD_FILE = DB_PATH / "leaderboard.json"
EVALUATIONS_FILE = DB_PATH / "evaluations.json"
PROMPTS_FILE = DB_PATH / "prompts.json"
SETTINGS_FILE = DB_PATH / "settings.json"
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

# Generic data functions
def get_data(collection: str, default: Any = None) -> Any:
    """Get data from a collection."""
    file_map = {
        'sessions': SESSIONS_FILE,
        'games': GAMES_FILE,
        'leaderboard': LEADERBOARD_FILE,
        'evaluations': EVALUATIONS_FILE,
        'prompts': PROMPTS_FILE,
        'settings': SETTINGS_FILE,
        'benchmark_tasks': TASKS_FILE
    }
    
    file_path = file_map.get(collection)
    if file_path:
        return load_json(file_path, default)
    return default if default is not None else []

def save_data(collection: str, data: Any):
    """Save data to a collection."""
    file_map = {
        'sessions': SESSIONS_FILE,
        'games': GAMES_FILE,
        'leaderboard': LEADERBOARD_FILE,
        'evaluations': EVALUATIONS_FILE,
        'prompts': PROMPTS_FILE,
        'settings': SETTINGS_FILE,
        'benchmark_tasks': TASKS_FILE
    }
    
    file_path = file_map.get(collection)
    if file_path:
        save_json(file_path, data)

# Session Management
def create_session(session_data: Dict[str, Any]) -> str:
    """Create a new session."""
    sessions = load_json(SESSIONS_FILE, {})
    session_id = str(uuid.uuid4())[:8].upper()  # Short ID like "ABCD1234"
    
    sessions[session_id] = {
        **session_data,
        "id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "waiting",
        "players": [],
        "current_round": 0,
        "scores": {}
    }
    
    save_json(SESSIONS_FILE, sessions)
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID."""
    sessions = load_json(SESSIONS_FILE, {})
    return sessions.get(session_id)

def update_session(session_id: str, updates: Dict[str, Any]):
    """Update session data."""
    sessions = load_json(SESSIONS_FILE, {})
    if session_id in sessions:
        sessions[session_id].update(updates)
        sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
        save_json(SESSIONS_FILE, sessions)
        return True
    return False

def list_sessions(active_only: bool = False) -> List[Dict[str, Any]]:
    """List all sessions."""
    sessions = load_json(SESSIONS_FILE, {})
    result = list(sessions.values())
    
    if active_only:
        result = [s for s in result if s.get("status") in ["waiting", "active"]]
    
    return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)

# Game Management
def create_game(game_data: Dict[str, Any]) -> str:
    """Create a new game record."""
    games = load_json(GAMES_FILE, {})
    game_id = str(uuid.uuid4())
    
    games[game_id] = {
        **game_data,
        "id": game_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "in_progress"
    }
    
    save_json(GAMES_FILE, games)
    return game_id

def get_game(game_id: str) -> Optional[Dict[str, Any]]:
    """Get game by ID."""
    games = load_json(GAMES_FILE, {})
    return games.get(game_id)

def update_game(game_id: str, updates: Dict[str, Any]):
    """Update game data."""
    games = load_json(GAMES_FILE, {})
    if game_id in games:
        games[game_id].update(updates)
        games[game_id]["updated_at"] = datetime.utcnow().isoformat()
        save_json(GAMES_FILE, games)
        return True
    return False

def list_games(session_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """List games, optionally filtered by session."""
    games = load_json(GAMES_FILE, {})
    result = list(games.values())
    
    if session_id:
        result = [g for g in result if g.get("session_id") == session_id]
    
    return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

# Leaderboard Management
def update_leaderboard(model_name: str, game_result: Dict[str, Any]):
    """Update leaderboard with game results."""
    leaderboard = load_json(LEADERBOARD_FILE, {})
    
    if model_name not in leaderboard:
        leaderboard[model_name] = {
            "model_name": model_name,
            "games_played": 0,
            "wins": 0,
            "losses": 0,
            "total_moves": 0,
            "valid_moves": 0,
            "mines_identified": 0,
            "mines_total": 0,
            "first_seen": datetime.utcnow().isoformat()
        }
    
    entry = leaderboard[model_name]
    entry["games_played"] += 1
    
    if game_result.get("won"):
        entry["wins"] += 1
    else:
        entry["losses"] += 1
    
    entry["total_moves"] += game_result.get("total_moves", 0)
    entry["valid_moves"] += game_result.get("valid_moves", 0)
    entry["mines_identified"] += game_result.get("mines_identified", 0)
    entry["mines_total"] += game_result.get("mines_total", 0)
    entry["last_updated"] = datetime.utcnow().isoformat()
    
    # Calculate rates
    if entry["games_played"] > 0:
        entry["win_rate"] = entry["wins"] / entry["games_played"]
    if entry["total_moves"] > 0:
        entry["valid_move_rate"] = entry["valid_moves"] / entry["total_moves"]
    if entry["mines_total"] > 0:
        entry["mine_identification_precision"] = entry["mines_identified"] / entry["mines_total"]
    
    save_json(LEADERBOARD_FILE, leaderboard)

def get_leaderboard() -> List[Dict[str, Any]]:
    """Get leaderboard entries sorted by win rate."""
    leaderboard = load_json(LEADERBOARD_FILE, {})
    entries = list(leaderboard.values())
    return sorted(entries, key=lambda x: x.get("win_rate", 0), reverse=True)

# Evaluation Management
def create_evaluation(eval_data: Dict[str, Any]) -> str:
    """Create a new evaluation."""
    evaluations = load_json(EVALUATIONS_FILE, {})
    eval_id = str(uuid.uuid4())
    
    evaluations[eval_id] = {
        **eval_data,
        "id": eval_id,
        "created_at": datetime.utcnow().isoformat(),
        "usage_count": 0,
        "rating": 0,
        "ratings": []
    }
    
    save_json(EVALUATIONS_FILE, evaluations)
    return eval_id

def get_evaluation(eval_id: str) -> Optional[Dict[str, Any]]:
    """Get evaluation by ID."""
    evaluations = load_json(EVALUATIONS_FILE, {})
    return evaluations.get(eval_id)

def list_evaluations(game_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List evaluations, optionally filtered by game type."""
    evaluations = load_json(EVALUATIONS_FILE, {})
    result = list(evaluations.values())
    
    if game_type:
        result = [e for e in result if e.get("game_type") == game_type]
    
    return sorted(result, key=lambda x: x.get("usage_count", 0), reverse=True)

# Prompt Management
def save_prompt(prompt_data: Dict[str, Any]) -> str:
    """Save a prompt."""
    prompts = load_json(PROMPTS_FILE, {})
    prompt_id = str(uuid.uuid4())
    
    prompts[prompt_id] = {
        **prompt_data,
        "id": prompt_id,
        "created_at": datetime.utcnow().isoformat(),
        "likes": 0,
        "usage_count": 0
    }
    
    save_json(PROMPTS_FILE, prompts)
    return prompt_id

def search_prompts(query: str = "", game_type: Optional[str] = None, 
                  tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search prompts."""
    prompts = load_json(PROMPTS_FILE, {})
    result = list(prompts.values())
    
    # Filter by query
    if query:
        query_lower = query.lower()
        result = [p for p in result if 
                 query_lower in p.get("name", "").lower() or
                 query_lower in p.get("description", "").lower() or
                 query_lower in p.get("content", "").lower()]
    
    # Filter by game type
    if game_type:
        result = [p for p in result if p.get("game_type") == game_type]
    
    # Filter by tags
    if tags:
        result = [p for p in result if 
                 any(tag in p.get("tags", []) for tag in tags)]
    
    return sorted(result, key=lambda x: x.get("likes", 0), reverse=True)

# Settings Management
def get_settings() -> Dict[str, Any]:
    """Get all settings."""
    return load_json(SETTINGS_FILE, {
        "api_keys": {},
        "features": {
            "competitions": True,
            "evaluations": True,
            "marketplace": True,
            "admin": True
        },
        "models": {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        }
    })

def update_settings(updates: Dict[str, Any]):
    """Update settings."""
    settings = get_settings()
    settings.update(updates)
    save_json(SETTINGS_FILE, settings)

# Initialize default data if needed
def init_db():
    """Initialize database with default data."""
    # Create default settings if not exists
    if not SETTINGS_FILE.exists():
        update_settings({})
    
    # Create some demo leaderboard entries if empty
    if not LEADERBOARD_FILE.exists():
        demo_entries = {
            "gpt-4": {
                "model_name": "gpt-4",
                "games_played": 250,
                "wins": 213,
                "losses": 37,
                "win_rate": 0.85,
                "valid_move_rate": 0.98,
                "mine_identification_precision": 0.92
            },
            "claude-3-opus": {
                "model_name": "claude-3-opus",
                "games_played": 200,
                "wins": 164,
                "losses": 36,
                "win_rate": 0.82,
                "valid_move_rate": 0.97,
                "mine_identification_precision": 0.90
            }
        }
        save_json(LEADERBOARD_FILE, demo_entries)

# Initialize on import
init_db()