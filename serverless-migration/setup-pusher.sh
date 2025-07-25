#!/bin/bash

echo "Setting up Pusher for real-time events..."

# Create Pusher configuration
cat > pusher-config.js << 'EOF'
// Client-side Pusher configuration
export const pusherConfig = {
  key: process.env.VITE_PUSHER_KEY,
  cluster: process.env.VITE_PUSHER_CLUSTER || 'us2',
  forceTLS: true
};

// Initialize Pusher client
export function initPusher() {
  const pusher = new Pusher(pusherConfig.key, pusherConfig);
  
  // Subscribe to global channel
  const globalChannel = pusher.subscribe('tilts-global');
  
  // Subscribe to session-specific channels
  const subscribeToSession = (sessionId) => {
    return pusher.subscribe(`session-${sessionId}`);
  };
  
  // Subscribe to game-specific channels
  const subscribeToGame = (gameId) => {
    return pusher.subscribe(`game-${gameId}`);
  };
  
  return {
    pusher,
    globalChannel,
    subscribeToSession,
    subscribeToGame
  };
}

// Event handlers
export const eventHandlers = {
  // Session events
  'session-created': (data) => console.log('New session:', data),
  'player-joined': (data) => console.log('Player joined:', data),
  'player-ready': (data) => console.log('Player ready:', data),
  'game-started': (data) => console.log('Game started:', data),
  
  // Game events
  'move-made': (data) => console.log('Move made:', data),
  'game-completed': (data) => console.log('Game completed:', data),
  'evaluation-update': (data) => console.log('Evaluation update:', data),
  
  // Real-time updates
  'board-update': (data) => console.log('Board update:', data),
  'score-update': (data) => console.log('Score update:', data),
};
EOF

# Create integration guide
cat > PUSHER_INTEGRATION.md << 'EOF'
# Pusher Integration Guide

## Setup Steps

1. Create a Pusher account at https://pusher.com
2. Create a new Channels app
3. Note your credentials:
   - App ID
   - Key
   - Secret
   - Cluster

## Environment Variables

Add to your `.env` files:
```
PUSHER_APP_ID=your-app-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
PUSHER_CLUSTER=us2
```

## Client Integration

```javascript
import { initPusher, eventHandlers } from './pusher-config.js';

// Initialize
const { pusher, globalChannel, subscribeToSession } = initPusher();

// Subscribe to events
globalChannel.bind('session-created', eventHandlers['session-created']);

// Session-specific subscription
const sessionChannel = subscribeToSession(sessionId);
sessionChannel.bind('player-joined', (data) => {
  // Update UI
});
```

## Server Integration

```javascript
// In Cloudflare Worker
import Pusher from 'pusher';

const pusher = new Pusher({
  appId: env.PUSHER_APP_ID,
  key: env.PUSHER_KEY,
  secret: env.PUSHER_SECRET,
  cluster: env.PUSHER_CLUSTER,
});

// Trigger events
await pusher.trigger('session-' + sessionId, 'player-joined', {
  playerId,
  playerName,
  timestamp: new Date().toISOString()
});
```

## Event Types

### Global Events (channel: tilts-global)
- session-created
- leaderboard-update

### Session Events (channel: session-{id})
- player-joined
- player-left
- player-ready
- game-started
- round-completed
- session-completed

### Game Events (channel: game-{id})
- move-made
- board-update
- evaluation-update
- game-completed
EOF

echo "Pusher configuration created!"
echo "Next steps:"
echo "1. Create a Pusher account at https://pusher.com"
echo "2. Create a new Channels app"
echo "3. Add credentials to your environment files"