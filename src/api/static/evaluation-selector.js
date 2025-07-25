/**
 * Evaluation Selector Component
 * 
 * Allows users to select and configure evaluations when creating games/competitions
 */

class EvaluationSelector {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.selectedMetrics = new Map(); // Store selected metrics with their weights
        this.availableMetrics = [];
        this.presets = {
            balanced: {
                name: 'Balanced',
                metrics: ['win_rate', 'valid_move_rate', 'mine_identification', 'board_coverage'],
                weights: { win_rate: 25, valid_move_rate: 25, mine_identification: 25, board_coverage: 25 }
            },
            speed_focused: {
                name: 'Speed Focused',
                metrics: ['win_rate', 'move_efficiency', 'time_efficiency'],
                weights: { win_rate: 50, move_efficiency: 30, time_efficiency: 20 }
            },
            accuracy_focused: {
                name: 'Accuracy Focused',
                metrics: ['valid_move_rate', 'mine_identification', 'safe_cell_accuracy'],
                weights: { valid_move_rate: 40, mine_identification: 40, safe_cell_accuracy: 20 }
            },
            strategic: {
                name: 'Strategic',
                metrics: ['reasoning_quality', 'board_coverage', 'move_efficiency'],
                weights: { reasoning_quality: 50, board_coverage: 30, move_efficiency: 20 }
            }
        };
        this.options = {
            maxMetrics: options.maxMetrics || 5,
            allowCustomWeights: options.allowCustomWeights !== false,
            onUpdate: options.onUpdate || (() => {})
        };
        
