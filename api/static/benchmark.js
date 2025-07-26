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
        
        // Create new visualizer - use tilts-board as container
        gameVisualizer = createGameVisualizer(config.game, 'tilts-board');
        
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
                hard: { rows: 16, cols: 30, mines: 99 },
                beginner: { rows: 9, cols: 9, mines: 10 },
                intermediate: { rows: 16, cols: 16, mines: 40 },
                expert: { rows: 16, cols: 30, mines: 99 }
            };
            Object.assign(gameConfig, difficultySettings[config.difficulty] || difficultySettings.medium);
        }
        
        console.log('Initializing game visualizer with config:', gameConfig);
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
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize event stream UI - but create a simple version if EventStreamUI doesn't work
    try {
        if (typeof EventStreamUI !== 'undefined') {
            eventStreamUI = new EventStreamUI('event-stream-ui');
        } else {
            console.log('EventStreamUI not found, using simple event display');
            // Create a simple event display
            const eventContainer = document.getElementById('event-stream-ui');
            if (eventContainer) {
                eventContainer.innerHTML = `
                    <div class="event-stream-header">
                        <h4>Live Game Stream</h4>
                    </div>
                    <div class="event-stream-container" id="event-stream-list" style="height: 400px; overflow-y: auto;">
                        <div class="event-placeholder">
                            <p class="text-muted">Waiting for game to start...</p>
                        </div>
                    </div>
                `;
                eventStreamUI = {
                    streamList: document.getElementById('event-stream-list')
                };
            }
        }
    } catch (error) {
        console.error('Error initializing EventStreamUI:', error);
    }
    
    // Initialize Supabase
    if (typeof initSupabase === 'function') {
        await initSupabase();
    } else {
        console.warn('initSupabase not available - Supabase realtime updates will not work');
    }
    
    // Form handler will be set up when modal is shown
    
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
    
    // Set up start evaluation button
    const startBtn = document.getElementById('start-eval-btn');
    if (startBtn) {
        startBtn.addEventListener('click', showEvalModal);
    } else {
        console.error('Start evaluation button not found');
    }
    
    // Set up provider change handler
    const providerSelect = document.getElementById('model-provider');
    if (providerSelect) {
        providerSelect.addEventListener('change', (e) => {
            updateModelOptions(e.target.value);
        });
    }
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
        modal.classList.add('active');
        modal.style.display = 'flex';
        
        // Set up form handler when modal is shown
        const playForm = document.getElementById('play-form');
        if (playForm && !playForm.hasAttribute('data-handler-attached')) {
            playForm.addEventListener('submit', handleStartEvaluation);
            playForm.setAttribute('data-handler-attached', 'true');
        }
        
        // Update model options for default provider
        const providerSelect = document.getElementById('model-provider');
        if (providerSelect) {
            updateModelOptions(providerSelect.value || 'openai');
        }
    } catch (error) {
        console.error('Error showing modal:', error);
    }
}

