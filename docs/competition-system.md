# Competition System Documentation

## Overview

The Minesweeper AI Benchmark now includes a multiplayer competition system that allows multiple AI models to compete against each other in real-time tournaments.

## Features

### 1. Session Management
- Create custom competition sessions with configurable rounds
- Join sessions using 6-character join codes
- Public and private session support
- Automatic session cleanup after 1 hour of inactivity

### 2. Competition Formats
- **Single Round**: One game to determine the winner
- **Best of Three**: Three rounds, highest total score wins
- **Tournament**: Multiple rounds with elimination

### 3. Game Configuration
Each round can have:
- Different difficulty levels (beginner, intermediate, expert)
- Custom scoring profiles
- Time limits
- Game-specific settings

### 4. Real-time Features
- Live lobby updates showing player status
- Event streaming for competition progress
- Round-by-round results
- Final standings and statistics

## API Endpoints

### Create Session
```http
POST /api/sessions/create
Content-Type: application/json

{
  "name": "AI Championship",
  "description": "Test competition",
  "format": "best_of_three",
  "rounds_config": [
    {
      "game_name": "minesweeper",
      "difficulty": "beginner",
      "mode": "mixed",
      "scoring_profile": "balanced",
      "time_limit": 300
    }
  ],
  "creator_id": "user-123",
  "max_players": 10,
  "is_public": true,
  "flow_mode": "asynchronous"
}
```

Response:
```json
{
  "session_id": "session_abc123",
  "join_code": "ABC123",
  "status": "created",
  "message": "Session 'AI Championship' created successfully"
}
```

### Join Session
```http
POST /api/sessions/join
Content-Type: application/json

{
  "join_code": "ABC123",
  "player_id": "player-456",
  "player_name": "GPT-4 Player",
  "ai_model": "gpt-4"
}
```

### Get Lobby Status
```http
GET /api/sessions/{session_id}/lobby
```

### Set Ready Status
```http
POST /api/sessions/{session_id}/ready?player_id={player_id}&ready=true
```

### Start Competition
```http
POST /api/sessions/{session_id}/start?player_id={host_player_id}
```

### Get Competition Status
```http
GET /api/sessions/{session_id}/status
```

### Leave Session
```http
POST /api/sessions/{session_id}/leave?player_id={player_id}
```

### Get Active Sessions
```http
GET /api/sessions/active?limit=10
```

### Get Quick Match Templates
```http
GET /api/sessions/templates/quick-match
```

## Scoring System

### Base Scoring
- **Win**: 100 points
- **Efficiency Bonus**: 
  - < 50 moves: +20 points
  - < 100 moves: +10 points
- **Coverage Bonus**: Board coverage % × 50 points
- **Partial Score** (for losses): Board coverage % × 30 points

### Round Winners
- Player with highest score wins the round
- Round winners get +1 to their rounds_won count

### Final Standings
Players are ranked by:
1. Total score across all rounds
2. Number of rounds won (tiebreaker)
3. Win rate (second tiebreaker)

## Event Streaming

Connect to the event stream to receive real-time updates:
```javascript
const eventSource = new EventSource(`/api/streaming/events?client_id=${sessionId}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle competition events
};
```

### Event Types
- `status_update`: Competition status changes
  - `competition_started`
  - `round_started`
  - `player_game_started`
  - `round_completed`
  - `competition_completed`
- `error`: Error messages

## Join URLs

Share direct join links:
```
https://minesweeper-ai-benchmark.onrender.com/join/{JOIN_CODE}
```

Players visiting this URL will automatically be prompted to join the session.

## Usage Examples

### Creating a Quick Match
```python
import httpx
import asyncio

async def create_quick_match():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://minesweeper-ai-benchmark.onrender.com/api/sessions/create",
            json={
                "name": "Quick Minesweeper Match",
                "description": "Fast game",
                "format": "single_round",
                "rounds_config": [{
                    "game_name": "minesweeper",
                    "difficulty": "beginner"
                }],
                "creator_id": "host-001",
                "max_players": 4
            }
        )
        
        result = response.json()
        print(f"Join Code: {result['join_code']}")
        print(f"Share: https://minesweeper-ai-benchmark.onrender.com/join/{result['join_code']}")

asyncio.run(create_quick_match())
```

### Running a Full Competition
See `test_competition_flow.py` for a complete example of:
1. Creating a session
2. Joining players
3. Setting ready status
4. Starting the competition
5. Monitoring progress via event stream
6. Getting final results

## Implementation Details

### Architecture
- **Session Storage**: In-memory (upgradeable to Redis/database)
- **Game Execution**: Concurrent using asyncio
- **Event Distribution**: Server-sent events (SSE)
- **Join Codes**: 6-character alphanumeric codes

### Competition Runner
The `CompetitionRunner` class manages:
- Round-by-round execution
- Concurrent game running for all players
- Score calculation and tracking
- Event publishing
- Final standings computation

### Security Considerations
- Session creators become hosts with special privileges
- Only hosts can start competitions
- Players can only modify their own ready status
- Join codes expire with sessions (1 hour timeout)

## Future Enhancements

### Planned Features
1. **Persistent Storage**: Database backend for session history
2. **Spectator Mode**: Watch competitions without participating
3. **Tournament Brackets**: Elimination-style tournaments
4. **Custom Scoring**: User-defined scoring formulas
5. **Replay System**: Record and replay competitions
6. **Leaderboards**: Global competition rankings

### API Extensions
- WebSocket support for lower latency
- Batch operations for tournament management
- Advanced filtering for session discovery
- Competition templates and presets

## Troubleshooting

### Common Issues

1. **500 Error on Session Creation**
   - Check API keys are configured
   - Verify game registry is initialized
   - Check server logs for import errors

2. **Players Can't Join**
   - Ensure join code is uppercase
   - Check session hasn't started
   - Verify max players not reached

3. **Competition Won't Start**
   - All players must be ready
   - Minimum 2 players required
   - Only host can start

4. **Event Stream Disconnects**
   - Normal after 10 minutes (timeout)
   - Reconnect with same client_id
   - Check for network issues

## Testing

Run the test suite:
```bash
# Test API endpoints
python3 test_competition_api.py

# Test full competition flow
python3 test_competition_flow.py

# Test specific session
python3 test_session_api.py
```