/**
 * Evaluation Visualization Component
 * 
 * Real-time display of evaluation scores during game play
 */

class EvaluationViz {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.evaluations = {};
        this.players = {};
        this.currentRound = 1;
        this.isCompetition = false;
        
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = `
            <div class="evaluation-viz">
                <div class="viz-header">
                    <h3>Live Evaluation Scores</h3>
                    <div class="round-indicator">Round ${this.currentRound}</div>
                </div>
                
                <div class="viz-content">
                    <div id="player-scores" class="player-scores-grid">
                        <!-- Player score cards will be rendered here -->
                    </div>
                    
                    <div id="evaluation-breakdown" class="evaluation-breakdown">
                        <!-- Evaluation breakdown will be rendered here -->
                    </div>
                </div>
                
                <div class="viz-footer">
                    <div class="legend">
                        <span class="legend-item">
                            <span class="legend-dot" style="background: var(--success)"></span>
                            High Score
                        </span>
                        <span class="legend-item">
                            <span class="legend-dot" style="background: var(--warning)"></span>
                            Medium Score
                        </span>
                        <span class="legend-item">
                            <span class="legend-dot" style="background: var(--danger)"></span>
                            Low Score
                        </span>
                    </div>
                </div>
            </div>
        `;
        
        this.updateDisplay();
    }

    attachEventListeners() {
        // Listen for evaluation updates from event stream
        document.addEventListener('evaluation-update', (event) => {
            this.handleEvaluationUpdate(event.detail);
        });
        
        // Listen for round changes
        document.addEventListener('round-change', (event) => {
            this.currentRound = event.detail.round;
            this.render();
        });
    }

    handleEvaluationUpdate(data) {
        const playerId = data.player_id;
        
        // Initialize player if not exists
        if (!this.players[playerId]) {
            this.players[playerId] = {
                name: data.player_name || `Player ${playerId.substring(0, 8)}`,
                total_score: 0,
                evaluations: {}
            };
        }
        
        // Update scores
        if (data.scores) {
            Object.entries(data.scores).forEach(([evalId, scoreData]) => {
                this.players[playerId].evaluations[evalId] = scoreData;
            });
            
            this.players[playerId].total_score = data.current_total || 0;
        }
        
        // Update evaluation metadata
        if (data.breakdown) {
            data.breakdown.forEach(item => {
                if (!this.evaluations[item.evaluation_id]) {
                    this.evaluations[item.evaluation_id] = {
                        name: item.name || 'Unknown Evaluation',
                        type: item.type || 'custom'
                    };
                }
            });
        }
        
        this.updateDisplay();
    }

    updateDisplay() {
        this.renderPlayerScores();
        this.renderEvaluationBreakdown();
    }

    renderPlayerScores() {
        const container = document.getElementById('player-scores');
        if (!container) return;
        
        const playerEntries = Object.entries(this.players);
        if (playerEntries.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No scores yet</p>';
            return;
        }
        
        // Sort by total score
        playerEntries.sort((a, b) => b[1].total_score - a[1].total_score);
        
        container.innerHTML = playerEntries.map(([playerId, player], index) => {
            const rank = index + 1;
            const scorePercent = player.total_score * 100;
            
            return `
                <div class="player-score-card ${rank === 1 ? 'leader' : ''}">
                    <div class="player-header">
                        <span class="player-rank">#${rank}</span>
                        <span class="player-name">${player.name}</span>
                        <span class="player-score">${scorePercent.toFixed(1)}%</span>
                    </div>
                    
                    <div class="score-bar">
                        <div class="score-bar-fill" style="width: ${scorePercent}%"></div>
                    </div>
                    
                    <div class="player-evaluations">
                        ${this.renderPlayerEvaluations(player.evaluations)}
                    </div>
                </div>
            `;
        }).join('');
    }

    renderPlayerEvaluations(evaluations) {
        const evalEntries = Object.entries(evaluations);
        if (evalEntries.length === 0) return '';
        
        return evalEntries.map(([evalId, scores]) => {
            const evalInfo = this.evaluations[evalId] || { name: 'Unknown' };
            const weighted = (scores.weighted || 0) * 100;
            
            return `
                <div class="eval-score-item">
                    <span class="eval-name">${evalInfo.name}</span>
                    <span class="eval-score">${weighted.toFixed(1)}</span>
                </div>
            `;
        }).join('');
    }

    renderEvaluationBreakdown() {
        const container = document.getElementById('evaluation-breakdown');
        if (!container) return;
        
        // Show breakdown for the leading player
        const playerEntries = Object.entries(this.players);
        if (playerEntries.length === 0) {
            container.innerHTML = '<p class="text-muted">No evaluation data</p>';
            return;
        }
        
        // Get leader
        playerEntries.sort((a, b) => b[1].total_score - a[1].total_score);
        const [leaderId, leader] = playerEntries[0];
        
        container.innerHTML = `
            <h4>Evaluation Breakdown</h4>
            <p class="text-muted">Leading Player: ${leader.name}</p>
            
            <div class="breakdown-chart">
                ${this.renderBreakdownChart(leader.evaluations)}
            </div>
            
            <div class="breakdown-details">
                ${this.renderBreakdownDetails(leader.evaluations)}
            </div>
        `;
    }

    renderBreakdownChart(evaluations) {
        const total = Object.values(evaluations).reduce((sum, scores) => 
            sum + (scores.weighted || 0), 0
        );
        
        if (total === 0) return '<p class="text-muted">No scores yet</p>';
        
        let cumulativePercent = 0;
        
        return `
            <div class="stacked-bar">
                ${Object.entries(evaluations).map(([evalId, scores], index) => {
                    const percent = ((scores.weighted || 0) / total) * 100;
                    const left = cumulativePercent;
                    cumulativePercent += percent;
                    
                    return `
                        <div class="bar-segment" 
                             style="left: ${left}%; width: ${percent}%; background: var(--color-${index % 6})"
                             title="${this.evaluations[evalId]?.name || 'Unknown'}: ${percent.toFixed(1)}%">
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    renderBreakdownDetails(evaluations) {
        return Object.entries(evaluations).map(([evalId, scores]) => {
            const evalInfo = this.evaluations[evalId] || { name: 'Unknown' };
            const raw = scores.raw || 0;
            const normalized = (scores.normalized || 0) * 100;
            const weighted = (scores.weighted || 0) * 100;
            
            return `
                <div class="breakdown-item">
                    <div class="breakdown-header">
                        <span class="eval-name">${evalInfo.name}</span>
                        <span class="eval-type">${evalInfo.type}</span>
                    </div>
                    <div class="breakdown-scores">
                        <span class="score-raw">Raw: ${raw.toFixed(1)}</span>
                        <span class="score-normalized">Normalized: ${normalized.toFixed(1)}%</span>
                        <span class="score-weighted">Weighted: ${weighted.toFixed(1)}%</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Public methods
    
    setCompetitionMode(isCompetition) {
        this.isCompetition = isCompetition;
        this.render();
    }

    reset() {
        this.evaluations = {};
        this.players = {};
        this.currentRound = 1;
        this.render();
    }

    updateRound(round) {
        this.currentRound = round;
        document.querySelector('.round-indicator').textContent = `Round ${round}`;
    }
}

// CSS for the evaluation visualization
const evaluationVizStyles = `
<style>
.evaluation-viz {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: calc(var(--unit) * 3);
}

.viz-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: calc(var(--unit) * 3);
}

.viz-header h3 {
    margin: 0;
}

.round-indicator {
    font-size: 0.875rem;
    color: var(--text-muted);
    background: var(--bg-tertiary);
    padding: calc(var(--unit) * 1) calc(var(--unit) * 2);
    border-radius: calc(var(--radius) / 2);
}

.player-scores-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: calc(var(--unit) * 2);
    margin-bottom: calc(var(--unit) * 4);
}

.player-score-card {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: calc(var(--unit) * 2);
    transition: all 0.2s ease;
}

.player-score-card.leader {
    border-color: var(--success);
    box-shadow: 0 0 0 1px var(--success);
}

.player-header {
    display: flex;
    align-items: center;
    gap: calc(var(--unit) * 2);
    margin-bottom: calc(var(--unit) * 2);
}

.player-rank {
    font-weight: 600;
    font-size: 1.25rem;
    color: var(--text-muted);
}

.player-name {
    flex: 1;
    font-weight: 500;
}

.player-score {
    font-size: 1.5rem;
    font-weight: 600;
}

.score-bar {
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: calc(var(--unit) * 2);
}

.score-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary), var(--success));
    transition: width 0.5s ease;
}

