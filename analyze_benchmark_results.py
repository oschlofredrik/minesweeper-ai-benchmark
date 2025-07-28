#!/usr/bin/env python3
"""
Comprehensive Benchmark Analysis Tool
Analyzes all game results and generates performance reports comparing AI models.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import statistics

class BenchmarkAnalyzer:
    def __init__(self, results_dir: str = "data/results"):
        self.results_dir = Path(results_dir)
        self.results = []
        self.model_stats = defaultdict(lambda: {
            'games': [],
            'total_games': 0,
            'completed_games': 0,
            'wins': 0,
            'losses': 0,
            'errors': 0,
            'total_moves': 0,
            'valid_moves': 0,
            'board_coverage': [],
            'durations': [],
            'mine_precision': [],
            'mine_recall': [],
            'game_types': defaultdict(int)
        })
    
    def load_results(self):
        """Load all result files from the results directory."""
        if not self.results_dir.exists():
            print(f"Results directory {self.results_dir} does not exist!")
            return
        
        # Load summary files
        for file_path in self.results_dir.glob("*_summary.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.results.append({
                        'file': file_path.name,
                        'type': 'summary',
                        'data': data
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Load play files
        for file_path in self.results_dir.glob("play_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.results.append({
                        'file': file_path.name,
                        'type': 'play',
                        'data': data
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    def analyze_results(self):
        """Analyze all loaded results and compile statistics."""
        for result in self.results:
            data = result['data']
            model_info = data.get('model', {})
            model_name = model_info.get('name', 'unknown')
            
            # Process game results
            game_results = data.get('game_results', [])
            for game in game_results:
                self.model_stats[model_name]['total_games'] += 1
                
                # Determine game type (default to minesweeper)
                game_type = game.get('game_type', 'minesweeper')
                self.model_stats[model_name]['game_types'][game_type] += 1
                
                # Check game status
                status = game.get('final_status', 'unknown')
                if status == 'won':
                    self.model_stats[model_name]['wins'] += 1
                    self.model_stats[model_name]['completed_games'] += 1
                elif status == 'lost':
                    self.model_stats[model_name]['losses'] += 1
                    self.model_stats[model_name]['completed_games'] += 1
                elif status == 'error':
                    self.model_stats[model_name]['errors'] += 1
                
                # Collect metrics
                num_moves = game.get('num_moves', 0)
                if num_moves > 0:
                    self.model_stats[model_name]['total_moves'] += num_moves
                    valid_rate = game.get('valid_move_rate', 0)
                    self.model_stats[model_name]['valid_moves'] += int(num_moves * valid_rate)
                
                # Board coverage
                coverage = game.get('board_coverage', 0)
                if coverage > 0:
                    self.model_stats[model_name]['board_coverage'].append(coverage)
                
                # Duration
                duration = game.get('duration', 0)
                if duration > 0:
                    self.model_stats[model_name]['durations'].append(duration)
                
                # Mine identification metrics
                if game_type == 'minesweeper':
                    precision = game.get('mine_precision', 0)
                    recall = game.get('mine_recall', 0)
                    if precision > 0:
                        self.model_stats[model_name]['mine_precision'].append(precision)
                    if recall > 0:
                        self.model_stats[model_name]['mine_recall'].append(recall)
    
    def generate_report(self) -> str:
        """Generate a comprehensive performance report."""
        report_lines = [
            "# AI Model Benchmark Performance Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nAnalyzed {len(self.results)} result files",
            "\n" + "="*80 + "\n"
        ]
        
        # Overall summary
        report_lines.append("## Overall Summary\n")
        total_games = sum(stats['total_games'] for stats in self.model_stats.values())
        total_models = len(self.model_stats)
        report_lines.append(f"- Total Models Evaluated: {total_models}")
        report_lines.append(f"- Total Games Played: {total_games}")
        
        # Game type distribution
        all_game_types = defaultdict(int)
        for stats in self.model_stats.values():
            for game_type, count in stats['game_types'].items():
                all_game_types[game_type] += count
        
        report_lines.append(f"\n### Game Type Distribution:")
        for game_type, count in sorted(all_game_types.items()):
            percentage = (count / total_games * 100) if total_games > 0 else 0
            report_lines.append(f"- {game_type.capitalize()}: {count} games ({percentage:.1f}%)")
        
        report_lines.append("\n" + "="*80 + "\n")
        
        # Model-specific analysis
        report_lines.append("## Model Performance Analysis\n")
        
        for model_name, stats in sorted(self.model_stats.items()):
            report_lines.append(f"### {model_name}\n")
            
            # Basic statistics
            total = stats['total_games']
            completed = stats['completed_games']
            wins = stats['wins']
            losses = stats['losses']
            errors = stats['errors']
            
            report_lines.append(f"**Games Played:** {total}")
            
            if completed > 0:
                win_rate = wins / completed * 100
                report_lines.append(f"**Win Rate:** {win_rate:.1f}% ({wins}/{completed} completed games)")
            else:
                report_lines.append(f"**Win Rate:** No completed games")
            
            if errors > 0:
                report_lines.append(f"**Error Rate:** {errors/total*100:.1f}% ({errors} errors)")
            
            # Game type breakdown
            if len(stats['game_types']) > 1:
                report_lines.append(f"\n**Performance by Game Type:**")
                for game_type, count in sorted(stats['game_types'].items()):
                    report_lines.append(f"- {game_type.capitalize()}: {count} games")
            
            # Move statistics
            if stats['total_moves'] > 0:
                valid_rate = stats['valid_moves'] / stats['total_moves'] * 100
                report_lines.append(f"\n**Move Statistics:**")
                report_lines.append(f"- Total Moves: {stats['total_moves']}")
                report_lines.append(f"- Valid Move Rate: {valid_rate:.1f}%")
            
            # Board coverage (for completed games)
            if stats['board_coverage']:
                avg_coverage = statistics.mean(stats['board_coverage'])
                report_lines.append(f"\n**Board Coverage:**")
                report_lines.append(f"- Average: {avg_coverage:.1f}%")
                if len(stats['board_coverage']) > 1:
                    report_lines.append(f"- Min: {min(stats['board_coverage']):.1f}%")
                    report_lines.append(f"- Max: {max(stats['board_coverage']):.1f}%")
            
            # Mine identification (Minesweeper specific)
            if stats['mine_precision']:
                report_lines.append(f"\n**Mine Identification (Minesweeper):**")
                report_lines.append(f"- Precision: {statistics.mean(stats['mine_precision']):.1f}%")
                report_lines.append(f"- Recall: {statistics.mean(stats['mine_recall']):.1f}%")
            
            # Timing
            if stats['durations']:
                avg_duration = statistics.mean(stats['durations'])
                report_lines.append(f"\n**Average Game Duration:** {avg_duration:.2f} seconds")
            
            report_lines.append("\n" + "-"*40 + "\n")
        
        # Comparative analysis
        if len(self.model_stats) > 1:
            report_lines.append("\n" + "="*80 + "\n")
            report_lines.append("## Comparative Analysis\n")
            
            # Create comparison table
            report_lines.append("### Performance Comparison Table\n")
            report_lines.append("| Model | Games | Win Rate | Valid Moves | Avg Duration |")
            report_lines.append("|-------|-------|----------|-------------|--------------|")
            
            for model_name, stats in sorted(self.model_stats.items()):
                games = stats['total_games']
                completed = stats['completed_games']
                win_rate = (stats['wins'] / completed * 100) if completed > 0 else 0
                valid_rate = (stats['valid_moves'] / stats['total_moves'] * 100) if stats['total_moves'] > 0 else 0
                avg_duration = statistics.mean(stats['durations']) if stats['durations'] else 0
                
                report_lines.append(
                    f"| {model_name} | {games} | {win_rate:.1f}% | {valid_rate:.1f}% | {avg_duration:.2f}s |"
                )
        
        # Key insights
        report_lines.append("\n" + "="*80 + "\n")
        report_lines.append("## Key Insights\n")
        
        # Find best performing model
        best_model = None
        best_win_rate = 0
        for model_name, stats in self.model_stats.items():
            if stats['completed_games'] > 0:
                win_rate = stats['wins'] / stats['completed_games']
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_model = model_name
        
        if best_model:
            report_lines.append(f"1. **Best Performing Model:** {best_model} with {best_win_rate*100:.1f}% win rate")
        
        # Note about incomplete data
        incomplete_games = sum(stats['total_games'] - stats['completed_games'] for stats in self.model_stats.values())
        if incomplete_games > 0:
            report_lines.append(f"\n2. **Data Quality Note:** {incomplete_games} games did not complete properly")
            report_lines.append("   - This may indicate technical issues during evaluation")
            report_lines.append("   - Consider re-running evaluations for affected models")
        
        # Game diversity
        if len(all_game_types) > 1:
            report_lines.append(f"\n3. **Game Diversity:** Models were tested on {len(all_game_types)} different game types")
            dominant_game = max(all_game_types.items(), key=lambda x: x[1])
            report_lines.append(f"   - Most common: {dominant_game[0].capitalize()} ({dominant_game[1]} games)")
        
        report_lines.append("\n" + "="*80 + "\n")
        
        return "\n".join(report_lines)
    
    def save_report(self, output_path: str = "benchmark_analysis_report.md"):
        """Save the report to a file."""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_path}")

def main():
    """Main entry point."""
    analyzer = BenchmarkAnalyzer()
    
    print("Loading benchmark results...")
    analyzer.load_results()
    
    print("Analyzing results...")
    analyzer.analyze_results()
    
    print("Generating report...")
    report = analyzer.generate_report()
    
    # Print report to console
    print("\n" + report)
    
    # Save report
    analyzer.save_report()

if __name__ == "__main__":
    main()