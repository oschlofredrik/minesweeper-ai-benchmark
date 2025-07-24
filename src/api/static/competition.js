/**
 * Competition management for Tilts
 */

class CompetitionManager {
    constructor() {
        this.sessionId = null;
        this.eventSource = null;
        this.isHost = false;
        this.playerId = null;
    }
    
    /**
     * Connect to competition event stream
     */
    connectToCompetition(sessionId) {
        this.sessionId = sessionId;
        
        // Close existing connection
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        // Connect to event stream for this session
        this.eventSource = new EventSource(`/api/streaming/events?client_id=${sessionId}`);
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleCompetitionEvent(data);
            } catch (error) {
                console.error('Failed to parse event:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
        };
    }
    
    /**
     * Handle competition events
     */
    handleCompetitionEvent(event) {
        console.log('Competition event:', event);
        
        switch (event.type) {
            case 'status_update':
                this.handleStatusUpdate(event.data);
                break;
                
            case 'game_started':
                this.handleGameStarted(event.data);
                break;
                
            case 'round_completed':
                this.handleRoundCompleted(event.data);
                break;
                
            case 'competition_completed':
                this.handleCompetitionCompleted(event.data);
                break;
                
            case 'error':
                this.handleError(event.data);
                break;
        }
    }
    
    /**
     * Handle status updates
     */
    handleStatusUpdate(data) {
        const statusEl = document.getElementById('competition-status');
        if (!statusEl) return;
        
        let statusHtml = '';
        
        switch (data.status) {
            case 'competition_started':
                statusHtml = `
                    <div class="status status-active">
                        Competition Started!
                    </div>
                    <div class="mt-2">
                        <strong>Players:</strong> ${data.players.join(', ')}
                    </div>
                    <div>
                        <strong>Total Rounds:</strong> ${data.total_rounds}
                    </div>
                `;
                break;
                
            case 'round_started':
                statusHtml = `
                    <div class="status status-active">
                        Round ${data.round} Started
                    </div>
                    <div class="mt-2">
                        <strong>Game:</strong> ${data.game}
                    </div>
                    <div>
                        <strong>Difficulty:</strong> ${data.difficulty}
                    </div>
                `;
                break;
                
            case 'player_game_started':
                statusHtml = `
                    <div class="status status-active">
                        ${data.player} is playing...
                    </div>
                `;
                break;
                
            case 'round_completed':
                statusHtml = `
                    <div class="status status-success">
                        Round ${data.round} Complete!
                    </div>
                    <div class="mt-2">
                        <strong>Winner:</strong> ${data.winner || 'No winner'}
                    </div>
                    ${this.renderStandings(data.scores)}
                `;
                break;
                
            case 'competition_completed':
                statusHtml = `
                    <div class="status status-success">
                        Competition Complete!
                    </div>
                    <div class="mt-2">
                        <strong>🏆 Winner:</strong> ${data.winner || 'No winner'}
                    </div>
                    ${this.renderFinalStandings(data.final_standings)}
                `;
                break;
        }
        
        statusEl.innerHTML = statusHtml;
    }
    
    /**
     * Handle game started event
     */
    handleGameStarted(data) {
        // Could show game visualization here
        console.log('Game started:', data);
    }
    
    /**
     * Handle round completed
     */
    handleRoundCompleted(data) {
        // Update UI with round results
        console.log('Round completed:', data);
    }
    