.player-evaluations {
    display: flex;
    flex-wrap: wrap;
    gap: calc(var(--unit) * 1);
    font-size: 0.75rem;
}

.eval-score-item {
    display: flex;
    gap: calc(var(--unit) * 1);
    background: var(--bg-tertiary);
    padding: calc(var(--unit) * 0.5) calc(var(--unit) * 1);
    border-radius: calc(var(--radius) / 2);
}

.eval-name {
    color: var(--text-muted);
}

.eval-score {
    font-weight: 500;
}

.evaluation-breakdown {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: calc(var(--unit) * 3);
}

.evaluation-breakdown h4 {
    margin: 0 0 calc(var(--unit) * 1) 0;
}

.breakdown-chart {
    margin: calc(var(--unit) * 3) 0;
}

.stacked-bar {
    position: relative;
    height: 40px;
    background: var(--bg-tertiary);
    border-radius: 20px;
    overflow: hidden;
}

.bar-segment {
    position: absolute;
    height: 100%;
    transition: all 0.5s ease;
}

.breakdown-details {
    display: grid;
    gap: calc(var(--unit) * 2);
}

.breakdown-item {
    padding: calc(var(--unit) * 2);
    background: var(--bg-secondary);
    border-radius: calc(var(--radius) / 2);
}

.breakdown-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: calc(var(--unit) * 1);
}

.eval-type {
    font-size: 0.75rem;
    color: var(--text-muted);
    background: var(--bg-tertiary);
    padding: calc(var(--unit) * 0.5) calc(var(--unit) * 1);
    border-radius: calc(var(--radius) / 2);
}

.breakdown-scores {
    display: flex;
    gap: calc(var(--unit) * 2);
    font-size: 0.875rem;
}

.breakdown-scores span {
    color: var(--text-muted);
}

.viz-footer {
    margin-top: calc(var(--unit) * 3);
    padding-top: calc(var(--unit) * 2);
    border-top: 1px solid var(--border);
}

.legend {
    display: flex;
    gap: calc(var(--unit) * 3);
    font-size: 0.75rem;
    color: var(--text-muted);
}

.legend-item {
    display: flex;
    align-items: center;
    gap: calc(var(--unit) * 1);
}

.legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

/* Color palette for evaluations */
:root {
    --color-0: #3b82f6;
    --color-1: #10b981;
    --color-2: #f59e0b;
    --color-3: #ef4444;
    --color-4: #8b5cf6;
    --color-5: #ec4899;
}
</style>
`;

// Inject styles
if (!document.getElementById('evaluation-viz-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'evaluation-viz-styles';
    styleElement.innerHTML = evaluationVizStyles;
    document.head.appendChild(styleElement.firstElementChild);
}

// Export for use
window.EvaluationViz = EvaluationViz;