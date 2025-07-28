#!/usr/bin/env python3
"""Test starting a competition."""

import asyncio
import httpx
import json

async def test_competition_start():
    """Test creating and starting a simple competition."""
    
    base_url = "https://minesweeper-ai-benchmark.onrender.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create session
        print("1. Creating session...")
        session_data = {
            "name": "Quick Competition Test",
            "description": "Testing competition start",
            "format": "single_round",
            "rounds_config": [{
                "game_name": "minesweeper",
                "difficulty": "beginner"
            }],
            "creator_id": "test-host-123",
            "max_players": 2
        }
        
        response = await client.post(f"{base_url}/api/sessions/create", json=session_data)
        if response.status_code != 200:
            print(f"❌ Failed to create session: {response.text}")
            return
            
        result = response.json()
        session_id = result["session_id"]
        join_code = result["join_code"]
        print(f"✅ Session created: {session_id} (Join: {join_code})")
        
        # 2. Join as second player
        print("\n2. Joining as second player...")
        join_data = {
            "join_code": join_code,
            "player_id": "test-player-456",
            "player_name": "AI Player 2",
            "ai_model": "gpt-4o-mini"
        }
        
        response = await client.post(f"{base_url}/api/sessions/join", json=join_data)
        if response.status_code != 200:
            print(f"❌ Failed to join: {response.text}")
            return
        print("✅ Player 2 joined")
        
        # 3. Set both players ready
        print("\n3. Setting players ready...")
        
        # Host ready
        response = await client.post(
            f"{base_url}/api/sessions/{session_id}/ready",
            params={"player_id": "test-host-123", "ready": True}
        )
        print("✅ Host ready")
        
        # Player 2 ready
        response = await client.post(
            f"{base_url}/api/sessions/{session_id}/ready",
            params={"player_id": "test-player-456", "ready": True}
        )
        result = response.json()
        print(f"✅ Player 2 ready (Can start: {result.get('can_start', False)})")
        
        # 4. Start competition
        print("\n4. Starting competition...")
        response = await client.post(
            f"{base_url}/api/sessions/{session_id}/start",
            params={"player_id": "test-host-123"}
        )
        
        if response.status_code == 200:
            print("✅ Competition started successfully!")
            print("\n5. Checking status...")
            
            # Check status
            response = await client.get(f"{base_url}/api/sessions/{session_id}/status")
            status = response.json()
            print(f"Status: {status['status']}")
            print(f"Players: {', '.join(status['players'])}")
            
            print(f"\n🎮 Competition is running!")
            print(f"Monitor at: {base_url}/api/sessions/{session_id}/status")
            
        else:
            print(f"❌ Failed to start: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_competition_start())