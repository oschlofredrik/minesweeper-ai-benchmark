// Benchmark page functionality
let eventStreamUI = null;
let currentJobId = null;
let gameVisualizer = null;
let currentGameType = 'minesweeper';

// Initialize game visualization
function initializeGameVisualization(config) {
    try {
        // Clean up existing visualizer
        if (gameVisualizer) {
            gameVisualizer.clear();
        }
        
        // Create new visualizer
        gameVisualizer = createGameVisualizer(config.game, 'game-board');
        
        // Initialize with game config
        const gameConfig = {
            rows: 16,
            cols: 16,
            mines: 40
        };
        
        // Override with difficulty settings
        if (config.game === 'minesweeper') {
            const difficultySettings = {
                easy: { rows: 9, cols: 9, mines: 10 },
                medium: { rows: 16, cols: 16, mines: 40 },
                hard: { rows: 16, cols: 30, mines: 99 }
            };
            Object.assign(gameConfig, difficultySettings[config.difficulty] || difficultySettings.medium);
        }
        
        gameVisualizer.initialize(gameConfig);
    } catch (error) {
        console.error('Failed to initialize game visualization:', error);
    }
}

// Handle game state updates
function handleGameStateUpdate(gameState) {
    if (gameVisualizer && gameState) {
        gameVisualizer.updateState(gameState);
    }
}

// Handle move highlights
function handleMoveHighlight(move) {
    if (gameVisualizer && move) {
        gameVisualizer.highlightMove(move);
    }
}

// Make functions globally available
window.showEvalModal = showEvalModal;
window.hideEvalModal = hideEvalModal;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize event stream UI
    eventStreamUI = new EventStreamUI('event-stream-ui');
    
    // Set up form handler
    document.getElementById('eval-form').addEventListener('submit', handleStartEvaluation);
    
    // Listen for game events
    document.addEventListener('game-state-update', (e) => {
        handleGameStateUpdate(e.detail);
    });
    
    document.addEventListener('move-completed', (e) => {
        handleMoveHighlight(e.detail);
    });
    
    // Load initial models
    updateModelOptions('openai');
    
    // Check available providers
    checkAvailableProviders();
});

// Check which providers have API keys configured
async function checkAvailableProviders() {
    try {
        const response = await fetch('/api/models');
        if (response.ok) {
            const data = await response.json();
            console.log('Available providers:', data.providers);
        }
    } catch (error) {
        console.error('Failed to check providers:', error);
    }
}

function showEvalModal() {
    try {
        const modal = document.getElementById('eval-modal');
        if (!modal) {
            console.error('Modal element not found');
            return;
        }
        modal.style.display = 'flex';
    } catch (error) {
        console.error('Error showing modal:', error);
    }
}

function hideEvalModal() {
    document.getElementById('eval-modal').style.display = 'none';
}

async function updateModelOptions(provider) {
    const modelSelect = document.querySelector('select[name="model"]');
    modelSelect.innerHTML = '<option value="">Loading models...</option>';
    
    try {
        const response = await fetch(`/api/models/${provider}`);
        if (response.ok) {
            const data = await response.json();
            
            modelSelect.innerHTML = '';
            
            // Add models to select
            Object.entries(data.models).forEach(([modelId, modelInfo]) => {
                const option = document.createElement('option');
                option.value = modelId;
                option.textContent = modelInfo.name;
                
                // Add indicator for special models
                if (modelInfo.reasoning_model) {
                    option.textContent += ' (Reasoning)';
                }
                if (!modelInfo.supports_functions) {
                    option.textContent += ' *';
                }
                
                // Select GPT-4 or Claude 3 Opus by default
                if (modelId === 'gpt-4' || modelId === 'claude-3-opus-20240229') {
                    option.selected = true;
                }
                
                modelSelect.appendChild(option);
            });
            
            // Show API key warning if not configured
            if (!data.has_api_key) {
                const warning = document.getElementById('api-key-warning') || createApiKeyWarning();
                warning.textContent = `⚠️ ${provider.toUpperCase()}_API_KEY not configured`;
                warning.style.display = 'block';
            } else {
                const warning = document.getElementById('api-key-warning');
                if (warning) warning.style.display = 'none';
            }
        } else {
            // Fallback to static options
            if (provider === 'openai') {
                modelSelect.innerHTML = `
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                `;
            } else if (provider === 'anthropic') {
                modelSelect.innerHTML = `
                    <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                    <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                    <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                `;
            }
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        // Use fallback options
        updateModelOptionsFallback(provider);
    }
}

function createApiKeyWarning() {
    const warning = document.createElement('div');
    warning.id = 'api-key-warning';
    warning.className = 'alert alert-warning';
    warning.style.marginTop = '8px';
    warning.style.fontSize = 'var(--font-size-small)';
    document.querySelector('[name="provider"]').closest('.form-group').appendChild(warning);
    return warning;
}

function updateModelOptionsFallback(provider) {
    const modelSelect = document.querySelector('select[name="model"]');
    
    if (provider === 'openai') {
        modelSelect.innerHTML = `
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
        `;
    } else if (provider === 'anthropic') {
        modelSelect.innerHTML = `
            <option value="claude-3-opus-20240229">Claude 3 Opus</option>
            <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
            <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
        `;
    }
}

async function handleStartEvaluation(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const evalConfig = {
        game: formData.get('game'),
        model: formData.get('model'),
        provider: formData.get('provider'),
        num_games: parseInt(formData.get('num-games')),
        difficulty: formData.get('difficulty'),
        scenario: formData.get('scenario') || null
    };
    
    // Skip task generation for now (not implemented in simplified version)
    
    try {
        const response = await fetch('/api/benchmark/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(evalConfig)
        });
        
        if (response.ok) {
            const result = await response.json();
            currentJobId = result.job_id;
            
            // Hide modal and show game board
            hideEvalModal();
            document.querySelector('.board-placeholder').style.display = 'none';
            document.getElementById('game-stats').style.display = 'flex';
            
            // Initialize visualization
            currentGameType = evalConfig.game;
            initializeGameVisualization(evalConfig);
            
            // Clear event stream
            eventStreamUI.clear();
            eventStreamUI.addEvent({
                type: 'system',
                message: `Starting ${evalConfig.num_games} ${evalConfig.game} games with ${evalConfig.model}...`
            });
            
            // Process results immediately (sync execution)
            if (result.status === 'completed' && result.games) {
                updateBenchmarkResults(result);
            } else {
                // Fallback to polling
                startGameUpdates(result.job_id);
            }
        } else {
            const errorText = await response.text();
            console.error('Failed to start evaluation:', errorText);
            try {
                const errorData = JSON.parse(errorText);
                alert(`Failed to start evaluation: ${errorData.error || 'Unknown error'}`);
            } catch {
                alert('Failed to start evaluation: Server error');
            }
        }
    } catch (error) {
        console.error('Error starting evaluation:', error);
        alert(`Error starting evaluation: ${error.message}`);
    }
}

