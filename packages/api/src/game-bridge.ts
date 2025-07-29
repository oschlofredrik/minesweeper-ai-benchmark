// Type definitions
type GameType = 'minesweeper' | 'risk' | 'sudoku' | 'number_puzzle';

// Placeholder for SimpleMinesweeper - will be imported from Python
class SimpleMinesweeper {
  rows: number;
  cols: number;
  num_mines: number;
  board: number[][];
  revealed: boolean[][];
  flags: boolean[][];
  game_over: boolean;
  won: boolean;

  constructor(rows: number, cols: number, mines: number) {
    this.rows = rows;
    this.cols = cols;
    this.num_mines = mines;
    this.board = Array(rows).fill(null).map(() => Array(cols).fill(0));
    this.revealed = Array(rows).fill(null).map(() => Array(cols).fill(false));
    this.flags = Array(rows).fill(null).map(() => Array(cols).fill(false));
    this.game_over = false;
    this.won = false;
  }

  reveal(row: number, col: number): { valid: boolean; message: string } {
    // Placeholder implementation
    return { valid: true, message: 'Revealed' };
  }

  flag(row: number, col: number): { valid: boolean; message: string } {
    // Placeholder implementation
    return { valid: true, message: 'Flagged' };
  }
}

export interface GameInstance {
  type: GameType;
  instance: any;
  getState: () => any;
  executeMove: (move: any) => { valid: boolean; message: string };
  isGameOver: () => boolean;
  isWon: () => boolean;
}

export function createGame(gameType: GameType, difficulty: string): GameInstance {
  if (gameType === 'minesweeper') {
    const difficulties = {
      easy: { rows: 9, cols: 9, mines: 10 },
      medium: { rows: 16, cols: 16, mines: 40 },
      hard: { rows: 16, cols: 30, mines: 99 }
    };
    
    const config = difficulties[difficulty as keyof typeof difficulties] || difficulties.medium;
    const game = new SimpleMinesweeper(config.rows, config.cols, config.mines);
    
    return {
      type: 'minesweeper',
      instance: game,
      getState: () => ({
        rows: game.rows,
        cols: game.cols,
        board: game.board,
        revealed: game.revealed,
        flagged: game.flags,
        gameOver: game.game_over,
        won: game.won,
        mineCount: game.num_mines
      }),
      executeMove: (move) => {
        const { action, row, col } = move;
        if (action === 'reveal') {
          return game.reveal(row, col);
        } else if (action === 'flag') {
          return game.flag(row, col);
        }
        return { valid: false, message: 'Invalid action' };
      },
      isGameOver: () => game.game_over,
      isWon: () => game.won
    };
  }
  
  throw new Error(`Unsupported game type: ${gameType}`);
}

export function formatGameStateForAI(game: GameInstance): string {
  if (game.type === 'minesweeper') {
    const state = game.getState();
    const { rows, cols, board, revealed, flagged, mineCount } = state;
    
    let stateStr = `Minesweeper Board (${rows}x${cols}, ${mineCount} mines):\n\n`;
    
    // Add column numbers
    stateStr += '   ';
    for (let c = 0; c < cols; c++) {
      stateStr += c.toString().padStart(3);
    }
    stateStr += '\n';
    
    // Add board
    for (let r = 0; r < rows; r++) {
      stateStr += r.toString().padStart(2) + ' ';
      for (let c = 0; c < cols; c++) {
        if (flagged[r][c]) {
          stateStr += '  F';
        } else if (!revealed[r][c]) {
          stateStr += '  .';
        } else if (board[r][c] === -1) {
          stateStr += '  *';
        } else if (board[r][c] === 0) {
          stateStr += '   ';
        } else {
          stateStr += '  ' + board[r][c];
        }
      }
      stateStr += '\n';
    }
    
    // Add game statistics
    const revealedCount = revealed.flat().filter(Boolean).length;
    const flaggedCount = flagged.flat().filter(Boolean).length;
    const totalCells = rows * cols;
    const safeCells = totalCells - mineCount;
    const progress = (revealedCount / safeCells * 100).toFixed(1);
    
    stateStr += `\nProgress: ${revealedCount}/${safeCells} safe cells revealed (${progress}%)`;
    stateStr += `\nFlags placed: ${flaggedCount}/${mineCount}`;
    
    return stateStr;
  }
  
  throw new Error(`Unsupported game type: ${game.type}`);
}