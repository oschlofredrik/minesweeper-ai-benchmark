#!/usr/bin/env python3
"""Migrate data from Render PostgreSQL to Supabase."""

import os
import json
import psycopg2
from datetime import datetime
from supabase import create_client, Client
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Render PostgreSQL connection
RENDER_DATABASE_URL = os.getenv("RENDER_DATABASE_URL")
if not RENDER_DATABASE_URL:
    print("Error: RENDER_DATABASE_URL not set in .env")
    print("Get it from Render dashboard > Database > Connection String")
    exit(1)

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: SUPABASE_URL or SUPABASE_ANON_KEY not set in .env")
    exit(1)

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def migrate_games():
    """Migrate games table."""
    print("\n=== Migrating Games ===")
    
    conn = psycopg2.connect(RENDER_DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Get all games from Render
        cur.execute("""
            SELECT id, job_id, game_type, difficulty, model_name, model_provider,
                   status, won, total_moves, valid_moves, duration, total_tokens,
                   moves, final_board_state, error_message, mines_identified,
                   mines_total, false_flags, coverage_ratio, territory_control,
                   total_armies, created_at, updated_at, full_transcript, task_id
            FROM games
            ORDER BY created_at
        """)
        
        games = cur.fetchall()
        print(f"Found {len(games)} games to migrate")
        
        # Migrate in batches
        batch_size = 50
        for i in range(0, len(games), batch_size):
            batch = games[i:i+batch_size]
            batch_data = []
            
            for game in batch:
                game_data = {
                    "id": game[0],
                    "job_id": game[1],
                    "game_type": game[2],
                    "difficulty": game[3],
                    "model_name": game[4],
                    "model_provider": game[5],
                    "status": game[6],
                    "won": game[7],
                    "total_moves": game[8],
                    "valid_moves": game[9],
                    "duration": game[10],
                    "total_tokens": game[11],
                    "moves": game[12] if game[12] else [],
                    "final_board_state": game[13] if game[13] else {},
                    "error_message": game[14],
                    "mines_identified": game[15],
                    "mines_total": game[16],
                    "false_flags": game[17],
                    "coverage_ratio": game[18],
                    "territory_control": game[19],
                    "total_armies": game[20],
                    "created_at": game[21].isoformat() if game[21] else None,
                    "updated_at": game[22].isoformat() if game[22] else None,
                    "full_transcript": game[23] if game[23] else {},
                    "task_id": game[24]
                }
                batch_data.append(game_data)
            
            # Insert batch into Supabase
            result = supabase.table("games").insert(batch_data).execute()
            print(f"Migrated games {i+1} to {min(i+batch_size, len(games))}")
            
    except Exception as e:
        print(f"Error migrating games: {e}")
    finally:
        cur.close()
        conn.close()

def migrate_leaderboard():
    """Migrate leaderboard entries."""
    print("\n=== Migrating Leaderboard ===")
    
    conn = psycopg2.connect(RENDER_DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Get all leaderboard entries
        cur.execute("""
            SELECT id, model_name, game_type, total_games, wins, losses,
                   win_rate, avg_moves, avg_duration, total_tokens,
                   avg_mines_identified, avg_coverage, created_at, updated_at
            FROM leaderboard_entries
            ORDER BY created_at
        """)
        
        entries = cur.fetchall()
        print(f"Found {len(entries)} leaderboard entries to migrate")
        
        for entry in entries:
            entry_data = {
                "id": entry[0],
                "model_name": entry[1],
                "game_type": entry[2],
                "total_games": entry[3],
                "wins": entry[4],
                "losses": entry[5],
                "win_rate": entry[6],
                "avg_moves": entry[7],
                "avg_duration": entry[8],
                "total_tokens": entry[9],
                "avg_mines_identified": entry[10],
                "avg_coverage": entry[11],
                "created_at": entry[12].isoformat() if entry[12] else None,
                "updated_at": entry[13].isoformat() if entry[13] else None
            }
            
            result = supabase.table("leaderboard_entries").insert(entry_data).execute()
            print(f"Migrated leaderboard entry for {entry[1]} ({entry[2]})")
            
    except Exception as e:
        print(f"Error migrating leaderboard: {e}")
    finally:
        cur.close()
        conn.close()

def migrate_evaluations():
    """Migrate evaluations."""
    print("\n=== Migrating Evaluations ===")
    
    conn = psycopg2.connect(RENDER_DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Check if evaluations table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'evaluations'
            )
        """)
        
        if not cur.fetchone()[0]:
            print("No evaluations table in Render database")
            return
        
        # Get all evaluations
        cur.execute("""
            SELECT id, name, description, author, config, version,
                   downloads, rating, tags, created_at, updated_at
            FROM evaluations
            ORDER BY created_at
        """)
        
        evaluations = cur.fetchall()
        print(f"Found {len(evaluations)} evaluations to migrate")
        
        for eval in evaluations:
            eval_data = {
                "id": eval[0],
                "name": eval[1],
                "description": eval[2],
                "author": eval[3],
                "config": eval[4] if eval[4] else {},
                "version": eval[5],
                "downloads": eval[6],
                "rating": eval[7],
                "tags": eval[8] if eval[8] else [],
                "created_at": eval[9].isoformat() if eval[9] else None,
                "updated_at": eval[10].isoformat() if eval[10] else None
            }
            
            result = supabase.table("evaluations").insert(eval_data).execute()
            print(f"Migrated evaluation: {eval[1]}")
            
    except Exception as e:
        print(f"Error migrating evaluations: {e}")
    finally:
        cur.close()
        conn.close()

def migrate_prompts():
    """Migrate prompts."""
    print("\n=== Migrating Prompts ===")
    
    conn = psycopg2.connect(RENDER_DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Check if prompts table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'prompts'
            )
        """)
        
        if not cur.fetchone()[0]:
            print("No prompts table in Render database")
            return
        
        # Get all prompts
        cur.execute("""
            SELECT id, name, description, content, tags, author,
                   game_type, model_type, performance_score,
                   created_at, updated_at
            FROM prompts
            ORDER BY created_at
        """)
        
        prompts = cur.fetchall()
        print(f"Found {len(prompts)} prompts to migrate")
        
        for prompt in prompts:
            prompt_data = {
                "id": prompt[0],
                "name": prompt[1],
                "description": prompt[2],
                "content": prompt[3],
                "tags": prompt[4] if prompt[4] else [],
                "author": prompt[5],
                "game_type": prompt[6],
                "model_type": prompt[7],
                "performance_score": prompt[8],
                "created_at": prompt[9].isoformat() if prompt[9] else None,
                "updated_at": prompt[10].isoformat() if prompt[10] else None
            }
            
            result = supabase.table("prompts").insert(prompt_data).execute()
            print(f"Migrated prompt: {prompt[1]}")
            
    except Exception as e:
        print(f"Error migrating prompts: {e}")
    finally:
        cur.close()
        conn.close()

def verify_migration():
    """Verify the migration was successful."""
    print("\n=== Verifying Migration ===")
    
    # Count records in Supabase
    games = supabase.table("games").select("id", count="exact").execute()
    leaderboard = supabase.table("leaderboard_entries").select("id", count="exact").execute()
    evaluations = supabase.table("evaluations").select("id", count="exact").execute()
    prompts = supabase.table("prompts").select("id", count="exact").execute()
    
    print(f"Supabase Games: {games.count}")
    print(f"Supabase Leaderboard: {leaderboard.count}")
    print(f"Supabase Evaluations: {evaluations.count}")
    print(f"Supabase Prompts: {prompts.count}")

def main():
    print("=== Render to Supabase Migration Tool ===")
    print(f"Source: Render PostgreSQL")
    print(f"Target: {SUPABASE_URL}")
    
    # Confirm before proceeding
    response = input("\nThis will migrate all data from Render to Supabase. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled")
        return
    
    # Run migrations
    migrate_games()
    migrate_leaderboard()
    migrate_evaluations()
    migrate_prompts()
    
    # Verify
    verify_migration()
    
    print("\n=== Migration Complete ===")
    print("Don't forget to update your application to use Supabase!")
    print("Your live URL: https://tilts.vercel.app/")

if __name__ == "__main__":
    main()