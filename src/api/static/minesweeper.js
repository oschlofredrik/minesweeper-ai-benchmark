// Minesweeper Game - Adapted for Tilts

class Cell {
    constructor(row, col) {
        this.row = row;
        this.col = col;
        this.bomb = false;
        this.revealed = false;
        this.flagged = false;
        this.adjBombs = 0;
    }

    getAdjCells(board) {
        const adj = [];
        const lastRow = board.length - 1;
        const lastCol = board[0].length - 1;
        
        // All 8 adjacent positions
        const positions = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],           [0, 1],
            [1, -1], [1, 0], [1, 1]
        ];
        
        positions.forEach(([dRow, dCol]) => {
            const newRow = this.row + dRow;
            const newCol = this.col + dCol;
            if (newRow >= 0 && newRow <= lastRow && newCol >= 0 && newCol <= lastCol) {
                adj.push(board[newRow][newCol]);
            }
        });
        
        return adj;
    }

    calcAdjBombs(board) {
        const adjCells = this.getAdjCells(board);
        this.adjBombs = adjCells.reduce((acc, cell) => acc + (cell.bomb ? 1 : 0), 0);
    }

    reveal(board, game) {
        if (this.revealed || this.flagged) return false;
        
        this.revealed = true;
        game.cellsRevealed++;
        
        if (this.bomb) {
            game.gameOver = true;
            return true;
        }
        
        // Auto-reveal adjacent cells if no adjacent bombs
        if (this.adjBombs === 0) {
            const adj = this.getAdjCells(board);
            adj.forEach(cell => {
                if (!cell.revealed && !cell.flagged) {
                    cell.reveal(board, game);
                }
            });
        }
        
        // Check win condition
        if (game.cellsRevealed === (game.size * game.size - game.bombCount)) {
            game.gameWon = true;
            game.gameOver = true;
        }
        
        return false;
    }

    flag() {
        if (!this.revealed) {
            this.flagged = !this.flagged;
            return this.flagged;
        }
        return false;
    }
}

class MinesweeperGame {
    constructor() {
        this.board = [];
        this.size = 9;
        this.bombCount = 10;
        this.gameOver = false;
        this.gameWon = false;
        this.startTime = null;
        this.timerInterval = null;
        this.cellsRevealed = 0;
        this.flagsPlaced = 0;
        
        this.initializeElements();
        this.bindEvents();
        this.newGame();
    }

    initializeElements() {
        this.boardElement = document.getElementById('minesweeper-board');
        this.timeElement = document.getElementById('game-time');
        this.minesElement = document.getElementById('mines-count');
        this.flagsElement = document.getElementById('flags-count');
        this.newGameBtn = document.getElementById('new-game-btn');
        this.startEvalBtn = document.getElementById('start-eval-btn');
        
        // Difficulty buttons
        this.easyBtn = document.getElementById('diff-easy');
        this.mediumBtn = document.getElementById('diff-medium');
        this.hardBtn = document.getElementById('diff-hard');
    }

