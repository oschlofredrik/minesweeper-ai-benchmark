import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { streamText, generateText, tool } from 'ai';
import { z } from 'zod';
import type { ModelConfig, GameType } from '@tilts/shared';
import { createGame, formatGameStateForAI, type GameInstance } from './game-bridge';

// Move schema for Minesweeper
const minesweeperMoveSchema = z.object({
  action: z.enum(['reveal', 'flag']),
  row: z.number().min(0),
  col: z.number().min(0),
  reasoning: z.string().optional()
});

// Tool definition for making moves
const makeMoveTool = tool({
  description: 'Make a move in Minesweeper',
  parameters: minesweeperMoveSchema,
  execute: async (args) => {
    // This will be handled by the game runner
    return { success: true, move: args };
  }
});

// Get the appropriate model based on provider and name
function getModel(provider: string, modelName: string) {
  switch (provider) {
    case 'openai':
      return openai(modelName);
    case 'anthropic':
      return anthropic(modelName);
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}

// Generate the system prompt for Minesweeper
function getMinesweeperSystemPrompt(): string {
  return `You are an expert Minesweeper player. Your goal is to clear the board without hitting any mines.

Game Rules:
- Reveal cells to uncover numbers (indicating adjacent mines) or empty spaces
- Flag cells you believe contain mines
- The game ends when all non-mine cells are revealed (win) or a mine is revealed (loss)

Strategy Tips:
- Start with corners or edges for better information
- Use number clues to deduce mine locations
- Flag confirmed mines to track progress
- When certain about a mine location, flag it before revealing nearby cells

You will receive the game state and should respond with your next move using the makeMove tool.`;
}


// Main evaluation handler
export async function evaluateWithSDK(config: {
  gameType: GameType;
  provider: string;
  modelName: string;
  game: GameInstance;
  streamCallback?: (event: any) => void;
}) {
  const { gameType, provider, modelName, game, streamCallback } = config;
  
  if (gameType !== 'minesweeper') {
    throw new Error(`Game type ${gameType} not yet supported`);
  }
  
  const model = getModel(provider, modelName);
  const systemPrompt = getMinesweeperSystemPrompt();
  const gameStateStr = formatGameStateForAI(game);
  
  // Use streaming for real-time updates
  if (streamCallback) {
    const result = await streamText({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: gameStateStr }
      ],
      tools: {
        makeMove: makeMoveTool
      },
      toolChoice: 'required',
      temperature: 0.7,
      maxTokens: 1000,
      onFinish: ({ text, toolCalls, finishReason }) => {
        streamCallback({
          type: 'finish',
          text,
          toolCalls,
          finishReason
        });
      }
    });
    
    // Stream the response
    for await (const delta of result.textStream) {
      streamCallback({
        type: 'text',
        content: delta
      });
    }
    
    // Get tool calls
    const toolCalls = await result.toolCalls;
    return { toolCalls, text: await result.text };
    
  } else {
    // Non-streaming version for simpler use cases
    const result = await generateText({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: gameStateStr }
      ],
      tools: {
        makeMove: makeMoveTool
      },
      toolChoice: 'required',
      temperature: 0.7,
      maxTokens: 1000
    });
    
    return {
      toolCalls: result.toolCalls,
      text: result.text
    };
  }
}

// Run a complete game evaluation
export async function runGameEvaluation(config: {
  gameType: GameType;
  provider: string;
  modelName: string;
  difficulty: string;
  gameId: string;
  onUpdate?: (update: any) => void;
}) {
  const { gameType, provider, modelName, difficulty, gameId, onUpdate } = config;
  
  // Initialize game based on type and difficulty
  const game = await initializeGame(gameType, difficulty);
  const moves = [];
  let moveCount = 0;
  const maxMoves = 200;
  
  // Send initial state
  if (onUpdate) {
    onUpdate({
      type: 'gameStart',
      gameId,
      gameType,
      difficulty,
      initialState: getGameState(game)
    });
  }
  
  // Play until game over or max moves
  while (!game.isGameOver() && moveCount < maxMoves) {
    try {
      // Get AI move
      const result = await evaluateWithSDK({
        gameType,
        provider,
        modelName,
        game,
        streamCallback: onUpdate ? (event) => {
          onUpdate({
            ...event,
            type: `move_${event.type}`,
            moveNumber: moveCount + 1
          });
        } : undefined
      });
      
      // Extract move from tool calls
      const moveCall = result.toolCalls?.find(tc => tc.toolName === 'makeMove');
      if (!moveCall) {
        throw new Error('No move returned by AI');
      }
      
      const move = moveCall.args as z.infer<typeof minesweeperMoveSchema>;
      
      // Execute move
      const moveResult = game.executeMove(move);
      
      moves.push({
        moveNumber: moveCount + 1,
        action: move.action,
        row: move.row,
        col: move.col,
        reasoning: move.reasoning,
        result: moveResult,
        timestamp: new Date().toISOString()
      });
      
      // Send move update
      if (onUpdate) {
        onUpdate({
          type: 'moveComplete',
          moveNumber: moveCount + 1,
          move,
          result: moveResult,
          gameState: game.getState()
        });
      }
      
      moveCount++;
      
    } catch (error) {
      console.error('Error during move:', error);
      if (onUpdate) {
        onUpdate({
          type: 'error',
          error: error.message,
          moveNumber: moveCount + 1
        });
      }
      break;
    }
  }
  
  // Game complete
  const finalState = game.getState();
  const result = {
    gameId,
    gameType,
    provider,
    modelName,
    difficulty,
    moves,
    totalMoves: moveCount,
    won: game.isWon(),
    gameOver: game.isGameOver(),
    duration: moves[moves.length - 1]?.timestamp ? 
      new Date(moves[moves.length - 1].timestamp).getTime() - new Date(moves[0].timestamp).getTime() : 0,
    finalState
  };
  
  if (onUpdate) {
    onUpdate({
      type: 'gameComplete',
      result
    });
  }
  
  return result;
}

// Helper functions using actual game logic
async function initializeGame(gameType: GameType, difficulty: string): Promise<GameInstance> {
  return createGame(gameType, difficulty);
}

function getGameState(game: GameInstance) {
  return game.getState();
}