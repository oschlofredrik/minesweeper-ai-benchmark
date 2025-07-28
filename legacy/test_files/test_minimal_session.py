#!/usr/bin/env python3
"""Minimal test to debug session creation."""

import requests
import json

url = "https://minesweeper-ai-benchmark.onrender.com/api/sessions/create"

data = {
    "name": "Debug Test",
    "description": "test",
    "format": "single_round",
    "rounds_config": [{"game_name": "minesweeper", "difficulty": "beginner"}],
    "creator_id": "test-001",
    "max_players": 2
}

print("Sending request to:", url)
print("Data:", json.dumps(data, indent=2))

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 500:
        # Try to get more error details
        print("\nTrying to get server logs...")
        
except Exception as e:
    print(f"Error: {e}")