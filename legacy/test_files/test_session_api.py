#!/usr/bin/env python3
"""Test session API endpoints."""

import asyncio
import httpx
import json

async def test_session_api():
    """Test the session creation and management API."""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Create a session
        print("1. Creating a competition session...")
        create_data = {
            "name": "Test Minesweeper Competition",
            "description": "minesweeper competition",
            "format": "single_round",
            "rounds_config": [{
                "game_name": "minesweeper",
                "difficulty": "medium",
                "mode": "mixed",
                "scoring_profile": "balanced",
                "time_limit": 300
            }],
            "creator_id": "test-user-123",
            "max_players": 20,
            "is_public": True,
            "flow_mode": "asynchronous"
        }
        
        response = await client.post(
            f"{base_url}/api/sessions/create",
            json=create_data,
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            session_id = result["session_id"]
            join_code = result["join_code"]
            print(f"✓ Session created! ID: {session_id}, Join Code: {join_code}")
            
            # Test 2: Get lobby status
            print("\n2. Getting lobby status...")
            lobby_response = await client.get(f"{base_url}/api/sessions/{session_id}/lobby")
            print(f"Lobby data: {json.dumps(lobby_response.json(), indent=2)}")
            
            # Test 3: Join session
            print("\n3. Joining session with another player...")
            join_data = {
                "join_code": join_code,
                "player_id": "player-456",
                "player_name": "AI Player 2",
                "ai_model": "gpt-4"
            }
            
            join_response = await client.post(
                f"{base_url}/api/sessions/join",
                json=join_data
            )
            print(f"Join response: {join_response.json()}")
            
            # Test 4: Get updated lobby
            print("\n4. Getting updated lobby...")
            lobby_response = await client.get(f"{base_url}/api/sessions/{session_id}/lobby")
            lobby_data = lobby_response.json()
            print(f"Players in lobby: {len(lobby_data['players'])}")
            for player in lobby_data['players']:
                print(f"  - {player['name']} ({player['ai_model']}) - Ready: {player['is_ready']}")
            
            # Test 5: Get quick match templates
            print("\n5. Getting quick match templates...")
            templates_response = await client.get(f"{base_url}/api/sessions/templates/quick-match")
            templates = templates_response.json()
            print(f"Available templates: {len(templates)}")
            for template in templates:
                print(f"  - {template['name']} ({template['game']})")
                
        else:
            print(f"✗ Failed to create session: {response.status_code}")
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_session_api())