// Minesweeper AI Benchmark Web App

// Global state
let currentMetric = 'global_score';
let currentTaskType = '';

// Ensure all API calls use the same protocol as the page
const API_BASE = '';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard();
    loadPlatformStats();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                showSection(link.getAttribute('href').substring(1));
            }
        });
    });

    // Filters
    document.getElementById('metric-select').addEventListener('change', (e) => {
        currentMetric = e.target.value;
        loadLeaderboard();
    });

    document.getElementById('task-type-select').addEventListener('change', (e) => {
        currentTaskType = e.target.value;
        loadLeaderboard();
    });

    // Play form
    const playForm = document.getElementById('play-form');
    if (playForm) {
        playForm.addEventListener('submit', handlePlay);
    }
}

// Show section
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    document.getElementById(sectionId).style.display = 'block';

    // Update nav active state
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
        }
    });
}

// Load leaderboard data
async function loadLeaderboard() {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '<tr><td colspan="8" class="loading">Loading...</td></tr>';

    try {
        let url = `/api/leaderboard?metric=${currentMetric}`;
        if (currentTaskType) {
            url += `&task_type=${currentTaskType}`;
        }

        const response = await fetch(`${API_BASE}${url}`);
        const data = await response.json();

        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">No results found</td></tr>';
            return;
        }

        data.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${entry.rank}</td>
                <td><strong>${formatModelName(entry.model_name)}</strong></td>
                <td>${formatScore(entry.global_score)}</td>
                <td>${formatPercent(entry.win_rate)}</td>
                <td>${formatPercent(entry.accuracy)}</td>
                <td>${formatPercent(entry.coverage)}</td>
                <td>${formatScore(entry.reasoning_score)}</td>
                <td>${entry.num_games}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="8" class="loading">Error loading data: ${error.message}</td></tr>`;
    }
}

// Currently selected game
let selectedGameId = null;
let eventsUpdateInterval = null;

// Select a game and show its events
async function selectGame(jobId, element) {
    selectedGameId = jobId;
    
    // Highlight selected game
    document.querySelectorAll('.game-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Find and highlight the clicked element
    if (!element && event && event.currentTarget) {
        element = event.currentTarget;
    }
    if (element) {
        element.classList.add('selected');
    }
    
    // Start updating events
    updateGameEvents();
    
    // Clear existing interval and set new one
    if (eventsUpdateInterval) {
        clearInterval(eventsUpdateInterval);
    }
    eventsUpdateInterval = setInterval(updateGameEvents, 1000);
}

// Update game events panel
async function updateGameEvents() {
    if (!selectedGameId) return;
    
    const eventsContainer = document.getElementById('events-container');
    if (!eventsContainer) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/play/games/${selectedGameId}`);
        const game = await response.json();
        
        if (!game) {
            eventsContainer.innerHTML = '<p class="empty-state">Game not found</p>';
            return;
        }
        
        // Build events HTML
        let eventsHtml = `
            <div class="event-item">
                <div class="event-timestamp">${game.started_at ? new Date(game.started_at).toLocaleTimeString() : 'Now'}</div>
                <div class="event-content">Game started - ${game.games_total || 0} games</div>
            </div>
        `;
        
        // Add progress events
        if (game.games_completed !== undefined && game.games_total > 0) {
            eventsHtml += `
                <div class="event-item">
                    <div class="event-timestamp">Current</div>
                    <div class="event-content">Playing game ${game.games_completed + 1}/${game.games_total}</div>
                </div>
            `;
        }
        
        // If we have detailed game results, show move-by-move events
        if (game.results_file) {
            try {
                const resultsResponse = await fetch(`${API_BASE}/api/play/games/${selectedGameId}/results`);
                if (resultsResponse.ok) {
                    const results = await resultsResponse.json();
                    
                    if (results.game_results) {
                        results.game_results.forEach((gameResult, gameIndex) => {
                            eventsHtml += `
                                <div class="event-item ${gameResult.won ? 'win' : 'loss'}">
                                    <div class="event-timestamp">Game ${gameIndex + 1}</div>
                                    <div class="event-content">
                                        ${gameResult.won ? '✓ WON' : '✗ LOST'} - 
                                        ${gameResult.num_moves} moves
                                    </div>
                                </div>
                            `;
                            
                            // Show last few moves for the most recent game
                            if (gameResult.moves && gameIndex === game.current_game - 2) {
                                const recentMoves = gameResult.moves.slice(-5);
                                recentMoves.forEach(move => {
                                    eventsHtml += `
                                        <div class="event-item move ${move.was_valid ? 'valid' : 'invalid'}">
                                            <div class="event-timestamp">Move ${move.move_number}</div>
                                            <div class="event-content">
                                                ${move.action} - ${move.was_valid ? 'Valid' : 'Invalid'}
                                            </div>
                                            ${move.reasoning ? `
                                                <div class="event-reasoning">
                                                    ${move.reasoning.substring(0, 150)}...
                                                </div>
                                            ` : ''}
                                        </div>
                                    `;
                                });
                            }
                        });
                    }
                }
            } catch (error) {
                console.error('Error loading game results:', error);
            }
        }
        
        // Add completion event
        if (game.status === 'completed') {
            eventsHtml += `
                <div class="event-item win">
                    <div class="event-timestamp">${new Date(game.completed_at).toLocaleTimeString()}</div>
                    <div class="event-content">
                        Evaluation completed - 
                        <a href="/summary/${selectedGameId}" target="_blank">View Summary</a>
                    </div>
                </div>
            `;
            
            // Stop updating once completed
            if (eventsUpdateInterval) {
                clearInterval(eventsUpdateInterval);
                eventsUpdateInterval = null;
            }
        } else if (game.status === 'failed') {
            eventsHtml += `
                <div class="event-item loss">
                    <div class="event-timestamp">${new Date(game.completed_at).toLocaleTimeString()}</div>
                    <div class="event-content">Evaluation failed: ${game.error || 'Unknown error'}</div>
                </div>
            `;
            
            // Stop updating once failed
            if (eventsUpdateInterval) {
                clearInterval(eventsUpdateInterval);
                eventsUpdateInterval = null;
            }
        }
        
        eventsContainer.innerHTML = eventsHtml;
        
        // Auto-scroll to bottom
        eventsContainer.scrollTop = eventsContainer.scrollHeight;
        
    } catch (error) {
        eventsContainer.innerHTML = `<p class="empty-state">Error loading events: ${error.message}</p>`;
    }
}

