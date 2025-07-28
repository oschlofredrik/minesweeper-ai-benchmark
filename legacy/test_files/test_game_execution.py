#!/usr/bin/env python3
"""Test end-to-end game execution on the deployed platform."""

import requests
import json
import time
import sys

# Use the deployed URL
BASE_URL = "https://tilts.vercel.app"

def test_play_endpoint():
    """Test the /api/play endpoint."""
    print("1. Testing /api/play endpoint...")
    
    payload = {
        "game": "minesweeper",
        "model": "gpt-4",
        "provider": "openai",
        "num_games": 1,
        "difficulty": "easy"
    }
    
    response = requests.post(f"{BASE_URL}/api/play", json=payload)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Job ID: {data.get('job_id')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Games: {data.get('games')}")
        return data.get('job_id')
    else:
        print(f"   Error: {response.text}")
        return None

def test_game_status(job_id):
    """Test the game status endpoint."""
    print(f"\n2. Testing /api/play/games/{job_id} endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/play/games/{job_id}")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Job Status: {data.get('status')}")
        print(f"   Total Games: {data.get('total_games')}")
        print(f"   Completed: {data.get('completed_games')}")
        if data.get('games'):
            print(f"   First Game: {data['games'][0]}")
    else:
        print(f"   Error: {response.text}")

def test_run_game_endpoint():
    """Test the /api/run_game endpoint."""
    print("\n3. Testing /api/run_game endpoint...")
    
    payload = {
        "game_id": "test-game-123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/run_game", json=payload)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Game Status: {data.get('status')}")
            print(f"   Won: {data.get('won')}")
            print(f"   Total Moves: {data.get('total_moves')}")
            print(f"   Valid Moves: {data.get('valid_moves')}")
            print(f"   Duration: {data.get('duration'):.2f}s")
            if data.get('moves'):
                print(f"   First Move: {data['moves'][0]}")
        else:
            print(f"   Error: {response.text}")
            # Try to see if it's a routing issue
            print(f"   Note: This endpoint may still be deploying on Vercel")
    except Exception as e:
        print(f"   Exception: {str(e)}")

def test_sessions_endpoint():
    """Test the sessions endpoints."""
    print("\n4. Testing /api/sessions endpoints...")
    
    # Create a session
    payload = {
        "name": "Test Session",
        "game_type": "minesweeper",
        "max_players": 10,
        "creator_id": "test-user",
        "creator_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/api/sessions/create", json=payload)
    print(f"   Create Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Join Code: {data.get('join_code')}")
        
        # List sessions
        response = requests.get(f"{BASE_URL}/api/sessions?active=true")
        print(f"   List Status: {response.status_code}")
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            print(f"   Active Sessions: {len(sessions)}")
    else:
        print(f"   Error: {response.text}")

def test_leaderboard_endpoint():
    """Test the leaderboard endpoint."""
    print("\n5. Testing /api/leaderboard endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/leaderboard")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        entries = data.get('entries', [])
        print(f"   Entries: {len(entries)}")
        if entries:
            print(f"   Top Entry: {entries[0].get('model_name')} - Win Rate: {entries[0].get('win_rate')}")
    else:
        print(f"   Error: {response.text}")

def main():
    """Run all tests."""
    print("Testing Tilts Platform End-to-End Game Execution")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Test play endpoint
    job_id = test_play_endpoint()
    
    # Test game status if we got a job ID
    if job_id:
        # Wait a bit
        time.sleep(1)
        test_game_status(job_id)
    
    # Test run game endpoint
    test_run_game_endpoint()
    
    # Test sessions
    test_sessions_endpoint()
    
    # Test leaderboard
    test_leaderboard_endpoint()
    
    print("\n" + "=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    main()