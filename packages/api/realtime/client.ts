import { createClient, SupabaseClient, RealtimeChannel } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase: SupabaseClient = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Channel management
const channels = new Map<string, RealtimeChannel>();

export interface RealtimeEvent {
  channel: string;
  event: string;
  payload: any;
  timestamp: string;
}

export interface PresenceState {
  user_id: string;
  status: 'online' | 'offline' | 'playing';
  session_id?: string;
  metadata?: any;
}

// Subscribe to game events
export function subscribeToGame(gameId: string, callbacks: {
  onMove?: (move: any) => void;
  onStateUpdate?: (state: any) => void;
  onGameEnd?: (result: any) => void;
}) {
  const channelName = `game:${gameId}`;
  
  // Clean up existing subscription
  if (channels.has(channelName)) {
    channels.get(channelName)?.unsubscribe();
  }
  
  const channel = supabase
    .channel(channelName)
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'games',
      filter: `id=eq.${gameId}`
    }, (payload) => {
      if (callbacks.onStateUpdate) {
        callbacks.onStateUpdate(payload.new);
      }
    })
    .on('broadcast', {
      event: 'move'
    }, (payload) => {
      if (callbacks.onMove) {
        callbacks.onMove(payload.payload);
      }
    })
    .on('broadcast', {
      event: 'game_end'
    }, (payload) => {
      if (callbacks.onGameEnd) {
        callbacks.onGameEnd(payload.payload);
      }
    })
    .subscribe();
  
  channels.set(channelName, channel);
  return channel;
}

// Subscribe to session events
export function subscribeToSession(sessionId: string, callbacks: {
  onPlayerJoin?: (player: any) => void;
  onPlayerLeave?: (player: any) => void;
  onGameStart?: () => void;
  onStatusUpdate?: (status: any) => void;
}) {
  const channelName = `session:${sessionId}`;
  
  if (channels.has(channelName)) {
    channels.get(channelName)?.unsubscribe();
  }
  
  const channel = supabase
    .channel(channelName)
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'session_players',
      filter: `session_id=eq.${sessionId}`
    }, (payload) => {
      if (callbacks.onPlayerJoin) {
        callbacks.onPlayerJoin(payload.new);
      }
    })
    .on('postgres_changes', {
      event: 'DELETE',
      schema: 'public',
      table: 'session_players',
      filter: `session_id=eq.${sessionId}`
    }, (payload) => {
      if (callbacks.onPlayerLeave) {
        callbacks.onPlayerLeave(payload.old);
      }
    })
    .on('broadcast', {
      event: 'game_start'
    }, () => {
      if (callbacks.onGameStart) {
        callbacks.onGameStart();
      }
    })
    .on('broadcast', {
      event: 'status_update'
    }, (payload) => {
      if (callbacks.onStatusUpdate) {
        callbacks.onStatusUpdate(payload.payload);
      }
    })
    .subscribe();
  
  channels.set(channelName, channel);
  return channel;
}

// Presence management
export function joinPresence(sessionId: string, userId: string, metadata?: any) {
  const channel = supabase.channel(`presence:${sessionId}`);
  
  channel
    .on('presence', { event: 'sync' }, () => {
      const state = channel.presenceState();
      console.log('Presence sync:', state);
    })
    .on('presence', { event: 'join' }, ({ key, newPresences }) => {
      console.log('User joined:', key, newPresences);
    })
    .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
      console.log('User left:', key, leftPresences);
    })
    .subscribe(async (status) => {
      if (status === 'SUBSCRIBED') {
        await channel.track({
          user_id: userId,
          online_at: new Date().toISOString(),
          metadata
        });
      }
    });
  
  return channel;
}

// Broadcast event
export async function broadcastEvent(channel: string, event: string, payload: any) {
  const ch = supabase.channel(channel);
  await ch.send({
    type: 'broadcast',
    event,
    payload
  });
}

// Send game move
export async function sendGameMove(gameId: string, move: any) {
  await broadcastEvent(`game:${gameId}`, 'move', {
    ...move,
    timestamp: new Date().toISOString()
  });
}

// Update session status
export async function updateSessionStatus(sessionId: string, status: any) {
  await broadcastEvent(`session:${sessionId}`, 'status_update', status);
}

// Cleanup subscriptions
export function unsubscribeAll() {
  channels.forEach(channel => channel.unsubscribe());
  channels.clear();
}

// Export Supabase client for direct use
export { supabase };