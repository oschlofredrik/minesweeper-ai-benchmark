#!/usr/bin/env python3
"""
Migrate existing JSON data to Supabase database.

Usage:
    python migrate-to-supabase.py [--dry-run]
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add the api directory to path
sys.path.insert(0, str(Path(__file__).parent / 'api'))

def migrate_data(dry_run=False):
    """Migrate JSON data to Supabase."""
    
    # Import both database modules
    try:
        from api import db as json_db
        from api import supabase_db
        
        if not supabase_db.HAS_SUPABASE:
            print("❌ Supabase not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY")
            return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have supabase package installed: pip install supabase")
        return False
    
    print("🚀 Starting data migration to Supabase...")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be written")
    
    # Statistics
    stats = {
        'sessions': {'total': 0, 'migrated': 0, 'errors': 0},
        'games': {'total': 0, 'migrated': 0, 'errors': 0},
        'evaluations': {'total': 0, 'migrated': 0, 'errors': 0},
        'prompts': {'total': 0, 'migrated': 0, 'errors': 0},
        'leaderboard': {'total': 0, 'migrated': 0, 'errors': 0}
    }
    
    # 1. Migrate Sessions
    print("\n📋 Migrating sessions...")
    try:
        sessions = json_db.load_json(json_db.SESSIONS_FILE, {})
        stats['sessions']['total'] = len(sessions)
        
        for session_id, session_data in sessions.items():
            try:
                if not dry_run:
                    # Ensure ID is set
                    session_data['id'] = session_id
                    # Use Supabase upsert to avoid duplicates
                    supabase_db.supabase.table('sessions').upsert(session_data).execute()
                stats['sessions']['migrated'] += 1
                print(f"  ✓ Session {session_id}")
            except Exception as e:
                stats['sessions']['errors'] += 1
                print(f"  ✗ Session {session_id}: {e}")
    except Exception as e:
        print(f"  ✗ Error loading sessions: {e}")
    
    # 2. Migrate Games
    print("\n🎮 Migrating games...")
    try:
        games = json_db.load_json(json_db.GAMES_FILE, {})
        stats['games']['total'] = len(games)
        
        for game_id, game_data in games.items():
            try:
                if not dry_run:
                    game_data['id'] = game_id
                    supabase_db.supabase.table('games').upsert(game_data).execute()
                stats['games']['migrated'] += 1
                print(f"  ✓ Game {game_id}")
            except Exception as e:
                stats['games']['errors'] += 1
                print(f"  ✗ Game {game_id}: {e}")
    except Exception as e:
        print(f"  ✗ Error loading games: {e}")
    
    # 3. Migrate Leaderboard
    print("\n🏆 Migrating leaderboard...")
    try:
        leaderboard = json_db.load_json(json_db.LEADERBOARD_FILE, {})
        stats['leaderboard']['total'] = len(leaderboard)
        
        for model_name, entry_data in leaderboard.items():
            try:
                if not dry_run:
                    entry_data['model_name'] = model_name
                    supabase_db.supabase.table('leaderboard_entries').upsert(entry_data).execute()
                stats['leaderboard']['migrated'] += 1
                print(f"  ✓ Leaderboard entry: {model_name}")
            except Exception as e:
                stats['leaderboard']['errors'] += 1
                print(f"  ✗ Leaderboard entry {model_name}: {e}")
    except Exception as e:
        print(f"  ✗ Error loading leaderboard: {e}")
    
    # 4. Migrate Evaluations
    print("\n📊 Migrating evaluations...")
    try:
        evaluations = json_db.load_json(json_db.EVALUATIONS_FILE, {})
        stats['evaluations']['total'] = len(evaluations)
        
        for eval_id, eval_data in evaluations.items():
            try:
                if not dry_run:
                    eval_data['id'] = eval_id
                    supabase_db.supabase.table('evaluations').upsert(eval_data).execute()
                stats['evaluations']['migrated'] += 1
                print(f"  ✓ Evaluation {eval_id}")
            except Exception as e:
                stats['evaluations']['errors'] += 1
                print(f"  ✗ Evaluation {eval_id}: {e}")
    except Exception as e:
        print(f"  ✗ Error loading evaluations: {e}")
    
    # 5. Migrate Prompts
    print("\n📝 Migrating prompts...")
    try:
        prompts = json_db.load_json(json_db.PROMPTS_FILE, {})
        stats['prompts']['total'] = len(prompts)
        
        for prompt_id, prompt_data in prompts.items():
            try:
                if not dry_run:
                    prompt_data['id'] = prompt_id
                    supabase_db.supabase.table('prompts').upsert(prompt_data).execute()
                stats['prompts']['migrated'] += 1
                print(f"  ✓ Prompt {prompt_id}")
            except Exception as e:
                stats['prompts']['errors'] += 1
                print(f"  ✗ Prompt {prompt_id}: {e}")
    except Exception as e:
        print(f"  ✗ Error loading prompts: {e}")
    
    # 6. Migrate Settings
    print("\n⚙️ Migrating settings...")
    try:
        settings = json_db.get_settings()
        for key, value in settings.items():
            if not dry_run:
                supabase_db.supabase.table('settings').upsert({
                    'key': key,
                    'value': value
                }).execute()
            print(f"  ✓ Setting: {key}")
    except Exception as e:
        print(f"  ✗ Error migrating settings: {e}")
    
    # Print summary
    print("\n" + "="*50)
    print("📊 MIGRATION SUMMARY")
    print("="*50)
    
    total_items = sum(s['total'] for s in stats.values())
    total_migrated = sum(s['migrated'] for s in stats.values())
    total_errors = sum(s['errors'] for s in stats.values())
    
    for category, stat in stats.items():
        if stat['total'] > 0:
            success_rate = (stat['migrated'] / stat['total']) * 100
            print(f"\n{category.upper()}:")
            print(f"  Total: {stat['total']}")
            print(f"  Migrated: {stat['migrated']} ({success_rate:.1f}%)")
            print(f"  Errors: {stat['errors']}")
    
    print(f"\nTOTAL:")
    print(f"  Items: {total_items}")
    print(f"  Migrated: {total_migrated}")
    print(f"  Errors: {total_errors}")
    
    if dry_run:
        print("\n🔍 This was a DRY RUN - no data was actually migrated")
        print("Run without --dry-run to perform the actual migration")
    else:
        print(f"\n✅ Migration completed at {datetime.now().isoformat()}")
    
    return total_errors == 0

def main():
    parser = argparse.ArgumentParser(description='Migrate JSON data to Supabase')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be migrated without actually doing it')
    args = parser.parse_args()
    
    # Check environment variables
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_ANON_KEY'):
        print("⚠️  SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
        print("   You can create a .env file with these values")
        sys.exit(1)
    
    # Load .env file if it exists
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        print("📄 Loading environment from .env file")
        from dotenv import load_dotenv
        load_dotenv()
    
    # Run migration
    success = migrate_data(dry_run=args.dry_run)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()