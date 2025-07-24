#!/usr/bin/env python3
"""Test script to verify new game-agnostic endpoints."""

import asyncio
from fastapi.testclient import TestClient
from src.api.main import app

def test_endpoints():
    """Test that new endpoints are available."""
    client = TestClient(app)
    
    # Test game endpoints
    endpoints = [
        ("/api/games/", "GET"),
        ("/api/games/modes/all", "GET"),
        ("/api/games/scoring-profiles", "GET"),
        ("/api/sessions/templates/quick-match", "GET"),
        ("/api/prompts/templates/analyze?prompt=test&game_name=minesweeper", "GET"),
        ("/api/sessions/queue/status", "GET"),
    ]
    
    print("Testing new game-agnostic endpoints:")
    print("-" * 50)
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            status = "✓" if response.status_code < 500 else "✗"
            print(f"{status} {method:6} {endpoint:40} - {response.status_code}")
            
            if response.status_code >= 500:
                print(f"  Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"✗ {method:6} {endpoint:40} - Error: {str(e)[:50]}")
    
    print("-" * 50)
    print("Endpoint testing complete!")

if __name__ == "__main__":
    test_endpoints()