const { openai } = require('@ai-sdk/openai');
const { generateText } = require('ai');

// Simple Minesweeper game logic (same as evaluate-ai-sdk.js)
class SimpleMinesweeper {
  constructor(rows = 16, cols = 16, mines = 40) {
    this.rows = rows;
    this.cols = cols;
    this.numMines = mines;
    this.board = Array(rows).fill().map(() => Array(cols).fill(0));
    this.revealed = Array(rows).fill().map(() => Array(cols).fill(false));
    this.flags = Array(rows).fill().map(() => Array(cols).fill(false));
    this.mines = new Set();
    this.gameOver = false;
    this.won = false;
    this._placeMines();
    this._calculateNumbers();
  }

  _placeMines() {
    const positions = [];
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        positions.push([r, c]);
      }
    }
    
    // Shuffle and take first numMines positions
    for (let i = positions.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [positions[i], positions[j]] = [positions[j], positions[i]];
    }
    
    for (let i = 0; i < this.numMines; i++) {
      const [r, c] = positions[i];
      this.mines.add(`${r},${c}`);
      this.board[r][c] = -1;
    }
  }

  _calculateNumbers() {
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        if (this.board[r][c] !== -1) {
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
  }

  getVisibleState() {
    const visible = [];
    for (let r = 0; r < this.rows; r++) {
      const row = [];
      for (let c = 0; c < this.cols; c++) {
        if (this.flags[r][c]) {
          row.push('F');
        } else if (!this.revealed[r][c]) {
          row.push('?');
        } else {
          row.push(this.board[r][c].toString());
        }
      }
      visible.push(row);
    }
    return visible;
  }

  reveal(row, col) {
    if (this.gameOver || this.revealed[row][col] || this.flags[row][col]) {
      return { valid: false, message: "Invalid move" };
    }

    this.revealed[row][col] = true;

    if (this.board[row][col] === -1) {
      this.gameOver = true;
      return { valid: true, message: "Hit mine - game over" };
    }

    // Auto-reveal neighbors if cell is 0
    if (this.board[row][col] === 0) {
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          const nr = row + dr;
          const nc = col + dc;
          if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols) {
            if (!this.revealed[nr][nc] && !this.flags[nr][nc]) {
              this.reveal(nr, nc);
            }
          }
        }
      }
    }

    // Check win condition
    const revealedCount = this.revealed.flat().filter(x => x).length;
    if (revealedCount === this.rows * this.cols - this.numMines) {
      this.won = true;
      this.gameOver = true;
      return { valid: true, message: "All safe cells revealed - you won!" };
    }

    return { valid: true, message: "Cell revealed" };
  }

  flag(row, col) {
    if (this.gameOver || this.revealed[row][col]) {
      return { valid: false, message: "Invalid flag" };
    }

    this.flags[row][col] = !this.flags[row][col];
    return { valid: true, message: this.flags[row][col] ? "Cell flagged" : "Cell unflagged" };
  }
}

