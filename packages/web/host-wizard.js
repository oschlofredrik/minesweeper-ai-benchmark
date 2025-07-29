// Host Competition Wizard
let currentStep = 1;
const totalSteps = 5;
let competitionConfig = {
    name: '',
    description: '',
    format: 'single_round',
    maxPlayers: 10,
    game: null,
    difficulty: 'medium',
    gameConfig: {},
    allowedModels: 'all',
    selectedModels: [],
    scoringMethod: 'default',
    evaluations: [],
    timeLimit: 'none',
    trackReasoning: false,
    publicResults: true
};

// Make selectScoringMethod available globally
window.selectScoringMethod = function(card) {
    // Clear previous selection
    document.querySelectorAll('.scoring-card').forEach(c => {
        c.classList.remove('selected');
    });
    
    // Select new method
    card.classList.add('selected');
    const method = card.dataset.scoring;
    competitionConfig.scoringMethod = method;
    
    // Show/hide relevant sections
    const customScoring = document.getElementById('custom-scoring');
    const defaultPreview = document.getElementById('default-evaluation-preview');
    
    if (method === 'default') {
        customScoring.style.display = 'none';
        defaultPreview.style.display = 'block';
        // Clear any selected evaluations
        competitionConfig.evaluations = [];
    } else if (method === 'custom' || method === 'composite') {
        customScoring.style.display = 'block';
        defaultPreview.style.display = 'none';
        // Initialize the inline evaluation selector
        setTimeout(() => initializeInlineEvaluationSelector(), 0);
    }
};

// Update default evaluation preview based on selected game
function updateDefaultEvaluationPreview(game) {
    const preview = document.getElementById('default-evaluation-preview');
    if (!preview) return;
    
    let metrics = [];
    switch(game) {
        case 'minesweeper':
            metrics = [
                'Win/Loss tracking',
                'Mines correctly identified',
                'Safe cells revealed efficiency',
                'Game completion time',
                'Move accuracy percentage'
            ];
            break;
        case 'risk':
            metrics = [
                'Territory control',
                'Battle win percentage',
                'Strategic positioning score',
                'Expansion efficiency',
                'Overall game placement'
            ];
            break;
        case 'sudoku':
            metrics = [
                'Puzzle completion status',
                'Solving time',
                'Error count',
                'Hint usage',
                'Difficulty-adjusted score'
            ];
            break;
        case 'number_puzzle':
            metrics = [
                'Correct answers',
                'Average solving time',
                'Streak bonuses',
                'Difficulty progression',
                'Overall accuracy rate'
            ];
            break;
        default:
            metrics = [
                'Win/Loss tracking',
                'Game completion time',
                'Move efficiency',
                'Basic performance metrics'
            ];
    }
    
    const metricsList = metrics.map(m => `<li>${m}</li>`).join('');
    preview.innerHTML = `
        <h5>Default Evaluation Includes:</h5>
        <ul>${metricsList}</ul>
    `;
}

// Initialize wizard
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    setupEventListeners();
    
    // Initialize first step
    updateWizardUI();
});

function setupEventListeners() {
    // Game selection
    document.querySelectorAll('.game-option').forEach(option => {
        option.addEventListener('click', () => selectGame(option));
    });
    
    // Difficulty selection
    document.querySelectorAll('.difficulty-option').forEach(option => {
        option.addEventListener('click', () => selectDifficulty(option));
    });
    
    // Model selection toggle
    const allowAllModels = document.getElementById('allow-all-models');
    if (allowAllModels) {
        allowAllModels.addEventListener('change', (e) => {
            document.getElementById('model-selection').style.display = 
                e.target.checked ? 'none' : 'block';
            competitionConfig.allowedModels = e.target.checked ? 'all' : 'custom';
        });
    }
    
    // Model selection
    document.querySelectorAll('.model-option').forEach(option => {
        option.addEventListener('click', () => toggleModel(option));
    });
}

