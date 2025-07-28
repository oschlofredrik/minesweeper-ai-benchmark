#!/usr/bin/env python3
"""Test complete competition flow from session creation to completion."""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List


class CompetitionTester:
    """Test the complete competition flow."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.join_code = None
        self.players = []
        
    async def test_full_flow(self):
        """Run the complete competition test flow."""
        print("🎮 Starting Competition System Test\n")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            self.client = client
            
            # Step 1: Create session
            await self.create_session()
            
            # Step 2: Join players
            await self.join_players()
            
            # Step 3: Set players ready
            await self.set_players_ready()
            
            # Step 4: Start competition
            await self.start_competition()
            
            # Step 5: Monitor competition progress
            await self.monitor_competition()
            
            # Step 6: Verify results
            await self.verify_results()
    
    async def create_session(self):
        """Create a competition session."""
        print("1️⃣ Creating competition session...")
        
        session_data = {
            "name": "Test Competition",
            "description": "Automated test of competition system",
            "format": "best_of_three",
            "rounds_config": [
                {
                    "game_name": "minesweeper",
                    "difficulty": "beginner",
                    "mode": "mixed",
                    "scoring_profile": "balanced",
                    "time_limit": 300
                },
                {
                    "game_name": "minesweeper",
                    "difficulty": "intermediate",
                    "mode": "mixed",
                    "scoring_profile": "balanced",
                    "time_limit": 300
                },
                {
                    "game_name": "minesweeper",
                    "difficulty": "expert",
                    "mode": "mixed",
                    "scoring_profile": "balanced",
                    "time_limit": 300
                }
            ],
            "creator_id": "test-host-001",
            "max_players": 4,
            "is_public": True,
            "flow_mode": "asynchronous"
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/sessions/create",
            json=session_data
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create session: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception("Session creation failed")
        
        result = response.json()
        self.session_id = result["session_id"]
        self.join_code = result["join_code"]
        
        print(f"✅ Session created!")
        print(f"   Session ID: {self.session_id}")
        print(f"   Join Code: {self.join_code}")
        print()
        
        # Add host to players list
        self.players.append({
            "player_id": "test-host-001",
            "name": "Host",
            "ai_model": "gpt-4o-mini",
            "is_host": True
        })
    
    async def join_players(self):
        """Join additional players to the session."""
        print("2️⃣ Joining players to session...")
        
        test_players = [
            {
                "player_id": "test-player-002",
                "player_name": "Claude Player",
                "ai_model": "claude-3-5-haiku-20241022"
            },
            {
                "player_id": "test-player-003",
                "player_name": "GPT-4 Player",
                "ai_model": "gpt-4"
            }
        ]
        
        for player in test_players:
            join_data = {
                "join_code": self.join_code,
                **player
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/sessions/join",
                json=join_data
            )
            
            if response.status_code == 200:
                print(f"✅ {player['player_name']} joined successfully")
                self.players.append({
                    **player,
                    "name": player["player_name"],
                    "is_host": False
                })
            else:
                print(f"❌ Failed to join {player['player_name']}: {response.status_code}")
                print(f"Response: {response.text}")
        
        print()
    
    async def set_players_ready(self):
        """Set all players as ready."""
        print("3️⃣ Setting players ready...")
        
        for player in self.players:
            response = await self.client.post(
                f"{self.base_url}/api/sessions/{self.session_id}/ready",
                params={
                    "player_id": player["player_id"],
                    "ready": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {player['name']} is ready")
                if result.get("can_start"):
                    print("   ⚡ Competition can now start!")
            else:
                print(f"❌ Failed to set {player['name']} ready: {response.status_code}")
        
        print()
    
    async def start_competition(self):
        """Start the competition (as host)."""
        print("4️⃣ Starting competition...")
        
        host = self.players[0]  # First player is host
        
        response = await self.client.post(
            f"{self.base_url}/api/sessions/{self.session_id}/start",
            params={"player_id": host["player_id"]}
        )
        
        if response.status_code == 200:
            print("✅ Competition started successfully!")
        else:
            print(f"❌ Failed to start competition: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception("Failed to start competition")
        
        print()
    
    async def monitor_competition(self):
        """Monitor the competition progress."""
        print("5️⃣ Monitoring competition progress...")
        print("   (This may take a few minutes depending on the number of rounds)\n")
        
        # Connect to event stream
        event_url = f"{self.base_url}/api/streaming/events?client_id={self.session_id}"
        
        start_time = time.time()
        last_status = None
        
        async with self.client.stream('GET', event_url) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        await self.handle_event(data)
                        
                        # Check for completion
                        if data.get("type") == "status_update":
                            status = data.get("data", {}).get("status")
                            if status == "competition_completed":
                                print("\n🏆 Competition completed!")
                                return
                            last_status = status
                        
                    except json.JSONDecodeError:
                        pass
                
                # Timeout after 10 minutes
                if time.time() - start_time > 600:
                    print("\n⏰ Timeout: Competition taking too long")
                    break
    
    async def handle_event(self, event: Dict[str, Any]):
        """Handle competition events."""
        event_type = event.get("type")
        data = event.get("data", {})
        
        if event_type == "status_update":
            status = data.get("status")
            
            if status == "competition_started":
                print(f"🎯 Competition started with {len(data.get('players', []))} players")
                print(f"   Total rounds: {data.get('total_rounds', 0)}")
            
            elif status == "round_started":
                print(f"\n📍 Round {data.get('round')} started")
                print(f"   Game: {data.get('game')}")
                print(f"   Difficulty: {data.get('difficulty')}")
            
            elif status == "player_game_started":
                print(f"   🎮 {data.get('player')} is playing...")
            
            elif status == "round_completed":
                print(f"\n✅ Round {data.get('round')} completed!")
                print(f"   Winner: {data.get('winner', 'No winner')}")
                
                # Show standings
                standings = data.get("scores", [])
                if standings:
                    print("   Current standings:")
                    for standing in standings[:3]:  # Top 3
                        print(f"     {standing['rank']}. {standing['player_name']}: "
                              f"{standing['total_score']:.1f} points "
                              f"({standing['rounds_won']} rounds won)")
            
            elif status == "competition_completed":
                print(f"\n🏁 Competition finished!")
                winner = data.get("winner")
                if winner:
                    print(f"   🏆 Winner: {winner}")
                
                # Show final standings
                final_standings = data.get("final_standings", [])
                if final_standings:
                    print("\n   Final Results:")
                    for standing in final_standings:
                        win_rate = standing.get("win_rate", 0) * 100
                        print(f"     {standing['rank']}. {standing['player_name']} "
                              f"({standing['ai_model']})")
                        print(f"        Score: {standing['total_score']:.1f}")
                        print(f"        Win Rate: {win_rate:.1f}%")
                        print(f"        Games: {standing['games_won']}/{standing['games_played']}")
        
        elif event_type == "error":
            print(f"\n❌ Error: {data.get('message', 'Unknown error')}")
    
    async def verify_results(self):
        """Verify the competition results."""
        print("\n6️⃣ Verifying competition results...")
        
        # Get final session status
        response = await self.client.get(
            f"{self.base_url}/api/sessions/{self.session_id}/status"
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Final status: {status['status']}")
            
            if status.get("completed_at"):
                print(f"   Completed at: {status['completed_at']}")
        else:
            print(f"❌ Failed to get final status: {response.status_code}")
        
        print("\n✨ Competition test completed successfully!")


async def test_quick_match():
    """Test quick match template functionality."""
    print("\n🎯 Testing Quick Match Templates\n")
    
    async with httpx.AsyncClient() as client:
        # Get available templates
        response = await client.get("http://localhost:8000/api/sessions/templates/quick-match")
        
        if response.status_code == 200:
            templates = response.json()
            print(f"Found {len(templates)} quick match templates:")
            for template in templates:
                print(f"  - {template['name']} ({template['game']})")
                print(f"    {template['description']}")
                print(f"    Difficulty: {template['difficulty']}, Duration: ~{template['estimated_duration']} min")
        else:
            print(f"Failed to get templates: {response.status_code}")


async def test_active_sessions():
    """Test listing active sessions."""
    print("\n📋 Testing Active Sessions List\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/sessions/active")
        
        if response.status_code == 200:
            sessions = response.json()
            if sessions:
                print(f"Found {len(sessions)} active sessions:")
                for session in sessions:
                    print(f"  - {session['name']} (Join: {session['join_code']})")
                    print(f"    Players: {session['players_count']}/{session['max_players']}")
                    print(f"    Format: {session['format']}")
            else:
                print("No active sessions found")
        else:
            print(f"Failed to get active sessions: {response.status_code}")


async def main():
    """Run all competition tests."""
    print("=" * 60)
    print("COMPETITION SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Test 1: Quick match templates
    await test_quick_match()
    
    # Test 2: Active sessions
    await test_active_sessions()
    
    # Test 3: Full competition flow
    tester = CompetitionTester()
    await tester.test_full_flow()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())