    /**
     * Handle competition completed
     */
    handleCompetitionCompleted(data) {
        // Show final results
        console.log('Competition completed:', data);
        
        // Close event stream
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
    
    /**
     * Handle errors
     */
    handleError(data) {
        const statusEl = document.getElementById('competition-status');
        if (statusEl) {
            statusEl.innerHTML = `
                <div class="status status-error">
                    Error: ${data.message}
                </div>
            `;
        }
    }
    
    /**
     * Render current standings
     */
    renderStandings(standings) {
        if (!standings || standings.length === 0) return '';
        
        let html = '<div class="standings mt-3"><h4>Current Standings</h4><table class="table">';
        html += '<thead><tr><th>Rank</th><th>Player</th><th>Score</th><th>Rounds Won</th></tr></thead><tbody>';
        
        standings.forEach(standing => {
            html += `
                <tr>
                    <td>${standing.rank}</td>
                    <td>${standing.player_name}</td>
                    <td>${standing.total_score.toFixed(1)}</td>
                    <td>${standing.rounds_won}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        return html;
    }
    
    /**
     * Render final standings
     */
    renderFinalStandings(standings) {
        if (!standings || standings.length === 0) return '';
        
        let html = '<div class="standings mt-3"><h4>Final Results</h4><table class="table">';
        html += '<thead><tr><th>Rank</th><th>Player</th><th>AI Model</th><th>Total Score</th><th>Win Rate</th></tr></thead><tbody>';
        
        standings.forEach(standing => {
            const winRate = (standing.win_rate * 100).toFixed(1);
            const rankEmoji = standing.rank === 1 ? '🏆 ' : '';
            
            html += `
                <tr class="${standing.rank === 1 ? 'winner-row' : ''}">
                    <td>${rankEmoji}${standing.rank}</td>
                    <td>${standing.player_name}</td>
                    <td>${standing.ai_model}</td>
                    <td>${standing.total_score.toFixed(1)}</td>
                    <td>${winRate}%</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        return html;
    }
    
    /**
     * Set player ready status
     */
    async setReady(ready = true) {
        if (!this.sessionId || !this.playerId) return;
        
        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/ready`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: this.playerId,
                    ready: ready
                })
            });
            
            const result = await response.json();
            
            if (result.can_start && this.isHost) {
                // Show start button
                document.getElementById('start-competition-btn').style.display = 'block';
            }
            
        } catch (error) {
            console.error('Failed to set ready status:', error);
        }
    }
    
    /**
     * Start the competition (host only)
     */
    async startCompetition() {
        if (!this.sessionId || !this.playerId || !this.isHost) return;
        
        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: this.playerId
                })
            });
            
            if (response.ok) {
                // Hide lobby, show competition view
                this.showCompetitionView();
            } else {
                const error = await response.json();
                alert(error.detail || 'Failed to start competition');
            }
            
        } catch (error) {
            console.error('Failed to start competition:', error);
        }
    }
    
    /**
     * Show competition view
     */
    showCompetitionView() {
        // Hide lobby modal
        const lobbyModal = document.getElementById('session-lobby-modal');
        if (lobbyModal) {
            lobbyModal.classList.remove('active');
        }
        
        // Show competition modal
        let competitionModal = document.getElementById('competition-modal');
        if (!competitionModal) {
            // Create competition modal
            competitionModal = document.createElement('div');
            competitionModal.id = 'competition-modal';
            competitionModal.className = 'modal-overlay active';
            competitionModal.innerHTML = `
                <div class="modal-content modal-large">
                    <div class="modal-header">
                        <h3>Competition in Progress</h3>
                        <button class="modal-close" onclick="competitionManager.closeCompetition()">&times;</button>
                    </div>
                    <div class="competition-content">
                        <div id="competition-status">
                            <div class="status status-active">
                                Waiting for competition to start...
                            </div>
                        </div>
                        <div id="competition-game-view" class="mt-4">
                            <!-- Game visualization would go here -->
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(competitionModal);
        } else {
            competitionModal.classList.add('active');
        }
    }
    
    /**
     * Close competition view
     */
    closeCompetition() {
        const modal = document.getElementById('competition-modal');
        if (modal) {
            modal.classList.remove('active');
        }
        
        // Disconnect event stream
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Global competition manager instance
window.competitionManager = new CompetitionManager();

// Add styles for competition view
const style = document.createElement('style');
style.textContent = `
    .competition-content {
        min-height: 400px;
    }
    
    .standings {
        margin-top: 20px;
    }
    
    .standings table {
        width: 100%;
    }
    
    .winner-row {
        background-color: rgba(74, 144, 226, 0.1);
        font-weight: bold;
    }
    
    #competition-game-view {
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 20px;
        min-height: 200px;
        background: var(--bg-secondary);
    }
`;
document.head.appendChild(style);