// Load platform statistics
async function loadPlatformStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();

        document.getElementById('total-evaluations').textContent = data.total_evaluations;
        document.getElementById('unique-models').textContent = data.unique_models;
        document.getElementById('total-tasks').textContent = data.total_tasks;
    } catch (error) {
        console.error('Failed to load platform stats:', error);
    }
}

// Format model name
function formatModelName(name) {
    // Extract just the model name from provider/model format
    const parts = name.split('/');
    const modelName = parts[parts.length - 1];
    
    // Add provider badge
    if (name.includes('openai')) {
        return `${modelName} <span class="muted">(OpenAI)</span>`;
    } else if (name.includes('anthropic')) {
        return `${modelName} <span class="muted">(Anthropic)</span>`;
    }
    return modelName;
}

// Format score
function formatScore(score) {
    if (score === null || score === undefined) return '-';
    
    const value = (score * 100).toFixed(1);
    const className = score >= 0.7 ? 'score-high' : score >= 0.4 ? 'score-medium' : 'score-low';
    
    return `<span class="score-badge ${className}">${value}</span>`;
}

// Format percentage
function formatPercent(value) {
    if (value === null || value === undefined) return '-';
    return (value * 100).toFixed(1) + '%';
}

// Auto-refresh leaderboard every 30 seconds
setInterval(() => {
    if (document.querySelector('nav a[href="#leaderboard"]').classList.contains('active')) {
        loadLeaderboard();
    }
}, 30000);

