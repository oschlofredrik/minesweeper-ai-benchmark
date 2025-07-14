// Minesweeper Visualization for AI Moves

class MinesweeperVisualization {
    constructor() {
        this.boardElement = document.getElementById('minesweeper-board');
        this.placeholder = document.querySelector('.board-placeholder');
        this.board = null;
        this.size = { rows: 0, cols: 0 };
        
        this.initializeElements();
        this.setupEventHandlers();
    }

    initializeElements() {
        this.startEvalBtn = document.getElementById('start-eval-btn');
        
        // Start evaluation button (opens modal)
        this.startEvalBtn?.addEventListener('click', () => this.openEvalModal());
    }

    setupEventHandlers() {
        // Listen for board updates from the event stream
        document.addEventListener('board-update', (event) => {
            this.updateBoard(event.detail);
        });
        
        // Listen for game start
        document.addEventListener('game-started', (event) => {
            this.initializeBoard(event.detail);
        });
        
        // Listen for move events
        document.addEventListener('move-completed', (event) => {
            this.highlightLastMove(event.detail);
        });
    }

    openEvalModal() {
        const modal = document.getElementById('eval-modal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    initializeBoard(gameData) {
        // Hide placeholder
        if (this.placeholder) {
            this.placeholder.style.display = 'none';
        }
        
        // Extract size from board_size string (e.g., "9x9")
        if (gameData.board_size) {
            const [rows, cols] = gameData.board_size.split('x').map(n => parseInt(n));
            this.size = { rows, cols };
        }
        
        // Initialize empty board
        this.board = [];
        for (let r = 0; r < this.size.rows; r++) {
            this.board[r] = [];
            for (let c = 0; c < this.size.cols; c++) {
                this.board[r][c] = {
                    state: 'hidden',
                    value: null,
                    flagged: false
                };
            }
        }
        
        this.render();
    }

    updateBoard(eventData) {
        if (!eventData || !eventData.board_data) return;
        
        const boardData = eventData.board_data;
        
        // Initialize board if needed
        if (!this.board && boardData.board_size) {
            this.size = boardData.board_size;
            this.initializeEmptyBoard();
        }
        
        // Reset all cells to hidden first
        for (let r = 0; r < this.size.rows; r++) {
            for (let c = 0; c < this.size.cols; c++) {
                this.board[r][c] = {
                    state: 'hidden',
                    value: null,
                    flagged: false
                };
            }
        }
        
        // Update revealed cells
        if (boardData.revealed) {
            boardData.revealed.forEach(cell => {
                if (this.board[cell.row] && this.board[cell.row][cell.col]) {
                    this.board[cell.row][cell.col].state = 'revealed';
                    this.board[cell.row][cell.col].value = cell.value;
                }
            });
        }
        
        // Update flagged cells
        if (boardData.flagged) {
            boardData.flagged.forEach(cell => {
                if (this.board[cell.row] && this.board[cell.row][cell.col]) {
                    this.board[cell.row][cell.col].flagged = true;
                }
            });
        }
        
        // Highlight last move if provided
        if (eventData.last_move) {
            this.highlightLastMove(eventData.last_move);
        }
        
        this.render();
    }
    
    initializeEmptyBoard() {
        this.board = [];
        for (let r = 0; r < this.size.rows; r++) {
            this.board[r] = [];
            for (let c = 0; c < this.size.cols; c++) {
                this.board[r][c] = {
                    state: 'hidden',
                    value: null,
                    flagged: false
                };
            }
        }
    }

    highlightLastMove(moveData) {
        // Temporarily highlight the last move
        const { row, col, action } = moveData;
        const cell = this.boardElement?.querySelector(`td[data-row="${row}"][data-col="${col}"]`);
        
        if (cell) {
            cell.classList.add('last-move');
            setTimeout(() => {
                cell.classList.remove('last-move');
            }, 1000);
        }
    }

    render() {
        if (!this.boardElement || !this.board) return;
        
        // Clear board
        this.boardElement.innerHTML = '';
        
        // Create cells
        for (let row = 0; row < this.size.rows; row++) {
            const tr = document.createElement('tr');
            
            for (let col = 0; col < this.size.cols; col++) {
                const td = document.createElement('td');
                const cell = this.board[row][col];
                
                td.dataset.row = row;
                td.dataset.col = col;
                
                if (cell.state === 'revealed') {
                    td.classList.add('revealed');
                    
                    if (cell.value === -1) {
                        // Mine
                        td.classList.add('bomb');
                        td.textContent = 'X';
                    } else if (cell.value === 0) {
                        // Empty
                        td.textContent = '';
                    } else if (cell.value > 0) {
                        // Number
                        td.textContent = cell.value;
                        td.dataset.adjBombs = cell.value;
                    }
                } else if (cell.flagged) {
                    td.classList.add('flagged');
                } else {
                    // Hidden
                    td.classList.add('hidden');
                }
                
                tr.appendChild(td);
            }
            
            this.boardElement.appendChild(tr);
        }
    }
}

// Initialize visualization when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.minesweeperViz = new MinesweeperVisualization();
});

// Connect to event stream updates
window.addEventListener('event-stream-update', (event) => {
    const { type, data } = event.detail;
    
    // Dispatch specific events based on type
    if (type === 'game_started') {
        document.dispatchEvent(new CustomEvent('game-started', { detail: data }));
    } else if (type === 'board_update') {
        document.dispatchEvent(new CustomEvent('board-update', { detail: data }));
    } else if (type === 'move_completed') {
        document.dispatchEvent(new CustomEvent('move-completed', { detail: data }));
    }
});