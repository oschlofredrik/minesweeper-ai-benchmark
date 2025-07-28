# Realtime Architecture Guide

## Overview
Phase 3 introduces Supabase Realtime for live updates, presence tracking, and spectator mode.

## Architecture

### 1. Database Layer
- **realtime_events**: Temporary event storage
- **presence**: Online user tracking
- **Realtime-enabled tables**: games, sessions, session_players

### 2. TypeScript Module
- `realtime/client.ts`: Core realtime functionality
- Channel management
- Presence tracking
- Event broadcasting

### 3. Frontend Integration
- `realtime-hooks.js`: Vanilla JS realtime connection
- `spectator-mode.js`: Live game spectating
- `realtime.css`: UI components

## Key Features

### Live Game Updates
```javascript
// Subscribe to game
RealtimeConnection.subscribeToGame(gameId, {
    onMove: (move) => console.log('Move:', move),
    onStateUpdate: (state) => console.log('Update:', state),
    onGameEnd: (result) => console.log('Game ended:', result)
});
```

### Presence System
```javascript
// Track user presence
RealtimeConnection.trackPresence(sessionId, userId, {
    status: 'online',
    role: 'player'
});
```

### Spectator Mode
```javascript
// Start spectating
spectatorMode.startSpectating(sessionId);
```

## Database Setup

### Enable Realtime
```sql
ALTER PUBLICATION supabase_realtime ADD TABLE games;
ALTER PUBLICATION supabase_realtime ADD TABLE sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE presence;
```

### Presence Table
- Tracks online users
- Auto-updates last_seen
- Cleanup stale presence

## Frontend Components

### Presence Indicators
- Live user status
- Animated indicators
- Auto-refresh

### Spectator View
- Live game grids
- Real-time leaderboard
- Event stream
- Player tracking

### Notifications
- Join/leave alerts
- Game events
- Status updates

## Usage Examples

### 1. Competition Lobby
```javascript
// Host creates session
const session = await createSession({
    name: "Friday Challenge",
    game_type: "minesweeper"
});

// Players join with presence
RealtimeConnection.trackPresence(session.id, playerId);

// Subscribe to updates
RealtimeConnection.subscribeToSession(session.id, {
    onPlayerJoin: updatePlayerList,
    onGameStart: startGames
});
```

### 2. Live Evaluation
```javascript
// AI makes move
await RealtimeConnection.broadcastMove(gameId, {
    action: 'reveal',
    row: 5,
    col: 3,
    reasoning: 'Safe based on adjacent cells'
});
```

### 3. Spectating
```javascript
// Watch live session
spectatorMode.startSpectating('session_123');

// Receives all game updates
// Shows live leaderboard
// Displays move-by-move action
```

## Performance Considerations

### Channel Management
- One channel per game/session
- Automatic cleanup on disconnect
- Reuse existing subscriptions

### Event Throttling
- Batch updates when possible
- Limit event frequency
- Use presence for status only

### Cleanup
- 5-minute retention for events
- 30-second presence timeout
- Automatic stale data removal

## Security

### Row Level Security
- Public read for development
- Authenticated writes
- Session-scoped access

### Future Enhancements
1. User authentication
2. Private sessions
3. Replay from realtime data
4. Analytics dashboard

## Migration Checklist

1. **Database**
   - [ ] Apply migration 003_enable_realtime.sql
   - [ ] Verify realtime publication

2. **Frontend**
   - [ ] Include realtime scripts
   - [ ] Initialize connection
   - [ ] Add presence UI

3. **Testing**
   - [ ] Create test session
   - [ ] Join with multiple browsers
   - [ ] Verify live updates
   - [ ] Test spectator mode

## Rollback
If issues occur:
1. Realtime is optional - base functionality remains
2. Disable by not loading realtime scripts
3. Falls back to polling automatically