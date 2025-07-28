#!/usr/bin/env python3
"""Test the improved lobby functionality."""

import asyncio
import httpx
import json

async def test_lobby_improvements():
    """Test the enhanced lobby with instructions."""
    
    base_url = "https://minesweeper-ai-benchmark.onrender.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a session
        print("1. Creating a test session...")
        session_data = {
            "name": "Lobby Test Session",
            "description": "Testing improved lobby UI",
            "format": "single_round",
            "rounds_config": [{
                "game_name": "minesweeper",
                "difficulty": "beginner"
            }],
            "creator_id": "test-host-ui",
            "max_players": 4
        }
        
        response = await client.post(f"{base_url}/api/sessions/create", json=session_data)
        if response.status_code != 200:
            print(f"Failed to create session: {response.text}")
            return
            
        result = response.json()
        session_id = result["session_id"]
        join_code = result["join_code"]
        
        print(f"✅ Session created!")
        print(f"   Session ID: {session_id}")
        print(f"   Join Code: {join_code}")
        print(f"\n📎 Share this link to test the improved lobby:")
        print(f"   {base_url}/join/{join_code}")
        
        # Join as another player without AI model initially
        print(f"\n2. Testing join without AI model...")
        join_data = {
            "join_code": join_code,
            "player_id": "test-player-ui",
            "player_name": "Test Player",
            "ai_model": None  # Will select in lobby
        }
        
        response = await client.post(f"{base_url}/api/sessions/join", json=join_data)
        if response.status_code == 200:
            print("✅ Successfully joined without pre-selecting AI model")
        else:
            print(f"❌ Failed to join: {response.text}")
        
        # Get lobby status to show current state
        print(f"\n3. Current lobby status:")
        response = await client.get(f"{base_url}/api/sessions/{session_id}/lobby")
        if response.status_code == 200:
            lobby = response.json()
            print(f"   Players: {len(lobby['players'])}")
            for player in lobby['players']:
                model_info = player['ai_model'] or 'Not selected'
                ready_status = '✅ Ready' if player['is_ready'] else '⏳ Not ready'
                print(f"   - {player['name']}: {model_info} ({ready_status})")
        
        print(f"\n✨ The improved lobby now includes:")
        print("   - Clear instructions on how to play")
        print("   - Model selection dropdown")
        print("   - Ready/Unready toggle button")
        print("   - Host indicator and controls")
        print("   - Better visual organization")

if __name__ == "__main__":
    asyncio.run(test_lobby_improvements())