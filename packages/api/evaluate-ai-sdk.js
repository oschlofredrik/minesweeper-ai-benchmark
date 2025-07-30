const { openai } = require('@ai-sdk/openai');
const { generateText } = require('ai');

// Simple Minesweeper game logic
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
  let prompt = `Current Minesweeper game state (${game.rows}x${game.cols} with ${game.numMines} mines):\n\n`;
  prompt += "Board (? = unrevealed, F = flagged, numbers = revealed):\n";
  
  // Add column numbers
  prompt += "   ";
  for (let c = 0; c < game.cols; c++) {
    prompt += c.toString().padStart(2, ' ') + " ";
  }
  prompt += "\n";
  
  // Add board with row numbers
  for (let r = 0; r < game.rows; r++) {
    prompt += r.toString().padStart(2, ' ') + " ";
    for (let c = 0; c < game.cols; c++) {
      prompt += state[r][c].padStart(2, ' ') + " ";
    }
    prompt += "\n";
  }
  
  prompt += "\nAnalyze the board and make the best move. Respond with a JSON object containing:\n";
  prompt += '{"action": "reveal" or "flag", "row": number, "col": number, "reasoning": "explanation"}';
  
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
      endpoint: 'evaluate-ai-sdk',
      description: 'Game evaluation using Vercel AI SDK',
      hasApiKey: !!process.env.OPENAI_API_KEY
    });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { 
      game = 'minesweeper',
      provider = 'openai',
      model = 'gpt-4o-mini',
      difficulty = 'easy',
      maxMoves = 5
    } = req.body;

    console.log('[AI-SDK] Starting evaluation with:', { game, provider, model, difficulty, maxMoves });

    // Initialize game
    const difficulties = {
      easy: { rows: 9, cols: 9, mines: 10 },
      medium: { rows: 16, cols: 16, mines: 40 },
      hard: { rows: 16, cols: 30, mines: 99 }
    };
    
    const config = difficulties[difficulty] || difficulties.easy;
    const gameInstance = new SimpleMinesweeper(config.rows, config.cols, config.mines);
    
    const moves = [];
    let moveCount = 0;

    // Play the game
    while (!gameInstance.gameOver && moveCount < maxMoves) {
      const prompt = getMinesweeperPrompt(gameInstance);
      
      console.log(`[AI-SDK] Move ${moveCount + 1}: Generating with ${model}`);
      
      // Use Vercel AI SDK to generate move
      const { text } = await generateText({
        model: openai(model),
        messages: [
          {
            role: 'system',
            content: 'You are an expert Minesweeper player. Analyze the game state and make optimal moves.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.7,
        maxTokens: 200
      });

      console.log(`[AI-SDK] AI response: ${text.substring(0, 100)}...`);

      // Extract move from response
      let move = null;
      try {
        const jsonMatch = text.match(/\{[^}]+\}/);
        if (jsonMatch) {
          move = JSON.parse(jsonMatch[0]);
        }
      } catch (e) {
        console.error('[AI-SDK] Failed to parse move:', e);
      }

      if (!move) {
        console.log('[AI-SDK] Could not extract valid move from AI response');
        break;
      }

      // Execute move
      const result = move.action === 'flag' 
        ? gameInstance.flag(move.row, move.col)
        : gameInstance.reveal(move.row, move.col);

      moves.push({
        moveNumber: moveCount + 1,
        action: move.action,
        position: { row: move.row, col: move.col },
        reasoning: move.reasoning || '',
        valid: result.valid,
        message: result.message,
        boardState: gameInstance.getVisibleState()
      });

      moveCount++;
      console.log(`[AI-SDK] Move ${moveCount}: ${move.action} at (${move.row}, ${move.col}) - ${result.message}`);
    }

    const response = {
      evaluationId: `ai-sdk-${Date.now()}`,
      status: 'completed',
      gameOver: gameInstance.gameOver,
      won: gameInstance.won,
      totalMoves: moves.length,
      moves: moves,
      finalBoard: gameInstance.getVisibleState()
    };

    console.log(`[AI-SDK] Evaluation complete: ${moves.length} moves, won: ${gameInstance.won}`);
    
    return res.status(200).json(response);

  } catch (error) {
    console.error('[AI-SDK] Error:', error);
    return res.status(500).json({
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
}