/**
 * Simple Minesweeper implementation for Vercel AI SDK
 */

export interface MinesweeperConfig {
  rows: number;
  cols: number;
  mines: number;
}

export class SimpleMinesweeper {
  rows: number;
  cols: number;
  mines: number;
  board: number[][];
  visible: boolean[][];
  flags: boolean[][];
  game_over: boolean = false;
  won: boolean = false;
  moves: number = 0;
  private mine_positions: Set<string> = new Set();
  
  constructor(rows: number, cols: number, mines: number) {
    this.rows = rows;
    this.cols = cols;
    this.mines = mines;
    this.board = Array(rows).fill(null).map(() => Array(cols).fill(0));
    this.visible = Array(rows).fill(null).map(() => Array(cols).fill(false));
    this.flags = Array(rows).fill(null).map(() => Array(cols).fill(false));
    
    // Place mines
    this.placeMines();
    // Calculate numbers
    this.calculateNumbers();
  }
  
  private placeMines() {
    let placed = 0;
    while (placed < this.mines) {
      const row = Math.floor(Math.random() * this.rows);
      const col = Math.floor(Math.random() * this.cols);
      const key = `${row},${col}`;
      
      if (!this.mine_positions.has(key)) {
        this.mine_positions.add(key);
        this.board[row][col] = -1;
        placed++;
      }
    }
  }
  
  private calculateNumbers() {
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        if (this.board[r][c] === -1) continue;
        
        let count = 0;
        for (let dr = -1; dr <= 1; dr++) {
          for (let dc = -1; dc <= 1; dc++) {
            if (dr === 0 && dc === 0) continue;
            const nr = r + dr;
            const nc = c + dc;
            if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols) {
              if (this.board[nr][nc] === -1) count++;
            }
          }
        }
        this.board[r][c] = count;
      }
    }
  }
  
  reveal(row: number, col: number): { valid: boolean; message: string } {
    if (this.game_over) {
      return { valid: false, message: "Game is over" };
    }
    
    if (row < 0 || row >= this.rows || col < 0 || col >= this.cols) {
      return { valid: false, message: "Invalid position" };
    }
    
    if (this.visible[row][col]) {
      return { valid: false, message: "Cell already revealed" };
    }
    
    if (this.flags[row][col]) {
      return { valid: false, message: "Cell is flagged" };
    }
    
    this.moves++;
    this.visible[row][col] = true;
    
    if (this.board[row][col] === -1) {
      this.game_over = true;
      this.won = false;
      return { valid: true, message: "Hit a mine! Game over." };
    }
    
    // Auto-reveal adjacent cells if this is a 0
    if (this.board[row][col] === 0) {
      this.revealAdjacent(row, col);
    }
    
    // Check win condition
    this.checkWin();
    
    return { valid: true, message: "Cell revealed" };
  }
  
  private revealAdjacent(row: number, col: number) {
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const nr = row + dr;
        const nc = col + dc;
        if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols) {
          if (!this.visible[nr][nc] && !this.flags[nr][nc] && this.board[nr][nc] !== -1) {
            this.visible[nr][nc] = true;
            if (this.board[nr][nc] === 0) {
              this.revealAdjacent(nr, nc);
            }
          }
        }
      }
    }
  }
  
  flag(row: number, col: number): { valid: boolean; message: string } {
    if (this.game_over) {
      return { valid: false, message: "Game is over" };
    }
    
    if (row < 0 || row >= this.rows || col < 0 || col >= this.cols) {
      return { valid: false, message: "Invalid position" };
    }
    
    if (this.visible[row][col]) {
      return { valid: false, message: "Cannot flag revealed cell" };
    }
    
    if (this.flags[row][col]) {
      return { valid: false, message: "Cell already flagged" };
    }
    
    this.moves++;
    this.flags[row][col] = true;
    
    // Check win condition
    this.checkWin();
    
    return { valid: true, message: "Cell flagged" };
  }
  
  unflag(row: number, col: number): { valid: boolean; message: string } {
    if (this.game_over) {
      return { valid: false, message: "Game is over" };
    }
    
    if (row < 0 || row >= this.rows || col < 0 || col >= this.cols) {
      return { valid: false, message: "Invalid position" };
    }
    
    if (!this.flags[row][col]) {
      return { valid: false, message: "Cell not flagged" };
    }
    
    this.moves++;
    this.flags[row][col] = false;
    
    return { valid: true, message: "Flag removed" };
  }
  
  analyze_board(focusArea: string): string {
    // Simple board analysis
    let safeCount = 0;
    let flaggedCount = 0;
    let hiddenCount = 0;
    
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        if (this.visible[r][c]) {
          safeCount++;
        } else if (this.flags[r][c]) {
          flaggedCount++;
        } else {
          hiddenCount++;
        }
      }
    }
    
    return `Board analysis: ${safeCount} safe cells revealed, ${flaggedCount} flagged, ${hiddenCount} hidden`;
  }
  
  private checkWin() {
    // Win if all non-mine cells are revealed
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        if (this.board[r][c] !== -1 && !this.visible[r][c]) {
          return;
        }
      }
    }
    
    this.game_over = true;
    this.won = true;
  }
  
  get_coverage(): number {
    let revealed = 0;
    let total = this.rows * this.cols - this.mines;
    
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        if (this.visible[r][c] && this.board[r][c] !== -1) {
          revealed++;
        }
      }
    }
    
    return total > 0 ? revealed / total : 0;
  }
  
  get_board_state(): string {
    const lines: string[] = [];
    
    // Add column headers
    const header = "    " + Array.from({ length: this.cols }, (_, i) => i.toString()).join(" ");
    lines.push(header);
    lines.push("   " + "-".repeat(this.cols * 2 + 1));
    
    for (let r = 0; r < this.rows; r++) {
      const row: string[] = [];
      for (let c = 0; c < this.cols; c++) {
        if (this.flags[r][c]) {
          row.push('🚩');
        } else if (!this.visible[r][c]) {
          row.push('?');
        } else if (this.board[r][c] === -1) {
          row.push('💣');
        } else if (this.board[r][c] === 0) {
          row.push('.');
        } else {
          row.push(this.board[r][c].toString());
        }
      }
      lines.push(`${r.toString().padStart(2)}| ${row.join(" ")}`);
    }
    
    return lines.join('\n');
  }
  
  to_json_state() {
    return {
      rows: this.rows,
      cols: this.cols,
      mines: this.mines,
      board: this.board,
      visible: this.visible,
      flags: this.flags,
      game_over: this.game_over,
      won: this.won,
      moves: this.moves,
      coverage: this.get_coverage()
    };
  }
}