// Model configurations
const modelConfigs = {
    openai: [
        {id: 'gpt-4', name: 'GPT-4'},
        {id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo'},
        {id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo'}
    ],
    anthropic: [
        {id: 'claude-3-opus-20240229', name: 'Claude 3 Opus'},
        {id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet'},
        {id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku'}
    ]
};

// Update model list based on provider
function updateModelList() {
    const provider = document.getElementById('model-provider').value;
    const modelSelect = document.getElementById('model-name');
    
    modelSelect.innerHTML = '';
    modelConfigs[provider].forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        modelSelect.appendChild(option);
    });
}

// Handle play (combined game generation and evaluation)
async function handlePlay(e) {
    e.preventDefault();
    
    const button = e.target.querySelector('button[type="submit"]');
    const statusDiv = document.getElementById('play-status');
    
    button.disabled = true;
    statusDiv.className = 'status-message info';
    statusDiv.textContent = 'Starting games...';
    
    const data = {
        model_name: document.getElementById('model-name').value,
        model_provider: document.getElementById('model-provider').value,
        num_games: parseInt(document.getElementById('num-games').value),
        difficulty: document.getElementById('game-difficulty').value || null,
        game_type: document.getElementById('game-type').value || null,
        api_key: document.getElementById('api-key').value || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/play`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusDiv.className = 'status-message success';
            statusDiv.textContent = `✅ ${result.message}`;
            pollJobStatus(result.job_id);
            updateGamesList();
        } else {
            statusDiv.className = 'status-message error';
            statusDiv.textContent = `❌ Error: ${result.detail}`;
        }
    } catch (error) {
        statusDiv.className = 'status-message error';
        statusDiv.textContent = `❌ Error: ${error.message}`;
    } finally {
        button.disabled = false;
    }
}

// Poll job status
async function pollJobStatus(jobId) {
    // Auto-select this game to show events
    selectedGameId = jobId;
    updateGameEvents();
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/play/games/${jobId}`);
            const job = await response.json();
            
            updateGamesList();
            
            // Update events if this is still the selected game
            if (selectedGameId === jobId) {
                updateGameEvents();
            }
            
            if (job.status === 'completed' || job.status === 'failed') {
                clearInterval(interval);
                if (job.status === 'completed') {
                    loadLeaderboard();
                    loadPlatformStats();
                }
            }
        } catch (error) {
            clearInterval(interval);
        }
    }, 2000);
}

// Update games list
async function updateGamesList() {
    try {
        const response = await fetch(`${API_BASE}/api/play/games`);
        const games = await response.json();
        
        const gamesList = document.getElementById('games-list');
        if (!gamesList) return;
        
        if (games.length === 0) {
            gamesList.innerHTML = '<p class="empty-state">No active games</p>';
        } else {
            gamesList.innerHTML = games.map(game => `
                <div class="game-item ${game.status}" onclick="selectGame('${game.job_id}', this)">
                    <div class="game-header">
                        <strong>${game.model_name}</strong>
                        <span class="game-status ${game.status}">${game.status.toUpperCase()}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${game.progress * 100}%"></div>
                    </div>
                    <p class="game-message">${game.message}</p>
                    ${game.status === 'completed' && game.current_metrics ? `
                        <div class="game-metrics">
                            <span>Win Rate: ${(game.current_metrics.win_rate * 100).toFixed(1)}%</span>
                            <span>Valid Moves: ${(game.current_metrics.valid_move_rate * 100).toFixed(1)}%</span>
                        </div>
                        <a href="/summary/${game.job_id}" class="view-summary">View Detailed Summary →</a>
                    ` : ''}
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading games:', error);
    }
}

// Auto-refresh games when on play page
setInterval(() => {
    if (document.querySelector('nav a[href="#play"]')?.classList.contains('active')) {
        updateGamesList();
    }
}, 5000);