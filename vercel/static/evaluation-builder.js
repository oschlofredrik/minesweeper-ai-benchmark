/**
 * Dynamic Evaluation Builder UI
 * 
 * Provides an intuitive interface for creating and testing evaluation rules
 */

class EvaluationBuilder {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.evaluation = {
            name: '',
            description: '',
            scoring_type: 'proportional',
            rules: [],
            normalization_config: {
                method: 'percentage_of_max',
                max_possible: 100
            },
            category: '',
            tags: []
        };
        this.ruleIdCounter = 0;
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = `
            <div class="evaluation-builder">
                <div class="builder-header">
                    <h2>Evaluation Builder</h2>
                    <div class="builder-actions">
                        <button class="button button-secondary" onclick="evaluationBuilder.importFromMarketplace()">
                            Import from Marketplace
                        </button>
                        <button class="button button-primary" onclick="evaluationBuilder.save()">
                            Save Evaluation
                        </button>
                    </div>
                </div>

                <div class="builder-content">
                    <!-- Basic Information -->
                    <div class="builder-section">
                        <h3>Basic Information</h3>
                        <div class="form-group">
                            <label>Name</label>
                            <input type="text" id="eval-name" class="form-control" 
                                   placeholder="e.g., Speed & Accuracy Challenge" 
                                   value="${this.evaluation.name}">
                        </div>
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="eval-description" class="form-control" rows="3"
                                      placeholder="Describe what this evaluation measures...">${this.evaluation.description}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Category</label>
                            <select id="eval-category" class="form-control">
                                <option value="">Select category...</option>
                                <option value="speed">Speed</option>
                                <option value="accuracy">Accuracy</option>
                                <option value="creativity">Creativity</option>
                                <option value="reasoning">Reasoning</option>
                                <option value="efficiency">Efficiency</option>
                                <option value="custom">Custom</option>
                            </select>
                        </div>
                    </div>

                    <!-- Scoring Method -->
                    <div class="builder-section">
                        <h3>Scoring Method</h3>
                        <div class="scoring-types">
                            <label class="radio-card ${this.evaluation.scoring_type === 'binary' ? 'selected' : ''}">
                                <input type="radio" name="scoring-type" value="binary" 
                                       ${this.evaluation.scoring_type === 'binary' ? 'checked' : ''}>
                                <div class="radio-card-content">
                                    <h4>Binary</h4>
                                    <p>Pass/fail scoring</p>
                                </div>
                            </label>
                            <label class="radio-card ${this.evaluation.scoring_type === 'proportional' ? 'selected' : ''}">
                                <input type="radio" name="scoring-type" value="proportional" 
                                       ${this.evaluation.scoring_type === 'proportional' ? 'checked' : ''}>
                                <div class="radio-card-content">
                                    <h4>Proportional</h4>
                                    <p>Percentage-based scoring</p>
                                </div>
                            </label>
                            <label class="radio-card ${this.evaluation.scoring_type === 'cumulative' ? 'selected' : ''}">
                                <input type="radio" name="scoring-type" value="cumulative" 
                                       ${this.evaluation.scoring_type === 'cumulative' ? 'checked' : ''}>
                                <div class="radio-card-content">
                                    <h4>Cumulative</h4>
                                    <p>Point accumulation</p>
                                </div>
                            </label>
                        </div>
                    </div>

                    <!-- Rules -->
                    <div class="builder-section">
                        <h3>Evaluation Rules</h3>
                        <div class="rule-components">
                            <div class="component-palette">
                                <div class="component-item" draggable="true" data-type="pattern_detection">
                                    <i class="fas fa-search"></i>
                                    <span>Pattern Match</span>
                                </div>
                                <div class="component-item" draggable="true" data-type="metric_threshold">
                                    <i class="fas fa-tachometer-alt"></i>
                                    <span>Metric Threshold</span>
                                </div>
                                <div class="component-item" draggable="true" data-type="cross_round_analysis">
                                    <i class="fas fa-history"></i>
                                    <span>Cross-Round</span>
                                </div>
                                <div class="component-item" draggable="true" data-type="penalty">
                                    <i class="fas fa-minus-circle"></i>
                                    <span>Penalty</span>
                                </div>
                            </div>
                            <div class="drop-hint">Drag components here or click to add</div>
                        </div>

                        <div id="rules-container" class="rules-list">
                            ${this.renderRules()}
                        </div>
                    </div>

                    <!-- Normalization -->
                    <div class="builder-section">
                        <h3>Score Normalization</h3>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="apply-log" 
                                       ${this.evaluation.normalization_config.apply_log ? 'checked' : ''}>
                                Apply log transformation for scores > 1
                            </label>
                        </div>
                        <div class="form-group">
                            <label>Normalization Method</label>
                            <select id="norm-method" class="form-control">
                                <option value="none">None</option>
                                <option value="min_max">Min-Max (0-1)</option>
                                <option value="percentage_of_max">Percentage of Maximum</option>
                            </select>
                        </div>
                    </div>

                    <!-- Test Section -->
                    <div class="builder-section">
                        <h3>Test Your Evaluation</h3>
                        <div class="test-area">
                            <div class="test-inputs">
                                <div class="form-group">
                                    <label>Test Prompt</label>
                                    <textarea id="test-prompt" class="form-control" rows="2"
                                              placeholder="Enter a test prompt...">Analyze this sales data and identify trends</textarea>
                                </div>
                                <div class="form-group">
                                    <label>Test Response</label>
                                    <textarea id="test-response" class="form-control" rows="4"
                                              placeholder="Enter a test response...">According to the data from 1987, the Northeast region shows consistent growth...</textarea>
                                </div>
                                <div class="form-group">
                                    <label>Response Time (seconds)</label>
                                    <input type="number" id="test-time" class="form-control" value="15">
                                </div>
                            </div>
                            <button class="button button-secondary" onclick="evaluationBuilder.testEvaluation()">
                                Run Test
                            </button>
                            <div id="test-results" class="test-results"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderRules() {
        if (this.evaluation.rules.length === 0) {
            return '<p class="text-muted">No rules added yet. Drag components from above to get started.</p>';
        }

        return this.evaluation.rules.map((rule, index) => {
            return `
                <div class="rule-card" data-rule-id="${rule.id}">
                    <div class="rule-header">
                        <h4>${this.getRuleTitle(rule.type)}</h4>
                        <div class="rule-actions">
                            <button class="icon-button" onclick="evaluationBuilder.editRule(${rule.id})">
                                <i class="fas fa-cog"></i>
                            </button>
                            <button class="icon-button" onclick="evaluationBuilder.deleteRule(${rule.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="rule-summary">
                        ${this.getRuleSummary(rule)}
                    </div>
                </div>
            `;
        }).join('');
    }

    getRuleTitle(type) {
        const titles = {
            'pattern_detection': 'Pattern Match',
            'metric_threshold': 'Metric Threshold',
            'cross_round_analysis': 'Cross-Round Tracking',
            'penalty': 'Penalty Rule'
        };
        return titles[type] || 'Unknown Rule';
    }

    getRuleSummary(rule) {
        switch (rule.type) {
            case 'pattern_detection':
                const patterns = rule.patterns || [];
                return `Detects ${patterns.length} pattern(s)`;
            
            case 'metric_threshold':
                return `Evaluates ${rule.metric || 'metric'} against thresholds`;
            
            case 'cross_round_analysis':
                return `Tracks ${rule.track || 'data'} across rounds`;
            
            case 'penalty':
                const penalties = rule.patterns || [];
                return `Applies ${penalties.length} penalty condition(s)`;
            
            default:
                return 'Custom rule';
        }
    }

    attachEventListeners() {
        // Component drag and drop
        document.querySelectorAll('.component-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                this.addRule(type);
            });

            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('ruleType', e.currentTarget.dataset.type);
            });
        });

        // Drop zone
        const dropZone = document.querySelector('.rules-list') || document.querySelector('.drop-hint');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('drag-over');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                const type = e.dataTransfer.getData('ruleType');
                if (type) {
                    this.addRule(type);
                }
            });
        }

        // Form inputs
        document.getElementById('eval-name')?.addEventListener('input', (e) => {
            this.evaluation.name = e.target.value;
        });

        document.getElementById('eval-description')?.addEventListener('input', (e) => {
            this.evaluation.description = e.target.value;
        });

        document.getElementById('eval-category')?.addEventListener('change', (e) => {
            this.evaluation.category = e.target.value;
        });

        // Scoring type
        document.querySelectorAll('input[name="scoring-type"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.evaluation.scoring_type = e.target.value;
                document.querySelectorAll('.radio-card').forEach(card => {
                    card.classList.remove('selected');
                });
                e.target.closest('.radio-card').classList.add('selected');
            });
        });
    }

    addRule(type) {
        const rule = this.createDefaultRule(type);
        this.evaluation.rules.push(rule);
        this.refreshRulesList();
        this.editRule(rule.id);
    }

    createDefaultRule(type) {
        const ruleId = ++this.ruleIdCounter;
        const defaults = {
            'pattern_detection': {
                id: ruleId,
                type: 'pattern_detection',
                patterns: [
                    {
                        name: 'example_pattern',
                        keywords: ['example'],
                        score: 10
                    }
                ]
            },
            'metric_threshold': {
                id: ruleId,
                type: 'metric_threshold',
                metric: 'response_time',
                thresholds: [
                    { operator: '<', value: 30, score: 100 },
                    { default: true, score: 0 }
                ]
            },
            'cross_round_analysis': {
                id: ruleId,
                type: 'cross_round_analysis',
                track: 'entity_mentions',
                scoring: {
                    callback_detected: 25,
                    escalation_detected: 30,
                    consistency_bonus: 20
                }
            },
            'penalty': {
                id: ruleId,
                type: 'penalty',
                patterns: [
                    {
                        keywords: ['inappropriate'],
                        penalty: -50,
                        reason: 'Inappropriate content'
                    }
                ]
            }
        };

        return defaults[type] || { id: ruleId, type: type };
    }

    editRule(ruleId) {
        const rule = this.evaluation.rules.find(r => r.id === ruleId);
        if (!rule) return;

        // Show rule editor modal
        this.showRuleEditor(rule);
    }

    showRuleEditor(rule) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal-content modal-large">
                <div class="modal-header">
                    <h3>Edit ${this.getRuleTitle(rule.type)}</h3>
                    <button class="modal-close" onclick="evaluationBuilder.closeRuleEditor()">&times;</button>
                </div>
                <div class="modal-body">
                    ${this.getRuleEditorContent(rule)}
                </div>
                <div class="modal-footer">
                    <button class="button button-secondary" onclick="evaluationBuilder.closeRuleEditor()">
                        Cancel
                    </button>
                    <button class="button button-primary" onclick="evaluationBuilder.saveRuleChanges(${rule.id})">
                        Save Changes
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    getRuleEditorContent(rule) {
        switch (rule.type) {
            case 'pattern_detection':
                return this.getPatternDetectionEditor(rule);
            case 'metric_threshold':
                return this.getMetricThresholdEditor(rule);
            case 'cross_round_analysis':
                return this.getCrossRoundEditor(rule);
            case 'penalty':
                return this.getPenaltyEditor(rule);
            default:
                return '<p>Rule editor not implemented</p>';
        }
    }

    getPatternDetectionEditor(rule) {
        return `
            <div class="rule-editor">
                <h4>Patterns to Detect</h4>
                <div id="patterns-list">
                    ${(rule.patterns || []).map((pattern, index) => `
                        <div class="pattern-item" data-index="${index}">
                            <div class="form-group">
                                <label>Pattern Name</label>
                                <input type="text" class="form-control" 
                                       value="${pattern.name || ''}" 
                                       data-field="name">
                            </div>
                            <div class="form-group">
                                <label>Keywords (comma-separated)</label>
                                <input type="text" class="form-control" 
                                       value="${(pattern.keywords || []).join(', ')}" 
                                       data-field="keywords">
                            </div>
                            <div class="form-group">
                                <label>Regex Pattern (optional)</label>
                                <input type="text" class="form-control" 
                                       value="${pattern.regex || ''}" 
                                       data-field="regex">
                            </div>
                            <div class="form-group">
                                <label>Score</label>
                                <input type="number" class="form-control" 
                                       value="${pattern.score || 0}" 
                                       data-field="score">
                            </div>
                            <button class="button button-sm button-danger" 
                                    onclick="evaluationBuilder.removePattern(${index})">
                                Remove Pattern
                            </button>
                        </div>
                    `).join('')}
                </div>
                <button class="button button-secondary" onclick="evaluationBuilder.addPattern()">
                    Add Pattern
                </button>
            </div>
        `;
    }

    getMetricThresholdEditor(rule) {
        return `
            <div class="rule-editor">
                <div class="form-group">
                    <label>Metric to Evaluate</label>
                    <select class="form-control" id="rule-metric">
                        <option value="response_time" ${rule.metric === 'response_time' ? 'selected' : ''}>
                            Response Time
                        </option>
                        <option value="token_count" ${rule.metric === 'token_count' ? 'selected' : ''}>
                            Token Count
                        </option>
                        <option value="accuracy" ${rule.metric === 'accuracy' ? 'selected' : ''}>
                            Accuracy Score
                        </option>
                    </select>
                </div>
                
