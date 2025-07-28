/**
 * Minesweeper AI Benchmark - Dieter Rams Edition
 * "Good design is as little design as possible"
 */

const API_BASE = '';

// State
let activeGames = new Map();
let selectedGameId = null;
let updateInterval = null;
let pauseUpdates = false;
let eventStreamUI = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('[INIT] DOMContentLoaded - Main initialization starting');
    
    // List all sections found
    const sections = document.querySelectorAll('.section');
    console.log(`[INIT] Found ${sections.length} sections:`, Array.from(sections).map(s => s.id));
    
    // Initialize core functionality
    initializeNavigation();
    initializePlayForm();
    
    // Set up start evaluation button - redirect to evaluate page
    const startEvalBtn = document.getElementById('start-eval-btn');
    if (startEvalBtn) {
        console.log('[app-rams.js] Setting up start-eval-btn handler');
        startEvalBtn.addEventListener('click', () => {
            console.log('[app-rams.js] Start evaluation button clicked - redirecting to evaluate page');
            window.location.href = '/static/evaluate.html';
        });
    }
    
    // Load initial data
    loadOverviewStats();
    loadLeaderboard();
    startGameUpdates();
    
    // Initialize event stream UI
    eventStreamUI = new EventStreamUI('event-stream-ui');
    
    // Set up form handlers
    const joinForm = document.getElementById('join-session-form');
    if (joinForm) {
        console.log('[INIT] Found join session form');
        joinForm.addEventListener('submit', function(e) {
            console.log('[FORM] Join session form submitted');
            e.preventDefault();
            handleJoinSession(e);
        });
    } else {
        console.log('[INIT] Join session form not found');
    }
    
    const createForm = document.getElementById('create-session-form');
    if (createForm) {
        console.log('[INIT] Found create session form:', createForm);
        createForm.addEventListener('submit', function(e) {
            console.log('[FORM] Create session form submitted');
            handleCreateSession(e);
        });
        
        // Also add a capture phase listener to ensure we catch it
        createForm.addEventListener('submit', function(e) {
            console.log('[FORM] Create session form submitted (capture phase)');
            e.preventDefault();
            e.stopPropagation();
        }, true);
    } else {
        console.log('[INIT] Create session form not found');
        console.log('[INIT] Available forms:', Array.from(document.querySelectorAll('form')).map(f => f.id));
    }
    
    // Check for join code in URL
    handleJoinFromURL();
    
    // Show initial section
    const hash = window.location.hash.substring(1);
    if (hash && document.getElementById(hash)) {
        console.log(`[INIT] Navigating to hash: ${hash}`);
        navigateTo(hash);
    } else {
        console.log('[INIT] Showing default section: overview');
        showSection('overview');
    }
    
    console.log('[INIT] Main initialization complete');
});

// Navigation
function initializeNavigation() {
    console.log('[INIT] Initializing navigation');
    document.querySelectorAll('.nav-link').forEach(link => {
        console.log(`[INIT] Setting up nav link: ${link.getAttribute('href')}`);
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('href').substring(1);
            console.log(`[NAV] Nav link clicked: ${section}`);
            navigateTo(section);
        });
    });
}

// Show section
function showSection(sectionId) {
    console.log(`[NAV] showSection called with: ${sectionId}`);
    
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        console.log(`[NAV] Hiding section: ${section.id}`);
        section.style.display = 'none';
    });
    
    // Show requested section
    const section = document.getElementById(sectionId);
    if (section) {
        console.log(`[NAV] Showing section: ${sectionId}`);
        section.style.display = 'block';
    } else {
        console.error(`[NAV] Section not found: ${sectionId}`);
    }
    
    // Load section-specific data
    switch(sectionId) {
        case 'overview':
            loadOverviewStats();
            break;
        case 'leaderboard':
            loadLeaderboard();
            break;
    }
}

// Play Form (now mostly unused - evaluation moved to separate page)
function initializePlayForm() {
    console.log('[initializePlayForm] Function called - minimal setup only');
    // Most functionality moved to evaluate.html
}


