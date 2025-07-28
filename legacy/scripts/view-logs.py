#!/usr/bin/env python3
"""View and filter Tilts platform logs."""
import json
import sys
import argparse
from datetime import datetime
from typing import Optional, List, Dict

def parse_log_line(line: str) -> Optional[Dict]:
    """Parse a JSON log line."""
    try:
        return json.loads(line)
    except:
        return None

def format_log_entry(entry: Dict, format_type: str = 'pretty') -> str:
    """Format a log entry for display."""
    if format_type == 'json':
        return json.dumps(entry)
    
    # Pretty format
    timestamp = entry.get('timestamp', '')
    level = entry.get('level', 'INFO')
    message = entry.get('message', '')
    
    # Color codes for levels
    colors = {
        'ERROR': '\033[91m',  # Red
        'WARNING': '\033[93m',  # Yellow
        'INFO': '\033[92m',  # Green
        'DEBUG': '\033[94m',  # Blue
    }
    reset = '\033[0m'
    
    output = f"{colors.get(level, '')}{timestamp} [{level}]{reset} {message}"
    
    # Add context fields
    context_fields = ['game_id', 'model_name', 'game_type', 'job_id', 'session_id']
    context = []
    for field in context_fields:
        if field in entry:
            context.append(f"{field}={entry[field]}")
    
    if context:
        output += f" ({', '.join(context)})"
    
    # Add error details if present
    if 'error' in entry:
        error_info = entry['error']
        output += f"\n  Error: {error_info.get('type', 'Unknown')} - {error_info.get('message', '')}"
    
    return output

def filter_logs(logs: List[Dict], args) -> List[Dict]:
    """Filter logs based on command line arguments."""
    filtered = logs
    
    if args.level:
        filtered = [log for log in filtered if log.get('level') == args.level.upper()]
    
    if args.game_id:
        filtered = [log for log in filtered if log.get('game_id') == args.game_id]
    
    if args.model:
        filtered = [log for log in filtered if args.model in log.get('model_name', '')]
    
    if args.game_type:
        filtered = [log for log in filtered if log.get('game_type') == args.game_type]
    
    if args.job_id:
        filtered = [log for log in filtered if log.get('job_id') == args.job_id]
    
    if args.error_only:
        filtered = [log for log in filtered if 'error' in log or log.get('level') == 'ERROR']
    
    return filtered

def main():
    parser = argparse.ArgumentParser(description='View and filter Tilts logs')
    parser.add_argument('logfile', nargs='?', default='-', help='Log file to read (- for stdin)')
    parser.add_argument('--level', choices=['debug', 'info', 'warning', 'error'], help='Filter by log level')
    parser.add_argument('--game-id', help='Filter by game ID')
    parser.add_argument('--model', help='Filter by model name (partial match)')
    parser.add_argument('--game-type', choices=['minesweeper', 'risk'], help='Filter by game type')
    parser.add_argument('--job-id', help='Filter by job ID')
    parser.add_argument('--error-only', action='store_true', help='Show only errors')
    parser.add_argument('--format', choices=['pretty', 'json'], default='pretty', help='Output format')
    parser.add_argument('--tail', type=int, help='Show only last N entries')
    parser.add_argument('--follow', '-f', action='store_true', help='Follow log file (like tail -f)')
    
    args = parser.parse_args()
    
    # Read logs
    logs = []
    
    if args.logfile == '-':
        # Read from stdin
        for line in sys.stdin:
            entry = parse_log_line(line.strip())
            if entry:
                logs.append(entry)
    else:
        # Read from file
        try:
            with open(args.logfile, 'r') as f:
                for line in f:
                    entry = parse_log_line(line.strip())
                    if entry:
                        logs.append(entry)
        except FileNotFoundError:
            print(f"Error: Log file '{args.logfile}' not found")
            sys.exit(1)
    
    # Filter logs
    filtered_logs = filter_logs(logs, args)
    
    # Apply tail if specified
    if args.tail:
        filtered_logs = filtered_logs[-args.tail:]
    
    # Display logs
    for log in filtered_logs:
        print(format_log_entry(log, args.format))
    
    # Follow mode (basic implementation)
    if args.follow and args.logfile != '-':
        import time
        with open(args.logfile, 'r') as f:
            # Move to end of file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    entry = parse_log_line(line.strip())
                    if entry and filter_logs([entry], args):
                        print(format_log_entry(entry, args.format))
                else:
                    time.sleep(0.1)

if __name__ == '__main__':
    main()