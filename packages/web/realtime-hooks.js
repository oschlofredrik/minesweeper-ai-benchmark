// Realtime Hooks for Tilts Platform
// Vanilla JS implementation (can be easily converted to React hooks)

class RealtimeConnection {
    constructor() {
        this.supabase = null;
        this.channels = new Map();
        this.initialized = false;
    }
    
    async initialize() {
        if (this.initialized) return;
        
        // Dynamically load Supabase client
        if (!window.supabase) {
            console.error('Supabase client not loaded');
            return;
        }
        
        this.supabase = window.supabase;
        this.initialized = true;
    }
    
    // Subscribe to game updates
    subscribeToGame(gameId, callbacks) {
        if (!this.initialized) {
            console.error('Realtime not initialized');
            return null;
        }
        
        const channelName = `game:${gameId}`;
        
        // Clean up existing subscription
        if (this.channels.has(channelName)) {
            this.channels.get(channelName).unsubscribe();
        }
        
        const channel = this.supabase
            .channel(channelName)
            .on('postgres_changes', {
                event: '*',
                schema: 'public',
                table: 'games',
                filter: `id=eq.${gameId}`
            }, (payload) => {
                console.log('Game update:', payload);
                if (callbacks.onUpdate) {
                    callbacks.onUpdate(payload);
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
            .subscribe((status) => {
                console.log(`Game channel ${channelName} status:`, status);
            });
        
        this.channels.set(channelName, channel);
        return channel;
    }
    
    // Subscribe to session updates
    subscribeToSession(sessionId, callbacks) {
        if (!this.initialized) {
            console.error('Realtime not initialized');
            return null;
        }
        
        const channelName = `session:${sessionId}`;
        
        if (this.channels.has(channelName)) {
            this.channels.get(channelName).unsubscribe();
        }
        
        const channel = this.supabase
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
            .subscribe((status) => {
                console.log(`Session channel ${channelName} status:`, status);
            });
        
        this.channels.set(channelName, channel);
        return channel;
    }
    
    // Presence tracking
    trackPresence(sessionId, userId, metadata = {}) {
        if (!this.initialized) return null;
        
        const channel = this.supabase.channel(`presence:${sessionId}`);
        
        channel
            .on('presence', { event: 'sync' }, () => {
                const state = channel.presenceState();
                console.log('Presence state:', state);
                this.onPresenceSync(state);
            })
            .on('presence', { event: 'join' }, ({ key, newPresences }) => {
                console.log('User joined:', key, newPresences);
                this.onPresenceJoin(key, newPresences);
            })
            .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
                console.log('User left:', key, leftPresences);
                this.onPresenceLeave(key, leftPresences);
            })
            .subscribe(async (status) => {
                if (status === 'SUBSCRIBED') {
                    await channel.track({
                        user_id: userId,
                        online_at: new Date().toISOString(),
                        ...metadata
                    });
                }
            });
        
        return channel;
    }
    
    // Broadcast game move
    async broadcastMove(gameId, move) {
        if (!this.initialized) return;
        
        const channel = this.supabase.channel(`game:${gameId}`);
        await channel.send({
            type: 'broadcast',
            event: 'move',
            payload: {
                ...move,
                timestamp: new Date().toISOString()
            }
        });
    }
    
    // Presence callbacks (to be overridden)
    onPresenceSync(state) {
        // Update UI with all present users
        const presenceContainer = document.getElementById('presence-container');
        if (presenceContainer) {
            const users = Object.values(state).flat();
            presenceContainer.innerHTML = users.map(user => `
                <div class="presence-user">
                    <span class="presence-indicator"></span>
                    ${user.user_id}
                </div>
            `).join('');
        }
    }
    
    onPresenceJoin(key, presences) {
        // Handle user join
        presences.forEach(presence => {
            this.showNotification(`${presence.user_id} joined`);
        });
    }
    
    onPresenceLeave(key, presences) {
        // Handle user leave
        presences.forEach(presence => {
            this.showNotification(`${presence.user_id} left`);
        });
    }
    
    showNotification(message) {
        // Simple notification
        const notification = document.createElement('div');
        notification.className = 'realtime-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
    
    // Cleanup
    disconnect() {
        this.channels.forEach(channel => channel.unsubscribe());
        this.channels.clear();
    }
}

// Create singleton instance
const realtimeConnection = new RealtimeConnection();

// Export for use
window.RealtimeConnection = realtimeConnection;

// Auto-initialize when Supabase is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Wait for Supabase to be loaded
    if (window.supabase) {
        await realtimeConnection.initialize();
    } else {
        // Retry after a delay
        setTimeout(async () => {
            if (window.supabase) {
                await realtimeConnection.initialize();
            }
        }, 1000);
    }
});