// Update model dropdown based on provider - fetch from SDK
async function updateCompeteModelOptions() {
    console.log('[updateCompeteModelOptions] Function called');
    
    const provider = document.getElementById('model-provider').value;
    const modelSelect = document.getElementById('model-name');
    
    console.log(`[updateCompeteModelOptions] Provider: ${provider}`);
    console.log(`[updateCompeteModelOptions] Model select element:`, modelSelect);
    
    if (!modelSelect) {
        console.error('[updateCompeteModelOptions] Model select element not found!');
        return;
    }
    
    console.log(`[updateCompeteModelOptions] Fetching models for provider: ${provider}`);
    modelSelect.innerHTML = '<option value="">Loading models...</option>';
    
    try {
        // Fetch models from models endpoint with cache busting
        const cacheBuster = new Date().getTime();
        const response = await fetch(`/api/models/${provider}?cb=${cacheBuster}`, {
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        console.log(`[updateCompeteModelOptions] Response status: ${response.status}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`[updateCompeteModelOptions] Full response data:`, data);
        console.log(`[updateCompeteModelOptions] Number of models:`, Object.keys(data.models || {}).length);
        console.log(`[updateCompeteModelOptions] Model IDs:`, Object.keys(data.models || {}));
        
        // Build options HTML - the API returns { models: { modelId: modelInfo } }
        const models = data.models || {};
        const optionsHtml = Object.entries(models)
            .map(([modelId, modelInfo]) => {
                let displayName = modelInfo.name;
                // Check both supportsTools and supports_functions for compatibility
                if (!modelInfo.supportsTools && !modelInfo.supports_functions) {
                    displayName += ' (No Tools)';
                }
                // Mark default selection
                const selected = (modelId === 'gpt-4' || modelId === 'claude-3-opus-20240229') ? ' selected' : '';
                return `<option value="${modelId}"${selected}>${displayName}</option>`;
            })
            .join('');
        
        modelSelect.innerHTML = optionsHtml;
        
        // Show API key warning if not configured
        if (!data.has_api_key) {
            console.warn(`${provider.toUpperCase()}_API_KEY not configured`);
        }
        
    } catch (error) {
        console.error('Failed to load models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
        alert(`Failed to load models: ${error.message}`);
    }
}


// Load overview statistics
async function loadOverviewStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const stats = await response.json();
        
        document.getElementById('total-evaluations').textContent = 
            stats.total_evaluations || '0';
        document.getElementById('models-tested').textContent = 
            stats.unique_models || '0';
        document.getElementById('best-win-rate').textContent = 
            stats.best_win_rate ? `${(stats.best_win_rate * 100).toFixed(1)}%` : '0%';
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load leaderboard
async function loadLeaderboard() {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Loading...</td></tr>';
    
    try {
        const response = await fetch(`${API_BASE}/api/leaderboard?metric=global_score`);
        const data = await response.json();
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No results yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(entry => `
            <tr>
                <td>${entry.rank}</td>
                <td>${entry.model_name}</td>
                <td class="text-strong">${entry.global_score.toFixed(3)}</td>
                <td>${entry.ms_s_score.toFixed(3)}</td>
                <td>${entry.ms_i_score.toFixed(3)}</td>
                <td>${(entry.win_rate * 100).toFixed(1)}%</td>
                <td>${entry.reasoning_score ? entry.reasoning_score.toFixed(2) : '-'}</td>
                <td>${entry.total_games || entry.num_games}</td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Failed to load</td></tr>';
    }
}

// Update games list
async function updateGamesList() {
    try {
        const response = await fetch(`${API_BASE}/api/play/games`);
        const games = await response.json();
        
        // Update active games map
        games.forEach(game => {
            activeGames.set(game.job_id, game);
        });
        
        // Update sidebar if it exists
        const sidebar = document.getElementById('active-games-sidebar');
        if (sidebar) {
            if (games.length === 0) {
                sidebar.innerHTML = '<p class="text-sm text-muted">No active games</p>';
            } else {
                sidebar.innerHTML = games.map(game => `
                    <div class="mb-2" style="cursor: pointer;" onclick="selectGame('${game.job_id}')">
                        <div class="text-sm">${game.model_name}</div>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${game.progress * 100}%"></div>
                        </div>
                        <div class="text-sm text-muted">${game.message}</div>
                    </div>
                `).join('');
            }
        }
        
        // Also update the active sessions sidebar if present
        const sessionsSidebar = document.getElementById('active-sessions-sidebar');
        if (sessionsSidebar && games.length > 0) {
            sessionsSidebar.innerHTML = games.map(game => `
                <div class="mb-2" style="cursor: pointer;" onclick="selectGame('${game.job_id}')">
                    <div class="text-sm">${game.model_name}</div>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${game.progress * 100}%"></div>
                    </div>
                    <div class="text-sm text-muted">${game.message}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to update games:', error);
    }
}

// Select game
function selectGame(gameId) {
    selectedGameId = gameId;
    
    // Connect event stream to selected game
    if (eventStreamUI) {
        eventStreamUI.connect(gameId);
    }
}

// Update event log
async function updateEventLog() {
    if (!selectedGameId) return;
    
    const container = document.getElementById('events-container');
    
    // Store which details elements are open before update
    const openDetails = new Set();
    container.querySelectorAll('details[open]').forEach(detail => {
        // Create a unique identifier for each detail element
        const summary = detail.querySelector('summary');
        if (summary) {
            openDetails.add(summary.textContent.trim());
        }
    });
    
    try {
        const response = await fetch(`${API_BASE}/api/play/games/${selectedGameId}`);
        const game = await response.json();
        
        let html = '<div class="text-sm">';
        
        // Start event
        html += `
            <div class="mb-2">
                <div class="text-muted">${formatTime(game.started_at)}</div>
                <div>Started ${game.games_total} games</div>
            </div>
        `;
        
        // Progress
        if (game.games_completed > 0) {
            html += `
                <div class="mb-2">
                    <div class="text-muted">Progress</div>
                    <div>${game.games_completed}/${game.games_total} completed</div>
                </div>
            `;
        }
        
        // Current metrics
        if (game.current_metrics) {
            html += `
                <div class="mb-2">
                    <div class="text-muted">Current Performance</div>
                    <div>Win Rate: ${(game.current_metrics.win_rate * 100).toFixed(1)}%</div>
                    <div>Valid Moves: ${(game.current_metrics.valid_move_rate * 100).toFixed(1)}%</div>
                </div>
            `;
        }
        
        // If completed, try to load detailed move data
        if (game.status === 'completed' && game.results_file) {
            try {
                const resultsResponse = await fetch(`${API_BASE}/api/play/games/${selectedGameId}/results`);
                if (resultsResponse.ok) {
                    const results = await resultsResponse.json();
                    
                    // Show detailed game-by-game moves
                    if (results.game_results) {
                        html += '<div class="mt-4"><div class="text-muted mb-2">Game Details</div>';
                        
                        results.game_results.forEach((gameResult, idx) => {
                            html += `
                                <details class="mb-3">
                                    <summary class="cursor-pointer mb-2">
                                        Game ${idx + 1}: ${gameResult.won ? '✓ WON' : '✗ LOST'} 
                                        (${gameResult.num_moves} moves)
                                    </summary>
                                    <div class="ml-4">
                            `;
                            
                            // Show moves with AI details
                            if (gameResult.moves && gameResult.moves.length > 0) {
                                gameResult.moves.forEach(move => {
                                    html += `
                                        <details class="mb-2 border-left pl-2">
                                            <summary class="text-sm cursor-pointer">
                                                Move ${move.move_number}: ${move.action} 
                                                ${move.was_valid ? '✓' : '✗'}
                                            </summary>
                                            <div class="ml-3 text-xs">
                                    `;
                                    
                                    // Show prompt if available
                                    if (move.prompt_sent) {
                                        html += `
                                            <details class="mb-1">
                                                <summary class="text-muted cursor-pointer">Prompt Sent to API</summary>
                                                <pre class="mt-1 p-2 bg-secondary overflow-x-auto" style="max-height: 300px; font-size: 11px; line-height: 1.4;">${escapeHtml(move.prompt_sent)}</pre>
                                            </details>
                                        `;
                                    }
                                    
                                    // Show full response if available
                                    if (move.full_response) {
                                        html += `
                                            <details class="mb-1">
                                                <summary class="text-muted cursor-pointer">Full AI Response</summary>
                                                <pre class="mt-1 p-2 bg-secondary overflow-x-auto" style="max-height: 300px; font-size: 11px; line-height: 1.4;">${escapeHtml(move.full_response)}</pre>
                                            </details>
                                        `;
                                    }
                                    
                                    // Show reasoning
                                    if (move.reasoning) {
                                        html += `
                                            <details class="mb-1">
                                                <summary class="text-muted cursor-pointer">AI Reasoning</summary>
                                                <div class="mt-1 p-2 bg-secondary">${escapeHtml(move.reasoning)}</div>
                                            </details>
                                        `;
                                    }
                                    
                                    // Show tokens used and timestamp
                                    const moveInfo = [];
                                    if (move.tokens_used) {
                                        moveInfo.push(`Tokens: ${move.tokens_used}`);
                                    }
                                    if (move.timestamp) {
                                        moveInfo.push(`Time: ${formatTime(move.timestamp)}`);
                                    }
                                    if (moveInfo.length > 0) {
                                        html += `<div class="text-muted text-xs">${moveInfo.join(' • ')}</div>`;
                                    }
                                    
                                    // Show error if any
                                    if (move.error) {
                                        html += `
                                            <div class="text-danger mt-1"><strong>Error:</strong> ${escapeHtml(move.error)}</div>
                                        `;
                                    }
                                    
                                    html += `
                                            </div>
                                        </details>
                                    `;
                                });
                            } else {
                                html += '<div class="text-muted text-sm ml-4">No move data available</div>';
                            }
                            
                            // Show game statistics
                            html += `
                                        <div class="mt-2 pt-2 border-top text-sm">
                                            <strong>Game Statistics:</strong>
                                            <div class="ml-2">
                                                <div>Board Coverage: ${(gameResult.board_coverage * 100).toFixed(1)}%</div>
                                                <div>Mines Found: ${gameResult.mines_correctly_flagged}/${gameResult.total_mines}</div>
                                                <div>Valid Move Rate: ${(gameResult.valid_move_rate * 100).toFixed(1)}%</div>
                                                <div>Duration: ${(gameResult.duration || 0).toFixed(1)}s</div>
                                            </div>
                                        </div>
                                    </div>
                                </details>
                            `;
                        });
                        
                        html += '</div>';
                    }
                }
            } catch (error) {
                console.error('Failed to load detailed results:', error);
            }
        }
        
        html += '</div>';
        container.innerHTML = html;
        
        // Restore open state of details elements
        container.querySelectorAll('details').forEach(detail => {
            const summary = detail.querySelector('summary');
            if (summary && openDetails.has(summary.textContent.trim())) {
                detail.open = true;
            }
        });
        
    } catch (error) {
        container.innerHTML = '<p class="text-sm text-muted">Failed to load events</p>';
    }
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start periodic updates
function startGameUpdates() {
    updateInterval = setInterval(() => {
        updateGamesList();
        // Event streaming handles real-time updates now
    }, 3000);
}

// Competition Functions
function showCreateSession() {
    const modal = document.getElementById('create-session-modal');
    const result = document.getElementById('create-session-result');
    
    // Copy form from compete section
    const form = document.getElementById('create-session-form');
    result.innerHTML = form.outerHTML;
    
    // Add event listener to copied form
    const newForm = result.querySelector('form');
    newForm.addEventListener('submit', handleCreateSession);
    
    modal.classList.add('active');
}

function showJoinSession() {
    console.log('[UI] showJoinSession called');
    const modal = document.getElementById('join-session-modal');
    if (modal) {
        console.log('[UI] Opening join session modal');
        modal.classList.add('active');
    } else {
        console.error('[UI] Join session modal not found');
    }
}

function hideModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

async function handleCreateSession(e) {
    console.log('[SESSION] handleCreateSession called');
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const creatorId = 'user-' + Math.random().toString(36).substr(2, 9);
    window.currentPlayerId = creatorId;
    
    console.log('[SESSION] Creating session with data:', {
        name: formData.get('session-name'),
        gameType: formData.get('game-type'),
        format: formData.get('competition-format'),
        maxPlayers: formData.get('max-players')
    });
    
    const sessionData = {
        name: formData.get('session-name'),
        description: `${formData.get('game-type')} competition`,
        format: formData.get('competition-format'),
        rounds_config: [{
            game_name: formData.get('game-type'),
            difficulty: 'medium',
            mode: 'mixed',
            scoring_profile: 'balanced',
            time_limit: 300,
            evaluations: selectedEvaluations  // Include selected evaluations
        }],
        creator_id: creatorId,
        max_players: parseInt(formData.get('max-players')),
        is_public: true,
        flow_mode: 'asynchronous'
    };
    
    try {
        const response = await fetch('/api/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showLobby(result.session_id, result.join_code, true, creatorId);
            hideModal('create-session-modal');
        } else {
            alert('Failed to create session');
        }
    } catch (error) {
        console.error('Error creating session:', error);
        alert('Error creating session');
    }
}

async function handleJoinSession(e) {
    console.log('[SESSION] handleJoinSession called');
    e.preventDefault();
    
    // Get join code and player info from the form
    const joinCode = document.getElementById('join-code').value.toUpperCase();
    const playerName = document.getElementById('player-name').value || 'Player-' + Math.random().toString(36).substr(2, 5);
    const playerModel = document.getElementById('player-model').value;
    const playerId = 'player-' + Math.random().toString(36).substr(2, 9);
    window.currentPlayerId = playerId;
    
    console.log('[SESSION] Joining with:', { joinCode, playerName, playerModel });
    
    try {
        const response = await fetch('/api/sessions/join', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                join_code: joinCode,
                player_id: playerId,
                player_name: playerName,
                ai_model: null  // Will be selected in lobby
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showLobby(result.session_id, joinCode, false, playerId);
            hideModal('join-session-modal');
        } else {
            alert('Invalid join code');
        }
    } catch (error) {
        console.error('Error joining session:', error);
        alert('Error joining session');
    }
}

function showLobby(sessionId, joinCode, isHost, playerId = null) {
    const modal = document.getElementById('session-lobby-modal');
    document.getElementById('lobby-join-code').textContent = joinCode;
    
    // Store session info globally
    window.currentSession = {
        sessionId: sessionId,
        playerId: playerId || window.currentPlayerId,
        isHost: isHost
    };
    
    if (isHost) {
        document.getElementById('start-competition-btn').style.display = 'block';
        document.getElementById('host-message').style.display = 'block';
    }
    
    // Initialize competition manager
    if (window.competitionManager) {
        window.competitionManager.sessionId = sessionId;
        window.competitionManager.playerId = playerId || window.currentPlayerId;
        window.competitionManager.isHost = isHost;
    }
    
    modal.classList.add('active');
    
    // Start polling for lobby updates
    updateLobby(sessionId);
    window.lobbyInterval = setInterval(() => updateLobby(sessionId), 2000);
}

async function updateLobby(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}/lobby`);
        if (response.ok) {
            const data = await response.json();
            renderLobbyPlayers(data.players);
        }
    } catch (error) {
        console.error('Error updating lobby:', error);
    }
}

function renderLobbyPlayers(players) {
    const container = document.getElementById('lobby-players');
    container.innerHTML = players.map(player => `
        <div class="player-card ${player.is_ready ? 'ready' : ''}">
            <div class="player-name">${player.name}</div>
            <div class="player-model">${player.ai_model || 'Not selected'}</div>
            ${player.is_ready ? '<div class="text-sm text-success">Ready</div>' : '<div class="text-sm text-muted">Waiting</div>'}
        </div>
    `).join('');
}

function leaveLobby() {
    hideModal('session-lobby-modal');
    if (window.lobbyInterval) {
        clearInterval(window.lobbyInterval);
    }
}

// Update player's AI model
async function updatePlayerModel() {
    const modelSelect = document.getElementById('lobby-model-select');
    const selectedModel = modelSelect.value;
    
    if (!selectedModel) {
        alert('Please select an AI model first');
        return;
    }
    
    if (!window.currentSession) {
        alert('Session information not found');
        return;
    }
    
    // For now, just store locally and show in UI
    window.currentPlayerModel = selectedModel;
    
    // Update UI to show selected model
    const btn = document.getElementById('update-model-btn');
    btn.textContent = 'Model Selected ✓';
    btn.disabled = true;
    
    setTimeout(() => {
        btn.textContent = 'Update Model';
        btn.disabled = false;
    }, 2000);
}

// Toggle ready status
async function toggleReady() {
    if (!window.currentSession) {
        alert('Session information not found');
        return;
    }
    
    if (!window.currentPlayerModel && !window.currentSession.isHost) {
        alert('Please select an AI model before marking ready');
        return;
    }
    
    const readyBtn = document.getElementById('ready-btn');
    const isReady = readyBtn.classList.contains('ready');
    
    try {
        // If using competition manager
        if (window.competitionManager && window.competitionManager.setReady) {
            await window.competitionManager.setReady(!isReady);
        } else {
            // Direct API call
            const response = await fetch(`/api/sessions/${window.currentSession.sessionId}/ready?player_id=${window.currentSession.playerId}&ready=${!isReady}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error('Failed to update ready status');
            }
        }
        
        // Update button UI
        if (!isReady) {
            readyBtn.classList.add('ready');
            document.getElementById('ready-btn-text').textContent = 'Click to Unready';
        } else {
            readyBtn.classList.remove('ready');
            document.getElementById('ready-btn-text').textContent = 'Click to Mark Ready';
        }
        
    } catch (error) {
        console.error('Error updating ready status:', error);
        alert('Failed to update ready status');
    }
}

// Start the competition (host only)
async function startCompetition() {
    if (!window.currentSession || !window.currentSession.isHost) {
        alert('Only the host can start the competition');
        return;
    }
    
    try {
        // Use competition manager if available
        if (window.competitionManager && window.competitionManager.startCompetition) {
            await window.competitionManager.startCompetition();
        } else {
            // Direct API call
            const response = await fetch(`/api/sessions/${window.currentSession.sessionId}/start?player_id=${window.currentSession.playerId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                // Clear lobby interval
                if (window.lobbyInterval) {
                    clearInterval(window.lobbyInterval);
                }
                
                // Show competition view
                if (window.competitionManager) {
                    window.competitionManager.showCompetitionView();
                } else {
                    alert('Competition started! Watch the progress in the event stream.');
                }
            } else {
                const error = await response.json();
                alert(error.detail || 'Failed to start competition');
            }
        }
    } catch (error) {
        console.error('Error starting competition:', error);
        alert('Failed to start competition');
    }
}

function navigateTo(section) {
    console.log(`[NAV] navigateTo called with: ${section}`);
    showSection(section);
    
    // Update nav
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + section) {
            console.log(`[NAV] Activating nav link: ${link.getAttribute('href')}`);
            link.classList.add('active');
        }
    });
    
    // Update URL without reload
    if (history.pushState) {
        history.pushState(null, null, '#' + section);
    }
}

// Session Management
async function loadActiveSessions() {
    try {
        const response = await fetch('/api/sessions/templates/quick-match');
        if (response.ok) {
            const templates = await response.json();
            renderSessionTemplates(templates);
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

function renderSessionTemplates(templates) {
    const container = document.getElementById('active-sessions-list');
    if (templates.length === 0) {
        container.innerHTML = '<p class="text-muted">No active sessions. Create one to get started!</p>';
        return;
    }
    
    container.innerHTML = templates.map(template => `
        <div class="session-card" onclick="useTemplate('${template.game}')">
            <div class="session-header">
                <div>
                    <h4>${template.name}</h4>
                    <p class="text-sm text-muted">${template.description}</p>
                </div>
                <span class="session-status waiting">Quick Match</span>
            </div>
            <div class="session-meta">
                <span>Duration: ~${template.estimated_duration} min</span>
                <span>Difficulty: ${template.difficulty}</span>
            </div>
        </div>
    `).join('');
}

async function useTemplate(gameName) {
    // Pre-fill create form with template
    document.getElementById('session-name').value = `Quick ${gameName.charAt(0).toUpperCase() + gameName.slice(1)} Match`;
    document.getElementById('game-type').value = gameName;
    document.getElementById('competition-format').value = 'single_round';
    showCreateSession();
}

// Competition features are initialized in main DOMContentLoaded handler

// Global evaluation selector instance
let evaluationSelector = null;
let selectedMetrics = [];

// Show evaluation selector modal
function showEvaluationSelector() {
    const modal = document.getElementById('evaluation-selector-modal');
    modal.classList.add('active');
    
    // Initialize selector if not already done
    if (!evaluationSelector) {
        evaluationSelector = new EvaluationSelector('evaluation-selector-container', {
            maxMetrics: 5,
            allowCustomWeights: true,
            onUpdate: (metrics) => {
                selectedMetrics = metrics;
                updateEvaluationSummary();
            }
        });
    }
}

// Hide evaluation selector modal
function hideEvaluationSelector() {
    const modal = document.getElementById('evaluation-selector-modal');
    modal.classList.remove('active');
}

// Save evaluation selection
function saveEvaluationSelection() {
    if (evaluationSelector) {
        const validation = evaluationSelector.validateSelection();
        if (!validation.valid) {
            alert(validation.message);
            return;
        }
        
        selectedMetrics = evaluationSelector.getSelectedMetrics();
        updateEvaluationSummary();
        hideEvaluationSelector();
    }
}

// Update evaluation summary display
function updateEvaluationSummary() {
    const summary = document.getElementById('selected-evaluations-summary');
    if (!summary) return;
    
    if (selectedMetrics.length === 0) {
        summary.textContent = 'No metrics selected (using default scoring)';
    } else {
        const names = selectedMetrics.map(m => {
            const percent = (m.weight * 100).toFixed(0);
            return `${m.name} (${percent}%)`;
        });
        summary.textContent = `${selectedMetrics.length} metrics: ${names.join(', ')}`;
    }
}

// Update difficulty options based on selected game
function updateDifficultyOptions() {
    const gameSelect = document.getElementById('game-select');
    const difficultySelect = document.getElementById('difficulty');
    
    if (!gameSelect || !difficultySelect) return;
    
    const game = gameSelect.value;
    
    // Clear existing options
    difficultySelect.innerHTML = '';
    
    // Add options based on game
    if (game === 'minesweeper') {
        difficultySelect.innerHTML = `
            <option value="">Auto</option>
            <option value="beginner">Beginner (9×9, 10 mines)</option>
            <option value="intermediate">Intermediate (16×16, 40 mines)</option>
            <option value="expert">Expert (16×30, 99 mines)</option>
        `;
    } else if (game === 'risk') {
        difficultySelect.innerHTML = `
            <option value="">Standard</option>
            <option value="scenario:north_america_conquest">Scenario: North America Conquest</option>
            <option value="scenario:defend_australia">Scenario: Defend Australia</option>
            <option value="scenario:europe_vs_asia">Scenario: Europe vs Asia</option>
            <option value="scenario:blitzkrieg">Scenario: Blitzkrieg</option>
            <option value="scenario:last_stand">Scenario: Last Stand</option>
        `;
    } else if (game === 'number_puzzle') {
        difficultySelect.innerHTML = `
            <option value="easy">Easy (1-10)</option>
            <option value="medium">Medium (1-100)</option>
            <option value="hard">Hard (1-1000)</option>
        `;
    } else {
        difficultySelect.innerHTML = '<option value="">Default</option>';
    }
}

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return 'Now';
    return new Date(timestamp).toLocaleTimeString();
}

// Handle join from URL
function handleJoinFromURL() {
    const path = window.location.pathname;
    const joinMatch = path.match(/^\/join\/([A-Z0-9]+)$/i);
    
    if (joinMatch) {
        const joinCode = joinMatch[1].toUpperCase();
        
        // Show join modal with pre-filled code
        document.getElementById('quick-join-code').value = joinCode;
        document.getElementById('join-session-modal').classList.add('active');
        
        // Auto-submit after a brief delay to show the code
        setTimeout(() => {
            const form = document.getElementById('quick-join-form');
            form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        }, 500);
        
        // Update URL to remove join code
        window.history.replaceState({}, document.title, '/');
    }
}