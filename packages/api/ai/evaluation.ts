import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { streamText, tool, CoreMessage } from 'ai';
import { z } from 'zod';
import { createClient } from '@supabase/supabase-js';
import { 
  GameType, 
  GameDifficulty, 
  ModelProvider,
  getMoveSchema 
} from '../../shared/dist/index.js';

// Initialize Supabase
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

export interface GameConfig {
  gameType: GameType;
  provider: ModelProvider;
  modelName: string;
  difficulty: GameDifficulty;
  sessionId?: string;
}

// Process a game move
async function processMove(_gameType: string, _move: any, gameState: any) {
  // This would integrate with the Python game engine
  // For now, return a mock response
  return {
    success: true,
    newState: gameState,
    gameOver: false,
    won: false
  };
}

// Analyze current game state
async function analyzeGameState(gameType: string, _gameState: any, _detail: string) {
  // Game-specific analysis logic
  return {
    analysis: `Current game state analysis for ${gameType}`,
    suggestions: [],
    riskLevel: 'medium'
  };
}

// Build game-specific messages
function buildGameMessages(config: GameConfig, gameState: any): CoreMessage[] {
  const systemPrompt = getSystemPrompt(config.gameType);
  const gameStateDescription = formatGameState(config.gameType, gameState);
  
  return [
    {
      role: 'system',
      content: systemPrompt
    },
    {
      role: 'user',
      content: gameStateDescription
    }
  ];
}

// Get system prompt for game type
function getSystemPrompt(gameType: string): string {
  switch (gameType) {
    case 'minesweeper':
      return `You are an expert Minesweeper player. Analyze the board carefully and make strategic moves.
Always explain your reasoning before making a move. Consider:
- Numbers indicate adjacent mines
- Use logic to deduce safe cells
- Flag cells you're certain contain mines`;
    
    case 'risk':
      return `You are a strategic Risk player. Analyze the board and make tactical decisions.
Consider territory control, reinforcement placement, and attack strategies.`;
    
    default:
      return `You are an expert game player. Analyze the game state and make optimal moves.`;
  }
}

// Format game state for AI
function formatGameState(_gameType: GameType, gameState: any): string {
  // This would format the game state appropriately
  // For now, return JSON representation
  return `Current game state:\n${JSON.stringify(gameState, null, 2)}`;
}

// Broadcast game update via Supabase
async function broadcastGameUpdate(sessionId: string, update: any) {
  if (!sessionId) return;
  
  await supabase
    .from('realtime_events')
    .insert({
      channel: `game:${sessionId}`,
      event: 'game_update',
      data: update,
      created_at: new Date().toISOString()
    });
}

// Main evaluation function using Vercel AI SDK
export async function runGameEvaluation(config: GameConfig, gameState: any) {
  // Select the appropriate model
  const model = config.provider === 'openai' 
    ? openai(config.modelName)
    : anthropic(config.modelName);

  // Define game-specific tools
  const gameTools = {
    makeMove: tool({
      description: 'Make a move in the game',
      parameters: getMoveSchema(config.gameType) || z.object({ action: z.string(), data: z.any() }),
      execute: async (move) => {
        const result = await processMove(config.gameType, move, gameState);
        if (config.sessionId) {
          await broadcastGameUpdate(config.sessionId, {
            move,
            result,
            timestamp: new Date().toISOString()
          });
        }
        return result;
      }
    }),
    analyzeBoard: tool({
      description: 'Analyze current game state in detail',
      parameters: z.object({
        detail: z.enum(['basic', 'detailed', 'strategic'])
      }),
      execute: async ({ detail }) => {
        return analyzeGameState(config.gameType, gameState, detail);
      }
    })
  };

  // Stream the game evaluation
  const result = await streamText({
    model: model as any,
    messages: buildGameMessages(config, gameState),
    tools: gameTools,
    toolChoice: 'required', // Force the model to use tools
    maxSteps: 50, // Allow up to 50 moves per game
    onStepFinish: async (event) => {
      // Log each step for debugging
      console.log('Step completed:', {
        text: event.text,
        toolCalls: event.toolCalls,
        toolResults: event.toolResults
      });
      
      // Broadcast progress
      if (config.sessionId) {
        await broadcastGameUpdate(config.sessionId, {
          type: 'step_complete',
          step: event,
          timestamp: new Date().toISOString()
        });
      }
    }
  });

  return result;
}

// Simplified evaluation for quick games
export async function runQuickEvaluation(
  gameType: string,
  provider: string,
  modelName: string,
  numGames: number
) {
  const results = [];
  
  for (let i = 0; i < numGames; i++) {
    // Initialize game state (would come from Python game engine)
    const gameState = { gameNumber: i + 1, board: [] };
    
    const config: GameConfig = {
      gameType: gameType as GameType,
      provider: provider as 'openai' | 'anthropic',
      modelName,
      difficulty: 'intermediate' as GameDifficulty
    };
    
    try {
      const evaluation = await runGameEvaluation(config, gameState);
      results.push({
        gameNumber: i + 1,
        success: true,
        result: evaluation
      });
    } catch (error: any) {
      results.push({
        gameNumber: i + 1,
        success: false,
        error: error.message
      });
    }
  }
  
  return results;
}