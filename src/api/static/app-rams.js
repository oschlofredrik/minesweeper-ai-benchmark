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
    initializeNavigation();
    initializePlayForm();
    loadOverviewStats();
    loadLeaderboard();
    startGameUpdates();
    
    // Initialize event stream UI
    eventStreamUI = new EventStreamUI('event-stream-ui');
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
    
    // Initialize model options on page load
    updateModelOptions();
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await startEvaluation();
    });
    
    // Modal handling
    const evalModal = document.getElementById('eval-modal');
    const modalClose = document.querySelector('.modal-close');
    
    // Close modal on successful submission
    window.closeEvalModal = function() {
        if (evalModal) evalModal.classList.remove('active');
    };
    
    // Close modal when clicking the X button
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            if (evalModal) evalModal.classList.remove('active');
        });
    }
    
    // Close modal when clicking outside
    if (evalModal) {
        evalModal.addEventListener('click', (e) => {
            if (e.target === evalModal) {
                evalModal.classList.remove('active');
            }
        });
    }
    
    // Close modal on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && evalModal && evalModal.classList.contains('active')) {
            evalModal.classList.remove('active');
        }
    });
}

// Update model dropdown based on provider
function updateModelOptions() {
    const provider = document.getElementById('model-provider').value;
    const modelSelect = document.getElementById('model-name');
    
    const models = {
        openai: [
            // Reasoning models (o1/o3/o4 series)
            { value: 'o4-mini', text: 'o4-mini (Latest Reasoning)' },
            { value: 'o3-mini', text: 'o3-mini (Reasoning)' },
            { value: 'o1-preview', text: 'o1-preview (Reasoning)' },
            { value: 'o1-preview-2024-09-12', text: 'o1-preview-2024-09-12' },
            { value: 'o1-mini', text: 'o1-mini (Reasoning)' },
            { value: 'o1-mini-2024-09-12', text: 'o1-mini-2024-09-12' },
            
            // GPT-4o series
            { value: 'gpt-4o', text: 'GPT-4o (Latest)' },
            { value: 'gpt-4o-2024-11-20', text: 'GPT-4o (2024-11-20)' },
            { value: 'gpt-4o-2024-08-06', text: 'GPT-4o (2024-08-06)' },
            { value: 'gpt-4o-2024-05-13', text: 'GPT-4o (2024-05-13)' },
            { value: 'gpt-4o-mini', text: 'GPT-4o Mini' },
            { value: 'gpt-4o-mini-2024-07-18', text: 'GPT-4o Mini (2024-07-18)' },
            
            // GPT-4 Turbo series
            { value: 'gpt-4-turbo', text: 'GPT-4 Turbo' },
            { value: 'gpt-4-turbo-2024-04-09', text: 'GPT-4 Turbo (2024-04-09)' },
            { value: 'gpt-4-turbo-preview', text: 'GPT-4 Turbo Preview' },
            { value: 'gpt-4-0125-preview', text: 'GPT-4 Turbo (2024-01-25)' },
            { value: 'gpt-4-1106-preview', text: 'GPT-4 Turbo (2023-11-06)' },
            
            // Classic GPT-4
            { value: 'gpt-4', text: 'GPT-4' },
            { value: 'gpt-4-0613', text: 'GPT-4 (2023-06-13)' },
            
            // GPT-3.5
            { value: 'gpt-3.5-turbo', text: 'GPT-3.5 Turbo' },
            { value: 'gpt-3.5-turbo-0125', text: 'GPT-3.5 Turbo (2024-01-25)' },
            { value: 'gpt-3.5-turbo-1106', text: 'GPT-3.5 Turbo (2023-11-06)' }
        ],
        anthropic: [
            // Claude 3.5 series
            { value: 'claude-3-5-sonnet-20241022', text: 'Claude 3.5 Sonnet (Latest)' },
            { value: 'claude-3-5-sonnet-20240620', text: 'Claude 3.5 Sonnet (2024-06-20)' },
            { value: 'claude-3-5-haiku-20241022', text: 'Claude 3.5 Haiku' },
            
            // Claude 3 series
            { value: 'claude-3-opus-20240229', text: 'Claude 3 Opus' },
            { value: 'claude-3-sonnet-20240229', text: 'Claude 3 Sonnet' },
            { value: 'claude-3-haiku-20240307', text: 'Claude 3 Haiku' },
            
            // Legacy models
            { value: 'claude-2.1', text: 'Claude 2.1' },
            { value: 'claude-2.0', text: 'Claude 2.0' },
            { value: 'claude-instant-1.2', text: 'Claude Instant 1.2' }
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
            
            // Close modal after successful start
            window.closeEvalModal();
            
            // Connect event stream
            if (eventStreamUI) {
                eventStreamUI.connect(result.job_id);
            }
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

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return 'Now';
    return new Date(timestamp).toLocaleTimeString();
}