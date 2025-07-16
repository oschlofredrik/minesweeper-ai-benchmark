#!/usr/bin/env python3
"""Diagnose leaderboard issues - can be run on Render."""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.storage import get_storage
from src.core.config import settings

def diagnose():
    """Diagnose leaderboard issues."""
    print("🔍 Diagnosing Leaderboard Issues")
    print("=" * 50)
    
    # Check environment
    print("\n1️⃣ Environment Check:")
    print(f"   DATABASE_URL set: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")
    print(f"   Running on Render: {'Yes' if os.getenv('RENDER') else 'No'}")
    
    # Check storage backend
    print("\n2️⃣ Storage Backend:")
    storage = get_storage()
    print(f"   Using database: {storage.use_database}")
    
    # Check leaderboard
    print("\n3️⃣ Leaderboard Data:")
    try:
        leaderboard = storage.get_leaderboard()
        print(f"   Entries found: {len(leaderboard)}")
        
        if leaderboard:
            print("\n   Top 5 entries:")
            for i, entry in enumerate(leaderboard[:5]):
                print(f"   {i+1}. {entry.get('model_name', 'Unknown')}: "
                      f"{entry.get('win_rate', 0):.1%} win rate, "
                      f"{entry.get('total_games', 0)} games")
        else:
            print("   ⚠️  No leaderboard entries found!")
            
    except Exception as e:
        print(f"   ❌ Error getting leaderboard: {type(e).__name__}: {str(e)}")
    
    # Check result files
    print("\n4️⃣ Result Files:")
    results_dir = Path("data/results")
    if results_dir.exists():
        summary_files = list(results_dir.glob("*_summary.json"))
        print(f"   Summary files found: {len(summary_files)}")
        
        if summary_files:
            # Check recent files
            recent_files = sorted(summary_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            print("\n   Recent result files:")
            
            total_games = 0
            total_wins = 0
            
            for file in recent_files:
                try:
                    with open(file) as f:
                        data = json.load(f)
                    
                    model = data.get('model', {}).get('name', 'Unknown')
                    metrics = data.get('metrics', {})
                    win_rate = metrics.get('win_rate', 0)
                    games = len(data.get('per_game_metrics', []))
                    
                    print(f"   - {model}: {win_rate:.1%} win rate, {games} games")
                    
                    # Count actual games
                    for game in data.get('per_game_metrics', []):
                        if game.get('status') in ['won', 'lost']:
                            total_games += 1
                            if game.get('won'):
                                total_wins += 1
                                
                except Exception as e:
                    print(f"   - Error reading {file.name}: {e}")
            
            if total_games > 0:
                print(f"\n   Aggregate stats from files:")
                print(f"   - Total completed games: {total_games}")
                print(f"   - Total wins: {total_wins}")
                print(f"   - Overall win rate: {total_wins/total_games:.1%}")
            else:
                print("\n   ⚠️  No completed games found in result files!")
    else:
        print("   ❌ Results directory not found!")
    
    # Diagnosis
    print("\n5️⃣ Diagnosis:")
    
    if not storage.use_database:
        print("   ⚠️  Using file storage (database not available)")
        if not leaderboard:
            print("   ❌ File-based leaderboard computation not implemented")
            print("   💡 Fix: Implement _compute_leaderboard_from_files() method")
    else:
        if not leaderboard:
            print("   ❌ Database connected but leaderboard is empty")
            print("   💡 Fix: Check if games are being saved to database")
    
    # Check if games are running but not completing
    print("\n6️⃣ Game Completion Check:")
    transcript_files = list(results_dir.glob("*_transcripts.json")) if results_dir.exists() else []
    if transcript_files:
        recent_transcript = sorted(transcript_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        try:
            with open(recent_transcript) as f:
                transcripts = json.load(f)
            
            incomplete_games = [t for t in transcripts if t.get('final_status') == 'in_progress']
            if incomplete_games:
                print(f"   ⚠️  Found {len(incomplete_games)} incomplete games")
                print("   💡 Games are starting but not making moves")
        except:
            pass

if __name__ == "__main__":
    diagnose()