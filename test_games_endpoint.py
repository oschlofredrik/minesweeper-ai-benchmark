#!/usr/bin/env python3
"""Test the games endpoint issue."""

import requests

url = "https://minesweeper-ai-benchmark.onrender.com/api/games"

print(f"Testing {url}...")
try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")