function selectGame(option) {
    // Clear previous selection
    document.querySelectorAll('.game-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Select new game
    option.classList.add('selected');
    competitionConfig.game = option.dataset.game;
    
    // Show game configuration
    document.getElementById('game-config').style.display = 'block';
    
    // Load game-specific configuration
    loadGameConfig(competitionConfig.game);
}

function loadGameConfig(game) {
    const configContainer = document.getElementById('game-specific-config');
    
    // Update the default evaluation preview based on game
    updateDefaultEvaluationPreview(game);
    
    switch(game) {
        case 'minesweeper':
            configContainer.innerHTML = `
                <div class="form-stack">
                    <div class="form-group">
                        <label>Board Size</label>
                        <select id="board-size">
                            <option value="9x9">9x9 (Beginner)</option>
                            <option value="16x16" selected>16x16 (Intermediate)</option>
                            <option value="30x16">30x16 (Expert)</option>
                            <option value="custom">Custom</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Number of Mines</label>
                        <input type="number" id="num-mines" min="1" max="99" value="40">
                    </div>
                </div>
            `;
            break;
            
        case 'risk':
            configContainer.innerHTML = `
                <div class="form-stack">
                    <div class="form-group">
                        <label>Map Size</label>
                        <select id="map-size">
                            <option value="small">Small (20 territories)</option>
                            <option value="medium" selected>Medium (42 territories)</option>
                            <option value="large">Large (60 territories)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Starting Armies</label>
                        <input type="number" id="starting-armies" min="10" max="50" value="25">
                    </div>
                </div>
            `;
            break;
            
        case 'sudoku':
            configContainer.innerHTML = `
                <div class="form-stack">
                    <div class="form-group">
                        <label>Grid Size</label>
                        <select id="grid-size">
                            <option value="9x9" selected>9x9 (Standard)</option>
                            <option value="16x16">16x16 (Large)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Pre-filled Cells</label>
                        <input type="range" id="prefilled" min="20" max="60" value="35">
                        <span id="prefilled-value">35%</span>
                    </div>
                </div>
            `;
            
            // Add range slider listener
            const prefilledSlider = document.getElementById('prefilled');
            if (prefilledSlider) {
                prefilledSlider.addEventListener('input', (e) => {
                    document.getElementById('prefilled-value').textContent = e.target.value + '%';
                });
            }
            break;
            
        case 'number_puzzle':
            configContainer.innerHTML = `
                <div class="form-stack">
                    <div class="form-group">
                        <label>Puzzle Type</label>
                        <select id="puzzle-type">
                            <option value="sequence">Number Sequences</option>
                            <option value="arithmetic">Arithmetic Puzzles</option>
                            <option value="logic">Logic Problems</option>
                            <option value="mixed" selected>Mixed Challenges</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Time per Puzzle</label>
                        <select id="puzzle-time">
                            <option value="30">30 seconds</option>
                            <option value="60" selected>1 minute</option>
                            <option value="120">2 minutes</option>
                        </select>
                    </div>
                </div>
            `;
            break;
    }
}

function selectDifficulty(option) {
    document.querySelectorAll('.difficulty-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    option.classList.add('selected');
    competitionConfig.difficulty = option.dataset.difficulty;
}

function toggleModel(option) {
    option.classList.toggle('selected');
    const model = option.dataset.model;
    
    if (option.classList.contains('selected')) {
        if (!competitionConfig.selectedModels.includes(model)) {
            competitionConfig.selectedModels.push(model);
        }
    } else {
        competitionConfig.selectedModels = competitionConfig.selectedModels.filter(m => m !== model);
    }
}

function nextStep() {
    if (validateCurrentStep()) {
        if (currentStep < totalSteps) {
            // Mark current step as completed
            document.querySelector(`.wizard-step[data-step="${currentStep}"]`).classList.add('completed');
            document.querySelector(`.wizard-step[data-step="${currentStep}"]`).classList.remove('active');
            
            currentStep++;
            
            // Mark new step as active
            document.querySelector(`.wizard-step[data-step="${currentStep}"]`).classList.add('active');
            
            updateWizardUI();
            
            // Update summary on last step
            if (currentStep === totalSteps) {
                updateSummary();
            }
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        // Remove active from current step
        document.querySelector(`.wizard-step[data-step="${currentStep}"]`).classList.remove('active');
        
        currentStep--;
        
        // Mark previous step as active (not completed)
        document.querySelector(`.wizard-step[data-step="${currentStep}"]`).classList.remove('completed');
        document.querySelector(`.wizard-step[data-step="${currentStep}"]`).classList.add('active');
        
        updateWizardUI();
    }
}

function validateCurrentStep() {
    switch(currentStep) {
        case 1:
            // Validate basic info
            competitionConfig.name = document.getElementById('competition-name').value;
            competitionConfig.description = document.getElementById('competition-description').value;
            competitionConfig.maxPlayers = parseInt(document.getElementById('max-players').value);
            competitionConfig.format = document.getElementById('competition-format').value;
            
            if (!competitionConfig.name) {
                alert('Please enter a competition name');
                return false;
            }
            return true;
            
        case 2:
            // Validate game selection
            if (!competitionConfig.game) {
                alert('Please select a game');
                return false;
            }
            
            // Save game configuration
            saveGameConfig();
            return true;
            
        case 3:
            // Validate model selection
            if (competitionConfig.allowedModels === 'custom' && competitionConfig.selectedModels.length === 0) {
                alert('Please select at least one AI model');
                return false;
            }
            return true;
            
        case 4:
            // Save scoring configuration
            competitionConfig.timeLimit = document.getElementById('time-limit').value;
            competitionConfig.trackReasoning = document.getElementById('track-reasoning').checked;
            competitionConfig.publicResults = document.getElementById('public-results').checked;
            
            // Validate evaluation selection if using custom scoring
            if (competitionConfig.scoringMethod !== 'default') {
                if (!evaluationSelector) {
                    alert('Please configure evaluation metrics');
                    return false;
                }
                
                const validation = evaluationSelector.validateSelection();
                if (!validation.valid) {
                    alert(validation.message);
                    return false;
                }
                
                // Get final selected evaluations
                competitionConfig.evaluations = evaluationSelector.getSelectedMetrics();
            }
            
            return true;
            
        default:
            return true;
    }
}

function saveGameConfig() {
    switch(competitionConfig.game) {
        case 'minesweeper':
            const boardSize = document.getElementById('board-size').value;
            const numMines = parseInt(document.getElementById('num-mines').value);
            
            if (boardSize === 'custom') {
                // Would need additional UI for custom size
                competitionConfig.gameConfig = { rows: 16, cols: 16, mines: numMines };
            } else {
                const [rows, cols] = boardSize.split('x').map(n => parseInt(n));
                competitionConfig.gameConfig = { rows, cols, mines: numMines };
            }
            break;
            
        case 'risk':
            competitionConfig.gameConfig = {
                mapSize: document.getElementById('map-size').value,
                startingArmies: parseInt(document.getElementById('starting-armies').value)
            };
            break;
            
        case 'sudoku':
            competitionConfig.gameConfig = {
                gridSize: document.getElementById('grid-size').value,
                prefilled: parseInt(document.getElementById('prefilled').value)
            };
            break;
            
        case 'number_puzzle':
            competitionConfig.gameConfig = {
                puzzleType: document.getElementById('puzzle-type').value,
                timePerPuzzle: parseInt(document.getElementById('puzzle-time').value)
            };
            break;
    }
}

function updateWizardUI() {
    // Hide all panels
    document.querySelectorAll('.wizard-panel').forEach(panel => {
        panel.style.display = 'none';
    });
    
    // Show current panel
    document.querySelector(`.wizard-panel[data-panel="${currentStep}"]`).style.display = 'block';
    
    // Update buttons
    document.getElementById('prev-button').style.display = currentStep > 1 ? 'block' : 'none';
    document.getElementById('next-button').style.display = currentStep < totalSteps ? 'block' : 'none';
    document.getElementById('create-button').style.display = currentStep === totalSteps ? 'block' : 'none';
}

function updateSummary() {
    document.getElementById('summary-name').textContent = competitionConfig.name;
    document.getElementById('summary-game').textContent = competitionConfig.game.charAt(0).toUpperCase() + competitionConfig.game.slice(1);
    document.getElementById('summary-format').textContent = competitionConfig.format.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    document.getElementById('summary-difficulty').textContent = competitionConfig.difficulty.charAt(0).toUpperCase() + competitionConfig.difficulty.slice(1);
    document.getElementById('summary-max-players').textContent = competitionConfig.maxPlayers;
    document.getElementById('summary-models').textContent = competitionConfig.allowedModels === 'all' ? 'All Available Models' : `${competitionConfig.selectedModels.length} Selected Models`;
    // Format scoring summary
    let scoringSummary = 'Default Game Scoring';
    if (competitionConfig.scoringMethod === 'custom' || competitionConfig.scoringMethod === 'composite') {
        scoringSummary = competitionConfig.scoringMethod === 'custom' ? 'Custom Evaluation' : 'Composite Score';
        if (competitionConfig.evaluations && competitionConfig.evaluations.length > 0) {
            const metricNames = competitionConfig.evaluations.map(e => e.name).join(', ');
            scoringSummary += ` (${metricNames})`;
        }
    }
    document.getElementById('summary-scoring').textContent = scoringSummary;
}

async function createCompetition() {
    try {
        // Prepare rounds configuration based on format
        const roundsConfig = prepareRoundsConfig();
        
        // Create session request
        const request = {
            name: competitionConfig.name,
            description: competitionConfig.description,
            format: competitionConfig.format,
            rounds_config: roundsConfig,
            creator_id: 'host-' + Math.random().toString(36).substr(2, 9),
            max_players: competitionConfig.maxPlayers,
            is_public: competitionConfig.publicResults,
            flow_mode: 'asynchronous'
        };
        
        // Save creator ID for later
        window.currentPlayerId = request.creator_id;
        
        const response = await fetch('/api/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create competition');
        }
        
        const result = await response.json();
        
        // Show success and join code
        document.getElementById('join-code').textContent = result.join_code;
        document.getElementById('creation-result').style.display = 'block';
        
        // Hide create button
        document.getElementById('create-button').style.display = 'none';
        
        // Save session info
        window.currentSessionId = result.session_id;
        window.currentJoinCode = result.join_code;
        
    } catch (error) {
        console.error('Error creating competition:', error);
        alert('Failed to create competition. Please try again.');
    }
}

function prepareRoundsConfig() {
    const rounds = [];
    
    switch(competitionConfig.format) {
        case 'single_round':
            rounds.push(createRoundConfig(1));
            break;
            
        case 'best_of_three':
            for (let i = 1; i <= 3; i++) {
                rounds.push(createRoundConfig(i));
            }
            break;
            
        case 'tournament':
            // For tournament, we'll create rounds dynamically
            // Start with qualifier rounds
            rounds.push(createRoundConfig(1, 'Qualifier'));
            rounds.push(createRoundConfig(2, 'Semi-Final'));
            rounds.push(createRoundConfig(3, 'Final'));
            break;
            
        case 'round_robin':
            // Number of rounds depends on players, start with 3
            for (let i = 1; i <= 3; i++) {
                rounds.push(createRoundConfig(i));
            }
            break;
    }
    
    return rounds;
}

function createRoundConfig(roundNumber, roundName = null) {
    const config = {
        round_number: roundNumber,
        round_name: roundName || `Round ${roundNumber}`,
        game_name: competitionConfig.game,
        difficulty: competitionConfig.difficulty,
        config: competitionConfig.gameConfig,
        time_limit: competitionConfig.timeLimit !== 'none' ? parseInt(competitionConfig.timeLimit) : null
    };
    
    // Add evaluations if custom scoring
    if (competitionConfig.scoringMethod !== 'default' && competitionConfig.evaluations.length > 0) {
        config.evaluations = competitionConfig.evaluations;
    }
    
    return config;
}

function goToLobby() {
    // Redirect to main page with lobby open
    window.location.href = `/?session=${window.currentSessionId}&join_code=${window.currentJoinCode}`;
}

// Evaluation selector integration
let evaluationSelector = null;

// Make evaluationSelector available globally for the evaluation selector component
window.evaluationSelector = null;

// Initialize evaluation selector when custom/composite scoring is selected
function initializeInlineEvaluationSelector() {
    const container = document.getElementById('evaluation-selector-inline');
    if (!container) return;
    
    if (!evaluationSelector) {
        // Create a new evaluation selector with inline options
        evaluationSelector = new EvaluationSelector('evaluation-selector-inline', {
            maxMetrics: 5,
            allowCustomWeights: true,
            onUpdate: (metrics) => {
                // Update competition config when metrics change
                competitionConfig.evaluations = metrics.map(m => ({
                    id: m.id,
                    name: m.name,
                    weight: m.weight
                }));
            }
        });
        
        // Also set the global reference
        window.evaluationSelector = evaluationSelector;
    }
    
    evaluationSelector.render();
}