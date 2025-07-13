/**
 * Minesweeper AI Benchmark - Dieter Rams Edition
 * "Good design is as little design as possible"
 */

const API_BASE = '';

// State
let activeGames = new Map();
let selectedGameId = null;
let updateInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializePlayForm();
    loadOverviewStats();
    loadLeaderboard();
    startGameUpdates();
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
        
        html += '</div>';
        container.innerHTML = html;
        
    } catch (error) {
        container.innerHTML = '<p class="text-sm text-muted">Failed to load events</p>';
    }
}

// Start periodic updates
function startGameUpdates() {
    updateInterval = setInterval(() => {
        updateGamesList();
        if (selectedGameId) {
            updateEventLog();
        }
    }, 2000);
}

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return 'Now';
    return new Date(timestamp).toLocaleTimeString();
}