function hideEvalModal() {
    const modal = document.getElementById('eval-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

async function updateModelOptions(provider) {
    const modelSelect = document.getElementById('model-name');
    if (!modelSelect) {
        console.error('Model select element not found');
        return;
    }
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
    const modelSelect = document.getElementById('model-name');
    if (!modelSelect) return;
    
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
    
    const evalConfig = {
        game: document.getElementById('game-select').value,
        model: document.getElementById('model-name').value,
        provider: document.getElementById('model-provider').value,
        num_games: parseInt(document.getElementById('num-games').value),
        difficulty: document.getElementById('difficulty').value,
        scenario: null
    };
    
    console.log('Starting evaluation with config:', evalConfig);
    
    // Validate config
    if (!evalConfig.model || !evalConfig.provider) {
        alert('Please select a model and provider');
        return;
    }
    
    // Hide modal IMMEDIATELY
    hideEvalModal();
    document.querySelector('.board-placeholder').style.display = 'none';
    document.getElementById('game-stats').style.display = 'flex';
    
    // Show the game board
    const gameBoard = document.getElementById('tilts-board');
    if (gameBoard) {
        gameBoard.style.display = 'table';
    }
    
    // Initialize visualization while waiting
    currentGameType = evalConfig.game;
    initializeGameVisualization(evalConfig);
    
    // Initialize event stream with starting message
    if (eventStreamUI && eventStreamUI.streamList) {
        eventStreamUI.streamList.innerHTML = `
            <div class="event-item event-system">
                <div class="event-content">
                    <p>Starting ${evalConfig.num_games} ${evalConfig.game} games with ${evalConfig.model}...</p>
                </div>
            </div>
        `;
    }
    
    try {
        console.log('Sending request to /api/benchmark/run');
        const response = await fetch('/api/benchmark/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(evalConfig)
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Benchmark started, result:', result);
            currentJobId = result.job_id;
            
            // Initialize event stream (clear happens automatically)
            if (eventStreamUI && eventStreamUI.streamList) {
                eventStreamUI.streamList.innerHTML = `
                    <div class="event-item event-system">
                        <div class="event-content">
                            <p>Starting ${evalConfig.num_games} ${evalConfig.game} games with ${evalConfig.model}...</p>
                        </div>
                    </div>
                `;
            }
            
            // Subscribe to realtime updates for this job
            if (result.job_id && typeof subscribeToGame === 'function') {
                console.log('Subscribing to realtime updates for job:', result.job_id);
                await subscribeToGame(result.job_id, handleRealtimeUpdate);
            } else if (result.job_id) {
                console.warn('subscribeToGame not available - realtime updates disabled');
            }
            
            // Process initial results if any
            if (result.games) {
                console.log('Processing initial results:', result.games);
                updateBenchmarkResults(result);
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
        if (game.status === 'completed' || game.status === 'error') {
            // Add completion event
            if (eventStreamUI && eventStreamUI.streamList) {
                const eventDiv = document.createElement('div');
                eventDiv.className = `event-item ${game.status === 'error' ? 'event-error' : 'event-system'}`;
                
                let message = '';
                if (game.status === 'error') {
                    message = `Game ${idx + 1} failed: ${game.error || 'Unknown error'}`;
                } else {
                    message = `Game ${idx + 1} completed: ${game.won ? 'Won' : 'Lost'} in ${game.total_moves} moves`;
                }
                
                eventDiv.innerHTML = `
                    <div class="event-content">
                        <p>${message}</p>
                    </div>
                `;
                eventStreamUI.streamList.appendChild(eventDiv);
            }
            
            // Show all moves in event stream
            if (game.moves && game.moves.length > 0) {
                game.moves.forEach((move, moveIdx) => {
                    if (eventStreamUI && eventStreamUI.streamList) {
                        // Add AI conversation for each move
                        const moveDiv = document.createElement('div');
                        moveDiv.className = 'event-item';
                        moveDiv.style.marginBottom = '1em';
                        
                        let moveHtml = `<div class="event-content">`;
                        
                        // Show board state before move
                        if (move.board_state && moveIdx === 0) {
                            moveHtml += `
                                <details>
                                    <summary><strong>Move ${move.move_number} - Board State</strong></summary>
                                    <pre style="font-family: monospace; font-size: 0.75em; line-height: 1.2;">${move.board_state}</pre>
                                </details>
                            `;
                        }
                        
                        // Show AI action
                        if (move.action) {
                            moveHtml += `
                                <p><strong>Move ${move.move_number}:</strong> ${move.action.action} at (${move.action.row}, ${move.action.col})</p>
                                ${move.action.reasoning ? `<p style="font-style: italic; color: #666; margin-left: 1em;">"${move.action.reasoning}"</p>` : ''}
                                ${move.valid === false ? `<p style="color: red;">Invalid: ${move.message}</p>` : ''}
                            `;
                        }
                        
                        moveHtml += `</div>`;
                        moveDiv.innerHTML = moveHtml;
                        eventStreamUI.streamList.appendChild(moveDiv);
                    }
                });
            }
            
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
        if (currentGame.moves?.length > 0 && eventStreamUI && eventStreamUI.streamList) {
            const lastMove = currentGame.moves[currentGame.moves.length - 1];
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event-item event-move';
            eventDiv.innerHTML = `
                <div class="event-content">
                    <p><strong>Move:</strong> ${lastMove.action} at ${lastMove.parameters?.position || 'unknown'}</p>
                    ${lastMove.reasoning ? `<p class="text-muted">${lastMove.reasoning}</p>` : ''}
                    ${lastMove.valid === false ? '<p class="text-error">Invalid move</p>' : ''}
                </div>
            `;
            eventStreamUI.streamList.appendChild(eventDiv);
        }
    }
}

function showCompletionSummary(data) {
    // Removed - completion is shown in the stats above
}

// Handle realtime updates from Supabase
function handleRealtimeUpdate(event, payload) {
    console.log('Realtime update:', event, payload);
    
    if (event === 'move') {
        // Add move to event stream
        if (eventStreamUI && eventStreamUI.streamList) {
            const moveDiv = document.createElement('div');
            moveDiv.className = 'event-item';
            moveDiv.style.marginBottom = '1em';
            
            let moveHtml = `<div class="event-content">`;
            
            // Show board state if first move
            if (payload.move_number === 1 && payload.board_state) {
                moveHtml += `
                    <details open>
                        <summary><strong>Move ${payload.move_number} - Board State</strong></summary>
                        <pre style="font-family: monospace; font-size: 0.75em; line-height: 1.2;">${payload.board_state}</pre>
                    </details>
                `;
            }
            
            // Show AI action
            if (payload.action) {
                moveHtml += `
                    <p><strong>Move ${payload.move_number}:</strong> ${payload.action.action} at (${payload.action.row}, ${payload.action.col})</p>
                    ${payload.action.reasoning ? `<p style="font-style: italic; color: #666; margin-left: 1em;">"${payload.action.reasoning}"</p>` : ''}
                    ${payload.valid === false ? `<p style="color: red;">Invalid: ${payload.message}</p>` : ''}
                `;
            }
            
            moveHtml += `</div>`;
            moveDiv.innerHTML = moveHtml;
            eventStreamUI.streamList.appendChild(moveDiv);
            
            // Auto-scroll to bottom
            eventStreamUI.streamList.scrollTop = eventStreamUI.streamList.scrollHeight;
        }
        
        // Update board visualization
        if (payload.game_state && gameVisualizer) {
            gameVisualizer.updateState(payload.game_state);
        }
        
        // Update move count
        document.getElementById('current-moves').textContent = payload.move_number || 0;
        
    } else if (event === 'complete') {
        // Game completed
        const completed = parseInt(document.getElementById('current-game-num').textContent) || 0;
        document.getElementById('current-game-num').textContent = completed + 1;
        
        // Update win rate
        if (payload.won) {
            const wins = parseInt(document.getElementById('wins-count')?.textContent) || 0;
            const total = completed + 1;
            const winRate = ((wins + 1) / total * 100).toFixed(1);
            document.getElementById('win-rate').textContent = `${winRate}%`;
        }
        
        // Add completion message
        if (eventStreamUI && eventStreamUI.streamList) {
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event-item event-system';
            eventDiv.innerHTML = `
                <div class="event-content">
                    <p>Game completed - ${payload.won ? 'Won' : 'Lost'} in ${payload.total_moves || 0} moves</p>
                </div>
            `;
            eventStreamUI.streamList.appendChild(eventDiv);
        }
    }
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