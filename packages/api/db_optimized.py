"""Optimized Supabase database module with caching and connection pooling."""
import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from functools import lru_cache, wraps
import uuid
from contextlib import contextmanager
from threading import Lock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration from environment
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

# Check if Supabase is configured
HAS_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# Connection pool settings
CONNECTION_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '5'))
CONNECTION_TIMEOUT = int(os.environ.get('DB_TIMEOUT', '30'))

# Cache settings
CACHE_TTL = int(os.environ.get('CACHE_TTL', '300'))  # 5 minutes default
LEADERBOARD_CACHE_TTL = int(os.environ.get('LEADERBOARD_CACHE_TTL', '60'))  # 1 minute for leaderboard

# Initialize connection pool
supabase_pool = []
pool_lock = Lock()

if HAS_SUPABASE:
    try:
        from supabase import create_client, Client
        
        # Create connection pool
        for _ in range(CONNECTION_POOL_SIZE):
            client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            supabase_pool.append(client)
            
        logger.info(f"Initialized Supabase connection pool with {CONNECTION_POOL_SIZE} connections")
    except ImportError:
        HAS_SUPABASE = False
        logger.warning("Supabase client not available, falling back to JSON storage")
else:
    logger.info("Supabase not configured, using JSON storage")

# In-memory cache
class Cache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = CACHE_TTL):
        """Set value in cache with TTL."""
        with self._lock:
            expiry = time.time() + ttl
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]

# Initialize cache
cache = Cache()

