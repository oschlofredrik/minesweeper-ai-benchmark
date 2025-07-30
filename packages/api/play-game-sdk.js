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
    
    // Debug: Log critical mine positions
    console.log('[DEBUG] Board generation complete:');
    if (this.mines.has('3,0')) {
      console.log('[DEBUG] ⚠️  Mine placed at (3,0)');
    }
    // Log first column mine distribution
    let firstColMines = 0;
    for (let r = 0; r < Math.min(5, this.rows); r++) {
      if (this.mines.has(`${r},0`)) {
        firstColMines++;
      }
    }
    console.log(`[DEBUG] Mines in first column (rows 0-4): ${firstColMines}`);
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
    prompt += r.toString().padStart(2, ' ') + " |";
    for (let c = 0; c < cols; c++) {
      const cell = state[r][c];
      // Make the board more readable with consistent spacing and clear symbols
      if (cell === '?') {
        prompt += " ? ";  // Unrevealed
      } else if (cell === 'F') {
        prompt += " F ";  // Flagged
      } else if (cell === '0') {
        prompt += " . ";  // Empty (0 mines nearby)
      } else if (cell === '-1') {
        prompt += " * ";  // Mine (game over)
      } else {
        prompt += ` ${cell} `;  // Number 1-8
      }
    }
    prompt += "|\n";
  }
  
  // Add bottom border
  prompt += "   +";
  for (let c = 0; c < cols; c++) {
    prompt += "---";
  }
  prompt += "+\n";
  
  prompt += "\nLegend:\n";
  prompt += "? = unrevealed cell (can be revealed or flagged)\n";
  prompt += "F = flagged cell (suspected mine)\n";
  prompt += ". = empty cell (0 mines nearby)\n";
  prompt += "1-8 = number of mines in adjacent cells\n";
  prompt += "* = revealed mine (game over)\n";
  prompt += "\nIMPORTANT RULES:\n";
  prompt += "1. You can only reveal cells marked with '?'. Cells showing numbers are already revealed!\n";
  prompt += "2. When a cell shows a number N, it means exactly N mines are in the 8 adjacent cells.\n";
  prompt += "3. If a revealed cell with number N has exactly N unrevealed neighbors, ALL of them are mines - flag them!\n";
  prompt += "4. If a revealed cell with number N already has N flagged neighbors, all other neighbors are safe to reveal.\n";
  prompt += "5. NEVER reveal a cell that must be a mine based on adjacent numbers!\n";
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
    
    // Capture initial board state
    const initialBoardState = game.getVisibleState();
    console.log(`[SDK] Initial board state captured`);

    // Play the game
    while (!game.gameOver && moves.length < max_moves) {
      const boardStateBeforeMove = game.getVisibleState();
      const prompt = getMinesweeperPrompt(game);
      
      // Log prompt for debugging
      console.log(`[SDK] Move ${moves.length + 1} - Prompt length: ${prompt.length} chars`);
      if (moves.length === 0) {
        console.log(`[SDK] First prompt preview:\n${prompt.substring(0, 300)}...`);
      } else if (moves.length === 1) {
        // Log second prompt to see if board updated
        console.log(`[SDK] Second move - FULL board state being sent to AI:`);
        // Show first 5 rows of the board for debugging
        const lines = prompt.split('\n');
        for (let i = 0; i < Math.min(20, lines.length); i++) {
          if (lines[i].includes('|') || lines[i].includes('Legend:')) {
            console.log(`[SDK] ${lines[i]}`);
          }
        }
      }
      
      const moveStart = Date.now();
      
      // Check if this is a reasoning model (O3/O1 series)
      const isReasoningModel = model.includes('o3') || model.includes('o1');
      
      // Prepare model settings
      const modelSettings = {
        model: openai(model),
        messages: [
          {
            role: 'system',
            content: isReasoningModel 
              ? 'You are playing Minesweeper. Analyze the board and choose the safest move. Reply with just: action row col'
              : `You are an expert Minesweeper player. CRITICAL RULES:
1. ALWAYS analyze ALL revealed numbers before making a move
2. If a revealed cell shows "1" and has only ONE unrevealed neighbor, that neighbor IS A MINE - NEVER reveal it!
3. If a revealed cell shows "2" and has only TWO unrevealed neighbors, both ARE MINES
4. Before revealing ANY cell, check ALL adjacent revealed numbers to ensure it's safe
5. Example: If cell (2,0) shows "1" and its only unrevealed neighbor is (3,0), then (3,0) is a mine!
6. Only reveal cells that are PROVEN SAFE by the numbers
7. When starting, prefer corners and edges that are far from revealed numbers
Give concise move commands in the format: action row col`
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        maxTokens: 50
      };
      
      // Add reasoning-specific parameters
      if (isReasoningModel) {
        modelSettings.reasoningEffort = 'medium'; // Can be 'low', 'medium', or 'high'
        // O3 models don't support temperature
      } else {
        modelSettings.temperature = 0.2; // Lower temperature for more careful play
      }
      
      // Use Vercel AI SDK to generate move
      const response = await generateText(modelSettings);
      let text = response.text || '';
      
      // Log reasoning tokens if available
      if (isReasoningModel && response.usage?.reasoningTokens) {
        console.log(`[SDK] Reasoning tokens used: ${response.usage.reasoningTokens}`);
      }

      const moveDuration = Date.now() - moveStart;
      console.log(`[SDK] AI response (${moveDuration}ms): ${text}`);
      
      // Check for empty response
      if (!text || text.trim() === '') {
        console.error(`[SDK] Empty response from ${model}. This may happen with reasoning models.`);
        if (isReasoningModel) {
          console.log(`[SDK] Retrying with simpler prompt...`);
          // Retry with even simpler prompt for reasoning models
          const retryResponse = await generateText({
            model: openai(model),
            messages: [{
              role: 'user',
              content: `${prompt}\n\nChoose your move. Format: action row col`
            }],
            reasoningEffort: 'low',
            maxTokens: 20
          });
          text = retryResponse.text || '';
          console.log(`[SDK] Retry response: ${text}`);
        }
        if (!text || text.trim() === '') {
          throw new Error('Empty response from AI model');
        }
      }
      
      // Debug: Log what the AI should be seeing
      if (moves.length === 1) {
        // After first move, log critical cells and board analysis
        const visibleBoard = game.getVisibleState();
        console.log(`[SDK] \n=== CRITICAL DEBUG - Move 2 Analysis ===`);
        console.log(`[SDK] Cell at (2,0): ${visibleBoard[2][0]}`);
        console.log(`[SDK] Cell at (3,0): ${visibleBoard[3][0]}`);
        console.log(`[SDK] Cell at (4,0): ${visibleBoard[4][0]}`);
        
        // Check if (2,0) shows a "1" which would indicate (3,0) is a mine
        if (visibleBoard[2][0] === '1') {
          console.log(`[SDK] WARNING: Cell (2,0) shows '1' - this means (3,0) MUST be a mine!`);
          // Count unrevealed neighbors of (2,0)
          let unrevealedNeighbors = 0;
          const neighbors = [
            [1,0], [1,1], // above
            [2,1],        // right
            [3,0], [3,1]  // below
          ];
          neighbors.forEach(([r,c]) => {
            if (r >= 0 && r < game.rows && c >= 0 && c < game.cols) {
              if (visibleBoard[r][c] === '?') {
                unrevealedNeighbors++;
                console.log(`[SDK]   - Neighbor (${r},${c}) is unrevealed`);
              }
            }
          });
          console.log(`[SDK] Total unrevealed neighbors of (2,0): ${unrevealedNeighbors}`);
          if (unrevealedNeighbors === 1) {
            console.log(`[SDK] CONFIRMED: Only one unrevealed neighbor, so (3,0) is definitely a mine!`);
          }
        }
        
        console.log(`[SDK] AI is about to choose: ${text}`);
        console.log(`[SDK] === END DEBUG ===\n`);
      }

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

      // Get board state AFTER the move
      const boardStateAfterMove = game.getVisibleState();

      // Record move
      moves.push({
        move_number: moves.length + 1,
        action: { action: action },  // Nested to match frontend expectations
        position: { row: row, col: col },  // Object format for position
        valid: result.valid,
        message: result.message,
        board_state: boardStateAfterMove,  // Use board state AFTER move
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
      totalMoves: moves.length,  // Changed to camelCase for frontend compatibility
      duration: duration,
      initialBoard: initialBoardState,  // Add initial board state
      finalBoard: game.getVisibleState(),  // Changed to camelCase
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