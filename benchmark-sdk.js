// Benchmark SDK - Frontend handler for Vercel AI SDK streaming
let currentStream = null;
let gameVisualizer = null;
let currentGameType = 'minesweeper';
let currentJobId = null;

// Initialize game visualization
function initializeGameVisualization(config) {
    try {
        // Clean up existing visualizer
        if (gameVisualizer) {
            gameVisualizer.clear();
        }
        
        // Create new visualizer
        gameVisualizer = createGameVisualizer(config.gameType, 'tilts-board');
        
        // Initialize with game config
        const gameConfig = {
            rows: 16,
            cols: 16,
            mines: 40
        };
        
        // Override with difficulty settings
        if (config.gameType === 'minesweeper') {
            const difficultySettings = {
                easy: { rows: 9, cols: 9, mines: 10 },
                medium: { rows: 16, cols: 16, mines: 40 },
                hard: { rows: 16, cols: 30, mines: 99 },
            };
            Object.assign(gameConfig, difficultySettings[config.difficulty] || difficultySettings.medium);
        }
        
        console.log('Initializing game visualizer with config:', gameConfig);
        gameVisualizer.initialize(gameConfig);
    } catch (error) {
        console.error('Failed to initialize game visualization:', error);
    }
}

// Handle streaming evaluation with Vercel AI SDK
async function handleStartEvaluationSDK(e) {
    e.preventDefault();
    
    const evalConfig = {
        gameType: document.getElementById('game-select').value,
        model: document.getElementById('model-name').value,
        provider: document.getElementById('model-provider').value,
        numGames: parseInt(document.getElementById('num-games').value),
        difficulty: document.getElementById('difficulty-select').value,
        scenario: null,
        streaming: true,
        temperature: 0.7,
        maxSteps: 50
    };
    
    console.log('[SDK] Starting evaluation with config:', evalConfig);
    
    // Update UI to show starting
    const eventStream = document.getElementById('event-stream-ui');
    if (eventStream && window.eventStreamUI) {
        window.eventStreamUI.addEvent({
            type: 'info',
            message: `Starting ${evalConfig.numGames} ${evalConfig.gameType} game(s) with ${evalConfig.model}...`
        });
    }
    
    // Validate config
    if (!evalConfig.model || !evalConfig.provider) {
        alert('Please select a model and provider');
        return;
    }
    
    // Hide form and show game visualization
    document.getElementById('eval-form-container').style.display = 'none';
    document.getElementById('game-visualization').style.display = 'grid';
    document.querySelector('.board-placeholder').style.display = 'none';
    document.getElementById('game-stats').style.display = 'flex';
    document.getElementById('stop-eval-btn').style.display = 'block';
    
    const gameBoard = document.getElementById('tilts-board');
    if (gameBoard) {
        gameBoard.style.display = 'table';
    }
    
    // Initialize visualization
    currentGameType = evalConfig.gameType;
    initializeGameVisualization(evalConfig);
    
    // Clear event stream
    const eventStreamList = document.getElementById('event-stream-list');
    if (eventStreamList) {
        eventStreamList.innerHTML = `
            <div class="event-item event-system">
                <div class="event-content">
                    <p>Starting ${evalConfig.numGames} ${evalConfig.gameType} games with ${evalConfig.model}...</p>
                </div>
            </div>
        `;
    }
    
    try {
        // Create job ID for tracking
        currentJobId = `eval_${Date.now()}`;
        
        // Use the play endpoint (optimized version handles benchmarks)
        const url = new URL('/api/play', window.location.origin);
        
        // Add SDK flag to environment or as query param
        const originalFlag = localStorage.getItem('USE_VERCEL_SDK');
        localStorage.setItem('USE_VERCEL_SDK', 'true');
        
        const requestBody = {
            ...evalConfig,
            game: evalConfig.gameType,  // Convert gameType to game
            num_games: evalConfig.numGames,  // Convert numGames to num_games
            use_sdk: useSDK  // Enable SDK evaluation
        };
        
        console.log('[SDK] Sending request to:', url.toString());
        console.log('[SDK] Request body:', requestBody);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        console.log('[SDK] Response status:', response.status);
        console.log('[SDK] Response headers:', response.headers);
        
        // Restore original flag
        if (originalFlag) {
            localStorage.setItem('USE_VERCEL_SDK', originalFlag);
        } else {
            localStorage.removeItem('USE_VERCEL_SDK');
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Get response data
        const result = await response.json();
        console.log('[SDK] Response data:', result);
        
        if (result.job_id) {
            console.log('[SDK] Job created with ID:', result.job_id);
            if (window.eventStreamUI) {
                window.eventStreamUI.addEvent({
                    type: 'success',
                    message: `Job created: ${result.job_id}`
                });
            }
            
            // TODO: Poll for job status
            pollJobStatus(result.job_id);
        } else {
            console.error('[SDK] No job ID in response');
        }
        
    } catch (error) {
        console.error('Error starting SDK evaluation:', error);
        alert(`Error starting evaluation: ${error.message}`);
    }
}

// Poll for job status
async function pollJobStatus(jobId) {
    console.log('[SDK] Starting to poll job:', jobId);
    
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/play/games/${jobId}`);
            const data = await response.json();
            
            console.log('[SDK] Job status:', data);
            
            if (data.status === 'completed' || data.status === 'error') {
                clearInterval(pollInterval);
                console.log('[SDK] Job finished:', data);
                
                if (window.eventStreamUI) {
                    window.eventStreamUI.addEvent({
                        type: data.status === 'completed' ? 'success' : 'error',
                        message: `Job ${data.status}: ${data.games?.length || 0} games completed`
                    });
                }
            }
        } catch (error) {
            console.error('[SDK] Error polling job:', error);
        }
    }, 2000);
    
    // Store interval for cleanup
    window.currentPollInterval = pollInterval;
}

// Process Vercel AI SDK stream
async function processSDKStream(reader) {
    const decoder = new TextDecoder();
    let buffer = '';
    let moveCount = 0;
    let gameStats = {
        total: 1,
        completed: 0,
        wins: 0
    };
    
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.trim().startsWith('data: ')) {
                    const dataStr = line.slice(6);
                    if (dataStr === '[DONE]') continue;
                    
                    try {
                        const data = JSON.parse(dataStr);
                        await handleSDKStreamEvent(data, moveCount, gameStats);
                        if (data.type === 'move') moveCount++;
                    } catch (e) {
                        console.error('Failed to parse stream data:', e, dataStr);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Stream processing error:', error);
    }
}

// Handle individual stream events from Vercel AI SDK
async function handleSDKStreamEvent(event, moveCount, gameStats) {
    const eventStreamList = document.getElementById('event-stream-list');
    
    switch (event.type) {
        case 'move':
            // Update visualization
            if (gameVisualizer && event.boardState) {
                gameVisualizer.updateFromBoardString(event.boardState);
            }
            
            // Highlight the move
            if (gameVisualizer && event.position) {
                gameVisualizer.highlightMove({
                    row: event.position.row,
                    col: event.position.col,
                    action: event.action
                });
            }
            
            // Add move to event stream
            if (eventStreamList) {
                const moveDiv = document.createElement('div');
                moveDiv.className = `event-item ${event.valid ? 'event-move' : 'event-error'}`;
                
                let positionStr = '';
                if (event.position) {
                    positionStr = `(${event.position.row}, ${event.position.col})`;
                } else if (event.territory) {
                    positionStr = event.territory;
                }
                
                moveDiv.innerHTML = `
                    <div class="event-header">
                        <span class="event-title">Move ${event.moveNumber}: ${event.action} ${positionStr}</span>
                        <span class="event-meta">${event.valid ? '✓' : '✗'}</span>
                    </div>
                    ${event.reasoning ? `
                        <div class="event-content">
                            <p class="reasoning">${event.reasoning}</p>
                        </div>
                    ` : ''}
                `;
                
                eventStreamList.appendChild(moveDiv);
                eventStreamList.scrollTop = eventStreamList.scrollHeight;
            }
            
            // Update move counter
            document.getElementById('current-move').textContent = event.moveNumber;
            break;
            
        case 'status':
            // Add status message
            if (eventStreamList) {
                const statusDiv = document.createElement('div');
                statusDiv.className = 'event-item event-system';
                statusDiv.innerHTML = `
                    <div class="event-content">
                        <p>${event.message}</p>
                    </div>
                `;
                eventStreamList.appendChild(statusDiv);
            }
            break;
            
        case 'complete':
            // Game completed
            gameStats.completed++;
            if (event.won) gameStats.wins++;
            
            // Update stats
            document.getElementById('current-game-num').textContent = gameStats.completed;
            document.getElementById('total-games').textContent = gameStats.total;
            document.getElementById('win-rate').textContent = 
                gameStats.completed > 0 ? `${((gameStats.wins / gameStats.completed) * 100).toFixed(1)}%` : '0%';
            
            // Add completion message
            if (eventStreamList) {
                const completeDiv = document.createElement('div');
                completeDiv.className = 'event-item event-complete';
                completeDiv.innerHTML = `
                    <div class="event-header">
                        <span class="event-title">Game Complete</span>
                        <span class="event-meta">${event.won ? 'Won' : 'Lost'}</span>
                    </div>
                    <div class="event-content">
                        <p>Total moves: ${event.moves}</p>
                        ${event.coverage !== undefined ? `<p>Coverage: ${(event.coverage * 100).toFixed(1)}%</p>` : ''}
                    </div>
                `;
                eventStreamList.appendChild(completeDiv);
            }
            break;
            
        case 'error':
            // Handle error
            console.error('Stream error:', event.message);
            if (eventStreamList) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'event-item event-error';
                errorDiv.innerHTML = `
                    <div class="event-content">
                        <p>Error: ${event.message}</p>
                    </div>
                `;
                eventStreamList.appendChild(errorDiv);
            }
            break;
    }
}

// Update batch results (for multiple games)
function updateBatchResults(data) {
    const eventStreamList = document.getElementById('event-stream-list');
    
    // Update stats
    if (data.summary) {
        document.getElementById('current-game-num').textContent = data.summary.gamesCompleted;
        document.getElementById('total-games').textContent = data.summary.totalGames;
        document.getElementById('win-rate').textContent = `${(data.summary.winRate * 100).toFixed(1)}%`;
    }
    
    // Show summary
    if (eventStreamList && data.games) {
        data.games.forEach((game, idx) => {
            const gameDiv = document.createElement('div');
            gameDiv.className = 'event-item event-complete';
            gameDiv.innerHTML = `
                <div class="event-header">
                    <span class="event-title">Game ${idx + 1}</span>
                    <span class="event-meta">${game.won ? 'Won' : 'Lost'}</span>
                </div>
                <div class="event-content">
                    <p>Moves: ${game.moves}</p>
                    ${game.usage ? `<p>Tokens: ${game.usage.totalTokens}</p>` : ''}
                </div>
            `;
            eventStreamList.appendChild(gameDiv);
        });
    }
}

// Initialize SDK mode
function initializeSDKMode() {
    const sdkCheckbox = document.getElementById('use-sdk-mode');
    if (!sdkCheckbox) return;
    
    // Load saved preference
    const savedPreference = localStorage.getItem('useVercelSDK') === 'true';
    sdkCheckbox.checked = savedPreference || window.location.search.includes('sdk=true');
    
    // Listen for changes
    sdkCheckbox.addEventListener('change', (e) => {
        const useSDK = e.target.checked;
        localStorage.setItem('useVercelSDK', useSDK ? 'true' : 'false');
        console.log(`SDK mode ${useSDK ? 'enabled' : 'disabled'}`);
        
        // Update form handler
        updateFormHandler(useSDK);
    });
    
    // Set initial handler
    updateFormHandler(sdkCheckbox.checked);
}

// Update form handler based on SDK mode
function updateFormHandler(useSDK) {
    const playForm = document.getElementById('play-form');
    if (!playForm) return;
    
    // Remove existing handlers
    const newForm = playForm.cloneNode(true);
    playForm.parentNode.replaceChild(newForm, playForm);
    
    // Add appropriate handler
    if (useSDK) {
        console.log('Using Vercel AI SDK handler');
        newForm.addEventListener('submit', handleStartEvaluationSDK);
        newForm.setAttribute('data-sdk-handler', 'true');
    } else {
        console.log('Using standard handler');
        newForm.addEventListener('submit', window.handleStartEvaluation);
        newForm.setAttribute('data-handler-attached', 'true');
    }
}

// Check if SDK is enabled and replace handler
document.addEventListener('DOMContentLoaded', () => {
    // Initialize SDK mode when modal is shown
    const showModalOriginal = window.showEvalModal;
    window.showEvalModal = function() {
        if (showModalOriginal) showModalOriginal.call(this);
        setTimeout(initializeSDKMode, 100); // Give modal time to render
    };
});

// Export for global access
window.handleStartEvaluationSDK = handleStartEvaluationSDK;

// Function to reset the benchmark view
function resetBenchmarkView() {
    document.getElementById('eval-form-container').style.display = 'block';
    document.getElementById('game-visualization').style.display = 'none';
    document.getElementById('stop-eval-btn').style.display = 'none';
    
    // Clear any ongoing evaluation
    if (window.currentEvaluation) {
        window.currentEvaluation.abort();
        window.currentEvaluation = null;
    }
    
    // Clear polling interval
    if (window.currentPollInterval) {
        clearInterval(window.currentPollInterval);
        window.currentPollInterval = null;
    }
}

// Set up stop button handler when ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const stopBtn = document.getElementById('stop-eval-btn');
        if (stopBtn) {
            stopBtn.addEventListener('click', resetBenchmarkView);
        }
    });
} else {
    const stopBtn = document.getElementById('stop-eval-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', resetBenchmarkView);
    }
}