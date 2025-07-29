// Spectator Mode for Tilts Platform
class SpectatorMode {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.sessionId = null;
        this.games = new Map();
        this.connection = null;
        this.isSpectating = false;
    }
    
    async startSpectating(sessionId) {
        this.sessionId = sessionId;
        this.isSpectating = true;
        
        // Initialize UI
        this.setupUI();
        
        // Connect to realtime
        if (window.RealtimeConnection) {
            this.connection = window.RealtimeConnection;
            
            // Subscribe to session updates
            this.connection.subscribeToSession(sessionId, {
                onPlayerJoin: (player) => this.handlePlayerJoin(player),
                onPlayerLeave: (player) => this.handlePlayerLeave(player),
                onGameStart: () => this.handleGameStart(),
                onStatusUpdate: (status) => this.handleStatusUpdate(status)
            });
            
            // Track presence as spectator
            this.connection.trackPresence(sessionId, `spectator_${Date.now()}`, {
                role: 'spectator'
            });
        }
        
        // Load current session state
        await this.loadSessionState();
    }
    
    setupUI() {
        this.container.innerHTML = `
            <div class="spectator-mode">
                <div class="spectator-header">
                    <h2>Spectator Mode</h2>
                    <span class="spectator-badge">LIVE</span>
                    <button class="button button-small" onclick="spectatorMode.stopSpectating()">
                        Exit Spectator
                    </button>
                </div>
                
                <div class="spectator-content">
                    <div class="spectator-players" id="spectator-players">
                        <h3>Players</h3>
                        <div class="players-grid" id="players-list">
                            <p class="text-muted">Loading players...</p>
                        </div>
                    </div>
                    
                    <div class="spectator-games" id="spectator-games">
                        <h3>Live Games</h3>
                        <div class="games-grid" id="games-list">
                            <p class="text-muted">No games in progress</p>
                        </div>
                    </div>
                    
                    <div class="spectator-leaderboard" id="spectator-leaderboard">
                        <h3>Session Leaderboard</h3>
                        <table class="table table-small">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Player</th>
                                    <th>Score</th>
                                    <th>Games</th>
                                </tr>
                            </thead>
                            <tbody id="leaderboard-body">
                                <tr>
                                    <td colspan="4" class="text-center text-muted">
                                        No scores yet
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="spectator-events" id="spectator-events">
                    <h4>Live Events</h4>
                    <div class="events-stream" id="events-stream"></div>
                </div>
            </div>
        `;
    }
    
    async loadSessionState() {
        try {
            const response = await fetch(`/api/sessions/${this.sessionId}`);
            if (response.ok) {
                const session = await response.json();
                this.updatePlayers(session.players || []);
                this.updateLeaderboard(session.scores || {});
            }
        } catch (error) {
            console.error('Failed to load session state:', error);
        }
    }
    
    handlePlayerJoin(player) {
        this.addEvent({
            type: 'player_join',
            message: `${player.name} joined the session`,
            timestamp: new Date().toISOString()
        });
        
        // Update players list
        this.loadSessionState();
    }
    
    handlePlayerLeave(player) {
        this.addEvent({
            type: 'player_leave',
            message: `${player.name} left the session`,
            timestamp: new Date().toISOString()
        });
        
        // Update players list
        this.loadSessionState();
    }
    
    handleGameStart() {
        this.addEvent({
            type: 'game_start',
            message: 'New game started!',
            timestamp: new Date().toISOString()
        });
        
        // Clear previous games
        this.games.clear();
        document.getElementById('games-list').innerHTML = 
            '<p class="text-muted">Games starting...</p>';
    }
    
    handleStatusUpdate(status) {
        // Update game states
        if (status.games) {
            this.updateGames(status.games);
        }
        
        // Update leaderboard
        if (status.scores) {
            this.updateLeaderboard(status.scores);
        }
    }
    
    updatePlayers(players) {
        const container = document.getElementById('players-list');
        
        if (players.length === 0) {
            container.innerHTML = '<p class="text-muted">No players yet</p>';
            return;
        }
        
        container.innerHTML = players.map(player => `
            <div class="player-card ${player.is_ready ? 'ready' : ''}">
                <div class="player-name">${player.name}</div>
                <div class="player-model">${player.ai_model || 'Not selected'}</div>
                <div class="player-status">
                    ${player.is_ready ? 
                        '<span class="status-ready">Ready</span>' : 
                        '<span class="status-waiting">Waiting</span>'}
                </div>
            </div>
        `).join('');
    }
    
    updateGames(games) {
        const container = document.getElementById('games-list');
        
        if (!games || games.length === 0) {
            container.innerHTML = '<p class="text-muted">No games in progress</p>';
            return;
        }
        
        container.innerHTML = games.map(game => {
            // Subscribe to individual game updates
            if (!this.games.has(game.id)) {
                this.subscribeToGame(game.id);
                this.games.set(game.id, game);
            }
            
            return `
                <div class="game-card" data-game-id="${game.id}">
                    <div class="game-header">
                        <span class="game-player">${game.player_name}</span>
                        <span class="game-status status-${game.status}">${game.status}</span>
                    </div>
                    <div class="game-progress">
                        <div class="progress-bar" style="width: ${game.progress * 100}%"></div>
                    </div>
                    <div class="game-stats">
                        <span>Moves: ${game.moves || 0}</span>
                        <span>Time: ${this.formatTime(game.duration || 0)}</span>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateLeaderboard(scores) {
        const tbody = document.getElementById('leaderboard-body');
        
        // Convert scores object to sorted array
        const sortedScores = Object.entries(scores)
            .map(([playerId, score]) => ({ playerId, ...score }))
            .sort((a, b) => (b.points || 0) - (a.points || 0));
        
        if (sortedScores.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted">No scores yet</td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = sortedScores.map((score, index) => `
            <tr>
                <td>${index + 1}</td>
                <td>${score.name || score.playerId}</td>
                <td>${score.points || 0}</td>
                <td>${score.games_played || 0}</td>
            </tr>
        `).join('');
    }
    
    subscribeToGame(gameId) {
        if (!this.connection) return;
        
        this.connection.subscribeToGame(gameId, {
            onMove: (move) => {
                this.addEvent({
                    type: 'game_move',
                    gameId,
                    message: `Move: ${move.action} at (${move.row}, ${move.col})`,
                    timestamp: move.timestamp
                });
            },
            onUpdate: (update) => {
                // Update game card
                const gameCard = document.querySelector(`[data-game-id="${gameId}"]`);
                if (gameCard && update.new) {
                    const progressBar = gameCard.querySelector('.progress-bar');
                    if (progressBar && update.new.progress) {
                        progressBar.style.width = `${update.new.progress * 100}%`;
                    }
                }
            },
            onGameEnd: (result) => {
                this.addEvent({
                    type: 'game_end',
                    gameId,
                    message: `Game ended: ${result.won ? 'Won' : 'Lost'}`,
                    timestamp: new Date().toISOString()
                });
            }
        });
    }
    
    addEvent(event) {
        const stream = document.getElementById('events-stream');
        if (!stream) return;
        
        const eventEl = document.createElement('div');
        eventEl.className = `event event-${event.type}`;
        
        const time = new Date(event.timestamp).toLocaleTimeString();
        
        eventEl.innerHTML = `
            <span class="event-time">${time}</span>
            <span class="event-message">${event.message}</span>
        `;
        
        stream.insertBefore(eventEl, stream.firstChild);
        
        // Keep only last 50 events
        while (stream.children.length > 50) {
            stream.removeChild(stream.lastChild);
        }
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    stopSpectating() {
        this.isSpectating = false;
        
        // Unsubscribe from all channels
        this.games.forEach((game, gameId) => {
            // Channels are managed by RealtimeConnection
        });
        
        this.games.clear();
        
        // Clear UI
        this.container.innerHTML = `
            <div class="spectator-stopped">
                <p>Spectator mode stopped</p>
                <button class="button" onclick="location.reload()">
                    Return to Dashboard
                </button>
            </div>
        `;
    }
}

// Create instance
const spectatorMode = new SpectatorMode('spectator-container');
window.spectatorMode = spectatorMode;