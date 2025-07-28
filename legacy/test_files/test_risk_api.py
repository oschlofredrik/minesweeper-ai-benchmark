#!/usr/bin/env python3
"""Test Risk game through the API."""

import asyncio
import json
import httpx

async def test_risk_game():
    """Test playing Risk through the API."""
    
    # API endpoint
    base_url = "http://localhost:8000"
    
    # Test data
    play_request = {
        "game": "risk",
        "model_name": "gpt-4o-mini",
        "model_provider": "openai",
        "num_games": 1,
        "difficulty": "scenario:north_america_conquest"
    }
    
    async with httpx.AsyncClient() as client:
        # Start play session
        print("Starting Risk game...")
        response = await client.post(
            f"{base_url}/api/play",
            json=play_request,
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"Error starting game: {response.status_code}")
            print(response.text)
            return
            
        result = response.json()
        job_id = result["job_id"]
        print(f"Started game with job ID: {job_id}")
        
        # Poll for status
        print("\nPolling for game status...")
        for i in range(30):  # Poll for up to 30 seconds
            await asyncio.sleep(1)
            
            status_response = await client.get(f"{base_url}/api/play/games/{job_id}")
            if status_response.status_code != 200:
                print(f"Error getting status: {status_response.status_code}")
                continue
                
            status = status_response.json()
            print(f"Status: {status['status']} - {status['message']}")
            
            if status['status'] in ['completed', 'failed']:
                print(f"\nGame {status['status']}!")
                
                if status['status'] == 'completed':
                    # Try to get results
                    results_response = await client.get(f"{base_url}/api/play/games/{job_id}/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        print(f"Games played: {results.get('num_games', 0)}")
                        print(f"Metrics: {json.dumps(results.get('metrics', {}), indent=2)}")
                break
        else:
            print("Timeout waiting for game to complete")

if __name__ == "__main__":
    asyncio.run(test_risk_game())