#!/usr/bin/env python3
"""
Migration script to move data from current system to serverless architecture
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import psycopg2
from supabase import create_client, Client
import requests

# Configuration
RENDER_DB_URL = os.getenv("RENDER_DATABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

class DataMigrator:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.render_conn = psycopg2.connect(RENDER_DB_URL) if RENDER_DB_URL else None
    
    async def migrate_leaderboard(self):
        """Migrate leaderboard entries"""
        print("Migrating leaderboard entries...")
        
        if self.render_conn:
            cursor = self.render_conn.cursor()
            cursor.execute("SELECT * FROM leaderboard_entries")
            entries = cursor.fetchall()
            
            # Transform and insert to Supabase
            for entry in entries:
                data = {
                    "model_name": entry[1],
                    "global_score": entry[2],
                    "games_played": entry[3],
                    "win_rate": entry[4],
                    "created_at": entry[5].isoformat() if entry[5] else None
                }
                
                self.supabase.table("leaderboard").insert(data).execute()
            
            print(f"✅ Migrated {len(entries)} leaderboard entries")
    
    async def migrate_games(self):
        """Migrate game history"""
        print("Migrating game history...")
        
        # Load from file storage if exists
        games_dir = "../data/results"
        if os.path.exists(games_dir):
            game_files = [f for f in os.listdir(games_dir) if f.endswith('.json')]
            
            for game_file in game_files:
                with open(os.path.join(games_dir, game_file), 'r') as f:
                    game_data = json.load(f)
                
                # Transform game data
                transformed = {
                    "id": game_data.get("job_id"),
                    "model_name": game_data.get("model_name"),
                    "game_state": game_data.get("final_board_state"),
                    "moves": game_data.get("moves", []),
                    "status": game_data.get("status"),
                    "started_at": game_data.get("start_time"),
                    "completed_at": game_data.get("end_time"),
                    "metadata": {
                        "win_rate": game_data.get("win_rate"),
                        "total_moves": game_data.get("total_moves"),
                        "valid_moves": game_data.get("valid_moves")
                    }
                }
                
                self.supabase.table("games").insert(transformed).execute()
            
            print(f"✅ Migrated {len(game_files)} games")
    
    async def migrate_prompts(self):
        """Migrate prompt templates"""
        print("Migrating prompt templates...")
        
        prompts_dir = "../data/prompts"
        if os.path.exists(prompts_dir):
            prompt_files = [f for f in os.listdir(prompts_dir) if f.endswith('.json')]
            
            for prompt_file in prompt_files:
                with open(os.path.join(prompts_dir, prompt_file), 'r') as f:
                    prompt_data = json.load(f)
                
                # Insert to Supabase
                self.supabase.table("prompt_templates").insert({
                    "name": prompt_data.get("name"),
                    "description": prompt_data.get("description"),
                    "content": prompt_data.get("template"),
                    "variables": prompt_data.get("variables", []),
                    "category": "imported",
                    "created_at": datetime.now().isoformat()
                }).execute()
            
            print(f"✅ Migrated {len(prompt_files)} prompt templates")
    
    async def setup_realtime_subscriptions(self):
        """Set up Supabase real-time subscriptions"""
        print("Setting up real-time subscriptions...")
        
        # This would be done in the frontend/API
        subscription_config = {
            "tables": ["sessions", "session_players", "games"],
            "events": ["INSERT", "UPDATE", "DELETE"],
            "channels": {
                "sessions": "public:sessions",
                "players": "public:session_players",
                "games": "public:games"
            }
        }
        
        with open("realtime-config.json", "w") as f:
            json.dump(subscription_config, f, indent=2)
        
        print("✅ Real-time configuration created")
    
    async def run_migration(self):
        """Run all migrations"""
        print("Starting data migration...")
        
        try:
            await self.migrate_leaderboard()
            await self.migrate_games()
            await self.migrate_prompts()
            await self.setup_realtime_subscriptions()
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
        
        finally:
            if self.render_conn:
                self.render_conn.close()

if __name__ == "__main__":
    print("Tilts Platform Data Migration")
    print("============================")
    
    # Check environment
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase credentials in environment")
        print("Set SUPABASE_URL and SUPABASE_ANON_KEY")
        exit(1)
    
    # Run migration
    migrator = DataMigrator()
    asyncio.run(migrator.run_migration())