/**
 * Evaluation Selector Component
 * 
 * Allows users to select and configure evaluations when creating games/competitions
 */

class EvaluationSelector {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.selectedEvaluations = [];
        this.availableEvaluations = [];
        this.presets = [];
        this.options = {
            maxEvaluations: options.maxEvaluations || 5,
            allowCustomWeights: options.allowCustomWeights !== false,
            showPresets: options.showPresets !== false,
            onUpdate: options.onUpdate || (() => {})
        };
        
        this.init();
    }

    async init() {
        await this.loadAvailableEvaluations();
        await this.loadPresets();
        this.render();
        this.attachEventListeners();
    }

    async loadAvailableEvaluations() {
        try {
            const response = await fetch('/api/evaluations?is_public=true&limit=50');
            const evaluations = await response.json();
            this.availableEvaluations = evaluations;
        } catch (error) {
            console.error('Failed to load evaluations:', error);
            this.availableEvaluations = [];
        }
    }

    async loadPresets() {
        try {
            const response = await fetch('/api/evaluations/presets');
            const presets = await response.json();
            this.presets = presets;
        } catch (error) {
            console.error('Failed to load presets:', error);
            this.presets = [];
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="evaluation-selector">
                <div class="selector-header">
                    <h3>Competition Evaluations</h3>
                    <p class="text-muted">Select how player performance will be evaluated</p>
                </div>

                ${this.options.showPresets ? this.renderPresets() : ''}

                <div class="evaluation-tabs">
                    <button class="tab-button active" data-tab="browse">Browse Evaluations</button>
                    <button class="tab-button" data-tab="selected">Selected (${this.selectedEvaluations.length})</button>
                    <button class="tab-button" data-tab="create">Create Custom</button>
                </div>

                <div class="tab-content">
                    <div id="browse-tab" class="tab-pane active">
                        ${this.renderBrowseTab()}
                    </div>
                    <div id="selected-tab" class="tab-pane">
                        ${this.renderSelectedTab()}
                    </div>
                    <div id="create-tab" class="tab-pane">
                        ${this.renderCreateTab()}
                    </div>
                </div>

                <div class="selector-footer">
                    <div class="weight-summary">
                        Total Weight: <span id="total-weight">0%</span>
                        ${this.getTotalWeight() !== 100 ? '<span class="text-error ml-2">Must equal 100%</span>' : ''}
                    </div>
                </div>
            </div>
        `;
    }

    renderPresets() {
        return `
            <div class="preset-section">
                <h4>Quick Presets</h4>
                <div class="preset-grid">
                    <button class="preset-card" onclick="evaluationSelector.applyPreset('balanced')">
                        <i class="fas fa-balance-scale"></i>
                        <h5>Balanced</h5>
                        <p>Equal focus on all aspects</p>
                    </button>
                    <button class="preset-card" onclick="evaluationSelector.applyPreset('speed_focused')">
                        <i class="fas fa-tachometer-alt"></i>
                        <h5>Speed Focused</h5>
                        <p>Prioritize fast completion</p>
                    </button>
                    <button class="preset-card" onclick="evaluationSelector.applyPreset('accuracy_focused')">
                        <i class="fas fa-bullseye"></i>
                        <h5>Accuracy Focused</h5>
                        <p>Prioritize correct solutions</p>
                    </button>
                    <button class="preset-card" onclick="evaluationSelector.applyPreset('creative')">
                        <i class="fas fa-lightbulb"></i>
                        <h5>Creative Challenge</h5>
                        <p>Reward innovative approaches</p>
                    </button>
                </div>
            </div>
        `;
    }

    renderBrowseTab() {
        const categories = [...new Set(this.availableEvaluations.map(e => e.category).filter(Boolean))];
        
        return `
            <div class="browse-content">
                <div class="filter-bar">
                    <input type="text" id="eval-search" placeholder="Search evaluations..." class="form-control">
                    <select id="eval-category" class="form-control">
                        <option value="">All Categories</option>
                        ${categories.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
                    </select>
                </div>

                <div class="evaluation-grid" id="evaluation-list">
                    ${this.renderEvaluationList()}
                </div>
            </div>
        `;
    }

    renderEvaluationList(filter = {}) {
        let evaluations = this.availableEvaluations;
        
        // Apply filters
        if (filter.search) {
            const searchLower = filter.search.toLowerCase();
            evaluations = evaluations.filter(e => 
                e.name.toLowerCase().includes(searchLower) ||
                (e.description && e.description.toLowerCase().includes(searchLower))
            );
        }
        
        if (filter.category) {
            evaluations = evaluations.filter(e => e.category === filter.category);
        }

        // Filter out already selected evaluations
        const selectedIds = this.selectedEvaluations.map(e => e.id);
        evaluations = evaluations.filter(e => !selectedIds.includes(e.id));

        if (evaluations.length === 0) {
            return '<p class="text-muted text-center">No evaluations found</p>';
        }

        return evaluations.map(eval => `
            <div class="evaluation-card" data-id="${eval.id}">
                <div class="eval-header">
                    <h5>${eval.name}</h5>
                    ${eval.category ? `<span class="badge">${eval.category}</span>` : ''}
                </div>
                <p class="eval-description">${eval.description || 'No description'}</p>
                <div class="eval-meta">
                    <span class="scoring-type">${eval.scoring_type}</span>
                    ${eval.average_rating ? `
                        <span class="rating">
                            <i class="fas fa-star"></i> ${eval.average_rating.toFixed(1)}
                        </span>
                    ` : ''}
                    ${eval.downloads ? `
                        <span class="downloads">
                            <i class="fas fa-download"></i> ${eval.downloads}
                        </span>
                    ` : ''}
                </div>
                <button class="button button-small" onclick="evaluationSelector.addEvaluation('${eval.id}')">
                    Add to Competition
                </button>
            </div>
        `).join('');
    }

    renderSelectedTab() {
        if (this.selectedEvaluations.length === 0) {
            return `
                <div class="empty-state">
                    <i class="fas fa-clipboard-list"></i>
                    <p>No evaluations selected yet</p>
                    <button class="button button-secondary" onclick="evaluationSelector.switchTab('browse')">
                        Browse Evaluations
                    </button>
                </div>
            `;
        }

        const totalWeight = this.getTotalWeight();
        const isValid = Math.abs(totalWeight - 100) < 0.01;

        return `
            <div class="selected-content">
                <div class="selected-evaluations">
                    ${this.selectedEvaluations.map((eval, index) => `
                        <div class="selected-eval-card" data-index="${index}">
                            <div class="eval-info">
                                <h5>${eval.name}</h5>
                                <p class="text-muted">${eval.description || 'No description'}</p>
                                ${eval.dimension ? `
                                    <div class="dimension-tag">
                                        <i class="fas fa-tag"></i> ${eval.dimension}
                                    </div>
                                ` : ''}
                            </div>
                            <div class="eval-controls">
                                <div class="weight-control">
                                    <label>Weight</label>
                                    <div class="weight-input-group">
                                        <input type="number" 
                                               class="form-control weight-input" 
                                               value="${eval.weight * 100}" 
                                               min="0" 
                                               max="100" 
                                               step="5"
                                               data-index="${index}"
                                               ${!this.options.allowCustomWeights ? 'disabled' : ''}>
                                        <span class="weight-suffix">%</span>
                                    </div>
                                </div>
                                <button class="icon-button" onclick="evaluationSelector.configureEvaluation(${index})" 
                                        title="Configure">
                                    <i class="fas fa-cog"></i>
                                </button>
                                <button class="icon-button text-danger" 
                                        onclick="evaluationSelector.removeEvaluation(${index})"
                                        title="Remove">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>

                ${this.options.allowCustomWeights ? `
                    <div class="weight-actions">
                        <button class="button button-small" onclick="evaluationSelector.autoBalanceWeights()">
                            Auto-Balance Weights
                        </button>
                        ${!isValid ? `
                            <span class="text-error">Weights must total 100%</span>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderCreateTab() {
        return `
            <div class="create-content">
                <div class="create-options">
                    <button class="option-card" onclick="evaluationSelector.createQuickEvaluation()">
                        <i class="fas fa-bolt"></i>
                        <h5>Quick Create</h5>
                        <p>Use templates to create a simple evaluation</p>
                    </button>
                    <button class="option-card" onclick="window.open('/evaluations/builder', '_blank')">
                        <i class="fas fa-tools"></i>
                        <h5>Advanced Builder</h5>
                        <p>Create complex evaluations with the full builder</p>
                    </button>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Search and filter
        const searchInput = document.getElementById('eval-search');
        const categorySelect = document.getElementById('eval-category');
        
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterEvaluations());
        }
        
        if (categorySelect) {
            categorySelect.addEventListener('change', () => this.filterEvaluations());
        }

        // Weight inputs
        document.querySelectorAll('.weight-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index);
                const weight = parseFloat(e.target.value) / 100;
                this.updateWeight(index, weight);
            });
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`)?.classList.add('active');
    }

    filterEvaluations() {
        const search = document.getElementById('eval-search')?.value || '';
        const category = document.getElementById('eval-category')?.value || '';
        
        const listContainer = document.getElementById('evaluation-list');
        if (listContainer) {
            listContainer.innerHTML = this.renderEvaluationList({ search, category });
        }
    }

    async addEvaluation(evaluationId) {
        // Find the evaluation
        const evaluation = this.availableEvaluations.find(e => e.id === evaluationId);
        if (!evaluation) return;

        // Check max evaluations
        if (this.selectedEvaluations.length >= this.options.maxEvaluations) {
            alert(`Maximum ${this.options.maxEvaluations} evaluations allowed`);
            return;
        }

        // Add to selected with default weight
        const weight = this.selectedEvaluations.length === 0 ? 1.0 : 0;
        this.selectedEvaluations.push({
            ...evaluation,
            weight: weight,
            dimension: null,
            config_overrides: {}
        });

        // Auto-balance if needed
        if (this.options.allowCustomWeights && this.selectedEvaluations.length > 1) {
            this.autoBalanceWeights();
        }

        // Update UI
        this.render();
        this.switchTab('selected');
        
        // Notify parent
        this.options.onUpdate(this.getSelectedEvaluations());
    }

    removeEvaluation(index) {
        this.selectedEvaluations.splice(index, 1);
        
        // Auto-balance remaining weights
        if (this.selectedEvaluations.length > 0 && this.options.allowCustomWeights) {
            this.autoBalanceWeights();
        }

        this.render();
        this.options.onUpdate(this.getSelectedEvaluations());
    }

    updateWeight(index, weight) {
        if (this.selectedEvaluations[index]) {
            this.selectedEvaluations[index].weight = Math.max(0, Math.min(1, weight));
            this.updateWeightDisplay();
            this.options.onUpdate(this.getSelectedEvaluations());
        }
    }

    autoBalanceWeights() {
        const count = this.selectedEvaluations.length;
        if (count === 0) return;

        const equalWeight = 1 / count;
        this.selectedEvaluations.forEach(eval => {
            eval.weight = equalWeight;
        });

        this.render();
        this.options.onUpdate(this.getSelectedEvaluations());
    }

    getTotalWeight() {
        return this.selectedEvaluations.reduce((sum, eval) => sum + (eval.weight || 0), 0) * 100;
    }

    updateWeightDisplay() {
        const total = this.getTotalWeight();
        const totalElement = document.getElementById('total-weight');
        if (totalElement) {
            totalElement.textContent = `${total.toFixed(0)}%`;
            totalElement.classList.toggle('text-error', Math.abs(total - 100) > 0.01);
        }
    }

    configureEvaluation(index) {
        const eval = this.selectedEvaluations[index];
        if (!eval) return;

        // Show configuration modal
        this.showConfigModal(eval, index);
    }

    showConfigModal(evaluation, index) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Configure ${evaluation.name}</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Evaluation Dimension</label>
                        <input type="text" id="eval-dimension" class="form-control" 
                               value="${evaluation.dimension || ''}"
                               placeholder="e.g., speed, accuracy, creativity">
                        <small class="text-muted">
                            Optional: Specify what aspect this evaluation measures
                        </small>
                    </div>
                    
                    <div class="form-group">
                        <label>Config Overrides (JSON)</label>
                        <textarea id="eval-overrides" class="form-control" rows="4"
                                  placeholder='{"threshold": 0.8, "bonus_points": 10}'>${
                            JSON.stringify(evaluation.config_overrides || {}, null, 2)
                        }</textarea>
                        <small class="text-muted">
                            Advanced: Override evaluation configuration
                        </small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="button button-secondary" onclick="this.closest('.modal-overlay').remove()">
                        Cancel
                    </button>
                    <button class="button button-primary" onclick="evaluationSelector.saveConfig(${index})">
                        Save Configuration
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    saveConfig(index) {
        const dimension = document.getElementById('eval-dimension')?.value || null;
        const overridesText = document.getElementById('eval-overrides')?.value || '{}';
        
        try {
            const overrides = JSON.parse(overridesText);
            this.selectedEvaluations[index].dimension = dimension;
            this.selectedEvaluations[index].config_overrides = overrides;
            
            // Close modal
            document.querySelector('.modal-overlay')?.remove();
            
            // Update display
            this.render();
            this.options.onUpdate(this.getSelectedEvaluations());
        } catch (error) {
            alert('Invalid JSON in config overrides');
        }
    }

    async applyPreset(presetName) {
        // Define preset configurations
        const presets = {
            balanced: [
                { name: 'Speed', category: 'speed', weight: 0.25 },
                { name: 'Accuracy', category: 'accuracy', weight: 0.25 },
                { name: 'Efficiency', category: 'efficiency', weight: 0.25 },
                { name: 'Reasoning', category: 'reasoning', weight: 0.25 }
            ],
            speed_focused: [
                { name: 'Speed', category: 'speed', weight: 0.60 },
                { name: 'Accuracy', category: 'accuracy', weight: 0.30 },
                { name: 'Efficiency', category: 'efficiency', weight: 0.10 }
            ],
            accuracy_focused: [
                { name: 'Accuracy', category: 'accuracy', weight: 0.70 },
                { name: 'Reasoning', category: 'reasoning', weight: 0.20 },
                { name: 'Speed', category: 'speed', weight: 0.10 }
            ],
            creative: [
                { name: 'Creativity', category: 'creativity', weight: 0.50 },
                { name: 'Reasoning', category: 'reasoning', weight: 0.30 },
                { name: 'Accuracy', category: 'accuracy', weight: 0.20 }
            ]
        };

        const preset = presets[presetName];
        if (!preset) return;

        // Clear current selections
        this.selectedEvaluations = [];

        // Try to find matching evaluations
        for (const item of preset) {
            const match = this.availableEvaluations.find(e => 
                e.category === item.category || 
                e.name.toLowerCase().includes(item.name.toLowerCase())
            );
            
            if (match) {
                this.selectedEvaluations.push({
                    ...match,
                    weight: item.weight,
                    dimension: item.name.toLowerCase()
                });
            }
        }

        // Update UI
        this.render();
        this.switchTab('selected');
        this.options.onUpdate(this.getSelectedEvaluations());
    }

    createQuickEvaluation() {
        // Show quick creation modal
        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Quick Create Evaluation</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Evaluation Name</label>
                        <input type="text" id="quick-eval-name" class="form-control" 
                               placeholder="e.g., Bonus Speed Points">
                    </div>
                    <div class="form-group">
                        <label>Type</label>
                        <select id="quick-eval-type" class="form-control">
                            <option value="time_bonus">Time Bonus (faster = more points)</option>
                            <option value="accuracy_threshold">Accuracy Threshold (pass/fail)</option>
                            <option value="move_efficiency">Move Efficiency</option>
                            <option value="pattern_match">Pattern Matching</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Parameters</label>
                        <div id="quick-eval-params">
                            <!-- Dynamic based on type -->
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="button button-secondary" onclick="this.closest('.modal-overlay').remove()">
                        Cancel
                    </button>
                    <button class="button button-primary" onclick="evaluationSelector.createQuickEval()">
                        Create & Add
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Update params when type changes
        document.getElementById('quick-eval-type').addEventListener('change', (e) => {
            this.updateQuickEvalParams(e.target.value);
        });
        
        // Initialize params
        this.updateQuickEvalParams('time_bonus');
    }

    updateQuickEvalParams(type) {
        const paramsDiv = document.getElementById('quick-eval-params');
        if (!paramsDiv) return;

        const paramTemplates = {
            time_bonus: `
                <div class="form-row">
                    <div class="form-group">
                        <label>Max Time (seconds)</label>
                        <input type="number" id="param-max-time" class="form-control" value="300">
                    </div>
                    <div class="form-group">
                        <label>Max Bonus Points</label>
                        <input type="number" id="param-max-bonus" class="form-control" value="100">
                    </div>
                </div>
            `,
            accuracy_threshold: `
                <div class="form-group">
                    <label>Minimum Accuracy (%)</label>
                    <input type="number" id="param-min-accuracy" class="form-control" 
                           value="80" min="0" max="100">
                </div>
            `,
            move_efficiency: `
                <div class="form-group">
                    <label>Optimal Moves</label>
                    <input type="number" id="param-optimal-moves" class="form-control" value="20">
                </div>
            `,
            pattern_match: `
                <div class="form-group">
                    <label>Keywords (comma-separated)</label>
                    <input type="text" id="param-keywords" class="form-control" 
                           placeholder="strategy, analysis, optimize">
                </div>
            `
        };

        paramsDiv.innerHTML = paramTemplates[type] || '';
    }

    async createQuickEval() {
        const name = document.getElementById('quick-eval-name')?.value;
        const type = document.getElementById('quick-eval-type')?.value;
        
        if (!name) {
            alert('Please enter an evaluation name');
            return;
        }

        // Create evaluation based on type
        const quickEval = {
            id: `quick-${Date.now()}`,
            name: name,
            description: `Quick evaluation: ${type.replace('_', ' ')}`,
            scoring_type: type === 'accuracy_threshold' ? 'binary' : 'proportional',
            category: 'custom',
            is_quick: true,
            weight: 0
        };

        // Add to selected
        this.selectedEvaluations.push(quickEval);
        
        // Auto-balance weights
        this.autoBalanceWeights();

        // Close modal
        document.querySelector('.modal-overlay')?.remove();

        // Update UI
        this.render();
        this.switchTab('selected');
        this.options.onUpdate(this.getSelectedEvaluations());
    }

    getSelectedEvaluations() {
        return this.selectedEvaluations.map(eval => ({
            evaluation_id: eval.id,
            weight: eval.weight,
            dimension: eval.dimension,
            config_overrides: eval.config_overrides,
            is_quick: eval.is_quick || false
        }));
    }

    validateSelection() {
        if (this.selectedEvaluations.length === 0) {
            return { valid: false, message: 'Please select at least one evaluation' };
        }

        const totalWeight = this.getTotalWeight();
        if (Math.abs(totalWeight - 100) > 0.01) {
            return { valid: false, message: 'Evaluation weights must total 100%' };
        }

        return { valid: true };
    }
}

// Export for use in other modules
window.EvaluationSelector = EvaluationSelector;