async function startGameUpdates(jobId) {
    // Poll for game updates
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/benchmark/jobs/${jobId}`);
            if (response.ok) {
                const data = await response.json();
                updateBenchmarkResults(data);
                
                // Check if all games completed
                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                }
            }
        } catch (error) {
            console.error('Error fetching game updates:', error);
        }
    }, 2000);
}

function updateBenchmarkResults(data) {
    // Update stats
    const completed = data.games?.filter(g => g.status === 'completed').length || 0;
    const total = data.config?.num_games || data.games?.length || 0;
    const wins = data.games?.filter(g => g.won).length || 0;
    
    document.getElementById('current-game-num').textContent = completed;
    document.getElementById('total-games').textContent = total;
    document.getElementById('win-rate').textContent = 
        completed > 0 ? `${((wins / completed) * 100).toFixed(1)}%` : '0%';
    
    // Process completed games
    data.games?.forEach((game, idx) => {
        if (game.status === 'completed') {
            // Add completion event
            eventStreamUI.addEvent({
                type: 'system',
                message: `Game ${idx + 1} completed: ${game.won ? 'Won' : 'Lost'} in ${game.total_moves} moves`
            });
            
            // Update visualization with final state
            if (game.final_state && gameVisualizer) {
                gameVisualizer.updateState(game.final_state);
                
                // Highlight last move if available
                if (game.moves && game.moves.length > 0) {
                    const lastMove = game.moves[game.moves.length - 1];
                    if (lastMove.action) {
                        gameVisualizer.highlightMove(lastMove.action);
                    }
                }
            }
            
            // Show move count
            document.getElementById('current-moves').textContent = game.total_moves || 0;
        }
    });
    
    // Show summary if completed
    if (data.status === 'completed' && data.summary) {
        showCompletionSummary(data);
    }
}

function updateGameStats(data) {
    const completed = data.completed_games || 0;
    const total = data.total_games || 0;
    const wins = data.games ? data.games.filter(g => g.won).length : 0;
    
    document.getElementById('current-game-num').textContent = completed;
    document.getElementById('total-games').textContent = total;
    document.getElementById('win-rate').textContent = 
        total > 0 ? `${((wins / completed) * 100).toFixed(1)}%` : '0%';
    
    // Update current game display
    const currentGame = data.games?.find(g => g.status === 'in_progress');
    if (currentGame) {
        document.getElementById('current-moves').textContent = currentGame.total_moves || 0;
        
        // Update board visualization if available
        if (currentGame.moves && window.updateMinesweeperBoard) {
            window.updateMinesweeperBoard(currentGame.moves[currentGame.moves.length - 1]);
        }
        
        // Add move to event stream
        if (currentGame.moves?.length > 0) {
            const lastMove = currentGame.moves[currentGame.moves.length - 1];
            eventStreamUI.addEvent({
                type: 'move',
                action: lastMove.action,
                position: lastMove.parameters?.position,
                reasoning: lastMove.reasoning,
                valid: lastMove.valid
            });
        }
    }
}

function showCompletionSummary(data) {
    const summary = data.summary || {};
    const summaryHtml = `
        <div class="completion-summary">
            <h3>Evaluation Complete</h3>
            <p>Total Games: ${summary.games_completed || 0}</p>
            <p>Wins: ${summary.wins || 0}</p>
            <p>Win Rate: ${((summary.win_rate || 0) * 100).toFixed(1)}%</p>
            <p>Average Moves: ${(summary.avg_moves || 0).toFixed(1)}</p>
            <a href="/leaderboard" class="button">View Leaderboard</a>
        </div>
    `;
    
    eventStreamUI.addEvent({
        type: 'system',
        message: summaryHtml
    });
}

async function generateTasksIfNeeded(evalConfig) {
    // Check if we have enough tasks
    const response = await fetch(`/api/tasks?game_type=${evalConfig.game}&difficulty=${evalConfig.difficulty}`);
    const data = await response.json();
    
    if (!data.tasks || data.tasks.length < evalConfig.num_games) {
        // Generate more tasks
        const needed = evalConfig.num_games - (data.tasks?.length || 0);
        await fetch(`/api/tasks/generate?game_type=${evalConfig.game}&difficulty=${evalConfig.difficulty}&count=${needed}`);
    }
}