        this.initializeMetrics();
        this.render();
        this.attachEventListeners();
    }

    initializeMetrics() {
        // Define available metrics with their metadata
        this.availableMetrics = [
            {
                id: 'win_rate',
                name: 'Win Rate',
                description: 'Percentage of games successfully completed',
                icon: '🎯',
                category: 'outcome'
            },
            {
                id: 'valid_move_rate',
                name: 'Valid Move Rate',
                description: 'Percentage of legal moves made',
                icon: '✓',
                category: 'accuracy'
            },
            {
                id: 'mine_identification',
                name: 'Mine Identification',
                description: 'Precision in flagging actual mines',
                icon: '🚩',
                category: 'accuracy'
            },
            {
                id: 'board_coverage',
                name: 'Board Coverage',
                description: 'Percentage of safe cells revealed',
                icon: '📊',
                category: 'efficiency'
            },
            {
                id: 'move_efficiency',
                name: 'Move Efficiency',
                description: 'Optimal move count vs actual moves',
                icon: '⚡',
                category: 'efficiency'
            },
            {
                id: 'reasoning_quality',
                name: 'Reasoning Quality',
                description: 'AI judge evaluation of explanations',
                icon: '💭',
                category: 'reasoning'
            },
            {
                id: 'time_efficiency',
                name: 'Time Efficiency',
                description: 'Speed of completion',
                icon: '⏱',
                category: 'speed'
            },
            {
                id: 'safe_cell_accuracy',
                name: 'Safe Cell Accuracy',
                description: 'Avoiding mine detonations',
                icon: '🛡',
                category: 'accuracy'
            },
            {
                id: 'strategic_score',
                name: 'Strategic Score',
                description: 'Overall strategic gameplay quality',
                icon: '♟',
                category: 'composite'
            }
        ];
    }

    render() {
        // Check if we're in inline mode (no modal)
        const isInline = !this.container.closest('.modal-content');
        
        this.container.innerHTML = `
            <div class="evaluation-selector ${isInline ? 'inline-mode' : ''}">
                ${!isInline ? `
                <div class="selector-header">
                    <h3>Competition Scoring Configuration</h3>
                    <p class="text-muted">Select metrics to evaluate player performance</p>
                </div>
                ` : ''}

                <div class="scoring-config">
                    <div class="config-header">
                        ${!isInline ? '<h4 class="config-title">Evaluation Metrics</h4>' : ''}
                        <div class="config-actions">
                            <div class="custom-dropdown preset-dropdown" id="preset-dropdown">
                                <div class="dropdown-trigger" onclick="window.evaluationSelector.toggleDropdown('preset-dropdown')">
                                    <span>Load Preset</span>
                                    <div class="dropdown-arrow"></div>
                                </div>
                                <div class="dropdown-menu">
                                    ${Object.entries(this.presets).map(([key, preset]) => `
                                        <div class="dropdown-option" onclick="window.evaluationSelector.applyPreset('${key}')">
                                            ${preset.name}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            <button class="auto-balance-btn" onclick="window.evaluationSelector.autoBalanceWeights()">
                                Auto-Balance Weights
                            </button>
                        </div>
                    </div>

                    <div class="metrics-grid" id="metrics-grid">
                        ${this.renderMetricCards()}
                    </div>

                    <div class="weight-total">
                        <div class="weight-total-label">Total Weight</div>
                        <div class="weight-total-value ${this.getTotalWeight() !== 100 ? 'error' : ''}" id="total-weight">
                            ${this.getTotalWeight()}%
                        </div>
                        ${this.getTotalWeight() !== 100 ? 
                            '<div class="weight-total-hint">Weights must total 100%</div>' : 
                            '<div class="weight-total-hint">Perfect balance achieved</div>'
                        }
                    </div>
                </div>
            </div>
        `;
    }

    renderMetricCards() {
        return this.availableMetrics.map(metric => {
            const isSelected = this.selectedMetrics.has(metric.id);
            const weight = this.selectedMetrics.get(metric.id) || 0;
            
            return `
                <div class="metric-card ${isSelected ? 'selected' : ''}" 
                     data-metric-id="${metric.id}"
                     onclick="window.evaluationSelector.toggleMetric('${metric.id}')">
                    <div class="metric-header">
                        <div class="metric-icon">${metric.icon}</div>
                        <div class="metric-checkbox"></div>
                    </div>
                    <div class="metric-content">
                        <h5 class="metric-name">${metric.name}</h5>
                        <p class="metric-description">${metric.description}</p>
                    </div>
                    ${isSelected ? `
                        <div class="metric-weight" onclick="event.stopPropagation()">
                            <div class="weight-slider">
                                <label>Weight:</label>
                                <input type="range" 
                                       min="0" 
                                       max="100" 
                                       value="${weight}"
                                       step="5"
                                       onchange="window.evaluationSelector.updateWeight('${metric.id}', this.value)"
                                       oninput="window.evaluationSelector.updateWeightDisplay('${metric.id}', this.value)">
                                <span class="weight-value" id="weight-${metric.id}">${weight}%</span>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    toggleMetric(metricId) {
        if (this.selectedMetrics.has(metricId)) {
            this.selectedMetrics.delete(metricId);
        } else {
            // Check max metrics limit
            if (this.selectedMetrics.size >= this.options.maxMetrics) {
                alert(`Maximum ${this.options.maxMetrics} metrics allowed`);
                return;
            }
            
            // Add metric with default weight
            const defaultWeight = this.selectedMetrics.size === 0 ? 100 : 0;
            this.selectedMetrics.set(metricId, defaultWeight);
        }
        
        this.render();
        this.attachEventListeners();
        this.options.onUpdate(this.getSelectedMetrics());
    }

    updateWeight(metricId, value) {
        const weight = parseInt(value);
        this.selectedMetrics.set(metricId, weight);
        this.updateTotalWeight();
        this.options.onUpdate(this.getSelectedMetrics());
    }

    updateWeightDisplay(metricId, value) {
        const weightDisplay = document.getElementById(`weight-${metricId}`);
        if (weightDisplay) {
            weightDisplay.textContent = `${value}%`;
        }
        
        // Update total weight display
        const total = this.calculateTotalFromCurrentInputs();
        const totalDisplay = document.getElementById('total-weight');
        if (totalDisplay) {
            totalDisplay.textContent = `${total}%`;
            totalDisplay.classList.toggle('error', total !== 100);
            
            const hint = totalDisplay.parentElement.querySelector('.weight-total-hint');
            if (hint) {
                hint.textContent = total !== 100 ? 'Weights must total 100%' : 'Perfect balance achieved';
            }
        }
    }

    calculateTotalFromCurrentInputs() {
        let total = 0;
        document.querySelectorAll('.metric-card.selected input[type="range"]').forEach(input => {
            total += parseInt(input.value);
        });
        return total;
    }

    updateTotalWeight() {
        const total = this.getTotalWeight();
        const totalDisplay = document.getElementById('total-weight');
        if (totalDisplay) {
            totalDisplay.textContent = `${total}%`;
            totalDisplay.classList.toggle('error', total !== 100);
        }
    }

    getTotalWeight() {
        let total = 0;
        this.selectedMetrics.forEach(weight => total += weight);
        return total;
    }

    autoBalanceWeights() {
        if (this.selectedMetrics.size === 0) return;
        
        const equalWeight = Math.floor(100 / this.selectedMetrics.size);
        const remainder = 100 - (equalWeight * this.selectedMetrics.size);
        
        let index = 0;
        this.selectedMetrics.forEach((weight, metricId) => {
            // Give the remainder to the first metric
            this.selectedMetrics.set(metricId, equalWeight + (index === 0 ? remainder : 0));
            index++;
        });
        
        this.render();
        this.attachEventListeners();
        this.options.onUpdate(this.getSelectedMetrics());
    }

    applyPreset(presetKey) {
        const preset = this.presets[presetKey];
        if (!preset) return;
        
        // Clear current selections
        this.selectedMetrics.clear();
        
        // Apply preset selections
        preset.metrics.forEach(metricId => {
            if (preset.weights[metricId]) {
                this.selectedMetrics.set(metricId, preset.weights[metricId]);
            }
        });
        
        // Close dropdown
        this.toggleDropdown('preset-dropdown');
        
        // Re-render
        this.render();
        this.attachEventListeners();
        this.options.onUpdate(this.getSelectedMetrics());
    }

    toggleDropdown(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        
        const trigger = dropdown.querySelector('.dropdown-trigger');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (trigger && menu) {
            const isActive = trigger.classList.contains('active');
            
            // Close all dropdowns first
            document.querySelectorAll('.dropdown-trigger').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.remove('active'));
            
            // Toggle this dropdown
            if (!isActive) {
                trigger.classList.add('active');
                menu.classList.add('active');
            }
        }
    }

    attachEventListeners() {
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.custom-dropdown')) {
                document.querySelectorAll('.dropdown-trigger').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.remove('active'));
            }
        });
    }

    getSelectedMetrics() {
        const metrics = [];
        this.selectedMetrics.forEach((weight, metricId) => {
            const metric = this.availableMetrics.find(m => m.id === metricId);
            if (metric) {
                metrics.push({
                    id: metricId,
                    name: metric.name,
                    weight: weight / 100 // Convert to decimal
                });
            }
        });
        return metrics;
    }

    validateSelection() {
        if (this.selectedMetrics.size === 0) {
            return { valid: false, message: 'Please select at least one metric' };
        }
        
        const totalWeight = this.getTotalWeight();
        if (totalWeight !== 100) {
            return { valid: false, message: 'Metric weights must total 100%' };
        }
        
        return { valid: true };
    }

}

// Export for use in other modules
window.EvaluationSelector = EvaluationSelector;