function getMinesweeperPrompt(game) {
  const state = game.getVisibleState();
  const rows = game.rows;
  const cols = game.cols;
  
  let prompt = `Minesweeper board (${rows}x${cols}):\n\n`;
  
  // Add column numbers
  prompt += "   ";
  for (let c = 0; c < cols; c++) {
    prompt += c.toString().padStart(2, ' ') + " ";
  }
  prompt += "\n";
  
  // Add board with row numbers
  for (let r = 0; r < rows; r++) {
    prompt += r.toString().padStart(2, ' ') + " ";
    for (let c = 0; c < cols; c++) {
      prompt += state[r][c].padStart(2, ' ') + " ";
    }
    prompt += "\n";
  }
  
  prompt += "\nLegend:\n";
  prompt += "? = unrevealed cell (can be revealed or flagged)\n";
  prompt += "F = flagged cell (suspected mine)\n";
  prompt += "0-8 = revealed cell showing number of adjacent mines\n";
  prompt += "-1 = revealed mine (game over)\n";
  prompt += "\nIMPORTANT: You can only reveal cells marked with '?'. Cells showing numbers are already revealed!\n";
  prompt += "\nChoose ONE move. Reply with just: action row col\n";
  prompt += "Example: reveal 3 5\n";
  prompt += "Example: flag 7 2\n";
  
  return prompt;
}

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method === 'GET') {
    return res.status(200).json({
      endpoint: 'play-game-sdk',
      description: 'Simple game playing with AI using Vercel SDK',
      hasApiKey: !!process.env.OPENAI_API_KEY,
      version: 'sdk-v1'
    });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { 
      difficulty = 'easy',
      model = 'gpt-4o-mini',
      max_moves = 50
    } = req.body;

    console.log('[SDK] Starting game with:', { difficulty, model, max_moves });

    // Initialize game
    const difficulties = {
      easy: { rows: 9, cols: 9, mines: 10 },
      medium: { rows: 16, cols: 16, mines: 40 },
      hard: { rows: 16, cols: 30, mines: 99 }
    };
    
    const config = difficulties[difficulty] || difficulties.easy;
    const game = new SimpleMinesweeper(config.rows, config.cols, config.mines);
    
    const moves = [];
    const startTime = Date.now();

    // Play the game
    while (!game.gameOver && moves.length < max_moves) {
      const boardState = game.getVisibleState();
      const prompt = getMinesweeperPrompt(game);
      
      // Log prompt for debugging
      console.log(`[SDK] Move ${moves.length + 1} - Prompt length: ${prompt.length} chars`);
      if (moves.length === 0) {
        console.log(`[SDK] First prompt preview:\n${prompt.substring(0, 300)}...`);
      }
      
      const moveStart = Date.now();
      
      // Use Vercel AI SDK to generate move
      const { text } = await generateText({
        model: openai(model),
        messages: [
          {
            role: 'system',
            content: 'You are an expert Minesweeper player. You must analyze the board carefully and only reveal cells marked with "?". Cells showing numbers (0-8) are already revealed and cannot be acted upon. When you see a number, it indicates how many mines are adjacent to that cell. Use this information to deduce safe cells. Give concise move commands in the format: action row col'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.7,
        maxTokens: 50
      });

      const moveDuration = Date.now() - moveStart;
      console.log(`[SDK] AI response (${moveDuration}ms): ${text}`);

      // Parse move - expecting format like "reveal 3 5"
      const parts = text.toLowerCase().trim().split(/\s+/);
      let action = null;
      let row = null;
      let col = null;

      // Try to find action and coordinates
      for (let i = 0; i < parts.length - 1; i++) {
        if (parts[i] === 'reveal' || parts[i] === 'flag') {
          action = parts[i];
          // Look for two numbers after the action
          for (let j = i + 1; j < parts.length - 1; j++) {
            const num1 = parseInt(parts[j]);
            const num2 = parseInt(parts[j + 1]);
            if (!isNaN(num1) && !isNaN(num2)) {
              row = num1;
              col = num2;
              break;
            }
          }
          if (row !== null) break;
        }
      }

      if (!action || row === null || col === null) {
        console.error(`[SDK] Could not parse AI response: ${text}`);
        throw new Error(`Invalid AI response format: ${text}`);
      }

      // Execute move
      const result = action === 'flag' 
        ? game.flag(row, col)
        : game.reveal(row, col);

      // Record move
      moves.push({
        move_number: moves.length + 1,
        action: action,
        row: row,
        col: col,
        valid: result.valid,
        message: result.message,
        board_state: boardState,
        raw_response: text
      });

      console.log(`[SDK] Move ${moves.length}: ${action} (${row}, ${col}) - ${result.message}`);
      
      // Debug: Show board state sample every 5 moves
      if (moves.length % 5 === 0) {
        const board = game.getVisibleState();
        console.log(`[SDK] Board state sample (first 3 rows):`);
        for (let i = 0; i < Math.min(3, board.length); i++) {
          console.log(`[SDK] Row ${i}: ${board[i].slice(0, 10).join(' ')}...`);
        }
      }
    }

    // Game complete
    const duration = (Date.now() - startTime) / 1000;
    
    const response = {
      game_id: `game_sdk_${Date.now()}`,
      status: 'completed',
      won: game.won,
      total_moves: moves.length,
      duration: duration,
      final_board: game.getVisibleState(),
      moves: moves,
      api_key_used: process.env.OPENAI_API_KEY ? process.env.OPENAI_API_KEY.substring(0, 20) + '...' : 'NO_KEY',
      endpoint_version: 'play-game-sdk-v1'
    };

    console.log(`[SDK] Game complete: ${moves.length} moves, won: ${game.won}, duration: ${duration}s`);
    
    return res.status(200).json(response);

  } catch (error) {
    console.error('[SDK] Error:', error);
    return res.status(500).json({
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
}