# Performance monitoring
class QueryMonitor:
    """Monitor database query performance."""
    
    def __init__(self):
        self.queries = defaultdict(list)
        self._lock = Lock()
    
    def record(self, query_type: str, duration: float):
        """Record query execution time."""
        with self._lock:
            self.queries[query_type].append({
                'timestamp': datetime.utcnow(),
                'duration': duration
            })
            
            # Keep only last 1000 entries per query type
            if len(self.queries[query_type]) > 1000:
                self.queries[query_type] = self.queries[query_type][-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        with self._lock:
            stats = {}
            for query_type, records in self.queries.items():
                if records:
                    durations = [r['duration'] for r in records]
                    stats[query_type] = {
                        'count': len(records),
                        'avg_duration': sum(durations) / len(durations),
                        'min_duration': min(durations),
                        'max_duration': max(durations),
                        'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations)
                    }
            return stats

# Initialize monitor
query_monitor = QueryMonitor()

# Decorators
def with_cache(ttl: int = CACHE_TTL):
    """Cache decorator for database queries."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def with_monitoring(query_type: str):
    """Monitor query performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                query_monitor.record(query_type, duration)
                
                if duration > 1.0:  # Log slow queries
                    logger.warning(f"Slow query detected: {query_type} took {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                query_monitor.record(f"{query_type}_error", duration)
                raise
        return wrapper
    return decorator

@contextmanager
def get_supabase_client():
    """Get a Supabase client from the pool."""
    if not HAS_SUPABASE or not supabase_pool:
        yield None
        return
    
    client = None
    try:
        with pool_lock:
            if supabase_pool:
                client = supabase_pool.pop()
        
        if client:
            yield client
        else:
            # All connections in use, create a temporary one
            logger.warning("Connection pool exhausted, creating temporary connection")
            temp_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            yield temp_client
    finally:
        if client and supabase_pool is not None:
            with pool_lock:
                supabase_pool.append(client)

# JSON fallback storage (optimized)
from pathlib import Path

# Use /tmp directory for Vercel
DB_PATH = Path("/tmp/tilts_db")
DB_PATH.mkdir(exist_ok=True)

# Database "tables" as JSON files
SESSIONS_FILE = DB_PATH / "sessions.json"
GAMES_FILE = DB_PATH / "games.json"
LEADERBOARD_FILE = DB_PATH / "leaderboard.json"
TASKS_FILE = DB_PATH / "benchmark_tasks.json"
EVALUATIONS_FILE = DB_PATH / "evaluations.json"
PROMPTS_FILE = DB_PATH / "prompts.json"
SETTINGS_FILE = DB_PATH / "settings.json"

# JSON operations with caching
@lru_cache(maxsize=10)
def load_json_cached(file_path: str, default: Any = None) -> Any:
    """Load JSON file with caching."""
    file_path = Path(file_path)
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return default if default is not None else {}

def save_json(file_path: Path, data: Any):
    """Save data to JSON file and invalidate cache."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    # Invalidate cache for this file
    load_json_cached.cache_clear()

# Session Management (Optimized)
@with_monitoring("create_session")
def create_session(session_data: Dict[str, Any]) -> str:
    """Create a new session."""
    if not HAS_SUPABASE:
        sessions = load_json_cached(str(SESSIONS_FILE), {})
        session_id = str(uuid.uuid4())
        session_data['id'] = session_id
        session_data['created_at'] = datetime.utcnow().isoformat()
        sessions[session_id] = session_data
        save_json(SESSIONS_FILE, sessions)
        return session_id
    
    with get_supabase_client() as client:
        session_id = session_data.get('id', str(uuid.uuid4()))
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
        
        result = client.table('sessions').insert(data).execute()
        
        # Invalidate sessions cache
        cache.invalidate_pattern('list_sessions')
        
        return result.data[0]['id'] if result.data else session_id

@with_cache(ttl=60)
@with_monitoring("get_session")
def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID or join code."""
    if not HAS_SUPABASE:
        sessions = load_json_cached(str(SESSIONS_FILE), {})
        # Check by ID
        if session_id in sessions:
            return sessions[session_id]
        # Check by join code
        for session in sessions.values():
            if session.get('join_code', '').upper() == session_id.upper():
                return session
        return None
    
    with get_supabase_client() as client:
        # Try by ID first
        result = client.table('sessions').select('*').eq('id', session_id).execute()
        if result.data:
            return result.data[0]
        
        # Try by join code
        result = client.table('sessions').select('*').eq('join_code', session_id.upper()).execute()
        return result.data[0] if result.data else None

# Leaderboard Management (Heavily Optimized)
@with_monitoring("batch_update_leaderboard")
def batch_update_leaderboard(game_results: List[Dict[str, Any]]):
    """Batch update leaderboard entries for multiple games."""
    if not HAS_SUPABASE:
        # JSON implementation
        leaderboard = load_json_cached(str(LEADERBOARD_FILE), {})
        
        for result in game_results:
            model_name = result.get('model_name')
            if not model_name:
                continue
                
            if model_name not in leaderboard:
                leaderboard[model_name] = {
                    'model_name': model_name,
                    'games_played': 0,
                    'wins': 0,
                    'losses': 0,
                    'total_moves': 0,
                    'valid_moves': 0,
                    'mines_identified': 0,
                    'mines_total': 0
                }
            
            entry = leaderboard[model_name]
            entry['games_played'] += 1
            if result.get('won'):
                entry['wins'] += 1
            else:
                entry['losses'] += 1
            
            entry['total_moves'] += result.get('total_moves', 0)
            entry['valid_moves'] += result.get('valid_moves', 0)
            entry['mines_identified'] += result.get('mines_identified', 0)
            entry['mines_total'] += result.get('mines_total', 0)
            
            # Calculate rates
            if entry['games_played'] > 0:
                entry['win_rate'] = entry['wins'] / entry['games_played']
            if entry['total_moves'] > 0:
                entry['valid_move_rate'] = entry['valid_moves'] / entry['total_moves']
            if entry['mines_total'] > 0:
                entry['mine_identification_precision'] = entry['mines_identified'] / entry['mines_total']
        
        save_json(LEADERBOARD_FILE, leaderboard)
        cache.delete('get_leaderboard')
        return
    
    with get_supabase_client() as client:
        # Group results by model
        model_updates = defaultdict(lambda: {
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'total_moves': 0,
            'valid_moves': 0,
            'mines_identified': 0,
            'mines_total': 0
        })
        
        for result in game_results:
            model_name = result.get('model_name')
            if not model_name:
                continue
            
            update = model_updates[model_name]
            update['games_played'] += 1
            if result.get('won'):
                update['wins'] += 1
            else:
                update['losses'] += 1
            
            update['total_moves'] += result.get('total_moves', 0)
            update['valid_moves'] += result.get('valid_moves', 0)
            update['mines_identified'] += result.get('mines_identified', 0)
            update['mines_total'] += result.get('mines_total', 0)
        
        # Fetch existing entries in one query
        model_names = list(model_updates.keys())
        existing = client.table('leaderboard_entries').select('*').in_('model_name', model_names).execute()
        existing_map = {e['model_name']: e for e in (existing.data or [])}
        
        updates_to_perform = []
        inserts_to_perform = []
        
        for model_name, update in model_updates.items():
            if model_name in existing_map:
                # Update existing entry
                entry = existing_map[model_name]
                entry['games_played'] += update['games_played']
                entry['wins'] += update['wins']
                entry['losses'] += update['losses']
                entry['total_moves'] += update['total_moves']
                entry['valid_moves'] += update['valid_moves']
                entry['mines_identified'] += update['mines_identified']
                entry['mines_total'] += update['mines_total']
                
                # Calculate rates
                if entry['games_played'] > 0:
                    entry['win_rate'] = entry['wins'] / entry['games_played']
                if entry['total_moves'] > 0:
                    entry['valid_move_rate'] = entry['valid_moves'] / entry['total_moves']
                if entry['mines_total'] > 0:
                    entry['mine_identification_precision'] = entry['mines_identified'] / entry['mines_total']
                
                updates_to_perform.append(entry)
            else:
                # Create new entry
                entry = {
                    'model_name': model_name,
                    'games_played': update['games_played'],
                    'wins': update['wins'],
                    'losses': update['losses'],
                    'total_moves': update['total_moves'],
                    'valid_moves': update['valid_moves'],
                    'mines_identified': update['mines_identified'],
                    'mines_total': update['mines_total'],
                    'win_rate': update['wins'] / update['games_played'] if update['games_played'] > 0 else 0,
                    'valid_move_rate': update['valid_moves'] / update['total_moves'] if update['total_moves'] > 0 else 0,
                    'mine_identification_precision': update['mines_identified'] / update['mines_total'] if update['mines_total'] > 0 else 0
                }
                inserts_to_perform.append(entry)
        
        # Perform batch operations
        if updates_to_perform:
            for entry in updates_to_perform:
                client.table('leaderboard_entries').update(entry).eq('model_name', entry['model_name']).execute()
        
        if inserts_to_perform:
            client.table('leaderboard_entries').insert(inserts_to_perform).execute()
        
        # Invalidate leaderboard cache
        cache.delete('get_leaderboard')

@with_cache(ttl=LEADERBOARD_CACHE_TTL)
@with_monitoring("get_leaderboard")
def get_leaderboard() -> List[Dict[str, Any]]:
    """Get leaderboard entries sorted by win rate."""
    if not HAS_SUPABASE:
        leaderboard = load_json_cached(str(LEADERBOARD_FILE), {})
        entries = list(leaderboard.values())
        return sorted(entries, key=lambda x: x.get('win_rate', 0), reverse=True)
    
    with get_supabase_client() as client:
        result = client.table('leaderboard_entries').select('*').order('win_rate', desc=True).execute()
        return result.data or []

# Game Management (Optimized)
@with_monitoring("list_games")
def list_games(session_id: Optional[str] = None, job_id: Optional[str] = None, 
               limit: int = 100, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    """List games with pagination and total count."""
    if not HAS_SUPABASE:
        games = load_json_cached(str(GAMES_FILE), {})
        games_list = list(games.values())
        
        # Filter
        if session_id:
            games_list = [g for g in games_list if g.get('session_id') == session_id]
        if job_id:
            games_list = [g for g in games_list if g.get('job_id') == job_id]
        
        # Sort by created_at
        games_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        total = len(games_list)
        return games_list[offset:offset + limit], total
    
    with get_supabase_client() as client:
        # Build query
        count_query = client.table('games').select('*', count='exact')
        data_query = client.table('games').select('*')
        
        if session_id:
            count_query = count_query.eq('session_id', session_id)
            data_query = data_query.eq('session_id', session_id)
        if job_id:
            count_query = count_query.eq('job_id', job_id)
            data_query = data_query.eq('job_id', job_id)
        
        # Get total count
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else 0
        
        # Get paginated data
        result = data_query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        return result.data or [], total

# Search Optimization
@with_cache(ttl=300)
@with_monitoring("search_prompts")
def search_prompts(query: str = "", game_type: Optional[str] = None, 
                  tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search prompts with optimized filtering."""
    if not HAS_SUPABASE:
        prompts = load_json_cached(str(PROMPTS_FILE), [])
        
        # Apply filters
        if query:
            query_lower = query.lower()
            prompts = [p for p in prompts if 
                      query_lower in p.get('name', '').lower() or
                      query_lower in p.get('description', '').lower() or
                      query_lower in p.get('content', '').lower()]
        
        if game_type:
            prompts = [p for p in prompts if p.get('game_type') == game_type]
        
        if tags:
            prompts = [p for p in prompts if 
                      any(tag in p.get('tags', []) for tag in tags)]
        
        return sorted(prompts, key=lambda x: x.get('likes', 0), reverse=True)
    
    with get_supabase_client() as client:
        # Build optimized query
        query_builder = client.table('prompts').select('*')
        
        if game_type:
            query_builder = query_builder.eq('game_type', game_type)
        
        if query:
            # Use full-text search if available, otherwise filter client-side
            query_builder = query_builder.ilike('name', f'%{query}%')
        
        result = query_builder.order('likes', desc=True).execute()
        prompts = result.data or []
        
        # Client-side filtering for tags (if needed)
        if tags:
            prompts = [p for p in prompts if 
                      any(tag in p.get('tags', []) for tag in tags)]
        
        return prompts

# Performance monitoring endpoint
def get_db_stats() -> Dict[str, Any]:
    """Get database performance statistics."""
    return {
        'query_stats': query_monitor.get_stats(),
        'cache_info': {
            'size': len(cache._cache),
            'ttl': CACHE_TTL,
            'leaderboard_ttl': LEADERBOARD_CACHE_TTL
        },
        'connection_pool': {
            'size': CONNECTION_POOL_SIZE,
            'available': len(supabase_pool) if HAS_SUPABASE else 0
        },
        'has_supabase': HAS_SUPABASE
    }

# Export all functions
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
    'batch_update_leaderboard',
    'get_leaderboard',
    'create_evaluation',
    'get_evaluation',
    'list_evaluations',
    'save_prompt',
    'search_prompts',
    'get_settings',
    'update_settings',
    'get_db_stats',
    'cache',
    'query_monitor'
]

# Import remaining functions from original module for compatibility
from supabase_db import (
    update_session, list_sessions, create_game, get_game, update_game,
    create_evaluation, get_evaluation, list_evaluations,
    save_prompt, get_settings, update_settings,
    update_leaderboard  # Keep for single updates
)