                <h4>Thresholds</h4>
                <div id="thresholds-list">
                    ${(rule.thresholds || []).map((threshold, index) => `
                        <div class="threshold-item" data-index="${index}">
                            ${!threshold.default ? `
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>Operator</label>
                                        <select class="form-control" data-field="operator">
                                            <option value="<" ${threshold.operator === '<' ? 'selected' : ''}>&lt;</option>
                                            <option value="<=" ${threshold.operator === '<=' ? 'selected' : ''}>&lt;=</option>
                                            <option value=">" ${threshold.operator === '>' ? 'selected' : ''}>&gt;</option>
                                            <option value=">=" ${threshold.operator === '>=' ? 'selected' : ''}>&gt;=</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label>Value</label>
                                        <input type="number" class="form-control" 
                                               value="${threshold.value || 0}" 
                                               data-field="value">
                                    </div>
                                </div>
                            ` : '<p>Default (else) condition</p>'}
                            
                            <div class="form-group">
                                <label>Score${threshold.score_formula ? ' Formula' : ''}</label>
                                <input type="text" class="form-control" 
                                       value="${threshold.score_formula || threshold.score || 0}" 
                                       data-field="score"
                                       placeholder="${threshold.score_formula ? 'e.g., 100 * (1 - response_time/60)' : 'Score value'}">
                            </div>
                            
                            ${!threshold.default ? `
                                <button class="button button-sm button-danger" 
                                        onclick="evaluationBuilder.removeThreshold(${index})">
                                    Remove
                                </button>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                
                <button class="button button-secondary" onclick="evaluationBuilder.addThreshold()">
                    Add Threshold
                </button>
            </div>
        `;
    }

    getCrossRoundEditor(rule) {
        return `
            <div class="rule-editor">
                <div class="form-group">
                    <label>Track Field</label>
                    <select class="form-control" id="rule-track">
                        <option value="entity_mentions" ${rule.track === 'entity_mentions' ? 'selected' : ''}>
                            Entity Mentions
                        </option>
                        <option value="year_mentions" ${rule.track === 'year_mentions' ? 'selected' : ''}>
                            Year Mentions
                        </option>
                        <option value="custom" ${rule.track === 'custom' ? 'selected' : ''}>
                            Custom Field
                        </option>
                    </select>
                </div>
                
                <h4>Scoring</h4>
                <div class="form-group">
                    <label>Callback Points</label>
                    <input type="number" class="form-control" id="callback-points"
                           value="${rule.scoring?.callback_detected || 25}">
                </div>
                <div class="form-group">
                    <label>Escalation Points</label>
                    <input type="number" class="form-control" id="escalation-points"
                           value="${rule.scoring?.escalation_detected || 30}">
                </div>
                <div class="form-group">
                    <label>Consistency Bonus</label>
                    <input type="number" class="form-control" id="consistency-points"
                           value="${rule.scoring?.consistency_bonus || 20}">
                </div>
            </div>
        `;
    }

    getPenaltyEditor(rule) {
        return `
            <div class="rule-editor">
                <h4>Penalty Conditions</h4>
                <div id="penalties-list">
                    ${(rule.patterns || []).map((penalty, index) => `
                        <div class="penalty-item" data-index="${index}">
                            <div class="form-group">
                                <label>Keywords (comma-separated)</label>
                                <input type="text" class="form-control" 
                                       value="${(penalty.keywords || []).join(', ')}" 
                                       data-field="keywords">
                            </div>
                            <div class="form-group">
                                <label>Penalty Points (negative)</label>
                                <input type="number" class="form-control" 
                                       value="${penalty.penalty || -10}" 
                                       data-field="penalty">
                            </div>
                            <div class="form-group">
                                <label>Reason</label>
                                <input type="text" class="form-control" 
                                       value="${penalty.reason || ''}" 
                                       data-field="reason">
                            </div>
                            <button class="button button-sm button-danger" 
                                    onclick="evaluationBuilder.removePenalty(${index})">
                                Remove
                            </button>
                        </div>
                    `).join('')}
                </div>
                <button class="button button-secondary" onclick="evaluationBuilder.addPenalty()">
                    Add Penalty Condition
                </button>
            </div>
        `;
    }

    closeRuleEditor() {
        document.querySelector('.modal-overlay')?.remove();
    }

    saveRuleChanges(ruleId) {
        const rule = this.evaluation.rules.find(r => r.id === ruleId);
        if (!rule) return;

        // Update rule based on editor inputs
        // This would be more sophisticated in production
        this.closeRuleEditor();
        this.refreshRulesList();
    }

    deleteRule(ruleId) {
        if (confirm('Are you sure you want to delete this rule?')) {
            this.evaluation.rules = this.evaluation.rules.filter(r => r.id !== ruleId);
            this.refreshRulesList();
        }
    }

    refreshRulesList() {
        const container = document.getElementById('rules-container');
        if (container) {
            container.innerHTML = this.renderRules();
        }
    }

    async testEvaluation() {
        const testData = {
            prompt: document.getElementById('test-prompt').value,
            response: document.getElementById('test-response').value,
            metadata: {
                response_time: parseFloat(document.getElementById('test-time').value) || 0
            }
        };

        const resultsDiv = document.getElementById('test-results');
        resultsDiv.innerHTML = '<div class="loading">Running test...</div>';

        // In a real implementation, this would call the API
        // For now, simulate the test
        setTimeout(() => {
            const mockResult = {
                raw_score: 75,
                normalized_score: 0.75,
                rule_breakdown: [
                    {
                        type: 'pattern_detection',
                        score: 25,
                        matches: [
                            { name: 'year_mention', matches: ['1987'], score: 10 }
                        ]
                    },
                    {
                        type: 'metric_threshold',
                        score: 50,
                        metric: 'response_time',
                        value: 15,
                        threshold_applied: '< 30'
                    }
                ]
            };

            this.displayTestResults(mockResult);
        }, 1000);
    }

    displayTestResults(result) {
        const resultsDiv = document.getElementById('test-results');
        resultsDiv.innerHTML = `
            <div class="test-result-card">
                <h4>Test Results</h4>
                <div class="result-scores">
                    <div class="score-item">
                        <label>Raw Score</label>
                        <div class="score-value">${result.raw_score}</div>
                    </div>
                    <div class="score-item">
                        <label>Normalized Score</label>
                        <div class="score-value">${(result.normalized_score * 100).toFixed(1)}%</div>
                    </div>
                </div>
                
                <h5>Rule Breakdown</h5>
                <div class="rule-results">
                    ${result.rule_breakdown.map(rule => `
                        <div class="rule-result">
                            <div class="rule-type">${this.getRuleTitle(rule.type)}</div>
                            <div class="rule-score">+${rule.score} points</div>
                            ${this.getRuleDetails(rule)}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    getRuleDetails(rule) {
        switch (rule.type) {
            case 'pattern_detection':
                return `
                    <div class="rule-details">
                        ${rule.matches.map(m => `
                            <div>• ${m.name}: ${m.matches.join(', ')} (+${m.score})</div>
                        `).join('')}
                    </div>
                `;
            
            case 'metric_threshold':
                return `
                    <div class="rule-details">
                        <div>• ${rule.metric}: ${rule.value} (${rule.threshold_applied})</div>
                    </div>
                `;
            
            default:
                return '';
        }
    }

    async save() {
        // Validate evaluation
        if (!this.evaluation.name) {
            alert('Please enter a name for the evaluation');
            return;
        }

        if (this.evaluation.rules.length === 0) {
            alert('Please add at least one rule');
            return;
        }

        // In a real implementation, this would save to the API
        console.log('Saving evaluation:', this.evaluation);
        alert('Evaluation saved successfully!');
    }

    importFromMarketplace() {
        // Show marketplace modal
        alert('Marketplace feature coming soon!');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('evaluation-builder-container')) {
        window.evaluationBuilder = new EvaluationBuilder('evaluation-builder-container');
    }
});