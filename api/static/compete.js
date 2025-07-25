// Compete page functionality
let currentSessionId = null;
let currentPlayerId = null;
let eventSource = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set up form handlers
    document.getElementById('create-session-form').addEventListener('submit', handleCreateSession);
    document.getElementById('join-session-form').addEventListener('submit', handleJoinSession);
    
    // Check for join code in URL
    const urlParams = new URLSearchParams(window.location.search);
    const joinCode = urlParams.get('join');
    if (joinCode) {
        document.querySelector('input[name="join-code"]').value = joinCode;
        // Focus on the name field
        document.querySelector('input[name="player-name"]').focus();
    }
    
    // Check if we should show join form
    if (window.location.hash === '#join') {
        document.querySelector('input[name="join-code"]').focus();
    }
    
    // Load active sessions
    loadActiveSessions();
});

async function handleCreateSession(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const creatorId = 'user-' + Math.random().toString(36).substr(2, 9);
    currentPlayerId = creatorId;
    
    const sessionData = {
        name: formData.get('session-name'),
        game_type: formData.get('game-type'),
        max_players: parseInt(formData.get('max-players')),
        creator_id: creatorId,
        creator_name: 'Host'
    };
    
    try {
        const response = await fetch('/api/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showLobby(result.session_id, result.join_code, true);
        } else {
            alert('Failed to create session');
        }
    } catch (error) {
        console.error('Error creating session:', error);
        alert('Error creating session');
    }
}

async function handleJoinSession(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const playerId = 'player-' + Math.random().toString(36).substr(2, 9);
    currentPlayerId = playerId;
    
    const joinData = {
        join_code: formData.get('join-code').toUpperCase(),
        player_id: playerId,
        player_name: formData.get('player-name'),
        ai_model: formData.get('player-model')
    };
    
    try {
        const response = await fetch('/api/sessions/join', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(joinData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showLobby(result.session_id, joinData.join_code, false);
        } else {
            const error = await response.text();
            alert(error || 'Failed to join session');
        }
    } catch (error) {
        console.error('Error joining session:', error);
        alert('Error joining session');
    }
}

function showLobby(sessionId, joinCode, isHost) {
    currentSessionId = sessionId;
    
    // Show lobby modal
    document.getElementById('lobby-modal').style.display = 'flex';
    document.getElementById('lobby-join-code').textContent = joinCode;
    
    // Show/hide start button for host
    const startBtn = document.getElementById('start-competition-btn');
    if (isHost) {
        startBtn.style.display = 'block';
        startBtn.onclick = () => startCompetition(sessionId);
    } else {
        startBtn.style.display = 'none';
    }
    
    // Start listening for updates
    startEventStream(sessionId);
}

function startEventStream(sessionId) {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource(`/api/sessions/${sessionId}/stream`);
    
    eventSource.addEventListener('session_update', (e) => {
        const session = JSON.parse(e.data);
        updateLobbyPlayers(session.players);
        
        // Check if competition started
        if (session.status === 'in_progress') {
            window.location.href = `/sessions/${sessionId}`;
        }
    });
    
    eventSource.addEventListener('error', (e) => {
        console.error('SSE error:', e);
        // Retry connection
        setTimeout(() => startEventStream(sessionId), 5000);
    });
}

function updateLobbyPlayers(players) {
    const container = document.getElementById('lobby-players');
    
    container.innerHTML = players.map(player => `
        <div class="lobby-player ${player.id === currentPlayerId ? 'current-player' : ''}">
            <div class="player-info">
                <span class="player-name">${player.name}</span>
                ${player.is_host ? '<span class="host-badge">Host</span>' : ''}
            </div>
            <div class="player-model">${player.model}</div>
        </div>
    `).join('');
}

function leaveLobby() {
    if (eventSource) {
        eventSource.close();
    }
    document.getElementById('lobby-modal').style.display = 'none';
    currentSessionId = null;
}

async function startCompetition(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}/start`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Will redirect via SSE update
        } else {
            alert('Failed to start competition');
        }
    } catch (error) {
        console.error('Error starting competition:', error);
        alert('Error starting competition');
    }
}

async function loadActiveSessions() {
    try {
        const response = await fetch('/api/sessions?active=true');
        const data = await response.json();
        const container = document.getElementById('active-sessions-list');
        
        if (data.sessions && data.sessions.length > 0) {
            container.innerHTML = data.sessions.map(session => `
                <div class="session-card">
                    <div class="session-header">
                        <div>
                            <h4>${session.name}</h4>
                            <p class="text-sm text-muted">${session.game_type} - ${session.players?.length || 0}/${session.max_players} players</p>
                        </div>
                        <button class="button button-small" onclick="quickJoin('${session.join_code}')">
                            Join ${session.join_code}
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-muted">No active sessions. Create one to get started!</p>';
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

function quickJoin(joinCode) {
    document.querySelector('input[name="join-code"]').value = joinCode;
    document.querySelector('input[name="player-name"]').focus();
}