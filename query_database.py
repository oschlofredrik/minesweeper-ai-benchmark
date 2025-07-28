#!/usr/bin/env python3
"""
Query the Supabase database for game results and model performance data.
"""

import os
import json
from datetime import datetime
from collections import defaultdict

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Supabase credentials not found in environment variables.")
    print("Please set SUPABASE_URL and SUPABASE_ANON_KEY")
    exit(1)

try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except ImportError:
    print("Supabase library not installed. Installing...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'supabase'])
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def query_games():
    """Query all games from the database."""
    print("\nQuerying games table...")
    try:
        response = supabase.table('games').select('*').order('created_at', desc=True).execute()
        games = response.data if response.data else []
        print(f"Found {len(games)} games in database")
        
        # Analyze games by model and type
        model_stats = defaultdict(lambda: {
            'total': 0,
            'won': 0,
            'lost': 0,
            'error': 0,
            'in_progress': 0,
            'game_types': defaultdict(int),
            'moves': [],
            'durations': []
        })
        
        for game in games:
            model = game.get('model_name', 'unknown')
            status = game.get('status', 'unknown')
            game_type = game.get('game_name', 'minesweeper')
            
            model_stats[model]['total'] += 1
            model_stats[model]['game_types'][game_type] += 1
            
            if status == 'won':
                model_stats[model]['won'] += 1
            elif status == 'lost':
                model_stats[model]['lost'] += 1
            elif status == 'error':
                model_stats[model]['error'] += 1
            elif status == 'in_progress':
                model_stats[model]['in_progress'] += 1
            
            # Collect move counts and durations
            moves = game.get('moves', 0)
            if moves > 0:
                model_stats[model]['moves'].append(moves)
            
            duration = game.get('duration', 0)
            if duration > 0:
                model_stats[model]['durations'].append(duration)
        
        return games, model_stats
    except Exception as e:
        print(f"Error querying games: {e}")
        return [], {}

def query_leaderboard():
    """Query leaderboard entries."""
    print("\nQuerying leaderboard...")
    try:
        response = supabase.table('leaderboard_entries').select('*').order('win_rate', desc=True).execute()
        entries = response.data if response.data else []
        print(f"Found {len(entries)} leaderboard entries")
        return entries
    except Exception as e:
        print(f"Error querying leaderboard: {e}")
        return []

def generate_database_report(games, model_stats, leaderboard):
    """Generate a report from database data."""
    report = []
    report.append("# Database Performance Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\nDatabase: Supabase")
    report.append("\n" + "="*80 + "\n")
    
    # Games summary
    report.append("## Games Summary\n")
    total_games = len(games) if isinstance(games, list) else 0
    report.append(f"Total Games in Database: {total_games}")
    
    if total_games > 0:
        # Status distribution
        status_counts = defaultdict(int)
        for game in games:
            status_counts[game.get('status', 'unknown')] += 1
        
        report.append("\n### Game Status Distribution:")
        for status, count in sorted(status_counts.items()):
            percentage = (count / total_games * 100)
            report.append(f"- {status}: {count} ({percentage:.1f}%)")
        
        # Game type distribution
        game_type_counts = defaultdict(int)
        for game in games:
            game_type_counts[game.get('game_name', 'minesweeper')] += 1
        
        report.append("\n### Game Type Distribution:")
        for game_type, count in sorted(game_type_counts.items()):
            percentage = (count / total_games * 100)
            report.append(f"- {game_type}: {count} ({percentage:.1f}%)")
    
    report.append("\n" + "="*80 + "\n")
    
    # Model performance
    report.append("## Model Performance (from Games)\n")
    
    for model, stats in sorted(model_stats.items()):
        report.append(f"### {model}\n")
        report.append(f"**Total Games:** {stats['total']}")
        
        if stats['won'] + stats['lost'] > 0:
            win_rate = stats['won'] / (stats['won'] + stats['lost']) * 100
            report.append(f"**Win Rate:** {win_rate:.1f}% ({stats['won']}/{stats['won'] + stats['lost']})")
        
        report.append(f"**Game Outcomes:**")
        report.append(f"- Won: {stats['won']}")
        report.append(f"- Lost: {stats['lost']}")
        report.append(f"- Error: {stats['error']}")
        report.append(f"- In Progress: {stats['in_progress']}")
        
        if len(stats['game_types']) > 0:
            report.append(f"\n**Games by Type:**")
            for game_type, count in sorted(stats['game_types'].items()):
                report.append(f"- {game_type}: {count}")
        
        if stats['moves']:
            avg_moves = sum(stats['moves']) / len(stats['moves'])
            report.append(f"\n**Average Moves:** {avg_moves:.1f}")
        
        if stats['durations']:
            avg_duration = sum(stats['durations']) / len(stats['durations'])
            report.append(f"**Average Duration:** {avg_duration:.2f} seconds")
        
        report.append("\n" + "-"*40 + "\n")
    
    # Leaderboard
    if leaderboard:
        report.append("\n" + "="*80 + "\n")
        report.append("## Leaderboard\n")
        report.append("| Rank | Model | Games | Win Rate | MS-S Score | MS-I Score |")
        report.append("|------|-------|-------|----------|------------|------------|")
        
        for i, entry in enumerate(leaderboard[:10], 1):
            model = entry.get('model_name', 'unknown')
            games = entry.get('total_games', 0)
            win_rate = entry.get('win_rate', 0) * 100
            ms_s = entry.get('ms_s_score', 0)
            ms_i = entry.get('ms_i_score', 0)
            
            report.append(f"| {i} | {model} | {games} | {win_rate:.1f}% | {ms_s:.3f} | {ms_i:.3f} |")
    
    # Find some interesting games to highlight
    report.append("\n" + "="*80 + "\n")
    report.append("## Notable Games\n")
    
    # Find completed games with high move counts
    if isinstance(games, list) and games:
        completed_games = [g for g in games if g.get('status') in ['won', 'lost'] and g.get('moves', 0) > 0]
    else:
        completed_games = []
    if completed_games:
        # Sort by move count
        completed_games.sort(key=lambda x: x.get('moves', 0), reverse=True)
        
        report.append("### Games with Most Moves:")
        for game in completed_games[:5]:
            model = game.get('model_name', 'unknown')
            moves = game.get('moves', 0)
            status = game.get('status', 'unknown')
            game_type = game.get('game_name', 'minesweeper')
            report.append(f"- {model} playing {game_type}: {moves} moves ({status})")
    
    # Find games by type
    if isinstance(games, list):
        risk_games = [g for g in games if g.get('game_name') == 'risk']
    else:
        risk_games = []
    if risk_games:
        report.append(f"\n### Risk Games Found: {len(risk_games)}")
        risk_won = sum(1 for g in risk_games if g.get('status') == 'won')
        report.append(f"- Won: {risk_won}")
        report.append(f"- Lost: {len(risk_games) - risk_won}")
    
    return "\n".join(report)

def main():
    """Main entry point."""
    print("Connecting to Supabase database...")
    
    # Query data
    games, model_stats = query_games()
    leaderboard = query_leaderboard()
    
    # Generate report
    if games or leaderboard:
        report = generate_database_report(games, model_stats, leaderboard)
        print("\n" + report)
        
        # Save report
        with open("database_analysis_report.md", "w") as f:
            f.write(report)
        print("\nReport saved to: database_analysis_report.md")
    else:
        print("\nNo data found in database.")

if __name__ == "__main__":
    main()