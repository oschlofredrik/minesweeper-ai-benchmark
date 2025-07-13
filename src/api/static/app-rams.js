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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializePlayForm();
    loadOverviewStats();
    loadLeaderboard();
    startGameUpdates();
    
    // Pause updates when hovering over event log
    const eventsContainer = document.getElementById('events-container');
    if (eventsContainer) {
        eventsContainer.addEventListener('mouseenter', () => {
            pauseUpdates = true;
            // Add visual indicator
            const indicator = document.getElementById('pause-indicator');
            if (indicator) indicator.style.display = 'block';
        });
        eventsContainer.addEventListener('mouseleave', () => {
            pauseUpdates = false;
            // Remove visual indicator
            const indicator = document.getElementById('pause-indicator');
            if (indicator) indicator.style.display = 'none';
        });
    }
});

// Navigation
function initializeNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('href').substring(1);
            showSection(section);
            
            // Update active state
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

// Show section
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
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

// Play Form
function initializePlayForm() {
    const form = document.getElementById('play-form');
    const modelProvider = document.getElementById('model-provider');
    
    // Update model options when provider changes
    modelProvider.addEventListener('change', updateModelOptions);
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await startEvaluation();
    });
}

// Update model dropdown based on provider
function updateModelOptions() {
    const provider = document.getElementById('model-provider').value;
    const modelSelect = document.getElementById('model-name');
    
    const models = {
        openai: [
            { value: 'gpt-4', text: 'GPT-4' },
            { value: 'gpt-3.5-turbo', text: 'GPT-3.5 Turbo' }
        ],
        anthropic: [
            { value: 'claude-3-opus', text: 'Claude 3 Opus' },
            { value: 'claude-3-sonnet', text: 'Claude 3 Sonnet' }
        ]
    };
    
    modelSelect.innerHTML = models[provider]
        .map(m => `<option value="${m.value}">${m.text}</option>`)
        .join('');
}

// Start evaluation
async function startEvaluation() {
    const statusDiv = document.getElementById('play-status');
    const submitButton = document.querySelector('#play-form button[type="submit"]');
    
    submitButton.disabled = true;
    statusDiv.innerHTML = '<div class="text-muted">Starting evaluation...</div>';
    
    const data = {
        model_provider: document.getElementById('model-provider').value,
        model_name: document.getElementById('model-name').value,
        num_games: parseInt(document.getElementById('num-games').value),
        difficulty: document.getElementById('difficulty').value || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusDiv.innerHTML = `<div class="status status-active">Evaluation started</div>`;
            activeGames.set(result.job_id, result);
            selectedGameId = result.job_id;
            updateGamesList();
            updateEventLog();
        } else {
            statusDiv.innerHTML = `<div class="status status-error">Error: ${result.detail}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status status-error">Error: ${error.message}</div>`;
    } finally {
        submitButton.disabled = false;
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
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No results yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(entry => `
            <tr>
                <td>${entry.rank}</td>
                <td>${entry.model_name}</td>
                <td>${entry.global_score.toFixed(3)}</td>
                <td>${(entry.win_rate * 100).toFixed(1)}%</td>
                <td>${(entry.valid_move_rate * 100).toFixed(1)}%</td>
                <td>${entry.total_games}</td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Failed to load</td></tr>';
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
        
        // Update sidebar
        const sidebar = document.getElementById('active-games-sidebar');
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
    } catch (error) {
        console.error('Failed to update games:', error);
    }
}

// Select game
function selectGame(gameId) {
    selectedGameId = gameId;
    updateEventLog();
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
        if (selectedGameId && !pauseUpdates) {
            updateEventLog();
        }
    }, 3000); // 3 seconds, but pauses on hover
}

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return 'Now';
    return new Date(timestamp).toLocaleTimeString();
}