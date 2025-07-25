// Benchmark page functionality
let eventStreamUI = null;
let currentJobId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize event stream UI
    eventStreamUI = new EventStreamUI('event-stream-ui');
    
    // Set up form handler
    document.getElementById('eval-form').addEventListener('submit', handleStartEvaluation);
});

function showEvalModal() {
    document.getElementById('eval-modal').style.display = 'flex';
}

function hideEvalModal() {
    document.getElementById('eval-modal').style.display = 'none';
}

function updateModelOptions(provider) {
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
        difficulty: formData.get('difficulty')
    };
    
    try {
        const response = await fetch('/api/play', {
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
            if (evalConfig.game === 'minesweeper') {
                window.initMinesweeperBoard();
            }
            
            // Start polling for updates
            startGameUpdates(result.job_id);
            
            // Clear event stream
            eventStreamUI.clear();
            eventStreamUI.addEvent({
                type: 'system',
                message: `Starting ${evalConfig.num_games} ${evalConfig.game} games with ${evalConfig.model}...`
            });
        } else {
            alert('Failed to start evaluation');
        }
    } catch (error) {
        console.error('Error starting evaluation:', error);
        alert('Error starting evaluation');
    }
}

async function startGameUpdates(jobId) {
    // Poll for game updates
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/play/games/${jobId}`);
            if (response.ok) {
                const data = await response.json();
                updateGameStats(data);
                
                // Check if all games completed
                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    showCompletionSummary(data);
                }
            }
        } catch (error) {
            console.error('Error fetching game updates:', error);
        }
    }, 2000);
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
    const summary = `
        <div class="completion-summary">
            <h3>Evaluation Complete</h3>
            <p>Total Games: ${data.total_games}</p>
            <p>Wins: ${data.games.filter(g => g.won).length}</p>
            <p>Win Rate: ${((data.games.filter(g => g.won).length / data.total_games) * 100).toFixed(1)}%</p>
            <a href="/sessions/${currentJobId}" class="button">View Detailed Results</a>
        </div>
    `;
    
    eventStreamUI.addEvent({
        type: 'system',
        message: summary
    });
}