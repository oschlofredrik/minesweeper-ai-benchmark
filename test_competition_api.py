#!/usr/bin/env python3
"""Test competition API endpoints individually."""

import asyncio
import httpx
import json
from datetime import datetime


async def test_api_endpoints():
    """Test each API endpoint."""
    base_url = "https://minesweeper-ai-benchmark.onrender.com"
    
    print("🧪 Testing Competition API Endpoints\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Create Session
        print("1. Testing POST /api/sessions/create")
        create_data = {
            "name": f"API Test Session {datetime.now().strftime('%H:%M:%S')}",
            "description": "Testing session creation",
            "format": "single_round",
            "rounds_config": [{
                "game_name": "minesweeper",
                "difficulty": "beginner",
                "mode": "mixed",
                "scoring_profile": "balanced",
                "time_limit": 300
            }],
            "creator_id": f"test-api-{datetime.now().timestamp()}",
            "max_players": 10,
            "is_public": True,
            "flow_mode": "asynchronous"
        }
        
        try:
            response = await client.post(f"{base_url}/api/sessions/create", json=create_data)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                session_id = result["session_id"]
                join_code = result["join_code"]
                print(f"   ✅ Session created: {session_id}")
                print(f"   Join code: {join_code}\n")
            else:
                print(f"   ❌ Error: {response.text}\n")
                return
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
            return
        
        # Test 2: Get Lobby Status
        print("2. Testing GET /api/sessions/{session_id}/lobby")
        try:
            response = await client.get(f"{base_url}/api/sessions/{session_id}/lobby")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                lobby = response.json()
                print(f"   ✅ Players: {len(lobby['players'])}")
                print(f"   Status: {lobby['status']}\n")
            else:
                print(f"   ❌ Error: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
        
        # Test 3: Join Session
        print("3. Testing POST /api/sessions/join")
        join_data = {
            "join_code": join_code,
            "player_id": "test-player-002",
            "player_name": "Test Player 2",
            "ai_model": "gpt-4o-mini"
        }
        
        try:
            response = await client.post(f"{base_url}/api/sessions/join", json=join_data)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Player joined successfully\n")
            else:
                print(f"   ❌ Error: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
        
        # Test 4: Set Ready Status
        print("4. Testing POST /api/sessions/{session_id}/ready")
        try:
            # Set host ready
            response = await client.post(
                f"{base_url}/api/sessions/{session_id}/ready",
                params={"player_id": create_data["creator_id"], "ready": True}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Host ready")
                print(f"   Can start: {result.get('can_start', False)}")
            else:
                print(f"   ❌ Error: {response.text}")
                
            # Set player 2 ready
            response = await client.post(
                f"{base_url}/api/sessions/{session_id}/ready",
                params={"player_id": "test-player-002", "ready": True}
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Player 2 ready")
                print(f"   Can start: {result.get('can_start', False)}\n")
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
        
        # Test 5: Get Competition Status
        print("5. Testing GET /api/sessions/{session_id}/status")
        try:
            response = await client.get(f"{base_url}/api/sessions/{session_id}/status")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                status = response.json()
                print(f"   ✅ Session status: {status['status']}")
                print(f"   Players: {', '.join(status['players'])}\n")
            else:
                print(f"   ❌ Error: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
        
        # Test 6: Get Quick Match Templates
        print("6. Testing GET /api/sessions/templates/quick-match")
        try:
            response = await client.get(f"{base_url}/api/sessions/templates/quick-match")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                templates = response.json()
                print(f"   ✅ Found {len(templates)} templates")
                for t in templates[:3]:  # Show first 3
                    print(f"      - {t['name']} ({t['game']})\n")
            else:
                print(f"   ❌ Error: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
        
        # Test 7: Get Active Sessions
        print("7. Testing GET /api/sessions/active")
        try:
            response = await client.get(f"{base_url}/api/sessions/active")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                sessions = response.json()
                print(f"   ✅ Found {len(sessions)} active sessions")
                if sessions:
                    for s in sessions[:3]:  # Show first 3
                        print(f"      - {s['name']} (Join: {s['join_code']})")
                print()
            else:
                print(f"   ❌ Error: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
        
        # Test 8: Leave Session
        print("8. Testing POST /api/sessions/{session_id}/leave")
        try:
            response = await client.post(
                f"{base_url}/api/sessions/{session_id}/leave",
                params={"player_id": "test-player-002"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Player left successfully\n")
            else:
                print(f"   ❌ Error: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
        
        print("✅ All API endpoint tests completed!")


async def test_join_url():
    """Test the join URL functionality."""
    print("\n🔗 Testing Join URL Functionality\n")
    
    # First create a session to get a join code
    async with httpx.AsyncClient() as client:
        create_data = {
            "name": "Join URL Test",
            "description": "Testing join URL",
            "format": "single_round",
            "rounds_config": [{
                "game_name": "minesweeper",
                "difficulty": "beginner"
            }],
            "creator_id": "test-join-url",
            "max_players": 4
        }
        
        response = await client.post(
            "https://minesweeper-ai-benchmark.onrender.com/api/sessions/create",
            json=create_data
        )
        
        if response.status_code == 200:
            result = response.json()
            join_code = result["join_code"]
            
            print(f"✅ Created session with join code: {join_code}")
            print(f"📎 Join URL: https://minesweeper-ai-benchmark.onrender.com/join/{join_code}")
            print("\nThis URL can be shared with players to automatically join the session!")
        else:
            print(f"❌ Failed to create session: {response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
    asyncio.run(test_join_url())