    bindEvents() {
        // New game button
        this.newGameBtn?.addEventListener('click', () => this.newGame());
        
        // Start evaluation button (opens modal)
        this.startEvalBtn?.addEventListener('click', () => this.openEvalModal());
        
        // Difficulty buttons
        this.easyBtn?.addEventListener('click', () => this.setDifficulty(9, 10));
        this.mediumBtn?.addEventListener('click', () => this.setDifficulty(16, 40));
        this.hardBtn?.addEventListener('click', () => this.setDifficulty(24, 99));
        
        // Board click handlers
        this.boardElement?.addEventListener('click', (e) => this.handleCellClick(e));
        this.boardElement?.addEventListener('contextmenu', (e) => this.handleRightClick(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.shiftKey && e.target.tagName === 'TD') {
                this.handleRightClick(e);
            }
        });
    }

    setDifficulty(size, bombs) {
        this.size = size;
        this.bombCount = bombs;
        this.newGame();
        
        // Update button states
        document.querySelectorAll('.difficulty-buttons button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        if (size === 9) this.easyBtn?.classList.add('active');
        else if (size === 16) this.mediumBtn?.classList.add('active');
        else if (size === 24) this.hardBtn?.classList.add('active');
    }

    newGame() {
        // Reset game state
        this.board = [];
        this.gameOver = false;
        this.gameWon = false;
        this.cellsRevealed = 0;
        this.flagsPlaced = 0;
        
        // Clear timer
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        this.startTime = null;
        
        // Create board
        this.createBoard();
        this.placeBombs();
        this.calculateNumbers();
        this.render();
        
        // Update counters
        this.updateCounters();
    }

    createBoard() {
        this.board = [];
        for (let row = 0; row < this.size; row++) {
            this.board[row] = [];
            for (let col = 0; col < this.size; col++) {
                this.board[row][col] = new Cell(row, col);
            }
        }
    }

    placeBombs() {
        let bombsPlaced = 0;
        while (bombsPlaced < this.bombCount) {
            const row = Math.floor(Math.random() * this.size);
            const col = Math.floor(Math.random() * this.size);
            
            if (!this.board[row][col].bomb) {
                this.board[row][col].bomb = true;
                bombsPlaced++;
            }
        }
    }

    calculateNumbers() {
        for (let row = 0; row < this.size; row++) {
            for (let col = 0; col < this.size; col++) {
                if (!this.board[row][col].bomb) {
                    this.board[row][col].calcAdjBombs(this.board);
                }
            }
        }
    }

    render() {
        if (!this.boardElement) return;
        
        // Clear board
        this.boardElement.innerHTML = '';
        
        // Create cells
        for (let row = 0; row < this.size; row++) {
            const tr = document.createElement('tr');
            
            for (let col = 0; col < this.size; col++) {
                const td = document.createElement('td');
                const cell = this.board[row][col];
                
                td.dataset.row = row;
                td.dataset.col = col;
                
                if (cell.revealed) {
                    td.classList.add('revealed');
                    
                    if (cell.bomb) {
                        td.classList.add('bomb');
                        td.textContent = 'X';
                    } else if (cell.adjBombs > 0) {
                        td.textContent = cell.adjBombs;
                        td.dataset.adjBombs = cell.adjBombs;
                    }
                } else if (cell.flagged) {
                    td.classList.add('flagged');
                }
                
                tr.appendChild(td);
            }
            
            this.boardElement.appendChild(tr);
        }
    }

    handleCellClick(e) {
        if (e.target.tagName !== 'TD' || this.gameOver) return;
        
        const row = parseInt(e.target.dataset.row);
        const col = parseInt(e.target.dataset.col);
        const cell = this.board[row][col];
        
        // Start timer on first click
        if (!this.startTime) {
            this.startTimer();
        }
        
        // Reveal cell
        const hitBomb = cell.reveal(this.board, this);
        
        if (hitBomb) {
            this.endGame(false);
        } else if (this.gameWon) {
            this.endGame(true);
        }
        
        this.render();
        this.updateCounters();
    }

    handleRightClick(e) {
        e.preventDefault();
        
        if (e.target.tagName !== 'TD' || this.gameOver) return;
        
        const row = parseInt(e.target.dataset.row);
        const col = parseInt(e.target.dataset.col);
        const cell = this.board[row][col];
        
        const wasFlagged = cell.flagged;
        cell.flag();
        
        if (cell.flagged && !wasFlagged) {
            this.flagsPlaced++;
        } else if (!cell.flagged && wasFlagged) {
            this.flagsPlaced--;
        }
        
        this.render();
        this.updateCounters();
    }

    startTimer() {
        this.startTime = Date.now();
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            if (this.timeElement) {
                this.timeElement.textContent = String(elapsed).padStart(3, '0');
            }
        }, 100);
    }

    updateCounters() {
        if (this.minesElement) {
            this.minesElement.textContent = String(this.bombCount - this.flagsPlaced).padStart(3, '0');
        }
        if (this.flagsElement) {
            this.flagsElement.textContent = String(this.flagsPlaced).padStart(3, '0');
        }
        if (this.timeElement && !this.startTime) {
            this.timeElement.textContent = '000';
        }
    }

    endGame(won) {
        this.gameOver = true;
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        // Reveal all bombs if lost
        if (!won) {
            for (let row = 0; row < this.size; row++) {
                for (let col = 0; col < this.size; col++) {
                    if (this.board[row][col].bomb) {
                        this.board[row][col].revealed = true;
                    }
                }
            }
        }
        
        this.render();
        
        // Show game over message
        setTimeout(() => {
            const message = won ? 'You won!' : 'Game over!';
            // Could show a modal or update status
            console.log(message);
        }, 100);
    }

    openEvalModal() {
        const modal = document.getElementById('eval-modal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    getBoardState() {
        // Export board state for AI evaluation
        const state = [];
        for (let row = 0; row < this.size; row++) {
            state[row] = [];
            for (let col = 0; col < this.size; col++) {
                const cell = this.board[row][col];
                if (cell.revealed) {
                    if (cell.bomb) {
                        state[row][col] = 'X';
                    } else if (cell.adjBombs === 0) {
                        state[row][col] = '.';
                    } else {
                        state[row][col] = cell.adjBombs.toString();
                    }
                } else if (cell.flagged) {
                    state[row][col] = 'F';
                } else {
                    state[row][col] = '?';
                }
            }
        }
        return state;
    }
}

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.minesweeperGame = new MinesweeperGame();
});