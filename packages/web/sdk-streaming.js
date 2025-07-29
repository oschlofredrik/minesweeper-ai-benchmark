// Vercel AI SDK Streaming Handler
class SDKStreamHandler {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.eventSource = null;
        this.evaluationId = null;
    }
    
    async connect(evaluationId) {
        this.evaluationId = evaluationId;
        
        // Show initial status
        this.addEvent({
            type: 'system',
            message: `Connected to SDK evaluation: ${evaluationId}`,
            timestamp: new Date().toISOString()
        });
        
        // For now, poll for updates
        // In production, this would use Server-Sent Events or WebSockets
        this.startPolling();
    }
    
    async startPolling() {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/evaluation/${this.evaluationId}/status`);
                if (response.ok) {
                    const data = await response.json();
                    this.handleUpdate(data);
                    
                    if (data.status === 'completed' || data.status === 'failed') {
                        clearInterval(pollInterval);
                    }
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000); // Poll every 2 seconds
    }
    
    handleUpdate(data) {
        if (data.progress !== undefined) {
            this.updateProgress(data.progress, data.games_completed, data.games_total);
        }
        
        if (data.events) {
            data.events.forEach(event => this.addEvent(event));
        }
    }
    
    updateProgress(progress, completed, total) {
        const progressBar = document.getElementById('sdk-progress');
        if (progressBar) {
            progressBar.style.width = `${progress * 100}%`;
            progressBar.textContent = `${completed}/${total} games`;
        }
    }
    
    addEvent(event) {
        const eventDiv = document.createElement('div');
        eventDiv.className = `sdk-event sdk-event-${event.type}`;
        
        const timestamp = new Date(event.timestamp).toLocaleTimeString();
        
        eventDiv.innerHTML = `
            <div class="sdk-event-header">
                <span class="sdk-event-type">${event.type}</span>
                <span class="sdk-event-time">${timestamp}</span>
            </div>
            <div class="sdk-event-content">
                ${this.formatEventContent(event)}
            </div>
        `;
        
        this.container.appendChild(eventDiv);
        this.container.scrollTop = this.container.scrollHeight;
    }
    
    formatEventContent(event) {
        switch (event.type) {
            case 'move':
                return `
                    <strong>${event.action}</strong> at (${event.row}, ${event.col})<br>
                    <em>${event.reasoning}</em>
                `;
            
            case 'game_complete':
                return `
                    Game ${event.gameNumber} completed: 
                    <strong>${event.won ? 'Won' : 'Lost'}</strong><br>
                    Moves: ${event.totalMoves}, Duration: ${event.duration}s
                `;
            
            case 'progress':
                return `Progress: ${event.completed}/${event.total} games completed`;
            
            default:
                return event.message || JSON.stringify(event.data);
        }
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Export for use in other scripts
window.SDKStreamHandler = SDKStreamHandler;