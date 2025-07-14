// Event Stream UI Components for Live Game Updates

class EventStreamUI {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.eventSource = null;
        this.currentGameNum = 0;
        this.eventBuffer = [];
        this.isScrolling = false;
        this.autoScroll = true;
        
        this.initializeUI();
        this.setupScrollDetection();
    }
    
    initializeUI() {
        this.container.innerHTML = `
            <div class="event-stream-header">
                <h4>Live Game Stream</h4>
                <div class="stream-controls">
                    <label class="toggle-switch">
                        <input type="checkbox" id="auto-scroll" checked>
                        <span>Auto-scroll</span>
                    </label>
                </div>
            </div>
            <div class="event-stream-container" id="event-stream-list">
                <div class="event-placeholder">
                    <p class="text-muted">Waiting for game to start...</p>
                </div>
            </div>
        `;
        
        // Setup auto-scroll toggle
        document.getElementById('auto-scroll').addEventListener('change', (e) => {
            this.autoScroll = e.target.checked;
        });
        
        this.streamList = document.getElementById('event-stream-list');
    }
    
    setupScrollDetection() {
        this.streamList.addEventListener('scroll', () => {
            const scrollTop = this.streamList.scrollTop;
            const scrollHeight = this.streamList.scrollHeight;
            const clientHeight = this.streamList.clientHeight;
            
            // Check if user is at bottom
            const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10;
            
            if (!isAtBottom && this.autoScroll) {
                // User scrolled up, disable auto-scroll
                this.autoScroll = false;
                document.getElementById('auto-scroll').checked = false;
            }
        });
    }
    
    connect(jobId) {
        if (this.eventSource) {
            this.disconnect();
        }
        
        // Clear placeholder
        this.streamList.innerHTML = '';
        
        // Create EventSource connection
        const url = `/api/stream/games/${jobId}/events`;
        this.eventSource = new EventSource(url);
        
        this.eventSource.onopen = () => {
            console.log('Event stream connected');
            this.addSystemEvent('Connected to live stream');
        };
        
        this.eventSource.onerror = (error) => {
            console.error('Event stream error:', error);
            this.addSystemEvent('Connection lost - retrying...', 'error');
        };
        
        // Setup event listeners for different event types
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Generic event handler
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleEvent(event.type || 'message', data);
            } catch (e) {
                console.error('Failed to parse event:', e);
            }
        };
        
        // Specific event types
        const eventTypes = [
            'connected', 'game_started', 'game_completed', 'game_won', 'game_lost',
            'move_started', 'move_thinking', 'move_reasoning', 'move_completed',
            'move_failed', 'board_update', 'metrics_update', 'error', 'status_update'
        ];
        
        eventTypes.forEach(type => {
            this.eventSource.addEventListener(type, (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleEvent(type, data);
                } catch (e) {
                    console.error(`Failed to parse ${type} event:`, e);
                }
            });
        });
    }
    
    handleEvent(type, data) {
        switch (type) {
            case 'connected':
                // Already handled in onopen
                break;
                
            case 'game_started':
                this.addGameStartEvent(data);
                break;
                
            case 'move_thinking':
                this.addThinkingEvent(data);
                break;
                
            case 'move_reasoning':
                this.addReasoningEvent(data);
                break;
                
            case 'move_completed':
                this.addMoveEvent(data);
                break;
                
            case 'move_failed':
                this.addFailedMoveEvent(data);
                break;
                
            case 'game_won':
            case 'game_lost':
                this.addGameEndEvent(data, type === 'game_won');
                break;
                
            case 'metrics_update':
                this.updateMetrics(data);
                break;
                
            case 'error':
                this.addErrorEvent(data);
                break;
                
            case 'status_update':
                this.addStatusEvent(data);
                break;
                
            default:
                console.log('Unknown event type:', type, data);
        }
        
        this.scrollToBottom();
    }
    
    addSystemEvent(message, type = 'info') {
        const event = document.createElement('div');
        event.className = `event-item system-event ${type}`;
        event.innerHTML = `
            <div class="event-icon">
                ${type === 'error' ? 'ERROR' : 'INFO'}
            </div>
            <div class="event-content">
                <div class="event-message">${message}</div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    addGameStartEvent(data) {
        this.currentGameNum = data.game_num || 1;
        const event = document.createElement('div');
        event.className = 'event-item game-start';
        event.innerHTML = `
            <div class="event-icon">START</div>
            <div class="event-content">
                <div class="event-title">Game ${this.currentGameNum} Started</div>
                <div class="event-details">
                    ${data.board_size} board • ${data.num_mines} mines • ${data.difficulty} difficulty
                </div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    addThinkingEvent(data) {
        const event = document.createElement('div');
        event.className = 'event-item thinking';
        event.id = `thinking-${data.game_num}-${data.move_num}`;
        event.innerHTML = `
            <div class="event-icon">
                <div class="thinking-indicator">...</div>
            </div>
            <div class="event-content">
                <div class="event-message">Analyzing board for move ${data.move_num}...</div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    addReasoningEvent(data) {
        if (data.partial) {
            // Handle streaming reasoning updates
            const existingEl = document.getElementById(`reasoning-${data.game_num}-${data.move_num}`);
            if (existingEl) {
                // Append to existing reasoning
                const textEl = existingEl.querySelector('.reasoning-text');
                if (textEl) {
                    textEl.textContent += data.reasoning;
                    this.scrollToBottom();
                }
                return;
            }
            
            // Create new streaming reasoning element
            const event = document.createElement('div');
            event.id = `reasoning-${data.game_num}-${data.move_num}`;
            event.className = 'event-item reasoning';
            event.innerHTML = `
                <div class="event-icon">REASON</div>
                <div class="event-content">
                    <div class="event-title">AI Reasoning (streaming...)</div>
                    <div class="reasoning-text streaming">${this.formatReasoning(data.reasoning)}</div>
                    <div class="event-time">${this.formatTime()}</div>
                </div>
            `;
            this.streamList.appendChild(event);
        } else {
            // Remove thinking indicator if exists
            const thinkingEl = document.getElementById(`thinking-${data.game_num}-${data.move_num}`);
            if (thinkingEl) {
                thinkingEl.remove();
            }
            
            // Update existing streaming element or create new one
            const existingEl = document.getElementById(`reasoning-${data.game_num}-${data.move_num}`);
            if (existingEl) {
                // Update the existing element to final state
                const titleEl = existingEl.querySelector('.event-title');
                const textEl = existingEl.querySelector('.reasoning-text');
                if (titleEl) titleEl.textContent = 'AI Reasoning';
                if (textEl) {
                    textEl.classList.remove('streaming');
                    textEl.textContent = this.formatReasoning(data.reasoning);
                }
            } else {
                // Create complete reasoning element
                const event = document.createElement('div');
                event.className = 'event-item reasoning';
                event.innerHTML = `
                    <div class="event-icon">REASON</div>
                    <div class="event-content">
                        <div class="event-title">AI Reasoning</div>
                        <div class="reasoning-text">${this.formatReasoning(data.reasoning)}</div>
                        <div class="event-time">${this.formatTime()}</div>
                    </div>
                `;
                this.streamList.appendChild(event);
            }
        }
    }
    
    addMoveEvent(data) {
        const event = document.createElement('div');
        event.className = `event-item move ${data.success ? 'success' : 'failed'}`;
        event.innerHTML = `
            <div class="event-icon">${this.getActionIcon(data.action)}</div>
            <div class="event-content">
                <div class="event-title">Move ${data.move_num}: ${data.action}</div>
                <div class="event-status">${data.success ? 'Valid move' : 'Invalid move'}</div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    addFailedMoveEvent(data) {
        const event = document.createElement('div');
        event.className = 'event-item move-failed';
        event.innerHTML = `
            <div class="event-icon">FAIL</div>
            <div class="event-content">
                <div class="event-title">Failed to parse move ${data.move_num}</div>
                <div class="event-error">${data.error}</div>
                <div class="event-details">Consecutive errors: ${data.consecutive_errors}</div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    addGameEndEvent(data, won) {
        const event = document.createElement('div');
        event.className = `event-item game-end ${won ? 'won' : 'lost'}`;
        event.innerHTML = `
            <div class="event-icon">${won ? 'WON' : 'LOST'}</div>
            <div class="event-content">
                <div class="event-title">Game ${data.game_num} ${won ? 'Won!' : 'Lost'}</div>
                <div class="event-stats">
                    ${data.moves} moves • ${(data.coverage * 100).toFixed(1)}% coverage • ${data.duration.toFixed(1)}s
                </div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    addErrorEvent(data) {
        const event = document.createElement('div');
        event.className = 'event-item error';
        event.innerHTML = `
            <div class="event-icon">🚨</div>
            <div class="event-content">
                <div class="event-title">Error</div>
                <div class="event-error">${data.message}</div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    addStatusEvent(data) {
        const event = document.createElement('div');
        event.className = 'event-item status';
        event.innerHTML = `
            <div class="event-icon">DONE</div>
            <div class="event-content">
                <div class="event-message">${data.message}</div>
                <div class="event-time">${this.formatTime()}</div>
            </div>
        `;
        this.streamList.appendChild(event);
    }
    
    updateMetrics(data) {
        // Update progress bar if exists
        const progressBar = document.querySelector('.progress-fill');
        if (progressBar) {
            progressBar.style.width = `${data.progress * 100}%`;
        }
        
        // Update metrics display if exists
        const metricsEl = document.querySelector('.current-metrics');
        if (metricsEl) {
            metricsEl.innerHTML = `
                Win Rate: ${(data.win_rate * 100).toFixed(1)}% • 
                Avg Moves: ${data.avg_moves.toFixed(1)} • 
                Progress: ${data.games_completed}/${data.games_total}
            `;
        }
    }
    
    getActionIcon(action) {
        if (action.toLowerCase().includes('reveal')) return 'REVEAL';
        if (action.toLowerCase().includes('flag')) return 'FLAG';
        if (action.toLowerCase().includes('unflag')) return 'UNFLAG';
        return 'MOVE';
    }
    
    formatReasoning(text) {
        // Format reasoning text with proper line breaks
        return text
            .replace(/\n/g, '<br>')
            .replace(/(\d+\.\s)/g, '<br>$1')
            .replace(/^<br>/, '');
    }
    
    formatTime() {
        return new Date().toLocaleTimeString();
    }
    
    scrollToBottom() {
        // Always scroll to bottom for new events
        requestAnimationFrame(() => {
            this.streamList.scrollTop = this.streamList.scrollHeight;
        });
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.addSystemEvent('Disconnected from stream');
        }
    }
}